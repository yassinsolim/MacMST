#!/usr/bin/env python3
"""Validate and summarize proposed DCP transport JSONL, without live access."""

import argparse
import collections
import json
import math
import pathlib
import re
import shutil
import sys
import tempfile


SCHEMA_VERSION = 1
MAX_PAYLOAD_BYTES = 1024 * 1024
MAX_RECORD_BYTES = 2 * MAX_PAYLOAD_BYTES + 65536
MAX_INPUT_BYTES = 256 * 1024 * 1024
MAX_RECORDS = 100000
MAX_INTEGER = (1 << 64) - 1
ANNOTATION_FIELDS = (
    "physical_dptx", "source_identity", "timing_identity", "payload_identity",
    "confidence", "evidence",
)
REQUIRED_FIELDS = (
    "schema_version", "capture_generation", "record_index", "timestamp_ns",
    "kind", "direction", "asc", "endpoint", "channel", "service", "opcode",
    "request_id", "payload_length", "raw_payload", "loss_state",
)


class TraceFormatError(ValueError):
    pass


def _integer(value, name, maximum=MAX_INTEGER):
    if type(value) is not int or not 0 <= value <= maximum:
        raise TraceFormatError(f"{name} must be a bounded nonnegative integer")


def _text(value, name):
    if not isinstance(value, str) or not value or len(value) > 256:
        raise TraceFormatError(f"{name} must be a nonempty string of at most 256 characters")


def _identifier(value, name):
    if isinstance(value, str):
        _text(value, name)
    elif value is not None:
        _integer(value, name)


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise TraceFormatError("duplicate JSON object key")
        result[key] = value
    return result


def _reject_constant(value):
    raise TraceFormatError("non-finite JSON number")


def _finite_float(value):
    number = float(value)
    if not math.isfinite(number):
        raise TraceFormatError("non-finite JSON number")
    return number


def validate_record(record):
    if not isinstance(record, dict):
        raise TraceFormatError("record must be a JSON object")
    if any(field not in record for field in REQUIRED_FIELDS):
        raise TraceFormatError("record is missing required schema fields")
    if type(record["schema_version"]) is not int or record["schema_version"] != SCHEMA_VERSION:
        raise TraceFormatError("unsupported schema_version")
    for name in ("capture_generation", "asc"):
        _text(record[name], name)
    for name in ("record_index", "timestamp_ns"):
        _integer(record[name], name)
    if record["kind"] not in ("request", "reply", "event", "loss"):
        raise TraceFormatError("invalid record kind")
    if record["direction"] not in ("host_to_dcp", "dcp_to_host", "none"):
        raise TraceFormatError("invalid direction")
    if (record["direction"] == "none") != (record["kind"] == "loss"):
        raise TraceFormatError("direction none is reserved for loss records")
    for name, maximum in (("endpoint", 255), ("channel", (1 << 32) - 1)):
        if record[name] is not None:
            _integer(record[name], name, maximum)
    if record["service"] is not None:
        _text(record["service"], "service")
    for name in ("opcode", "request_id"):
        _identifier(record[name], name)
    _integer(record["payload_length"], "payload_length", MAX_PAYLOAD_BYTES)
    raw_payload = record["raw_payload"]
    if not isinstance(raw_payload, str) or len(raw_payload) != 2 * record["payload_length"]:
        raise TraceFormatError("raw_payload length does not match payload_length")
    if re.fullmatch(r"[0-9a-fA-F]*", raw_payload) is None:
        raise TraceFormatError("raw_payload must be hexadecimal without separators")
    loss = record["loss_state"]
    if not isinstance(loss, dict) or not {"status", "dropped_records", "detail"} <= loss.keys():
        raise TraceFormatError("loss_state requires status, dropped_records and detail")
    if loss["status"] not in ("none", "dropped", "wrapped", "truncated", "unknown"):
        raise TraceFormatError("invalid loss_state status")
    if loss["dropped_records"] is not None:
        _integer(loss["dropped_records"], "dropped_records")
    if loss["detail"] is not None:
        _text(loss["detail"], "loss detail")
    if loss["status"] == "none" and loss["dropped_records"] != 0:
        raise TraceFormatError("loss-free records require dropped_records zero")
    if loss["status"] == "dropped" and not loss["dropped_records"]:
        raise TraceFormatError("dropped status requires a positive dropped_records count")
    if record["kind"] == "loss" and loss["status"] == "none":
        raise TraceFormatError("loss record cannot report no loss")
    declared = record.get("declared_payload_length", record["payload_length"])
    _integer(declared, "declared_payload_length")
    if declared < record["payload_length"]:
        raise TraceFormatError("declared_payload_length is smaller than retained payload")
    if declared > record["payload_length"] and loss["status"] not in ("truncated", "unknown"):
        raise TraceFormatError("incomplete payload requires explicit truncation or unknown loss")
    if loss["status"] == "truncated" and declared <= record["payload_length"]:
        raise TraceFormatError("truncated payload requires a larger declared_payload_length")
    if "correlation" in record:
        correlation = record["correlation"]
        if not isinstance(correlation, dict) or not {"scope", "evidence"} <= correlation.keys():
            raise TraceFormatError("correlation requires scope and evidence")
        for name in ("scope", "evidence"):
            _text(correlation[name], "correlation " + name)
        if record["kind"] not in ("request", "reply") or record["request_id"] is None:
            raise TraceFormatError("correlation requires a request/reply and a request_id")
        if record["endpoint"] is None or record["channel"] is None:
            raise TraceFormatError("correlation requires an endpoint and channel")
    if "annotations" in record:
        annotations = record["annotations"]
        if not isinstance(annotations, dict):
            raise TraceFormatError("annotations must be an object")
        for name in ANNOTATION_FIELDS[:-1]:
            if name in annotations:
                _text(annotations[name], "annotation " + name)
        evidence = annotations.get("evidence", "UNKNOWN")
        if evidence != "UNKNOWN":
            if not isinstance(evidence, list) or not evidence:
                raise TraceFormatError("annotation evidence must be UNKNOWN or a nonempty list")
            for entry in evidence:
                _text(entry, "annotation evidence entry")
        if any(annotations.get(name, "UNKNOWN") != "UNKNOWN" for name in ANNOTATION_FIELDS[:4]):
            if evidence == "UNKNOWN" or annotations.get("confidence", "UNKNOWN") == "UNKNOWN":
                raise TraceFormatError("identity annotations require confidence and evidence")
    return record


def annotations_for(record):
    supplied = record.get("annotations", {})
    return {name: supplied.get(name, "UNKNOWN") for name in ANNOTATION_FIELDS}


def read_records(path):
    path = pathlib.Path(path)
    if not path.is_file():
        raise TraceFormatError("input must be a regular offline file")
    total_bytes = 0
    with path.open("rb") as source:
        for line_number in range(1, MAX_RECORDS + 2):
            line = source.readline(MAX_RECORD_BYTES + 1)
            if not line:
                return
            total_bytes += len(line)
            if len(line) > MAX_RECORD_BYTES or total_bytes > MAX_INPUT_BYTES or line_number > MAX_RECORDS:
                raise TraceFormatError(f"line {line_number}: input exceeds resource limits")
            try:
                record = json.loads(line.decode("utf-8"), object_pairs_hook=_unique_object,
                                    parse_constant=_reject_constant, parse_float=_finite_float)
                yield validate_record(record)
            except (UnicodeError, ValueError, RecursionError) as error:
                detail = error.msg if isinstance(error, json.JSONDecodeError) else str(error)
                raise TraceFormatError(f"line {line_number}: {detail}") from error


def _correlation_key(record):
    correlation = record.get("correlation")
    if correlation is None:
        return None
    identity = record["request_id"]
    return (record["capture_generation"], record["asc"], record["endpoint"],
            record["channel"], record["service"], correlation["scope"],
            type(identity).__name__, identity)


def summarize(records, retained_records=None):
    kinds = collections.Counter()
    channels = collections.Counter()
    services = collections.Counter()
    opcodes = collections.Counter()
    losses = collections.Counter()
    positions = {}
    pending = {}
    ambiguous = set()
    result = {"schema_version": SCHEMA_VERSION, "record_count": 0, "payload_bytes": 0,
              "sequence_gaps": 0, "reported_dropped_records": 0, "loss_count_unknown": False,
              "record_coverage_complete": True, "matched_pairs": 0, "orphan_replies": 0,
              "uncorrelated_records": 0, "ambiguous_correlations": 0,
              "invalidated_requests": 0, "annotation_records": 0,
              "ownership": "UNKNOWN", "ownership_inferred": False,
              "correlation_basis": "producer-declared scope and IDs; not independently verified"}
    for record in records:
        validate_record(record)
        generation = record["capture_generation"]
        previous_index, previous_time = positions.get(generation, (-1, 0))
        if record["record_index"] <= previous_index or record["timestamp_ns"] < previous_time:
            raise TraceFormatError("record ordering or monotonic timestamp regressed within generation")
        gap = record["record_index"] - previous_index - 1
        result["sequence_gaps"] += gap
        positions[generation] = record["record_index"], record["timestamp_ns"]
        loss = record["loss_state"]
        if gap or loss["status"] != "none":
            result["record_coverage_complete"] = False
            invalidated = [key for key in pending if key[0] == generation]
            result["invalidated_requests"] += len(invalidated)
            for key in invalidated:
                del pending[key]
        losses[loss["status"]] += 1
        result["reported_dropped_records"] += loss["dropped_records"] or 0
        result["loss_count_unknown"] |= loss["status"] != "none" and loss["dropped_records"] is None
        result["record_count"] += 1
        result["payload_bytes"] += record["payload_length"]
        result["annotation_records"] += "annotations" in record
        kinds[record["kind"]] += 1
        channels[(record["asc"], record["endpoint"], record["channel"])] += 1
        services[record["service"]] += 1
        opcodes[(type(record["opcode"]).__name__, record["opcode"])] += 1
        key = _correlation_key(record)
        if record["kind"] in ("request", "reply"):
            if key is None or loss["status"] != "none":
                result["uncorrelated_records"] += 1
            elif key in ambiguous:
                result["uncorrelated_records"] += 1
            elif record["kind"] == "request":
                if key in pending:
                    del pending[key]
                    ambiguous.add(key)
                    result["ambiguous_correlations"] += 1
                else:
                    pending[key] = record["direction"]
            elif key not in pending:
                result["orphan_replies"] += 1
            elif pending.pop(key) == record["direction"]:
                ambiguous.add(key)
                result["ambiguous_correlations"] += 1
            else:
                result["matched_pairs"] += 1
        if retained_records is not None:
            retained_records.write(json.dumps(record, sort_keys=True, ensure_ascii=True, allow_nan=False) + "\n")
    result["pending_requests"] = len(pending)
    result["capture_generations"] = sorted(positions)
    result["kinds"] = dict(sorted(kinds.items()))
    result["loss_states"] = dict(sorted(losses.items()))
    result["channels"] = [dict(zip(("asc", "endpoint", "channel"), key), records=count)
                          for key, count in sorted(channels.items(), key=lambda item: json.dumps(item[0]))]
    result["services"] = [{"service": key, "records": count}
                          for key, count in sorted(services.items(), key=lambda item: json.dumps(item[0]))]
    result["opcodes"] = [{"opcode": key[1], "records": count}
                         for key, count in sorted(opcodes.items(), key=lambda item: json.dumps(item[0]))]
    if not result["record_count"]:
        raise TraceFormatError("input contains no records")
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=pathlib.Path, help="regular offline JSONL file")
    parser.add_argument("--records", action="store_true", help="emit all validated records instead of a summary")
    arguments = parser.parse_args(argv)
    try:
        if arguments.records:
            with tempfile.TemporaryFile(mode="w+", encoding="utf-8") as retained:
                summarize(read_records(arguments.input), retained)
                retained.seek(0)
                shutil.copyfileobj(retained, sys.stdout)
        else:
            summary = summarize(read_records(arguments.input))
            print(json.dumps(summary, sort_keys=True, indent=2, allow_nan=False))
    except (OSError, TraceFormatError) as error:
        parser.error(str(error))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())