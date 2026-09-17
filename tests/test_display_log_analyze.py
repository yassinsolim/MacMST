import importlib.util
import contextlib
import io
import json
import pathlib
import tempfile
import unittest
from unittest import mock


ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("display_log_analyze", ROOT / "tools/display_log_analyze.py")
logs = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(logs)


def record(message, stamp="2026-09-16 11:20:00.000000+0000", **fields):
    return {"timestamp": stamp, "processImagePath": "/kernel", "eventMessage": "DCPDPDeviceProxy: " + message,
            "subsystem": "synthetic.display", "category": "lifecycle", "messageType": "Default", **fields}


class DisplayLogTests(unittest.TestCase):
    def test_timestamp_ordering_preserves_input_and_timezone(self):
        values = [record("created device", "2026-09-16 05:20:02.123456789-0600"),
                  record("link detected", "2026-09-16T11:20:00Z")]
        result = logs.analyze_records(values)
        self.assertEqual([item["input_index"] for item in result["normalized_records"]], [0, 1])
        self.assertEqual(result["summary"]["timestamp_order"][0]["before_input_index"], 1)
        self.assertEqual(logs.timestamp_ns(values[0]["timestamp"]) % 1000000000, 123456789)

    def test_equal_timestamps_have_no_causal_order(self):
        result = logs.analyze_records([record("link detected"), record("created device")])
        edge = result["summary"]["timestamp_order"][0]
        self.assertEqual(edge["confidence"], "UNKNOWN")
        self.assertFalse(edge["causal_order_proved"])

    def test_process_subsystem_and_category_filtering(self):
        self.assertFalse(logs.in_scope(record("created device", processImagePath="/usr/bin/other")))
        self.assertFalse(logs.in_scope(record("created device"), subsystems=("other",)))
        self.assertFalse(logs.in_scope(record("created device"), categories=("other",)))
        self.assertTrue(logs.in_scope(record("created device"), subsystems=("synthetic.display",)))
        self.assertFalse(logs.in_scope(record("created device", eventMessage="unrelated display activity")))

    def test_redacted_message_does_not_invent_identity(self):
        result = logs.analyze_records([record("created source id=<private> -> DPTX0")])
        self.assertEqual(result["normalized_records"][0]["classification"]["events"], ["UNKNOWN_EVENT"])
        self.assertEqual(result["summary"]["source_identity"], "PUBLIC_LOG_SOURCE_IDENTITIES_NOT_ESTABLISHED")

    def test_second_sink_looking_value_is_not_second_entity(self):
        result = logs.analyze_records([record("sink=2 EDID length=256")])
        self.assertEqual(result["summary"]["second_downstream"], "NO_SECOND_DOWNSTREAM_ENTITY_IN_SCOPED_LOGS")

    def test_false_positive_sink_number_is_not_discovery(self):
        result = logs.analyze_records([record("sink count query returned 2 cached flags")])
        self.assertFalse(result["normalized_records"][0]["classification"]["second_downstream_statement"])

    def test_explicit_second_downstream_discovery_is_not_source_proof(self):
        result = logs.analyze_records([record("discovered second downstream sink on port 2")])
        self.assertEqual(result["summary"]["second_downstream"], "SECOND_DOWNSTREAM_ENTITY_LOGGED")
        self.assertFalse(result["summary"]["same_dptx_multi_source_established"])

    def test_mirror_keyword_without_decision(self):
        result = logs.analyze_records([record("mirror capability flag=1")])
        self.assertEqual(result["summary"]["mirror_policy"], "PUBLIC_LOG_MIRROR_POLICY_UNRESOLVED")

    def test_explicit_mirror_decision(self):
        result = logs.analyze_records([record("policy selected mirror mode for this connection")])
        self.assertEqual(result["summary"]["mirror_policy"], "PUBLIC_LOG_MIRROR_POLICY_FOUND")

    def test_mst_mentioned_without_decision(self):
        result = logs.analyze_records([record("MST capability version=1")])
        self.assertEqual(result["summary"]["mst_policy"], "PUBLIC_LOG_MST_POLICY_GATE_UNRESOLVED")

    def test_explicit_mst_rejection(self):
        result = logs.analyze_records([record("MST topology rejected because link is non-tunneled")])
        self.assertEqual(result["summary"]["mst_policy"], "PUBLIC_LOG_MST_POLICY_GATE_FOUND")

    def test_source_word_in_unrelated_context(self):
        result = logs.analyze_records([record("source file line 42, stream buffer allocations=2")])
        self.assertEqual(result["summary"]["source_identity"], "PUBLIC_LOG_SOURCE_IDENTITIES_NOT_ESTABLISHED")

    def test_explicit_source_identity_binding(self):
        result = logs.analyze_records([record("source 0 -> DPTX0"), record("source 1 -> DPTX0")])
        self.assertEqual(result["summary"]["source_identity"], "PUBLIC_LOG_SOURCE_IDENTITIES_FOUND")
        self.assertEqual(result["normalized_records"][1]["classification"]["source_bindings"][0]["source_label"], "1")
        self.assertFalse(result["summary"]["same_dptx_multi_source_established"])

    def test_missing_activity_ids_remain_missing(self):
        value = logs.analyze_records([record("created device")])["normalized_records"][0]
        self.assertIsNone(value["activity_id"])
        self.assertIsNone(value["signpost_id"])

    def test_reconnect_sequence_order_is_log_time_not_user_time(self):
        values = [record("HPD changed to low", "2026-09-16T11:20:01Z"),
                  record("HPD changed to high", "2026-09-16T11:20:03Z"),
                  record("announced EPIC service", "2026-09-16T11:20:04Z"),
                  record("created logical display", "2026-09-16T11:20:05Z")]
        result = logs.analyze_records(values)
        self.assertEqual(len(result["summary"]["timestamp_order"]), 3)
        self.assertTrue(all(item["timestamp_kind"] == "LOG_EVENT_TIMESTAMP" for item in result["normalized_records"]))
        self.assertTrue(all(not edge["causal_order_proved"] for edge in result["summary"]["timestamp_order"]))

    def test_irrelevant_home_path_or_network_content_is_dropped(self):
        result = logs.analyze_records([record("opened /Users/private-person/Documents/secret.txt"),
                                       record("url https://private.example/document")])
        self.assertFalse(result["filtered_records"])
        self.assertEqual(result["summary"]["dropped_for_privacy"], 2)

    def test_personal_serial_redacted_not_reconstructed(self):
        result = logs.analyze_records([record("device serial=PRIVATE123 initialized")])
        self.assertNotIn("PRIVATE123", str(result))
        self.assertIn("[REDACTED_IDENTIFIER]", result["normalized_records"][0]["message"])

    def test_only_typed_registry_id_can_correlate(self):
        message = "DCPDPDeviceProxy<0x10000def1> Unit 0 DCPEXT0 registry entry id=0x10000def2"
        identifiers = logs.explicit_identifiers(message)
        self.assertEqual(identifiers["registry_entry_id"], ["0x10000def2"])
        self.assertEqual(identifiers["unit"], ["0"])

    def test_negated_or_hypothetical_decisions_are_unknown(self):
        for message in ("MST not disabled", "example source 1 -> DPTX0", "would select mirror mode"):
            result = logs.analyze_records([record(message)])
            self.assertEqual(result["normalized_records"][0]["classification"]["events"], ["UNKNOWN_EVENT"])

    def test_window_and_record_budgets(self):
        self.assertFalse(logs.in_scope(record("created device", "2026-09-16T11:30:00Z")))
        with self.assertRaises(ValueError):
            logs.analyze_records([record("created device")] * 1001)
        with self.assertRaises(ValueError):
            logs.timestamp_ns("2026-09-16 11:20:00")

    def test_exact_historical_command_only(self):
        with mock.patch.object(logs.subprocess, "Popen") as process:
            for command in (["/usr/bin/log", "stream"], ["/usr/bin/log", "show"], ["sudo", "log", "show"]):
                with self.assertRaises(ValueError):
                    logs.execute_historical(command)
            process.assert_not_called()
        self.assertIn(logs.PREDICATE, logs.historical_command())
        self.assertNotIn("--last", logs.historical_command())

    def test_ndjson_duplicate_and_malformed_input_rejected(self):
        for raw in (b'{"timestamp":1,"timestamp":2}', b'{bad}', b'42'):
            with self.assertRaises(ValueError):
                logs.parse_ndjson(raw)
        self.assertEqual(logs.parse_ndjson(b"[]"), [])
        self.assertEqual(logs.parse_ndjson(logs.json_bytes(record("created device")))[0]["eventMessage"], record("created device")["eventMessage"])

    def test_documented_predicate_and_window_are_exact(self):
        expected = ('process == "kernel" AND (\n'
                    '\teventMessage CONTAINS[c] "DCPDPDeviceProxy" OR\n'
                    '\teventMessage CONTAINS[c] "DCPDPServiceProxy" OR\n'
                    '\teventMessage CONTAINS[c] "DCPAVVideoInterfaceProxy" OR\n'
                    '\teventMessage CONTAINS[c] "AppleDCPDPTXRemotePortProxy" OR\n'
                    '\teventMessage CONTAINS[c] "AppleDCPDP2HDMI"\n)')
        self.assertEqual(logs.PREDICATE, expected)
        self.assertEqual(logs.timestamp_ns(logs.WINDOW_END) - logs.timestamp_ns(logs.WINDOW_START), 950000000000)

    def test_correlation_does_not_use_pointer_or_timestamp(self):
        snapshot = {"capture_generation": "synthetic", "graph": {"objects": [
            {"registry_entry_id": "0x100", "class": "DCPDPDeviceProxy", "properties": {"Unit": 0},
             "registry_path": "IOService:/RTBuddy(DCPEXT0)/DCPDPDeviceProxy"}]}}
        source = [record("pointer=0x100"), record("Unit 0 DCPEXT0"), record("registry entry id=0x100")]
        values = logs.analyze_records(source)["normalized_records"]
        correlations = logs.correlate(values, snapshot)
        self.assertEqual(correlations[0]["confidence"], "UNKNOWN")
        self.assertEqual(correlations[1]["confidence"], "INFERRED_LOG")
        self.assertEqual(correlations[2]["explicit_registry_id_value_matches"], ["0x100"])
        self.assertFalse(any(value["source_identity_proved"] for value in correlations))

    def test_mocked_historical_capture_is_hash_bound_and_no_live_command(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory).resolve()
            baseline = root / "artifacts/runtime/m5p3/connected"
            baseline.mkdir(parents=True)
            (baseline / "snapshot.json").write_bytes(logs.json_bytes({"capture_generation": "synthetic", "graph": {"objects": []}}))
            command = {"status": "OK", "argv": logs.historical_command(), "output_complete": True}
            raw = logs.json_bytes(record("created device Unit 0 DCPEXT0"))
            with mock.patch.object(logs, "REPOSITORY", root), mock.patch.object(logs, "m5p3_inputs", return_value={"synthetic": True}), \
                    mock.patch.object(logs, "tool_provenance", return_value={"synthetic": True}), \
                    mock.patch.object(logs, "execute_historical", return_value=(command, raw)) as execute, \
                    contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(logs.historical_capture(), 0)
                execute.assert_called_once_with(logs.historical_command())
                output = root / "artifacts/runtime/m5p4/historical"
                manifest = json.loads((output / "manifest.json").read_bytes())
                self.assertEqual(manifest["historical_availability"], "M5P3_HISTORICAL_LOGS_RETAINED")
                self.assertFalse(manifest["live_cycle_performed"])
                self.assertIsNone(manifest["user_transition_timestamp"])
                for name, expected in json.loads((output / "hashes.json").read_bytes()).items():
                    self.assertEqual(logs.digest((output / name).read_bytes()), expected)
                with self.assertRaises(ValueError):
                    logs.historical_capture()

    def test_empty_logs_are_not_evidence_of_storage_expiration(self):
        result = logs.analyze_records([])
        self.assertEqual(result["summary"]["second_downstream"], "SECOND_DOWNSTREAM_LOG_EVIDENCE_UNRESOLVED")
        self.assertFalse(result["summary"]["same_dptx_multi_source_established"])

    def test_redacted_identifier_and_non_system_sender_are_not_retained(self):
        value = record("created device guid=private-guid", senderImagePath="/Volumes/personal/location")
        result = logs.analyze_records([value])
        self.assertIsNone(result["normalized_records"][0]["sender_image"])
        self.assertNotIn("private-guid", str(result))
        self.assertEqual(result["summary"]["second_downstream"], "SECOND_DOWNSTREAM_LOG_EVIDENCE_UNRESOLVED")


if __name__ == "__main__":
    unittest.main()