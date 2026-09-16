#!/usr/bin/env python3
"""Analyze an offline capture bundle/file or validate human-supplied platform facts."""

import argparse
import json
import pathlib

if __package__:
    from . import dcp_trace_bundle as bundle
    from . import dcp_trace_evidence as evidence
    from . import dcp_trace_import as trace
    from . import dcp_trace_schema as schema
else:
    import dcp_trace_bundle as bundle
    import dcp_trace_evidence as evidence
    import dcp_trace_import as trace
    import dcp_trace_schema as schema


def analyze(path, review_name=None):
    path = pathlib.Path(path)
    if path.is_dir():
        capture = bundle.validate_bundle(path, review_name)
        result = evidence.evaluate(capture["records"], capture["review"])
        result["bundle"] = {name: capture[name] for name in ("manifest", "source_info", "hashes", "integrity", "authenticity")}
    else:
        schema.require(review_name is None, "INVALID_REVIEW", "real provenance review requires a complete bundle")
        result = evidence.evaluate(trace.read_records(path))
    result.update(platform_target_state="M5_OBSERVER_CODE_NOT_READY_FOR_TARGET_TEST",
                  purchase_state="SACRIFICIAL_M5_STILL_PREMATURE", hub_state="USB_C_HUB_CONNECTION_NOT_REQUIRED")
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=pathlib.Path)
    parser.add_argument("--json", action="store_true", help="machine-readable analysis and errors")
    parser.add_argument("--review", help="explicit human provenance review filename already hashed within the bundle")
    parser.add_argument("--platform-result", action="store_true", help="validate a human-authored result JSON and its local hashed logs only")
    arguments = parser.parse_args(argv)
    try:
        if arguments.platform_result:
            schema.require(arguments.review is None, "INVALID_REVIEW", "platform-result validation does not accept capture reviews")
            result = bundle.validate_human_result(arguments.input)
        else:
            result = analyze(arguments.input, arguments.review)
    except (OSError, schema.TraceFormatError) as error:
        issues = error.issues if isinstance(error, schema.TraceFormatError) else [schema.Issue("IO_ERROR", str(error))]
        print(schema.dumps({"validation_status": "INVALID", "issues": [issue.as_dict() for issue in issues]}))
        return 2
    if arguments.json:
        print(json.dumps(result, sort_keys=True, indent=2))
    elif arguments.platform_result:
        print(result["status"] + ": external claims only; no hardware authorization")
    else:
        print(result["summary"]["validation_status"] + ": offline capture analysis")
        for gate, outcome in result["gates"].items():
            print(gate + ": " + outcome["status"])
        print("Real-evidence passes: " + str(result["real_evidence_passes"]))
        print("Platform: " + result["platform_target_state"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())