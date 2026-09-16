#!/usr/bin/env python3
"""Validate and summarize offline observer schema v1 JSONL; no live access."""

import argparse
import collections
import json
import os
import pathlib
import shutil
import stat
import sys
import tempfile

if __package__:
    from . import dcp_trace_schema as schema
    from .dcp_trace_correlation import Correlator
else:
    import dcp_trace_schema as schema
    from dcp_trace_correlation import Correlator


SCHEMA_VERSION = schema.SCHEMA_VERSION
MAX_PAYLOAD_BYTES = schema.MAX_PAYLOAD_BYTES
MAX_RECORD_BYTES = schema.MAX_RECORD_BYTES
MAX_INPUT_BYTES = schema.MAX_INPUT_BYTES
MAX_RECORDS = schema.MAX_RECORDS
ANNOTATION_FIELDS = schema.ANNOTATION_FIELDS
TraceFormatError = schema.TraceFormatError
validate_record = schema.validate_record


def annotations_for(record):
    supplied = record.get("annotations", {})
    return {name: supplied.get(name, "UNKNOWN") for name in ANNOTATION_FIELDS}


def read_records(path):
    path = pathlib.Path(path)
    if path.is_symlink() or not path.is_file():
        raise TraceFormatError("input must be a regular nonsymlink offline file", "INVALID_INPUT")
    descriptor = os.open(path, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW)
    with os.fdopen(descriptor, "rb") as source:
        if not stat.S_ISREG(os.fstat(source.fileno()).st_mode):
            raise TraceFormatError("input must be a regular file", "INVALID_INPUT")
        yield from read_record_stream(source)


def read_record_stream(source):
    total_bytes = 0
    for line_number in range(1, MAX_RECORDS + 2):
        line = source.readline(MAX_RECORD_BYTES + 1)
        if not line:
            return
        total_bytes += len(line)
        if len(line) > MAX_RECORD_BYTES or total_bytes > MAX_INPUT_BYTES or line_number > MAX_RECORDS:
            raise TraceFormatError(f"line {line_number}: input exceeds resource limits", "RESOURCE_LIMIT")
        try:
            yield schema.parse_record(line).require_valid()
        except TraceFormatError as error:
            raise TraceFormatError([schema.Issue(issue.code, f"line {line_number}: {issue.message}",
                                                issue.field, issue.severity) for issue in error.issues]) from error


def summarize(records, retained_records=None, include_correlations=False):
    kinds = collections.Counter()
    channels = collections.Counter()
    services = collections.Counter()
    opcodes = collections.Counter()
    losses = collections.Counter()
    positions = {}
    validator = schema.StreamValidator()
    correlator = Correlator()
    diagnostics = []
    issue_counts = collections.Counter()
    result = {"schema_version": SCHEMA_VERSION, "record_count": 0, "payload_bytes": 0,
              "sequence_gaps": 0, "reported_dropped_records": 0, "loss_count_unknown": False,
              "record_coverage_complete": True, "matched_pairs": 0, "orphan_replies": 0,
              "uncorrelated_records": 0, "ambiguous_correlations": 0,
              "invalidated_requests": 0, "annotation_records": 0,
              "ownership": "UNKNOWN", "ownership_inferred": False,
              "correlation_basis": "producer-declared scope and IDs; not independently verified"}
    for record in records:
        validation = validator.feed(record)
        validation.require_valid()
        for issue in validation.issues:
            issue_counts[issue.code] += 1
            if len(diagnostics) < 100:
                diagnostics.append(dict(issue.as_dict(), sequence=record["sequence"],
                                        capture_generation=record["capture_generation"]))
        generation = record["capture_generation"]
        previous_index = positions.get(generation, -1)
        gap = record["sequence"] - previous_index - 1
        result["sequence_gaps"] += gap
        positions[generation] = record["sequence"]
        loss = record["loss_state"]
        if gap or loss["status"] != "none":
            result["record_coverage_complete"] = False
        losses[loss["status"]] += 1
        result["reported_dropped_records"] += loss["dropped_records"] or 0
        result["loss_count_unknown"] |= loss["status"] != "none" and loss["dropped_records"] is None
        result["record_count"] += 1
        if result["record_count"] > MAX_RECORDS:
            raise TraceFormatError("too many records", "RESOURCE_LIMIT")
        result["payload_bytes"] += record["payload_length"]
        result["annotation_records"] += "annotations" in record
        kinds[record["kind"]] += 1
        channels[(record["asc"], record["endpoint"], record["channel"])] += 1
        services[record["service"]] += 1
        opcodes[(type(record["opcode"]).__name__, record["opcode"])] += 1
        correlator.feed(record, bool(gap))
        if retained_records is not None:
            retained_records.write(json.dumps(record, sort_keys=True, ensure_ascii=True, allow_nan=False) + "\n")
    result.update(correlator.summary())
    if result["ambiguous_correlations"]:
        issue_counts["AMBIGUOUS_CORRELATION"] += result["ambiguous_correlations"]
    result["validation_status"] = "VALID_WITH_WARNINGS" if issue_counts else "VALID"
    result["issue_counts"] = dict(sorted(issue_counts.items()))
    result["diagnostics"] = diagnostics
    result["capture_id"] = validator.capture
    result["synthetic"] = validator.producer["synthetic"] if validator.producer else None
    if include_correlations:
        result["correlations"] = correlator.outcomes
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
        raise TraceFormatError("input contains no records", "EMPTY_CAPTURE")
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=pathlib.Path, help="regular offline JSONL file")
    parser.add_argument("--records", action="store_true", help="emit all validated records instead of a summary")
    parser.add_argument("--json", action="store_true", help="also emit validation errors as JSON")
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
        if arguments.json:
            issues = error.issues if isinstance(error, TraceFormatError) else [schema.Issue("IO_ERROR", str(error))]
            print(json.dumps({"validation_status": "INVALID", "issues": [issue.as_dict() for issue in issues]}, sort_keys=True))
            return 2
        parser.error(str(error))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())