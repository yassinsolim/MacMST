#!/usr/bin/env python3
"""Evaluate a local AUX capture; never acquire, transmit, or infer DCP ownership."""

import argparse
import hashlib
import json
import pathlib

import dp_aux_decode as aux
import dp_mst_decode as mst


DECODER_VERSION = "macmst-wire-1"


def qualify_messages(messages):
    pending = {}
    exchanges = []
    unpaired = []
    for message in sorted(messages, key=lambda item: item["end_sequence"]):
        if not message["complete"]:
            unpaired.append(message)
            pending.clear()
            continue
        key = (message["lct"], message["rad"], message["sequence_number"], message["path"], message["broadcast"])
        if message["channel"].endswith("request"):
            key = (message["channel"].split("_")[0],) + key
            if key in pending:
                unpaired.append(pending[key])
            pending[key] = message
            continue
        key = (message["channel"].split("_")[0],) + key
        request = pending.pop(key, None)
        if request is None or request["request_id"] != message["request_id"]:
            unpaired.append(message)
            if request:
                unpaired.append(request)
            continue
        consistent = True
        if message.get("reply_type") == "ACK":
            if message.get("port") is not None and request.get("port") != message["port"]:
                consistent = False
            if message.get("payload_id") is not None and request.get("payload_id") != message["payload_id"]:
                consistent = False
            if request["request_id"] in (0x20, 0x22):
                consistent &= len(bytes.fromhex(message.get("data_hex", ""))) == request.get("length")
            if request["request_id"] == 0x11 and request.get("pbn") != message.get("pbn"):
                consistent = False
        exchanges.append({"request": request, "reply": message,
                          "accepted": consistent and message["reply_type"] == "ACK",
                          "consistent": consistent})
    unpaired.extend(pending.values())
    return exchanges, unpaired


def analyze(capture):
    decoded = aux.decode_capture(capture)
    sideband = mst.from_aux(decoded)
    exchanges, unpaired = qualify_messages(sideband["messages"])
    coverage = capture.get("coverage", {})
    if not isinstance(coverage, dict):
        raise ValueError("Invalid coverage declaration")
    if not isinstance(capture.get("acquisition", {}), dict):
        raise ValueError("Invalid acquisition metadata")
    interval = capture.get("interval", {})
    if not isinstance(interval, dict):
        raise ValueError("Invalid interval")
    start = aux.integer(interval.get("start_ns"), "interval start")
    end = aux.integer(interval.get("end_ns"), "interval end", start)
    if any(not start <= event["timestamp"] <= end for event in decoded["events"]):
        raise ValueError("Event outside declared interval")
    generation = capture.get("capture_generation")
    link = capture.get("physical_link_id")
    if not isinstance(generation, str) or not generation or not isinstance(link, str) or not link:
        raise ValueError("Explicit generation and physical link required")
    loss_intervals = capture.get("loss_intervals", [])
    if not isinstance(loss_intervals, list):
        raise ValueError("Invalid loss intervals")
    for gap in loss_intervals:
        if not isinstance(gap, dict):
            raise ValueError("Invalid loss interval")
        gap_start = aux.integer(gap.get("start_ns"), "gap start", start, end)
        aux.integer(gap.get("end_ns"), "gap end", gap_start, end)
    problems = []
    for field in ("armed_before_attach", "complete", "filters_disabled"):
        if coverage.get(field) is not True:
            problems.append("coverage_" + field + "_not_established")
    if coverage.get("loss_state") != "none" or loss_intervals:
        problems.append("capture_loss_or_unknown_loss")
    if not decoded["events"]:
        problems.append("empty_capture")
    if any(not item["complete"] for item in decoded["transactions"]):
        problems.append("unqualified_aux_transaction")
    if unpaired or any(not item["consistent"] for item in exchanges):
        problems.append("unqualified_sideband_exchange")
    complete = not problems
    completeness = "COMPLETE_FOR_INTERVAL" if complete else "CAPTURE_INCOMPLETE"
    capability = []
    enables = []
    mst_control = []
    slots = []
    act_reads = []
    sink_counts = []
    timeline = []
    operations = []
    coding = None
    for transaction in decoded["transactions"]:
        request, reply = transaction["request"], transaction["reply"]
        item = request or reply
        timeline.append({"timestamp": item["timestamp"], "layer": "AUX", "kind": item["kind"],
                         "sequence": item["sequence"], "command": item.get("aux_command_name"),
                         "address": item.get("address"), "accepted": transaction["accepted"],
                         "complete": transaction["complete"], "reason": transaction["reason"]})
        if not transaction["complete"]:
            operations.append((item["sequence"], "uncertain", None))
            coding = None
        if not transaction["accepted"] or request.get("aux_type") != "native":
            continue
        command, address = request["aux_command"], request["address"]
        data = bytes.fromhex((reply if command == 9 else request)["data_hex"])
        evidence = {"aux_sequences": [request["sequence"], reply["sequence"]],
                    "timestamp": request["timestamp"], "raw_hex": data.hex()}
        if address <= 0x108 < address + len(data):
            coding = {1: "8b10b", 2: "128b132b"}.get(data[0x108 - address])
        if command == 9 and address <= 0x21 < address + len(data):
            capability.append({**evidence, "value": data[0x21 - address]})
        if address <= 0x111 < address + len(data):
            value = data[0x111 - address]
            mst_control.append({**evidence, "command": command, "value": value})
            if value & 1:
                enables.append({**evidence, "value": value, "basis": "state_read" if command == 9 else "acknowledged_write"})
            elif command == 8:
                operations.append((reply["sequence"], "reset", None))
        if command == 8 and address < 0x1c3 and address + len(data) > 0x1c0:
            fields = {"payload_id": None, "start_slot": None, "slot_count": None}
            for register, field in ((0x1c0, "payload_id"), (0x1c1, "start_slot"), (0x1c2, "slot_count")):
                if address <= register < address + len(data):
                    fields[field] = data[register - address]
            slot = {**evidence, **fields, "link_coding": coding}
            slot["qualified"] = (coding == "8b10b" and all(value is not None for value in fields.values()) and
                                 0 < fields["payload_id"] < 128 and 1 <= fields["start_slot"] <= 63 and
                                 0 <= fields["slot_count"] <= 63 and
                                 fields["start_slot"] + fields["slot_count"] <= 64)
            slots.append(slot)
            operations.append((reply["sequence"], "slots", slot))
        if command == 9 and address <= 0x2c0 < address + len(data):
            status = {**evidence, "value": data[0x2c0 - address]}
            act_reads.append(status)
            operations.append((reply["sequence"], "status", status))
        for register in (0x200, 0x2002):
            if command == 9 and address <= register < address + len(data):
                value = data[register - address]
                sink_counts.append({**evidence, "address": register, "raw_value": value,
                                    "count": ((value & 0x80) >> 1) | (value & 0x3f)})
    topologies = []
    remote_requests = []
    resource_requests = []
    resource_replies = []
    allocation_requests = []
    payload_queries = []
    payload_clears = []
    payload_state_problems = []
    notifications = []
    accepted_allocations = []
    for message in sideband["messages"]:
        timeline.append({"timestamp": message["timestamp"], "layer": "MST", "kind": message["channel"],
                         "message_type": message["message_type"], "port": message["port"],
                         "rad": message["rad"], "complete": message["complete"],
                         "errors": message["errors"], "end_sequence": message["end_sequence"]})
        if not message["complete"]:
            operations.append((message["end_sequence"], "uncertain", None))
        if not message["complete"] or not message["channel"].endswith("request"):
            continue
        evidence = {"end_sequence": message["end_sequence"], "timestamp": message["timestamp"],
                    "rad": message["rad"], "port": message["port"], "request_id": message["request_id"]}
        if message["channel"] == "up_request" and message["request_id"] == 2:
            notifications.append({**evidence, "branch_guid": message["branch_guid"],
                                  "ddps": message.get("ddps"), "peer_type": message["peer_type"]})
        if message["channel"] != "down_request":
            continue
        if message["request_id"] in (0x20, 0x21, 0x22, 0x23):
            remote_requests.append({**evidence, "address": message.get("address"),
                                    "i2c_device": message.get("i2c_device"), "length": message.get("length"),
                                    "data_hex": message.get("data_hex"),
                                    "preceding_i2c": message.get("preceding_i2c")})
        elif message["request_id"] == 0x10:
            resource_requests.append(evidence)
        elif message["request_id"] == 0x11:
            allocation_requests.append({**evidence, "payload_id": message["payload_id"], "pbn": message["pbn"]})
    for exchange in exchanges:
        request, reply = exchange["request"], exchange["reply"]
        if not exchange["accepted"] or request["channel"] != "down_request":
            continue
        if request["request_id"] == 1:
            ports = reply.get("ports", [])
            outputs = [port for port in ports if not port["input"]]
            peers = [port for port in outputs if port["peer_type"] != 0 and (port["ddps"] or port["legacy_present"])]
            topologies.append({"rad": reply["rad"], "branch_guid": reply["branch_guid"],
                               "branch_identity_established": bool(reply["branch_guid"] and int(reply["branch_guid"], 16)),
                               "ports": ports, "downstream_port_count": len(outputs), "peer_count": len(peers),
                               "request_sequence": request["end_sequence"], "reply_sequence": reply["end_sequence"]})
        elif request["request_id"] == 0x11:
            allocation = {"rad": request["rad"], "port": request["port"], "payload_id": request["payload_id"],
                          "requested_pbn": request["pbn"], "accepted_pbn": reply["pbn"],
                          "request_sequence": request["end_sequence"], "reply_sequence": reply["end_sequence"]}
            accepted_allocations.append(allocation)
            operations.append((reply["end_sequence"], "allocation", allocation))
        elif request["request_id"] == 0x10:
            resource_replies.append({"rad": request["rad"], "port": request["port"],
                                     "full_pbn": reply["full_pbn"], "available_pbn": reply["available_pbn"],
                                     "fec_capable": reply["fec_capable"],
                                     "request_sequence": request["end_sequence"], "reply_sequence": reply["end_sequence"]})
        elif request["request_id"] == 0x12:
            query = {"rad": request["rad"], "port": request["port"],
                     "payload_id": request["payload_id"], "pbn": reply["pbn"],
                     "request_sequence": request["end_sequence"], "reply_sequence": reply["end_sequence"]}
            payload_queries.append(query)
            operations.append((reply["end_sequence"], "query", query))
        elif request["request_id"] == 0x14:
            payload_clears.append({"rad": request["rad"], "broadcast": request["broadcast"],
                                   "request_sequence": request["end_sequence"], "reply_sequence": reply["end_sequence"]})
            root_clear = request["lct"] == 1 and request["rad"] == ""
            if not root_clear:
                payload_state_problems.append("non_root_clear_scope_unresolved")
            operations.append((reply["end_sequence"], "reset" if root_clear else "uncertain", None))
    for message in unpaired:
        operations.append((message["end_sequence"], "uncertain", None))
    for exchange in exchanges:
        if not exchange["consistent"]:
            operations.append((exchange["reply"]["end_sequence"], "uncertain", None))
    active = {}
    maximum = 0
    table_epoch = 0
    low_act_epoch = None
    act_completions = []
    for sequence, operation, value in sorted(operations, key=lambda item: item[0]):
        if operation in ("reset", "uncertain"):
            active.clear()
            table_epoch = 0
            low_act_epoch = None
        elif operation == "allocation":
            key = (value["rad"], value["port"], value["payload_id"])
            if value["accepted_pbn"] and value["payload_id"]:
                active[key] = value
            else:
                active.pop(key, None)
            maximum = max(maximum, len({key[2] for key in active}))
        elif operation == "query":
            key = (value["rad"], value["port"], value["payload_id"])
            previous = active.get(key, {})
            if previous.get("accepted_pbn", previous.get("pbn", 0)) != value["pbn"]:
                payload_state_problems.append("payload_query_conflicts_with_history")
            if value["pbn"] and value["payload_id"]:
                active[key] = value
            else:
                active.pop(key, None)
            maximum = max(maximum, len({key[2] for key in active}))
        elif operation == "slots":
            table_epoch = table_epoch + 1 if value["qualified"] else 0
            low_act_epoch = None
            if not value["qualified"]:
                payload_state_problems.append("unqualified_slot_write")
            elif value["slot_count"] and value["payload_id"] not in {key[2] for key in active}:
                payload_state_problems.append("unmatched_local_payload_id")
        elif operation == "status":
            if table_epoch and not value["value"] & 2:
                low_act_epoch = table_epoch
            if table_epoch and low_act_epoch == table_epoch and value["value"] & 3 == 3:
                act_completions.append({**value, "table_epoch": table_epoch, "end_sequence": sequence})
                low_act_epoch = None
    edid_paths = sorted({(item["rad"], item["port"]) for item in remote_requests
                         if item["request_id"] == 0x22 and item["i2c_device"] == 0x50})
    payload_complete = complete and coverage.get("initial_payload_table_empty") is True and not payload_state_problems
    mst_enable = ("MST_ENABLE_ESTABLISHED" if enables else
                  "MST_ENABLE_NOT_OBSERVED_IN_COMPLETE_CAPTURE" if complete else "MST_ENABLE_UNRESOLVED")

    def gate(**values):
        return {"completeness": completeness, **values}

    gates = {
        "W1.1": gate(capability_reads=capability),
        "W1.2": gate(result=mst_enable, evidence=enables, control_observations=mst_control),
        "W1.3": gate(complete_messages=sum(message["complete"] for message in sideband["messages"]),
                     rejected_or_partial_messages=sum(not message["complete"] for message in sideband["messages"])),
        "W1.4": gate(topologies=topologies, notifications=notifications),
        "W1.5": gate(remote_accesses=remote_requests, edid_probed_paths=[{"rad": rad, "port": port} for rad, port in edid_paths],
                     edid_probed_path_count=len(edid_paths), edid_contents_validated=False),
        "W1.6": gate(resource_requests=resource_requests, accepted_resources=resource_replies),
        "W1.7": gate(requests=allocation_requests, accepted=accepted_allocations, slots=slots,
                 queries=payload_queries, clears=payload_clears,
                 state_problems=sorted(set(payload_state_problems)),
                 retained_payload_ids_at_end=sorted({key[2] for key in active}),
                     observed_payload_ids=sorted({item["payload_id"] for item in [*accepted_allocations, *payload_queries]
                                                  if item.get("accepted_pbn", item.get("pbn")) and item["payload_id"]}),
                     observed_max_concurrent_ids=maximum,
                     exclusive_max_concurrent_ids=maximum if payload_complete else None,
                     only_one_payload_established=payload_complete and maximum == 1,
                     allocation_history_complete=payload_complete),
        "W1.8": gate(status_reads=act_reads,
                 completion_observed=bool(act_completions) if complete and all(slot["qualified"] for slot in slots) else None,
                     completion_evidence=act_completions, actual_act_packet_observed=False),
        "W1.9": gate(sink_count_reads=sink_counts, result="SOFTWARE_COUNTER_BINDING_UNRESOLVED")}
    analysis = {"schema_version": 1, "capture_id": decoded["capture_id"], "capture_generation": generation,
                "physical_link_id": link, "evidence_kind": capture["evidence_kind"], "decoder_version": DECODER_VERSION,
                "completeness": completeness, "completeness_problems": problems,
                "interval": interval, "loss_intervals": loss_intervals, "gates": gates,
                "hardware_authorized": False, "real_source_ownership_established": False,
                "timeline": sorted(timeline, key=lambda item: (item["timestamp"], item.get("sequence", item.get("end_sequence", -1))))}
    return {"aux": decoded, "mst": sideband, "analysis": analysis}


def json_bytes(value):
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()


def write_bundle(capture_path, destination, decoder_commit=None):
    source = pathlib.Path(capture_path)
    if not source.is_file() or source.is_symlink():
        raise ValueError("Input must be a regular local file")
    with source.open("rb") as stream:
        original = stream.read(aux.MAX_INPUT_BYTES + 1)
    if len(original) > aux.MAX_INPUT_BYTES:
        raise ValueError("Capture exceeds offline input limit")
    capture = aux.parse_capture(original)
    result = analyze(capture)
    output = pathlib.Path(destination).absolute()
    if output.exists() or any(parent.is_symlink() for parent in (output, *output.parents)):
        raise ValueError("Bundle destination must be new and nonsymlinked")
    manifest = {"schema_version": 1, "capture_id": capture["capture_id"],
                "capture_generation": capture["capture_generation"], "evidence_kind": capture["evidence_kind"],
                "physical_link_id": capture["physical_link_id"], "interval": capture["interval"],
                "acquisition": capture.get("acquisition", {}), "coverage": capture.get("coverage", {}),
                "loss_intervals": capture.get("loss_intervals", []), "decoder_commit": decoder_commit,
                "decoder_version": DECODER_VERSION, "raw_file": "raw/capture.json",
                "raw_sha256": hashlib.sha256(original).hexdigest(), "hardware_authorized": False,
                "decoder_source_sha256": {name: hashlib.sha256(pathlib.Path(__file__).with_name(name).read_bytes()).hexdigest()
                                           for name in ("dp_aux_decode.py", "dp_mst_decode.py", "dp_wire_analyze.py")}}
    files = {"raw/capture.json": original, "manifest.json": json_bytes(manifest),
             "aux-events.jsonl": b"".join(json.dumps(item, sort_keys=True).encode() + b"\n" for item in result["aux"]["events"]),
             "mst-events.jsonl": b"".join(json.dumps(item, sort_keys=True).encode() + b"\n" for item in result["mst"]["messages"]),
             "analysis.json": json_bytes(result["analysis"])}
    files["hashes.json"] = json_bytes({name: hashlib.sha256(data).hexdigest() for name, data in files.items()})
    output.mkdir(parents=True, exist_ok=False)
    (output / "raw").mkdir()
    for name, data in files.items():
        with (output / name).open("xb") as stream:
            stream.write(data)
    return result["analysis"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("capture", type=pathlib.Path)
    parser.add_argument("--bundle", type=pathlib.Path)
    parser.add_argument("--decoder-commit")
    parser.add_argument("--timeline", action="store_true")
    arguments = parser.parse_args()
    try:
        result = (write_bundle(arguments.capture, arguments.bundle, arguments.decoder_commit) if arguments.bundle
                  else analyze(aux.load_capture(arguments.capture))["analysis"])
        print(json.dumps(result["timeline"] if arguments.timeline else result, sort_keys=True, indent=2))
    except (ValueError, OSError) as error:
        parser.exit(2, str(error) + "\n")


if __name__ == "__main__":
    main()