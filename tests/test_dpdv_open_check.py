import copy
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tools"))
import dpdv_open_check as experiment

EXECUTABLES = tuple(pathlib.Path(value).resolve() for value in sys.argv[1:4]) if len(sys.argv) == 4 else ()


def public_fixture():
    processor = "IOService:/root/dcpext0@F6E00000/RTBuddy(DCPEXT0)"
    device_path = processor + "/endpoint/DCPDPDeviceProxy"
    service_path = processor + "/service/DCPDPServiceProxy"
    link_path = "IOService:/root/Port-USB-C@4/DisplayPort"
    def entry(class_name, entry_id, path, properties):
        return {"class": class_name, "entry_id_raw": entry_id, "path": path,
                "property_status_code_raw": 0, "properties": properties}
    return {"display_enumeration_ok": True, "errors": [], "host": {"soc": "Apple M5"},
            "displays": [{"active": True, "built_in": False, "mode_width": 1920, "mode_height": 1080,
                          "pixel_width": 1920, "pixel_height": 1080, "refresh_hz": 60, "in_mirror_set": False}],
            "public_displayport_interface": {"active_external_display_count": 1, "result": "PUBLIC_IOFRAMEBUFFER_PATH_UNAVAILABLE"},
            "external_dp_candidates": [{"location": "External", "unit_raw": 0, "device_interface_supported_raw": True,
                "matching_service_count": 1, "processor_path": processor, "device_path": device_path, "service_path": service_path,
                "device_entry_id_raw": 100, "service_entry_id_raw": 200, "active_transport_paths": [link_path]}],
            "registry": {
                "DCPDPDeviceProxy": {"query_status_code_raw": 0, "entries": [entry("DCPDPDeviceProxy", 100, device_path,
                    {"Location": "External", "Unit": 0, "IODPDeviceUserInterfaceSupported": True})]},
                "DCPDPServiceProxy": {"query_status_code_raw": 0, "entries": [entry("DCPDPServiceProxy", 200, service_path,
                    {"Location": "External", "Unit": 0, "IODPServiceUserInterfaceSupported": True})]},
                "IOPortTransportStateDisplayPort": {"query_status_code_raw": 0, "entries": [entry("IOPortTransportStateDisplayPort", 300, link_path,
                    {"Active": True, "HPD_State": 2, "LaneCount": 2, "LinkRate": 4, "LinkRateDescription": "8.1 Gbps (HBR3)", "Tunneled": False, "SinkCount": 1})]}}}


class DpdvContractTests(unittest.TestCase):
    @unittest.skipUnless(EXECUTABLES, "Binary paths required")
    def test_exact_import_and_one_callsite_audit(self):
        audit = experiment.audit_binaries(*EXECUTABLES)
        self.assertEqual(len(audit), 3)

    @unittest.skipUnless(EXECUTABLES, "Binary paths required")
    def test_existing_attempt_marker_refuses_without_spawning(self):
        with tempfile.TemporaryDirectory() as directory:
            marker = pathlib.Path(directory) / "attempted"
            marker.write_text("existing forensic marker\n")
            completed = subprocess.run([str(EXECUTABLES[1]), "--open-once", "/nonexistent/macmst_dpdv_open_helper",
                                        "1", "2", "3", str(marker)], capture_output=True, text=True, check=True)
            result = json.loads(completed.stdout)
            self.assertEqual(result["runner_outcome"], "attempt_marker_refused")
            self.assertEqual(result["spawn_attempts"], 0)
            self.assertEqual(marker.read_text(), "existing forensic marker\n")
            self.assertEqual(completed.stderr, "")

    def test_valid_preflight_and_transient_id_comparison(self):
        report = public_fixture()
        state, identities = experiment.preflight(report)
        self.assertEqual(identities, {"device_id_raw": 100, "service_id_raw": 200, "transport_id_raw": 300})
        changed = copy.deepcopy(report)
        changed["external_dp_candidates"][0]["device_entry_id_raw"] = 101
        changed["registry"]["DCPDPDeviceProxy"]["entries"][0]["entry_id_raw"] = 101
        self.assertEqual(experiment.preflight(changed)[0], state)
        self.assertEqual(experiment.comparison(state, experiment.semantic_state(changed)), "NO_PUBLIC_DISPLAY_STATE_CHANGE")

    def test_preflight_stop_records_zero_attempts_without_subprocesses(self):
        with tempfile.TemporaryDirectory() as directory:
            output = pathlib.Path(directory)
            before = output / "before"
            before.mkdir()
            captured = public_fixture()
            captured["displays"][0]["active"] = False
            (before / "macmst-probe.json").write_text(json.dumps(captured))
            (before / "manifest.json").write_text("{}")
            experiment.record_preflight_stop(output, {"global_gate": "NOT_READY_FOR_DPCD_TEST"}, before,
                                             "Expected one active external logical display")
            result = json.loads((output / "result.json").read_text())
            self.assertEqual(result["outcome"], "EXPERIMENT_NOT_RUN")
            self.assertEqual(result["private_open_attempts"], 0)
            self.assertEqual(result["helper_spawn_attempts"], 0)
            self.assertEqual(result["before_state"]["external_display_count"], 0)
            self.assertEqual(result["before_report_sha256"], experiment.sha256(before / "macmst-probe.json"))
            self.assertFalse((output / "prepared.json").exists())

    def test_ambiguity_and_missing_external_stop_preflight(self):
        for candidates in ([], [public_fixture()["external_dp_candidates"][0]] * 2):
            report = public_fixture()
            report["external_dp_candidates"] = candidates
            with self.assertRaises(ValueError):
                experiment.preflight(report)
        report = public_fixture()
        report["displays"] = []
        with self.assertRaises(ValueError):
            experiment.preflight(report)

    def test_wrong_flags_types_path_and_link_stop_preflight(self):
        for key, value in (("HPD_State", 0), ("LaneCount", 4), ("LinkRate", 3), ("SinkCount", 2),
                           ("Active", False), ("Tunneled", True), ("LaneCount", True)):
            report = public_fixture()
            report["registry"]["IOPortTransportStateDisplayPort"]["entries"][0]["properties"][key] = value
            with self.assertRaises(ValueError):
                experiment.preflight(report)
        for key, value in (("Location", "Embedded"), ("Unit", False), ("IODPDeviceUserInterfaceSupported", False)):
            report = public_fixture()
            report["registry"]["DCPDPDeviceProxy"]["entries"][0]["properties"][key] = value
            with self.assertRaises(ValueError):
                experiment.preflight(report)

    def test_semantic_after_changes_and_unavailable_are_distinct(self):
        before = experiment.semantic_state(public_fixture())
        for field, value in (("mode_width", 1280), ("refresh_hz", 75)):
            changed = public_fixture()
            changed["displays"][0][field] = value
            self.assertEqual(experiment.comparison(before, experiment.semantic_state(changed)), "PUBLIC_DISPLAY_STATE_CHANGED")
        changed = public_fixture()
        changed["displays"] = []
        self.assertEqual(experiment.comparison(before, experiment.semantic_state(changed)), "PUBLIC_DISPLAY_STATE_CHANGED")
        self.assertEqual(experiment.comparison(before, None), "AFTER_STATE_UNAVAILABLE")

    def test_dry_run_requires_reaped_zero_operation_and_identity_agreement(self):
        identities = {"device_id_raw": 100, "service_id_raw": 200, "transport_id_raw": 300}
        result = {"runner_outcome": "success", "spawn_attempts": 1, "reaped": True, "termination_sent": False,
                  "failure_trigger": None, "exit_code": 0, "signal_raw": None, "selector_calls": 0,
                  "stdout_bytes": 64, "stderr_bytes_omitted": 0,
                  "frame": {"phase": "DRY_RUN_READY", "flags": 0, "open_return_raw": None, "close_return_raw": None, **identities}}
        self.assertTrue(experiment.valid_dry_run(result, identities))
        for key, value in (("reaped", False), ("spawn_attempts", 2), ("selector_calls", 1),
                   ("stdout_bytes", 128), ("stderr_bytes_omitted", 1)):
            self.assertFalse(experiment.valid_dry_run({**result, key: value}, identities))
        self.assertFalse(experiment.valid_dry_run(result, {**identities, "device_id_raw": 999}))

    def test_outcomes_never_promote_timeout_or_changed_state(self):
        result = {"runner_outcome": "success", "reaped": True, "exit_code": 0, "spawn_attempts": 1,
                  "termination_sent": False, "signal_raw": None, "frame": {"phase": "CLOSE_SUCCEEDED"}}
        self.assertEqual(experiment.classify(result, "NO_PUBLIC_DISPLAY_STATE_CHANGE"), "DPDV_OPEN_CLOSE_SUCCEEDED_NO_PUBLIC_STATE_CHANGE")
        self.assertEqual(experiment.classify(result, "PUBLIC_DISPLAY_STATE_CHANGED"), "DPDV_OPEN_AFFECTED_DISPLAY_STATE")
        self.assertEqual(experiment.classify({**result, "runner_outcome": "reap_timeout"}, "NO_PUBLIC_DISPLAY_STATE_CHANGE"), "DPDV_OPEN_RUNTIME_HANG")
        denied = {**result, "runner_outcome": "operation_failure", "frame": {"phase": "OPEN_FAILED", "connection_returned": False}}
        self.assertEqual(experiment.classify(denied, "NO_PUBLIC_DISPLAY_STATE_CHANGE"), "DPDV_OPEN_DENIED_CLEANLY")
        self.assertIsNone(experiment.classify(denied, "AFTER_STATE_UNAVAILABLE"))
        self.assertEqual(experiment.classify({**result, "frame": {"phase": "CLOSE_FAILED"}}, "NO_PUBLIC_DISPLAY_STATE_CHANGE"), "DPDV_CLOSE_FAILED")


if __name__ == "__main__":
    unittest.main(argv=[sys.argv[0]])