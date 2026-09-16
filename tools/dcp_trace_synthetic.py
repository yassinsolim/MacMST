#!/usr/bin/env python3
"""Produce artificial observer records, never an emulation of Apple DCP behavior."""

import argparse
import copy
import hashlib
import pathlib
import sys

if __package__:
    from . import dcp_trace_schema as schema
else:
    import dcp_trace_schema as schema


SCENARIOS = (
    "one_service", "request_reply", "multiple_endpoints", "scoped_request_ids",
    "unknown_opcode", "unknown_service", "raw_body", "zero_length", "maximum_body",
    "wrap_loss", "dropped", "truncated", "malformed", "unrelated_dptx", "two_sources",
    "endpoint_is_source", "two_timings", "two_bindings", "api_space", "wire_vcs",
    "endpoints_one_source", "recreated_source", "sequential_timings", "duplicate_packet",
    "id_generation_reset", "payload_changed", "loss_between_sources", "incomplete_reply",
    "inferred_sources", "ext0_ext1", "duplicate_event",
)


def make_record(sequence=0, scenario="one_service", payload=b"\x00\xff", **changes):
    record = {
        "schema_version": 1, "capture_id": "synthetic-" + scenario,
        "capture_generation": "generation-0", "boot_generation": "boot-0",
        "lifetime_generation": "lifetime-0", "sequence": sequence,
        "timestamp_ns": 1000 + sequence, "timestamp_units": "ns", "clock": "monotonic",
        "kind": "event", "direction": "host_to_dcp", "asc": "synthetic-asc",
        "endpoint": 42, "channel": 7, "service": "synthetic-service", "opcode": 99,
        "request_id": None, "payload_length": len(payload), "declared_payload_length": len(payload),
        "raw_payload": payload.hex(), "record_complete": True, "truncated": False,
        "loss_state": {"status": "none", "dropped_records": 0, "detail": None},
        "producer": {"name": "macmst-synthetic", "version": "1", "commit": "UNKNOWN", "synthetic": True},
        "extensions": {"synthetic": {"scenario": scenario, "notice": "Artificial test data; not Apple DCP behavior."}},
    }
    record.update(changes)
    return record


def annotate(record, assertion="source_context", owner="synthetic-dptx-0", source="synthetic-source-A", **changes):
    annotation = {
        "claim_id": "synthetic-claim-" + str(record["sequence"]), "assertion": assertion,
        "physical_dptx": owner, "source_identity": source, "timing_identity": "UNKNOWN",
        "payload_identity": "UNKNOWN", "confidence": "VERIFIED",
        "evidence": ["Synthetic independent ground truth; not a hardware result."],
        "capture_id": record["capture_id"], "capture_generation": record["capture_generation"],
        "boot_generation": record["boot_generation"], "lifetime_generation": record["lifetime_generation"],
        "simultaneous": True, "independent": True, "coexistence_id": "synthetic-snapshot-0",
        "start_ns": 1000, "end_ns": 2000,
        "provenance": {
            "origin": "synthetic", "mapping_basis": "explicit_contract",
            "method": "Independent synthetic oracle, not inferred from an endpoint/service/port/payload ID.",
            "independently_validated": True,
            "references": [{"capture_id": record["capture_id"], "capture_generation": record["capture_generation"],
                            "sequence": record["sequence"],
                            "payload_sha256": hashlib.sha256(bytes.fromhex(record["raw_payload"])).hexdigest()}],
        },
    }
    annotation.update(changes)
    record["annotations"] = annotation
    return record


def scenario_records(name):
    if name not in SCENARIOS:
        raise ValueError("unknown synthetic scenario")

    def make(sequence=0, **changes):
        return make_record(sequence, scenario=name, **changes)

    if name in ("request_reply", "scoped_request_ids", "id_generation_reset", "incomplete_reply"):
        request = make(kind="request", request_id=7, correlation={"scope": "synthetic-scope", "evidence": "Synthetic pairing contract"})
        reply = make(1, kind="reply", direction="dcp_to_host", request_id=7,
                     correlation={"scope": "synthetic-scope", "evidence": "Synthetic pairing contract"})
        if name == "scoped_request_ids":
            reply["correlation"]["scope"] = "different-scope"
        if name == "id_generation_reset":
            reply.update(sequence=0, timestamp_ns=0, capture_generation="generation-1", boot_generation="boot-1")
        if name == "incomplete_reply":
            reply.update(record_complete=False, truncated=True, declared_payload_length=8,
                         loss_state={"status": "truncated", "dropped_records": None, "detail": "synthetic partial reply"})
        return [request, reply]
    if name == "multiple_endpoints":
        return [make(), make(1, endpoint=43, service="other-synthetic-service")]
    if name == "unknown_opcode":
        return [make(opcode="unknown-0xffff", extensions={"future": {"opaque": [0, None, "raw"]}, "synthetic": True})]
    if name == "unknown_service":
        return [make(service=None)]
    if name == "raw_body":
        return [make(payload=bytes(range(32)), undecoded_extension={"retain": True})]
    if name == "zero_length":
        return [make(payload=b"")]
    if name == "maximum_body":
        return [make(payload=bytes(range(256)) * (schema.MAX_PAYLOAD_BYTES // 256))]
    if name in ("wrap_loss", "dropped"):
        loss = make(1, kind="loss", direction="none", payload=b"",
                    loss_state={"status": "wrapped" if name == "wrap_loss" else "dropped",
                                "dropped_records": None if name == "wrap_loss" else 3,
                                "detail": "synthetic transport loss"})
        tail = make(0, capture_generation="generation-1", timestamp_ns=0) if name == "wrap_loss" else make(5)
        return [make(), loss, tail]
    if name == "truncated":
        return [make(record_complete=False, truncated=True, declared_payload_length=8,
                     loss_state={"status": "truncated", "dropped_records": None, "detail": "synthetic partial body"})]
    if name == "malformed":
        return [make(raw_payload="00")]
    if name == "one_service":
        return [make()]
    first = annotate(make(payload=b"synthetic-A"))
    second = annotate(make(1, payload=b"synthetic-B"), source="synthetic-source-B")
    if name == "api_space":
        first["annotations"].update(assertion="source_api_space", source_identity="UNKNOWN",
                                     source_space=["synthetic-source-A", "synthetic-source-B"], simultaneous=False)
        return [first]
    if name in ("two_timings", "sequential_timings"):
        for index, item in enumerate((first, second)):
            item["annotations"].update(assertion="timing_generator", source_identity="UNKNOWN",
                                        timing_identity="synthetic-timing-" + str(index))
    if name in ("two_bindings", "payload_changed"):
        for index, item in enumerate((first, second)):
            item["annotations"].update(assertion="source_payload_binding", payload_identity="synthetic-payload-" + str(index))
    if name == "wire_vcs":
        for index, item in enumerate((first, second)):
            item["annotations"].update(assertion="wire_vc", source_identity="UNKNOWN",
                                        vc_identity="synthetic-vc-" + str(index), timing_identity="synthetic-timing-" + str(index))
            item["annotations"]["provenance"]["mapping_basis"] = "independent_measurement"
            item["annotations"]["provenance"]["observation_plane"] = "dp_main_link"
    if name in ("unrelated_dptx", "ext0_ext1"):
        first["annotations"]["physical_dptx"] = "synthetic-EXT0"
        second["annotations"]["physical_dptx"] = "synthetic-EXT1"
    if name in ("endpoints_one_source", "recreated_source", "payload_changed"):
        second["annotations"]["source_identity"] = first["annotations"]["source_identity"]
    if name == "endpoints_one_source":
        second["endpoint"] = 43
    if name in ("recreated_source", "sequential_timings"):
        first["annotations"].update(start_ns=1000, end_ns=1001, simultaneous=False)
        second["annotations"].update(start_ns=1001, end_ns=1002, simultaneous=False)
        second["lifetime_generation"] = second["annotations"]["lifetime_generation"] = "recreated-lifetime"
    if name == "endpoint_is_source":
        for index, item in enumerate((first, second)):
            item["endpoint"] = 42 + index
            item["annotations"]["source_identity"] = str(42 + index)
            item["annotations"]["provenance"].update(mapping_basis="heuristic", independently_validated=False,
                                                        method="Misleading endpoint equals source assumption")
    if name == "inferred_sources":
        for item in (first, second):
            item["annotations"]["confidence"] = "INFERRED"
    if name == "duplicate_packet":
        return [first, copy.deepcopy(first)]
    if name == "duplicate_event":
        duplicate = copy.deepcopy(first)
        duplicate.update(sequence=1, timestamp_ns=1001)
        return [first, duplicate]
    if name == "loss_between_sources":
        loss = make(1, kind="loss", direction="none", payload=b"",
                    loss_state={"status": "unknown", "dropped_records": None, "detail": "synthetic unbounded gap"})
        second["sequence"] = second["annotations"]["provenance"]["references"][0]["sequence"] = 2
        second["timestamp_ns"] = 1002
        return [first, loss, second]
    return [first, second]


def encode_scenario(name):
    return "".join(schema.dumps(record) + "\n" for record in scenario_records(name))


def neutral_topology():
    return {"version": 1, "nodes": [{"id": "host", "kind": "mac"},
                                    {"id": "output", "kind": "physical_output", "port_index": 0},
                                    {"id": "hub", "kind": "hub", "label": "Synthetic generic hub"},
                                    {"id": "sink-a", "kind": "sink"}, {"id": "sink-b", "kind": "sink"}],
            "edges": [{"source": "host", "target": "output", "connection_type": "usb-c"},
                      {"source": "output", "target": "hub", "connection_type": "usb-c-dp-alt-mode"},
                      {"source": "hub", "target": "sink-a", "connection_type": "displayport"},
                      {"source": "hub", "target": "sink-b", "connection_type": "displayport"}]}


def write_bundle(root, name):
    if __package__:
        from . import dcp_trace_import as trace
    else:
        import dcp_trace_import as trace
    records = scenario_records(name)
    summary = trace.summarize(records)
    manifest = {"bundle_version": 1, "schema_version": 1, "capture_id": records[0]["capture_id"], "synthetic": True,
                "machine": {"model": "SYNTHETIC", "soc": "SYNTHETIC", "os_version": "SYNTHETIC", "os_build": "SYNTHETIC"},
                "producer": records[0]["producer"], "capture_start": "2000-01-01T00:00:00Z", "capture_end": "2000-01-01T00:00:01Z",
                "observer_configuration": {"synthetic_scenario": name}, "stimulus_description": "Artificial fixture, no hardware activity",
                "topology": neutral_topology(), "tool_commits": {"synthetic": "UNKNOWN"},
                "known_loss": {"reported_dropped_records": summary["reported_dropped_records"], "sequence_gaps": summary["sequence_gaps"],
                               "incomplete_records": sum(not record["record_complete"] for record in records),
                               "loss_count_unknown": summary["loss_count_unknown"]}}
    source = {"kind": "synthetic", "producer": records[0]["producer"], "description": "Artificial records; not captured Apple traffic"}
    contents = {"records.jsonl": encode_scenario(name), "manifest.json": schema.dumps(manifest) + "\n",
                "source-info.json": schema.dumps(source) + "\n"}
    hashes = {"algorithm": "sha256", "files": {path: hashlib.sha256(value.encode()).hexdigest() for path, value in contents.items()}}
    contents["hashes.json"] = schema.dumps(hashes) + "\n"
    root = pathlib.Path(root)
    root.mkdir(parents=True, exist_ok=False)
    for path, content in contents.items():
        with (root / path).open("x", encoding="utf-8") as destination:
            destination.write(content)
    (root / "analysis").mkdir()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scenario", choices=SCENARIOS)
    output = parser.add_mutually_exclusive_group()
    output.add_argument("--output", type=pathlib.Path, help="create a new synthetic JSONL file; never overwrite")
    output.add_argument("--bundle", type=pathlib.Path, help="create a new self-contained synthetic bundle directory")
    arguments = parser.parse_args(argv)
    content = encode_scenario(arguments.scenario)
    try:
        if arguments.bundle:
            write_bundle(arguments.bundle, arguments.scenario)
        elif arguments.output:
            with arguments.output.open("x", encoding="utf-8") as destination:
                destination.write(content)
        else:
            sys.stdout.write(content)
    except (OSError, schema.TraceFormatError) as error:
        parser.error(str(error))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())