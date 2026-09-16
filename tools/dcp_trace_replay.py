#!/usr/bin/env python3
"""Replay stored observer records through offline validation and correlation."""

import argparse
import json
import math
import pathlib
import time

if __package__:
    from . import dcp_trace_import as trace
    from . import dcp_trace_schema as schema
else:
    import dcp_trace_import as trace
    import dcp_trace_schema as schema


def select_records(records, filters):
    unknown = set(filters) - {"endpoint", "channel", "service", "opcode"}
    if unknown:
        raise schema.TraceFormatError("unsupported replay filter", "INVALID_FILTER")
    selected = []
    for record in records:
        has_loss = record["kind"] == "loss" or not record["record_complete"] or record["loss_state"]["status"] != "none"
        matches = all(type(record[name]) is type(value) and record[name] == value for name, value in filters.items())
        if has_loss or matches:
            selected.append(record)
    return selected


def replay(path, filters=None, realtime=False, speed=1.0, delay=None):
    if not math.isfinite(speed) or speed <= 0:
        raise schema.TraceFormatError("replay speed must be finite and positive", "INVALID_SPEED")
    records = list(trace.read_records(path))
    summary = trace.summarize(records, include_correlations=True)
    selected = select_records(records, filters or {})
    if realtime:
        wait = time.sleep if delay is None else delay
        previous = None
        for record in selected:
            if previous is not None and previous["capture_generation"] == record["capture_generation"]:
                interval = (record["timestamp_ns"] - previous["timestamp_ns"]) / 1000000000 / speed
                wait(min(interval, 1.0))
            previous = record
    summary["replay"] = {"selected_records": len(selected), "omitted_records": len(records) - len(selected),
                         "filters": filters or {}, "loss_records_always_retained": True,
                         "ordering": "validated input order; never repaired or sorted",
                         "summary_scope": "entire input before filtering", "realtime": realtime}
    return selected, summary


def _opcode(value):
    try:
        parsed = schema.loads(value)
    except schema.TraceFormatError:
        parsed = value
    schema.identifier(parsed, "opcode filter")
    return parsed


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=pathlib.Path)
    output = parser.add_mutually_exclusive_group()
    output.add_argument("--jsonl", action="store_true", help="emit original validated selected records, including loss markers")
    output.add_argument("--json", action="store_true", help="emit a machine-readable whole-input summary")
    for field in ("endpoint", "channel"):
        parser.add_argument("--" + field, type=int)
    parser.add_argument("--service")
    parser.add_argument("--opcode", type=_opcode, help="JSON scalar or literal string; typed matching")
    parser.add_argument("--realtime", action="store_true", help="optional host delay, capped at one second per interval; default off")
    parser.add_argument("--speed", type=float, default=1.0)
    arguments = parser.parse_args(argv)
    filters = {field: getattr(arguments, field) for field in ("endpoint", "channel", "service", "opcode")
               if getattr(arguments, field) is not None}
    try:
        selected, summary = replay(arguments.input, filters, arguments.realtime, arguments.speed)
    except (OSError, schema.TraceFormatError) as error:
        issues = error.issues if isinstance(error, schema.TraceFormatError) else [schema.Issue("IO_ERROR", str(error))]
        print(schema.dumps({"validation_status": "INVALID", "issues": [issue.as_dict() for issue in issues]}))
        return 2
    if arguments.jsonl:
        for record in selected:
            print(schema.dumps(record))
    elif arguments.json:
        print(json.dumps(summary, sort_keys=True, indent=2))
    else:
        print(f"{summary['validation_status']}: {summary['record_count']} records; {len(selected)} selected")
        print(f"Explicit pairs: {summary['matched_pairs']}; ambiguous: {summary['ambiguous_correlations']}")
        print(f"Loss states: {schema.dumps(summary['loss_states'])}; ownership: UNKNOWN")
        print("Synthetic capture" if summary["synthetic"] else "Observed label only; provenance requires independent review")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())