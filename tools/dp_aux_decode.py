#!/usr/bin/env python3
"""Offline DisplayPort AUX decoding. This module has no acquisition interface."""

import argparse
import copy
import json
import math
import pathlib
import re
import statistics


SCHEMA_VERSION = 1
DECODER_VERSION = "macmst-aux-1"
MAX_INPUT_BYTES = 16 * 1024 * 1024
MAX_RECORDS = 100000
COMMANDS = {0: "I2C_WRITE", 1: "I2C_READ", 2: "I2C_WRITE_STATUS_UPDATE",
            4: "I2C_WRITE_MOT", 5: "I2C_READ_MOT", 6: "I2C_WRITE_STATUS_UPDATE_MOT",
            8: "NATIVE_WRITE", 9: "NATIVE_READ"}
REPLIES = {0: "ACK", 1: "NACK", 2: "DEFER", 3: "RESERVED"}
DIRECTIONS = {"source_to_sink", "sink_to_source", "unknown"}


def integer(value, name, minimum=0, maximum=2**63 - 1):
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError(f"Invalid {name}")
    return value


def raw_bytes(value):
    if not isinstance(value, str) or len(value) > 8192:
        raise ValueError("Invalid or oversized raw hex")
    try:
        return bytes.fromhex(value)
    except ValueError as error:
        raise ValueError("Invalid raw hex") from error


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON key")
        result[key] = value
    return result


def load_capture(path):
    path = pathlib.Path(path)
    if not path.is_file() or path.is_symlink():
        raise ValueError("Input must be a regular local file")
    with path.open("rb") as stream:
        raw = stream.read(MAX_INPUT_BYTES + 1)
    return parse_capture(raw)


def parse_capture(raw):
    if len(raw) > MAX_INPUT_BYTES:
        raise ValueError("Capture exceeds offline input limit")

    def finite_float(value):
        result = float(value)
        if not math.isfinite(result):
            raise ValueError("Non-finite JSON")
        return result

    try:
        return json.loads(raw, object_pairs_hook=unique_object, parse_float=finite_float,
                          parse_constant=lambda value: (_ for _ in ()).throw(ValueError("Non-finite JSON")))
    except RecursionError as error:
        raise ValueError("JSON nesting exceeds decoder limit") from error


def recover_waveform(record):
    representation = record.get("representation")
    samples = record.get("samples") if representation == "digital_samples" else record.get("symbols")
    if not isinstance(samples, list) or not samples or len(samples) > 2000000:
        raise ValueError("Invalid or oversized waveform")
    if any(type(sample) is not int or sample not in (0, 1) for sample in samples):
        raise ValueError("Waveform must contain binary samples")
    period = integer(record.get("sample_period_ns"), "sample period", 1, 1000)
    if representation == "digital_samples" and period > 100:
        raise ValueError("Digital waveform requires at least 10 MS/s")
    runs = []
    start = 0
    for index in range(1, len(samples) + 1):
        if index == len(samples) or samples[index] != samples[start]:
            runs.append((samples[start], start, index - start))
            start = index
    short = [length * period for level, start, length in runs if 380 <= length * period <= 680]
    if not short:
        return [{**record, "raw_hex": "", "kind": "unknown", "truncated": True,
                 "waveform_errors": ["clock_not_recovered"]}]
    half_period = statistics.median(short[:64])
    cells = []
    positions = []
    invalid = []
    for level, start, length in runs:
        count = max(1, round(length * period / half_period))
        error = abs(length * period - count * half_period) > half_period * 0.25
        for index in range(count):
            cells.append(str(level))
            positions.append(round(start * period + index * half_period))
            invalid.append(error)
    wire = "".join(cells)
    output = []
    cursor = 0
    covered = []
    while cursor < len(wire):
        match = re.search(r"(?:01){8,}11110000", wire[cursor:])
        if not match:
            break
        first = cursor + match.start()
        payload_start = cursor + match.end()
        stop = wire.find("11110000", payload_start)
        missing_stop = stop < 0
        end = len(wire) if missing_stop else stop
        encoded = wire[payload_start:end]
        errors = []
        bits = []
        if len(encoded) % 2:
            errors.append("partial_manchester_symbol")
        for index in range(0, len(encoded) - 1, 2):
            pair = encoded[index:index + 2]
            if pair not in ("01", "10"):
                errors.append("invalid_manchester_symbol")
                break
            bits.append("1" if pair == "10" else "0")
        if len(bits) % 8:
            errors.append("partial_byte")
        raw = bytes(int("".join(bits[index:index + 8]), 2) for index in range(0, len(bits) - 7, 8))
        if any(invalid[first:end]):
            errors.append("timing_outside_tolerance")
        packet = {key: value for key, value in record.items() if key not in ("samples", "symbols")}
        packet.update(raw_hex=raw.hex(), timestamp_ns=record["timestamp_ns"] + positions[first],
                      truncated=bool(record.get("truncated", False) or missing_stop or len(bits) % 8),
                      waveform_errors=sorted(set(errors)), recovered_half_period_ns=half_period,
                      waveform_range_ns=[positions[first], positions[end - 1] + half_period if end else positions[first]],
                      preamble_zero_bits=(payload_start - first - 8) // 2)
        output.append(packet)
        covered.append((first, min(len(wire), end + 8)))
        cursor = end + 8
    if output:
        previous = 0
        for first, end in [*covered, (len(wire), len(wire))]:
            if len(set(wire[previous:first])) > 1:
                output.append({"kind": "unknown", "direction": "unknown", "loss_state": record.get("loss_state", "unknown"),
                               "timestamp_ns": record["timestamp_ns"] + positions[previous],
                               "raw_hex": "", "truncated": True,
                               "waveform_errors": ["unparsed_waveform_region"]})
            previous = end
        output.sort(key=lambda item: item["timestamp_ns"])
    if not output:
        packet = {key: value for key, value in record.items() if key not in ("samples", "symbols")}
        packet.update(raw_hex="", kind="unknown", truncated=True, waveform_errors=["no_complete_sync"])
        output.append(packet)
    return output


def decode_packet(record, capture_id, sequence):
    if not isinstance(record, dict):
        raise ValueError("Record must be an object")
    raw = raw_bytes(record.get("raw_hex", ""))
    direction = record.get("direction", "unknown")
    if not isinstance(direction, str) or direction not in DIRECTIONS:
        raise ValueError("Invalid direction")
    basis = record.get("direction_basis")
    if direction != "unknown" and (not isinstance(basis, str) or not basis.strip()):
        raise ValueError("Known direction requires provenance")
    kind = record.get("kind", "unknown")
    if not isinstance(kind, str) or kind not in {"request", "reply", "unknown", "loss"}:
        raise ValueError("Invalid packet kind")
    loss = record.get("loss_state", "unknown")
    if not isinstance(loss, str) or loss not in {"none", "lost", "unknown"}:
        raise ValueError("Invalid loss state")
    errors = record.get("waveform_errors", [])
    if not isinstance(errors, list) or any(not isinstance(error, str) for error in errors):
        raise ValueError("Invalid waveform errors")
    event = {"schema_version": SCHEMA_VERSION, "capture_id": capture_id,
             "sequence": sequence, "timestamp": integer(record.get("timestamp_ns"), "timestamp_ns"),
             "timestamp_unit": "ns", "direction": direction,
             "direction_confidence": "unknown" if direction == "unknown" else "declared",
             "direction_basis": basis, "kind": kind, "aux_command": None, "address": None,
             "request_raw": raw.hex() if kind == "request" else None,
             "reply_raw": raw.hex() if kind == "reply" else None, "raw_hex": raw.hex(),
             "reply_status": None, "malformed": False,
             "truncated": record.get("truncated", False), "loss_state": loss,
             "decoder_version": DECODER_VERSION, "errors": list(errors),
             "raw_record": copy.deepcopy(record)}
    if type(event["truncated"]) is not bool:
        raise ValueError("Invalid truncation flag")
    if kind == "loss":
        event["loss_state"] = "lost"
        return event
    if kind == "unknown":
        event["malformed"] = bool(event["errors"])
        return event
    if not raw:
        event["truncated"] = True
        event["errors"].append("missing_header")
        event["malformed"] = bool(record.get("waveform_errors"))
        return event
    if ((kind == "request" and direction == "sink_to_source") or
            (kind == "reply" and direction == "source_to_sink")):
        event["errors"].append("kind_direction_conflict")
    if kind == "request":
        command = raw[0] >> 4
        event.update(aux_command=command, aux_command_name=COMMANDS.get(command, "UNKNOWN"),
                     aux_type="native" if command & 8 else "i2c", mot=bool(command & 4))
        if command not in COMMANDS:
            event["errors"].append("unknown_command")
        if len(raw) < 3:
            event["truncated"] = True
        else:
            event["address"] = ((raw[0] & 15) << 16) | (raw[1] << 8) | raw[2]
            if not command & 8 and event["address"] > 0x7f:
                event["errors"].append("reserved_i2c_address_bits")
            if len(raw) == 3 and not command & 8:
                event.update(length=0, address_only=True, data_hex="")
            elif len(raw) < 4:
                event["truncated"] = True
            else:
                length = (raw[3] & 15) + 1
                event.update(length=length, address_only=False, data_hex=raw[4:].hex())
                if raw[3] & 0xf0:
                    event["errors"].append("reserved_length_bits")
                expected = 4 + (length if command in (0, 4, 8) else 0)
                if len(raw) < expected:
                    event["truncated"] = True
                if len(raw) > expected:
                    event["errors"].append("excess_request_bytes")
    else:
        status = raw[0] >> 4
        event.update(reply_status={"raw": status, "native": REPLIES[status & 3],
                                  "i2c": REPLIES[(status >> 2) & 3]}, data_hex=raw[1:].hex())
        if raw[0] & 15 or (status & 3) == 3 or (status >> 2) == 3:
            event["errors"].append("reserved_reply_bits")
        if len(raw) > 17:
            event["errors"].append("excess_reply_bytes")
    event["malformed"] = bool(event["errors"])
    return event


def reconstruct(events):
    transactions = []
    pending = None
    for event in events:
        if event["kind"] == "request":
            if pending is not None:
                transactions.append({"request": pending, "reply": None, "accepted": False,
                                     "complete": False, "reason": "missing_reply"})
            pending = event
            continue
        if event["kind"] == "reply" and pending is not None:
            status = event["reply_status"]
            valid = all(not item["malformed"] and not item["truncated"] and
                        item["loss_state"] == "none" for item in (pending, event))
            valid = valid and pending["direction"] == "source_to_sink" and event["direction"] == "sink_to_source"
            valid = valid and 0 <= event["timestamp"] - pending["timestamp"] <= 1000000
            if status and pending.get("aux_type") == "native" and status["raw"] & 12:
                valid = False
            accepted = bool(valid and status and status["native"] == "ACK" and
                            (pending.get("aux_type") == "native" or status["i2c"] == "ACK"))
            if accepted:
                expected = pending.get("length", 0) if pending.get("aux_command") in (1, 5, 9) else 0
                if len(raw_bytes(event.get("data_hex", ""))) != expected:
                    valid = accepted = False
            transactions.append({"request": pending, "reply": event, "accepted": accepted,
                                 "complete": bool(valid), "reason": None if valid else "unqualified_reply"})
            pending = None
        else:
            if pending is not None:
                transactions.append({"request": pending, "reply": None, "accepted": False,
                                     "complete": False, "reason": "interrupted"})
                pending = None
            transactions.append({"request": None, "reply": event, "accepted": False,
                                 "complete": False, "reason": "unmatched_or_unknown"})
    if pending is not None:
        transactions.append({"request": pending, "reply": None, "accepted": False,
                             "complete": False, "reason": "missing_reply"})
    return transactions


def decode_capture(capture):
    if (not isinstance(capture, dict) or type(capture.get("schema_version")) is not int or
            capture.get("schema_version") != SCHEMA_VERSION):
        raise ValueError("Unsupported capture schema")
    capture_id = capture.get("capture_id")
    if not isinstance(capture_id, str) or not capture_id or len(capture_id) > 128:
        raise ValueError("Invalid capture ID")
    if capture.get("evidence_kind") not in ("synthetic", "hardware"):
        raise ValueError("Explicit evidence kind required")
    records = capture.get("records")
    if not isinstance(records, list) or len(records) > MAX_RECORDS:
        raise ValueError("Invalid record count")
    expanded = []
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            raise ValueError("Record must be an object")
        if record.get("evidence_kind", capture["evidence_kind"]) != capture["evidence_kind"]:
            raise ValueError("Mixed evidence origins")
        if capture["evidence_kind"] == "hardware" and str(record.get("direction_basis", "")).startswith("synthetic"):
            raise ValueError("Synthetic direction provenance cannot become hardware evidence")
        representation = record.get("representation", "bytes")
        if representation not in ("bytes", "digital_samples", "ideal_symbols"):
            raise ValueError("Unknown raw representation")
        if representation == "ideal_symbols" and capture["evidence_kind"] != "synthetic":
            raise ValueError("Ideal symbols require synthetic evidence origin")
        integer(record.get("timestamp_ns"), "timestamp_ns")
        recovered = [record] if representation == "bytes" else recover_waveform(record)
        for item in recovered:
            expanded.append({**item, "acquisition_record": index})
        if len(expanded) > MAX_RECORDS:
            raise ValueError("Too many recovered packets")
    events = [decode_packet(record, capture_id, sequence) for sequence, record in enumerate(expanded)]
    if any(after["timestamp"] < before["timestamp"] for before, after in zip(events, events[1:])):
        raise ValueError("Records must retain monotonic acquisition order")
    gaps = capture.get("loss_intervals", [])
    if not isinstance(gaps, list) or len(gaps) + len(events) > MAX_RECORDS:
        raise ValueError("Invalid or oversized loss intervals")
    for index, gap in enumerate(gaps):
        if not isinstance(gap, dict):
            raise ValueError("Invalid loss interval")
        start = integer(gap.get("start_ns"), "gap start")
        end = integer(gap.get("end_ns"), "gap end", start)
        events.append(decode_packet({"kind": "loss", "timestamp_ns": start,
                                     "end_ns": end, "manifest_loss_interval": index,
                                     "direction": "unknown", "loss_state": "lost"}, capture_id, 0))
    if gaps:
        events.sort(key=lambda event: (event["timestamp"], event["kind"] != "loss"))
        loss_end = -1
        for sequence, event in enumerate(events):
            event["sequence"] = sequence
            if "manifest_loss_interval" in event["raw_record"]:
                loss_end = max(loss_end, event["raw_record"]["end_ns"])
            if event["timestamp"] <= loss_end:
                event["loss_state"] = "lost"
    return {"schema_version": SCHEMA_VERSION, "capture_id": capture_id,
            "evidence_kind": capture["evidence_kind"], "decoder_version": DECODER_VERSION,
            "raw_records": copy.deepcopy(records), "loss_intervals": copy.deepcopy(gaps),
            "events": events, "transactions": reconstruct(events)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("capture", type=pathlib.Path)
    arguments = parser.parse_args()
    try:
        print(json.dumps(decode_capture(load_capture(arguments.capture)), sort_keys=True, allow_nan=False))
    except (ValueError, OSError) as error:
        parser.exit(2, str(error) + "\n")


if __name__ == "__main__":
    main()