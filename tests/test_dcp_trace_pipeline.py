import copy
import contextlib
import io
import json
import pathlib
import tempfile
import unittest
from unittest import mock

from tools import dcp_trace_schema as schema
from tools import dcp_trace_import as trace
from tools import dcp_trace_synthetic as synthetic
from tools import dcp_trace_replay as replay


def transport_record(sequence=0, **changes):
    value = {"schema_version": 1, "capture_id": "synthetic-test", "capture_generation": "generation-0",
             "boot_generation": "boot-0", "lifetime_generation": "lifetime-0",
             "sequence": sequence, "timestamp_ns": 1000 + sequence, "timestamp_units": "ns", "clock": "monotonic",
             "kind": "event", "direction": "host_to_dcp", "asc": "synthetic-asc",
             "endpoint": 42, "channel": 7, "service": "synthetic-service", "opcode": "unknown",
             "request_id": None, "payload_length": 2, "declared_payload_length": 2,
             "raw_payload": "00ff", "record_complete": True, "truncated": False,
             "loss_state": {"status": "none", "dropped_records": 0, "detail": None},
             "producer": {"name": "synthetic-test", "version": "1", "commit": "UNKNOWN", "synthetic": True}}
    value.update(changes)
    return value


class FormalSchemaTests(unittest.TestCase):
    def assert_code(self, value, code):
        result = schema.inspect_record(value)
        self.assertEqual(result.status, "INVALID")
        self.assertEqual(result.issues[0].code, code)

    def test_complete_record_valid(self):
        self.assertEqual(schema.inspect_record(transport_record()).status, "VALID")

    def test_unknown_extension_warning_preserves_values(self):
        value = transport_record(future={"nested": [None, 1, "opaque"]})
        original = copy.deepcopy(value)
        result = schema.parse_record(schema.dumps(value))
        self.assertEqual(result.status, "VALID_WITH_WARNINGS")
        self.assertEqual(result.issues[0].code, "UNKNOWN_EXTENSION_FIELD")
        self.assertEqual(result.record, original)

    def test_malformed_json_explicit_classification(self):
        result = schema.parse_record(b'{"schema_version":')
        self.assertEqual(result.status, "INVALID")
        self.assertEqual(result.issues[0].code, "MALFORMED_JSON")

    def test_proposed_record_is_not_silently_upgraded(self):
        value = transport_record()
        del value["capture_id"]
        self.assert_code(value, "MISSING_FIELD")
        self.assertNotIn("capture_id", value)

    def test_unsupported_version(self):
        self.assert_code(transport_record(schema_version=2), "UNSUPPORTED_SCHEMA")

    def test_direction_and_endpoint_types(self):
        self.assert_code(transport_record(direction=[]), "INVALID_DIRECTION")
        self.assert_code(transport_record(endpoint=True), "INVALID_ENDPOINT")

    def test_impossible_length_and_payload_mismatch(self):
        self.assert_code(transport_record(payload_length=-1), "IMPOSSIBLE_LENGTH")
        self.assert_code(transport_record(raw_payload="00"), "PAYLOAD_LENGTH_MISMATCH")

    def test_truncated_valid_with_warning(self):
        value = transport_record(declared_payload_length=8, record_complete=False, truncated=True,
                                 loss_state={"status": "truncated", "dropped_records": None, "detail": None})
        result = schema.inspect_record(value)
        self.assertEqual(result.status, "VALID_WITH_WARNINGS")
        self.assertIn("TRUNCATED_RECORD", [issue.code for issue in result.issues])

    def test_false_completeness_is_not_repaired(self):
        self.assert_code(transport_record(record_complete=False), "INVALID_COMPLETENESS")

    def test_clock_units_explicit(self):
        self.assert_code(transport_record(timestamp_units="seconds"), "INVALID_ENUM")
        self.assert_code(transport_record(clock="wall"), "INVALID_ENUM")

    def test_invalid_annotation_confidence(self):
        self.assert_code(transport_record(annotations={"confidence": "certain"}), "MALFORMED_ANNOTATION")

    def test_annotation_generation_mismatch(self):
        self.assert_code(transport_record(annotations={"capture_generation": "other"}), "CAPTURE_GENERATION_MISMATCH")

    def test_alias_cannot_disagree_with_sequence(self):
        self.assert_code(transport_record(record_index=2), "SEQUENCE_MISMATCH")

    def test_sequence_duplicate_and_regression(self):
        for last, code in ((2, "DUPLICATE_SEQUENCE"), (1, "SEQUENCE_REGRESSION")):
            validator = schema.StreamValidator()
            validator.feed(transport_record(2))
            result = validator.feed(transport_record(last))
            self.assertEqual(result.issues[-1].code, code)

    def test_new_generation_may_restart_clock_and_sequence(self):
        validator = schema.StreamValidator()
        validator.feed(transport_record(5))
        result = validator.feed(transport_record(0, capture_generation="new", boot_generation="new", timestamp_ns=0))
        self.assertEqual(result.status, "VALID")

    def test_closed_generation_cannot_reappear(self):
        validator = schema.StreamValidator()
        validator.feed(transport_record())
        validator.feed(transport_record(capture_generation="new"))
        self.assertEqual(validator.feed(transport_record(1)).issues[-1].code, "CAPTURE_GENERATION_MISMATCH")

    def test_capture_id_cannot_change_midfile(self):
        validator = schema.StreamValidator()
        validator.feed(transport_record())
        self.assertEqual(validator.feed(transport_record(1, capture_id="other")).status, "INVALID")

    def test_duplicate_json_keys_and_nonfinite_rejected(self):
        for value in ('{"same": 1, "same": 2}', '{"number": NaN}', '{"number": 1e999}'):
            self.assertEqual(schema.parse_record(value).status, "INVALID")

    def test_direct_api_rejects_non_json_extension_values(self):
        for extension in (float("nan"), b"bytes", {1: "numeric key"}):
            self.assert_code(transport_record(extensions={"future": extension}), "MALFORMED_JSON")

    def test_unknown_nested_extension_is_warned_and_preserved(self):
        record = transport_record()
        record["producer"]["future"] = {"opaque": True}
        result = schema.inspect_record(record)
        self.assertEqual(result.status, "VALID_WITH_WARNINGS")
        self.assertEqual(result.record["producer"]["future"], {"opaque": True})


class SyntheticReplayTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = pathlib.Path(self.directory.name) / "synthetic.jsonl"

    def write(self, scenario):
        self.path.write_text(synthetic.encode_scenario(scenario), encoding="utf-8")
        return self.path

    def test_all_scenarios_deterministic_and_synthetic(self):
        for name in synthetic.SCENARIOS:
            with self.subTest(scenario=name):
                first = synthetic.encode_scenario(name)
                self.assertEqual(first, synthetic.encode_scenario(name))
                self.assertTrue(all(record["producer"]["synthetic"] for record in map(json.loads, first.splitlines())))

    def test_scenarios_valid_except_deliberate_invalids(self):
        for name in synthetic.SCENARIOS:
            with self.subTest(scenario=name):
                if name in ("malformed", "duplicate_packet"):
                    with self.assertRaises(schema.TraceFormatError):
                        trace.summarize(synthetic.scenario_records(name))
                else:
                    self.assertIn(trace.summarize(synthetic.scenario_records(name))["validation_status"], ("VALID", "VALID_WITH_WARNINGS"))

    def test_replay_matches_importer(self):
        path = self.write("request_reply")
        records, result = replay.replay(path)
        direct = trace.summarize(trace.read_records(path), include_correlations=True)
        self.assertEqual({key: value for key, value in result.items() if key != "replay"}, direct)
        self.assertEqual(records, synthetic.scenario_records("request_reply"))

    def test_no_delay_by_default(self):
        with mock.patch.object(replay.time, "sleep", side_effect=AssertionError("must not wait")):
            replay.replay(self.write("request_reply"))

    def test_optional_delay_uses_injected_clock_without_waiting(self):
        wait = mock.Mock()
        replay.replay(self.write("request_reply"), realtime=True, delay=wait)
        wait.assert_called_once_with(1e-9)

    def test_filter_keeps_loss_and_whole_input_diagnostics(self):
        selected, summary = replay.replay(self.write("dropped"), {"endpoint": 255})
        self.assertEqual([record["kind"] for record in selected], ["loss"])
        self.assertEqual(summary["reported_dropped_records"], 3)
        self.assertFalse(summary["record_coverage_complete"])

    def test_invalid_record_cannot_be_hidden_by_filter(self):
        with self.assertRaises(schema.TraceFormatError):
            replay.replay(self.write("malformed"), {"endpoint": 255})

    def test_filter_retains_loss_attached_to_normal_reply_or_event(self):
        for scenario in ("truncated", "incomplete_reply"):
            with self.subTest(scenario=scenario):
                selected, summary = replay.replay(self.write(scenario), {"endpoint": 255})
                self.assertEqual(len(selected), 1)
                self.assertFalse(selected[0]["record_complete"])
                self.assertFalse(summary["record_coverage_complete"])

    def test_filters_preserve_identifier_types(self):
        path = self.write("request_reply")
        self.assertEqual(len(replay.replay(path, {"opcode": 99})[0]), 2)
        self.assertEqual(replay.replay(path, {"opcode": "99"})[0], [])

    def test_scope_and_generation_separate_reused_request_ids(self):
        for name in ("scoped_request_ids", "id_generation_reset"):
            self.assertEqual(replay.replay(self.write(name))[1]["matched_pairs"], 0)

    def test_wrap_preserves_generation_boundary(self):
        records, summary = replay.replay(self.write("wrap_loss"))
        self.assertEqual(records[-1]["capture_generation"], "generation-1")
        self.assertEqual(len(summary["capture_generations"]), 2)
        self.assertTrue(summary["loss_count_unknown"])

    def test_replayed_jsonl_is_an_exact_value_roundtrip(self):
        self.write("unknown_opcode")
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.assertEqual(replay.main([str(self.path), "--jsonl"]), 0)
        self.assertEqual([json.loads(line) for line in output.getvalue().splitlines()], synthetic.scenario_records("unknown_opcode"))

    def test_synthetic_producer_refuses_to_overwrite(self):
        self.write("one_service")
        original = self.path.read_bytes()
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            synthetic.main(["zero_length", "--output", str(self.path)])
        self.assertEqual(self.path.read_bytes(), original)

    def test_correlation_exposes_explicit_classification(self):
        summary = replay.replay(self.write("request_reply"))[1]
        self.assertEqual([entry["status"] for entry in summary["correlations"]], ["CORRELATION_EXPLICIT"] * 2)

    def test_bad_speed_and_unsupported_filter_rejected(self):
        path = self.write("one_service")
        for speed in (0, -1, float("nan")):
            with self.assertRaises(schema.TraceFormatError):
                replay.replay(path, speed=speed)
        with self.assertRaises(schema.TraceFormatError):
            replay.replay(path, {"source": "invented"})


if __name__ == "__main__":
    unittest.main()