import contextlib
import copy
import importlib.util
import io
import json
import pathlib
import tempfile
import unittest
from unittest import mock


SOURCE = pathlib.Path(__file__).resolve().parents[1] / "tools" / "dcp_trace_import.py"
SPEC = importlib.util.spec_from_file_location("dcp_trace_import", SOURCE)
trace = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(trace)


def record(index=0, kind="event", payload=b"\x00\xff", **changes):
    value = {"schema_version": 1, "capture_generation": "synthetic-generation",
             "record_index": index, "timestamp_ns": 1000 + index, "kind": kind,
             "direction": "dcp_to_host" if kind == "reply" else "host_to_dcp",
             "asc": "synthetic-asc", "endpoint": 42, "channel": 7,
             "service": "synthetic-service", "opcode": 99, "request_id": None,
             "payload_length": len(payload), "raw_payload": payload.hex(),
             "loss_state": {"status": "none", "dropped_records": 0, "detail": None}}
    value.update(changes)
    return value


def exchange(index=0, kind="request", **changes):
    changes.setdefault("request_id", 23)
    changes.setdefault("correlation", {"scope": "synthetic-channel-lifetime",
                                        "evidence": "Synthetic request/reply contract, not hardware evidence"})
    return record(index, kind, **changes)


class TraceSchemaTests(unittest.TestCase):
    def test_request_reply_and_zero_length_records(self):
        records = [exchange(), exchange(1, "reply", payload=b"")]
        result = trace.summarize(records)
        self.assertEqual(result["matched_pairs"], 1)
        self.assertEqual(result["pending_requests"], 0)
        self.assertEqual(result["payload_bytes"], 2)
        self.assertEqual(result["ownership"], "UNKNOWN")
        self.assertFalse(result["ownership_inferred"])

    def test_unknown_opcode_and_extension_fields_are_preserved(self):
        source = record(opcode="future-opcode", service=None, future={"array": [1, None, "raw"]})
        source["loss_state"]["future_reason"] = {"code": 9}
        original = copy.deepcopy(source)
        output = io.StringIO()
        summary = trace.summarize([source], output)
        self.assertEqual(source, original)
        self.assertEqual(json.loads(output.getvalue()), original)
        self.assertEqual(summary["opcodes"], [{"opcode": "future-opcode", "records": 1}])

    def test_maximum_retained_payload_and_oversize_rejection(self):
        trace.validate_record(record(payload=b"a" * trace.MAX_PAYLOAD_BYTES))
        with self.assertRaises(trace.TraceFormatError):
            trace.validate_record(record(payload=b"a" * (trace.MAX_PAYLOAD_BYTES + 1)))

    def test_malformed_required_fields_rejected(self):
        invalid = [dict(schema_version=True), dict(schema_version=2), dict(endpoint=True),
                   dict(channel=-1), dict(timestamp_ns=-1), dict(raw_payload="00"),
                   dict(raw_payload="xxff"), dict(raw_payload=" 0ff"), dict(payload_length=True),
                   dict(kind="command"), dict(direction="none"), dict(asc=""), dict(request_id=False)]
        for change in invalid:
            with self.subTest(change=change), self.assertRaises(trace.TraceFormatError):
                trace.validate_record(record(**change))
        source = record()
        del source["channel"]
        with self.assertRaises(trace.TraceFormatError):
            trace.validate_record(source)

    def test_truncation_must_be_explicit_and_length_bound(self):
        with self.assertRaises(trace.TraceFormatError):
            trace.validate_record(record(declared_payload_length=10))
        partial = record(declared_payload_length=10,
                         loss_state={"status": "truncated", "dropped_records": None, "detail": "synthetic truncation"})
        summary = trace.summarize([partial])
        self.assertFalse(summary["record_coverage_complete"])
        self.assertTrue(summary["loss_count_unknown"])
        with self.assertRaises(trace.TraceFormatError):
            trace.validate_record(record(loss_state=partial["loss_state"]))

    def test_dropped_record_reporting_and_pending_invalidation(self):
        lost = record(1, "loss", payload=b"", direction="none",
                      loss_state={"status": "dropped", "dropped_records": 3, "detail": "synthetic loss"})
        summary = trace.summarize([exchange(), lost, exchange(2, "reply")])
        self.assertEqual(summary["reported_dropped_records"], 3)
        self.assertEqual(summary["matched_pairs"], 0)
        self.assertEqual(summary["invalidated_requests"], 1)
        self.assertEqual(summary["orphan_replies"], 1)
        self.assertFalse(summary["record_coverage_complete"])

    def test_wrap_record_does_not_invent_drop_count(self):
        wrapped = record(kind="loss", payload=b"", direction="none",
                         loss_state={"status": "wrapped", "dropped_records": None, "detail": None})
        summary = trace.summarize([wrapped])
        self.assertTrue(summary["loss_count_unknown"])
        self.assertEqual(summary["reported_dropped_records"], 0)
        self.assertFalse(summary["record_coverage_complete"])

    def test_invalid_loss_combinations_rejected(self):
        for state in ({"status": "none", "dropped_records": 2, "detail": None},
                      {"status": "dropped", "dropped_records": 0, "detail": None},
                      {"status": "unknown", "dropped_records": False, "detail": None},
                      {"status": "none"}):
            with self.subTest(state=state), self.assertRaises(trace.TraceFormatError):
                trace.validate_record(record(loss_state=state))

    def test_correlation_requires_explicit_scope_and_evidence(self):
        summary = trace.summarize([record(kind="request", request_id=1), record(1, "reply", request_id=1)])
        self.assertEqual(summary["matched_pairs"], 0)
        self.assertEqual(summary["uncorrelated_records"], 2)
        for correlation in ({"scope": "test"}, {"scope": "", "evidence": "test"}):
            with self.assertRaises(trace.TraceFormatError):
                trace.validate_record(exchange(correlation=correlation))

    def test_sequence_gap_prevents_pairing_across_missing_records(self):
        summary = trace.summarize([exchange(), exchange(2, "reply")])
        self.assertEqual(summary["sequence_gaps"], 1)
        self.assertEqual(summary["matched_pairs"], 0)
        self.assertFalse(summary["record_coverage_complete"])

    def test_ids_never_match_across_context_or_generation(self):
        for changes in (dict(capture_generation="other"), dict(asc="other"), dict(endpoint=1),
                        dict(channel=2), dict(service="other"), dict(request_id="23"),
                        dict(correlation={"scope": "other", "evidence": "synthetic"})):
            with self.subTest(changes=changes):
                summary = trace.summarize([exchange(), exchange(1, "reply", **changes)])
                self.assertEqual(summary["matched_pairs"], 0)

    def test_duplicate_inflight_ids_are_ambiguous(self):
        summary = trace.summarize([exchange(), exchange(1), exchange(2, "reply")])
        self.assertEqual(summary["ambiguous_correlations"], 1)
        self.assertEqual(summary["matched_pairs"], 0)

    def test_same_direction_is_not_a_pair_and_id_can_be_reused_after_reply(self):
        summary = trace.summarize([exchange(), exchange(1, "reply", direction="host_to_dcp")])
        self.assertEqual(summary["matched_pairs"], 0)
        self.assertEqual(summary["ambiguous_correlations"], 1)
        summary = trace.summarize([exchange(), exchange(1, "reply"), exchange(2), exchange(3, "reply")])
        self.assertEqual(summary["matched_pairs"], 2)

    def test_regressing_index_and_timestamp_rejected(self):
        for second in (exchange(0, "reply"), exchange(1, "reply", timestamp_ns=1)):
            with self.assertRaises(trace.TraceFormatError):
                trace.summarize([exchange(), second])

    def test_missing_annotations_remain_unknown(self):
        self.assertEqual(trace.annotations_for(record()), {name: "UNKNOWN" for name in trace.ANNOTATION_FIELDS})
        annotated = record(annotations={"physical_dptx": "synthetic-only", "confidence": "UNVERIFIED",
                                       "evidence": ["synthetic fixture"], "future": 5})
        summary = trace.summarize([annotated])
        self.assertEqual(summary["annotation_records"], 1)
        self.assertEqual(summary["ownership"], "UNKNOWN")
        self.assertEqual(trace.annotations_for(annotated)["source_identity"], "UNKNOWN")
        with self.assertRaises(trace.TraceFormatError):
            trace.validate_record(record(annotations={"source_identity": "unjustified"}))


class TraceFileTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = pathlib.Path(self.directory.name) / "synthetic.jsonl"

    def test_duplicate_keys_nonfinite_invalid_utf8_and_partial_json_rejected(self):
        raw = json.dumps(record()).encode()
        invalid_lines = [raw[:-1], b"\xff", b"\n", b"[]", raw[:-1] + b', "schema_version": 1}',
                         raw[:-1] + b', "extension": NaN}', raw[:-1] + b', "extension": 1e999}']
        for value in invalid_lines:
            with self.subTest(value=value[:24]):
                self.path.write_bytes(value + b"\n")
                with self.assertRaises(trace.TraceFormatError):
                    list(trace.read_records(self.path))

    def test_reader_accepts_complete_final_record_without_newline(self):
        self.path.write_text(json.dumps(record()), encoding="utf-8")
        self.assertEqual(list(trace.read_records(self.path)), [record()])

    def test_resource_limits_reject_instead_of_silently_truncating(self):
        self.path.write_text(json.dumps(record()) + "\n", encoding="utf-8")
        for name, limit in (("MAX_RECORD_BYTES", 30), ("MAX_INPUT_BYTES", 30), ("MAX_RECORDS", 0)):
            with self.subTest(name=name), mock.patch.object(trace, name, limit):
                with self.assertRaises(trace.TraceFormatError):
                    list(trace.read_records(self.path))

    def test_empty_and_nonfile_input_rejected(self):
        self.path.write_bytes(b"")
        with self.assertRaises(trace.TraceFormatError):
            trace.summarize(trace.read_records(self.path))
        with self.assertRaises(trace.TraceFormatError):
            list(trace.read_records(pathlib.Path(self.directory.name)))

    def test_cli_summary_and_validated_records_preserve_extensions(self):
        records = [exchange(extension={"unknown": True}), exchange(1, "reply")]
        self.path.write_text("\n".join(json.dumps(value) for value in records), encoding="utf-8")
        for mode in ([], ["--records"]):
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                self.assertEqual(trace.main([str(self.path)] + mode), 0)
            if mode:
                self.assertEqual([json.loads(line) for line in output.getvalue().splitlines()], records)
            else:
                self.assertEqual(json.loads(output.getvalue())["matched_pairs"], 1)

    def test_cli_does_not_publish_partial_records_on_invalid_input(self):
        self.path.write_text(json.dumps(record()) + "\n{", encoding="utf-8")
        output = io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as exit_context:
                trace.main([str(self.path), "--records"])
        self.assertEqual(exit_context.exception.code, 2)
        self.assertEqual(output.getvalue(), "")


if __name__ == "__main__":
    unittest.main()