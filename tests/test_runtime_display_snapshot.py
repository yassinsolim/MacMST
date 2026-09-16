import importlib.util
import contextlib
import io
import json
import pathlib
import plistlib
import sys
import tempfile
import unittest
from unittest import mock


ROOT = pathlib.Path(__file__).resolve().parents[1]
with mock.patch.object(sys, "path", [str(ROOT / "tools")] + sys.path):
    SPEC = importlib.util.spec_from_file_location("runtime_display_snapshot", ROOT / "tools/runtime_display_snapshot.py")
    runtime = importlib.util.module_from_spec(SPEC)
    SPEC.loader.exec_module(runtime)


def snapshot(generation, children, properties=None, boot="synthetic-boot"):
    tree = runtime.parse_registry_tree(("+-o Private Computer <class IORegistryRoot, id 0x1>\n"
        "  +-o arm-io <class AppleARMIO, id 0x2>\n"
        "    +-o dcpext0 <class AppleARMIODevice, id 0x3>\n" + children).encode())
    return {"schema_version": 1, "capture_generation": generation, "capture_policy_sha256": "synthetic-policy",
            "environment": {"boot_session": boot},
            "graph": runtime.normalize_registry(tree, properties or {}, generation)}


DEVICE = "      +-o DCPDPDeviceProxy <class DCPDPDeviceProxy, id 0x4>\n"


class RuntimeParserTests(unittest.TestCase):
    def test_persistent_object(self):
        result = runtime.diff_snapshots(snapshot("off", DEVICE), snapshot("on", DEVICE))
        event = next(item for item in result["events"] if item["after"] == "0x4")
        self.assertEqual(event["kinds"], ["PERSISTENT"])
        self.assertIsNone(event["stable_semantic_id"])

    def test_created_object(self):
        result = runtime.diff_snapshots(snapshot("off", ""), snapshot("on", DEVICE))
        self.assertIn("CREATED_ON_CONNECT", next(item for item in result["events"] if item["after"] == "0x4")["kinds"])

    def test_removed_object(self):
        result = runtime.diff_snapshots(snapshot("off", DEVICE), snapshot("on", ""))
        self.assertIn("REMOVED_ON_CONNECT", next(item for item in result["events"] if item["before"] == "0x4")["kinds"])

    def test_property_change(self):
        def properties(value):
            return {"DCPDPDeviceProxy": [{"entry_id": "0x4", "properties": runtime.select_properties({"Unit": value})}]}
        result = runtime.diff_snapshots(snapshot("off", DEVICE, properties(0)), snapshot("on", DEVICE, properties(1)))
        event = next(item for item in result["events"] if item["after"] == "0x4")
        self.assertIn("PROPERTY_CHANGED", event["kinds"])
        self.assertEqual(event["property_changes"]["Unit"]["after"], 1)

    def test_recreated_id_is_only_a_correspondence_candidate(self):
        result = runtime.diff_snapshots(snapshot("off", DEVICE), snapshot("on", DEVICE.replace("0x4", "0x5")))
        event = next(item for item in result["events"] if item["after"] == "0x5")
        self.assertEqual(event["kinds"], ["IDENTITY_RECREATED"])
        self.assertFalse(event["same_object_proved"])
        self.assertIsNone(event["stable_semantic_id"])

    def test_multiple_child_objects(self):
        added = DEVICE + "        +-o DCPAVServiceProxy <class DCPAVServiceProxy, id 0x5>\n" + \
            "        +-o DCPAVVideoInterfaceProxy <class DCPAVVideoInterfaceProxy, id 0x6>\n"
        result = runtime.diff_snapshots(snapshot("off", DEVICE), snapshot("on", added))
        self.assertIn("CHILD_ADDED", next(item for item in result["events"] if item["after"] == "0x4")["kinds"])
        self.assertEqual(len([item for item in result["events"] if item["kinds"] == ["CREATED_ON_CONNECT"]]), 2)

    def test_ambiguous_provider_mapping(self):
        tree = runtime.parse_registry_tree(("+-o Private <class IORegistryRoot, id 0x1>\n"
            "  +-o dcpext0 <class AppleDCPExpert, id 0x2>\n"
            "    +-o DCPDPDeviceProxy <class DCPDPDeviceProxy, id 0x4>\n"
            "  +-o dcpext1 <class AppleDCPExpert, id 0x3>\n"
            "    +-o DCPDPDeviceProxy <class DCPDPDeviceProxy, id 0x4>\n").encode())
        graph = runtime.normalize_registry(tree, {}, "off")
        node = next(item for item in graph["objects"] if item["registry_entry_id"] == "0x4")
        self.assertIsNone(node["provider"])
        self.assertEqual(node["provider_resolution"], "AMBIGUOUS")
        self.assertFalse(any(item["child"] == "0x4" for item in graph["edges"]))

    def test_two_sinks_never_prove_two_sources(self):
        children = DEVICE + "        +-o IODisplayA <class IODisplay, id 0x5>\n" + \
            "        +-o IODisplayB <class IODisplay, id 0x6>\n"
        result = runtime.diff_snapshots(snapshot("off", ""), snapshot("on", children))
        self.assertEqual(result["same_dptx_sources"], "PASSIVE_SAME_DPTX_SOURCE_EVIDENCE_NOT_ESTABLISHED")
        self.assertFalse(result["source_identity_inferred_from_counts"])

    def test_two_epic_units_never_prove_two_sources(self):
        children = DEVICE + "      +-o DCPDPDeviceProxy2 <class DCPDPDeviceProxy, id 0x5>\n"
        properties = {"DCPDPDeviceProxy": [{"entry_id": identity, "properties": runtime.select_properties({"EPICUnit": unit})}
                                          for identity, unit in (("0x4", 0), ("0x5", 1))]}
        connected = snapshot("on", children, properties)
        self.assertEqual(len(runtime.graph_summary(connected["graph"])["epic_objects"]), 2)
        result = runtime.diff_snapshots(snapshot("off", ""), connected)
        self.assertEqual(result["same_dptx_sources"], "PASSIVE_SAME_DPTX_SOURCE_EVIDENCE_NOT_ESTABLISHED")

    def test_no_same_id_persistence_across_boots(self):
        result = runtime.diff_snapshots(snapshot("off", DEVICE, boot="one"), snapshot("on", DEVICE, boot="two"))
        self.assertFalse(result["same_boot"])
        self.assertFalse(any("PERSISTENT" in item["kinds"] for item in result["events"]))

    def test_provider_changed(self):
        connected = "      +-o DCPAVServiceProxy <class DCPAVServiceProxy, id 0x5>\n" + \
            "        +-o DCPDPDeviceProxy <class DCPDPDeviceProxy, id 0x4>\n"
        result = runtime.diff_snapshots(snapshot("off", DEVICE), snapshot("on", connected))
        self.assertIn("PROVIDER_CHANGED", next(item for item in result["events"] if item["after"] == "0x4")["kinds"])

    def test_raw_typed_bytes_and_sensitive_values(self):
        raw = plistlib.dumps([{"IORegistryEntryID": 4, "EPICUnit": 0, "PortAddress": b"\x00\xff",
                              "SerialNumber": "PRIVATE", "IODisplayEDID": b"PRIVATE", "Unknown": "PRIVATE",
                              "IOPropertyMatch": {"EPICName": "dcpdp-device-epic", "serial": "PRIVATE"}}])
        result = runtime.parse_registry_properties(raw)
        self.assertNotIn("PRIVATE", json.dumps(result))
        self.assertEqual(result[0]["properties"]["values"]["PortAddress"]["raw_hex"], "00ff")

    def test_tree_omits_unrelated_names_and_personal_root(self):
        graph = snapshot("off", DEVICE + "      +-o Personal Phone <class IOUSBHostDevice, id 0x8>\n")["graph"]
        self.assertNotIn("Personal", json.dumps(graph))
        self.assertNotIn("Private Computer", json.dumps(graph))
        self.assertFalse(any(item["registry_entry_id"] == "0x8" for item in graph["objects"]))

    def test_current_ioreg_entry_root_is_structural_and_name_is_omitted(self):
        tree = runtime.parse_registry_tree(b'+-o PRIVATE NAME <class IORegistryEntry, id 0x100000100>\n  +-o dcp <class AppleDCPExpert, id 0x100000200>\n')
        graph = runtime.normalize_registry(tree, {}, "off")
        self.assertNotIn("PRIVATE NAME", json.dumps(graph))
        root = next(item for item in graph["objects"] if item["provider_resolution"] == "ROOT")
        self.assertEqual(root["name"], "IOServiceRoot")
        self.assertEqual(root["registry_path"], "IOService:/")
        self.assertEqual(graph["objects"][1]["registry_path"], "IOService:/dcp")

    def test_property_conflict_is_not_silently_overwritten(self):
        properties = {name: [{"entry_id": "0x4", "properties": runtime.select_properties({"Unit": unit})}]
                      for name, unit in (("first", 0), ("second", 1))}
        graph = snapshot("off", DEVICE, properties)["graph"]
        node = next(item for item in graph["objects"] if item["registry_entry_id"] == "0x4")
        self.assertNotIn("Unit", node["properties"])
        self.assertEqual(node["conflicting_property_keys"], ["Unit"])

    def test_invalid_or_duplicate_generation_rejected(self):
        value = snapshot("off", DEVICE)
        with self.assertRaises(ValueError):
            runtime.diff_snapshots(value, value)
        with self.assertRaises(ValueError):
            runtime.entry_id(True)
        with self.assertRaises(ValueError):
            runtime.parse_registry_tree(b"not an IOService tree")

    def test_empty_successful_class_query_is_not_parse_failure(self):
        self.assertEqual(runtime.parse_registry_properties(b""), [])
        self.assertEqual(runtime.parse_registry_properties(plistlib.dumps([])), [])

    def test_public_command_allowlist_rejects_privilege_and_device_tools(self):
        with mock.patch.object(runtime.subprocess, "run") as runner:
            for argv in (("sudo", "ioreg"), ("/bin/sh", "-c", "ioreg"), ("build/macmst", "probe"), ("/usr/sbin/ioreg", "-l")):
                with self.assertRaises(ValueError):
                    runtime.execute_public(argv)
            runner.assert_not_called()
        self.assertEqual(len(runtime.command_plan()), 42)

    def test_profiler_keeps_target_descriptors_not_unrelated_devices(self):
        raw = {"SPDisplaysDataType": [{"spdisplays_ndrvs": [{"_name": "PRIVATE DISPLAY",
                "spdisplays_connection_type": "spdisplays_internal", "_spdisplays_display-serial-number": "PRIVATE SERIAL"}]}],
               "SPUSBDataType": [{"_name": "PRIVATE COMPUTER", "_items": [
                   {"_name": "PRIVATE PHONE", "vendor_id": "0x1234", "product_id": "0x5678", "serial_num": "PRIVATE SERIAL"},
                   {"_name": "USB Hub", "vendor_id": "0x05e3 (Genesys)", "product_id": "0x0625", "serial_num": "PRIVATE SERIAL"}]}],
               "SPThunderboltDataType": [{"_name": "PRIVATE COMPUTER", "uid": "PRIVATE UID", "receptacle_1": {"link_status_key": "inactive"}}]}
        result = runtime.parse_profiler(json.dumps(raw).encode())
        self.assertNotIn("PRIVATE", json.dumps(result))
        self.assertEqual(len(result["usb_hub_candidates"]), 1)
        self.assertTrue(result["displays"][0]["builtin"])
        self.assertEqual(result["thunderbolt_port_context"][0]["receptacles"]["receptacle_1"]["link_status_key"], "inactive")

    def test_profiler_without_required_sections_fails(self):
        with self.assertRaises(ValueError):
            runtime.parse_profiler(b'{}')
        with self.assertRaises(ValueError):
            runtime.parse_profiler(b'{"SPDisplaysDataType":NaN,"SPUSBDataType":[]}')

    def test_unknown_display_location_does_not_remove_monitor_record(self):
        profiler = runtime.parse_profiler(json.dumps({"SPDisplaysDataType": [{"spdisplays_ndrvs": [
            {"_name": "Color LCD", "spdisplays_connection_type": "spdisplays_internal"},
            {"_name": "VG248", "_spdisplays_display-vendor-id": "469", "_spdisplays_display-product-id": "24a5",
             "spdisplays_online": "spdisplays_yes", "spdisplays_mirror": "spdisplays_off"}]}],
            "SPUSBDataType": []}).encode())
        tree = runtime.parse_registry_tree(b'+-o root <class IORegistryRoot, id 0x1>\n  +-o dcp <class AppleDCPExpert, id 0x2>\n')
        value, _, _ = runtime.build_snapshot(tree, tree, {}, profiler, {"boot_before": 1, "boot_after": 1}, "connected", "on", {})
        summary = value["summary"]
        self.assertEqual((summary["display_record_count"], summary["builtin_display_count"],
                          summary["external_display_count"], summary["unknown_display_location_count"]), (2, 1, 0, 1))
        self.assertEqual(summary["expected_monitor_record_count"], 1)
        self.assertIsNone(profiler["displays"][1]["builtin"])
        self.assertEqual(value["source_semantics"], "NOT_ESTABLISHED_BY_PUBLIC_IDENTITIES")

    def test_two_authentication_providers_same_unit_are_not_source_identities(self):
        children = ("      +-o dcpdptx-hdcp-auth-session:0 <class AFKEndpointInterface, id 0x4>\n"
                    "        +-o auth <class AppleDCPDPTXRemoteHDCPAuthSessionProxy, id 0x5>\n"
                    "      +-o dcpdptx-hdcp-auth-session:0 <class AFKEndpointInterface, id 0x6>\n"
                    "        +-o auth <class AppleDCPDPTXRemoteHDCPAuthSessionProxy, id 0x7>\n")
        properties = {"AFKEndpointInterface": [{"entry_id": identity, "properties": runtime.select_properties({
            "EPICName": "dcpdptx-hdcp-auth-session", "EPICUnit": 0, "EPICProviderClass": provider})}
            for identity, provider in (("0x4", "AppleDCPDPTXHDCP1Controller"), ("0x6", "AppleDCPDPTXHDCP2Controller"))]}
        connected = snapshot("on", children, properties)
        result = runtime.diff_snapshots(snapshot("off", ""), connected)
        self.assertEqual(runtime.graph_summary(connected["graph"])["class_counts"]["AppleDCPDPTXRemoteHDCPAuthSessionProxy"], 2)
        self.assertTrue(all(not node["source_identity_established"] for node in connected["graph"]["objects"]))
        self.assertTrue(all(node["stable_semantic_id"] is None for node in connected["graph"]["objects"]))
        self.assertEqual(result["same_dptx_sources"], "PASSIVE_SAME_DPTX_SOURCE_EVIDENCE_NOT_ESTABLISHED")

    def test_newly_retained_ancestor_is_excluded_from_relevant_cardinality(self):
        children = ("      +-o bridge <class IOService, id 0x4>\n"
                    "        +-o DCPDPDeviceProxy <class DCPDPDeviceProxy, id 0x5>\n")
        connected = snapshot("on", children)
        result = runtime.diff_snapshots(snapshot("off", ""), connected)
        ancestor = next(node for node in connected["graph"]["objects"] if node["registry_entry_id"] == "0x4")
        self.assertEqual(ancestor["scope"], "ancestor_context")
        self.assertNotIn("IOService", {row["class"] for row in result["cardinality"]})
        self.assertEqual(len([event for event in result["events"] if event["kinds"] == ["CREATED_ON_CONNECT"]]), 2)
        self.assertIn("not proof of causation", result["causation_limit"])

    def test_normalization_source_hash_mismatch_blocks_diff(self):
        before, after = snapshot("off", DEVICE), snapshot("on", DEVICE)
        before["tool_provenance"] = {"source_sha256": {"capture": "old"}}
        after["tool_provenance"] = {"source_sha256": {"capture": "new"}}
        with self.assertRaisesRegex(ValueError, "normalization code differs"):
            runtime.diff_snapshots(before, after)

    def test_bool_and_integer_property_changes_are_distinct(self):
        properties = {"DCPDPDeviceProxy": [{"entry_id": "0x4", "properties": runtime.select_properties({"Tunneled": True})}]}
        before = snapshot("off", DEVICE, properties)
        properties["DCPDPDeviceProxy"][0]["properties"] = runtime.select_properties({"Tunneled": 1})
        after = snapshot("on", DEVICE, properties)
        result = runtime.diff_snapshots(before, after)
        self.assertIn("PROPERTY_CHANGED", next(item for item in result["events"] if item["after"] == "0x4")["kinds"])

    def test_missing_confirmation_stops_before_provenance_or_commands(self):
        with tempfile.TemporaryDirectory() as directory, mock.patch.object(runtime, "REPOSITORY", pathlib.Path(directory)), \
                mock.patch.object(runtime, "tool_provenance") as provenance, mock.patch.object(runtime, "execute_public") as execute:
            with self.assertRaises(ValueError):
                runtime.capture("connected", "on", pathlib.Path(directory) / "artifacts/runtime/m5p3/connected")
            provenance.assert_not_called()
            execute.assert_not_called()

    def test_output_cannot_overwrite_or_escape(self):
        with tempfile.TemporaryDirectory() as directory, mock.patch.object(runtime, "REPOSITORY", pathlib.Path(directory)):
            for path in (pathlib.Path(directory), pathlib.Path(directory) / "outside", pathlib.Path(directory) / "artifacts/runtime/m5p3"):
                with self.assertRaises(ValueError):
                    runtime.safe_output(path)

    def test_boot_metadata_has_units_and_no_unrelated_text(self):
        result = runtime.boot_value(b'{ sec = 1000, usec = 250 } Wed Sep 16 00:00:00 2026\n')
        self.assertEqual(result, {"seconds_since_unix_epoch": 1000, "microseconds": 250})

    def test_capture_replays_from_filtered_inputs(self):
        tree = runtime.parse_registry_tree(("+-o PRIVATE COMPUTER <class IORegistryRoot, id 0x1>\n"
            "  +-o arm-io <class AppleARMIO, id 0x2>\n"
            "    +-o dcpext0 <class AppleARMIODevice, id 0x3>\n" + DEVICE).encode())
        profiler = runtime.parse_profiler(json.dumps({"SPDisplaysDataType": [{"spdisplays_ndrvs": [
            {"_name": "Color LCD", "spdisplays_connection_type": "spdisplays_internal"}]}], "SPUSBDataType": []}).encode())
        environment = {"os_version": "26.6.2", "os_build": "25G83", "machine_model": "Mac17,2", "soc": "Apple M5",
                       "boot_before": {"seconds_since_unix_epoch": 1000, "microseconds": 0},
                       "boot_after": {"seconds_since_unix_epoch": 1000, "microseconds": 0}}
        value, filtered, properties = runtime.build_snapshot(tree, tree, {}, profiler, environment, "disconnected", "off", {"synthetic": True})
        self.assertTrue(value["validation"]["disconnected_absence_confirmed"])
        self.assertNotIn("PRIVATE", json.dumps(filtered))
        commands = [{"label": label, "argv": list(argv), "status": "OK"} for label, argv in runtime.command_plan()]
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory) / "capture"
            runtime.write_capture(path, value, filtered, properties, commands, "SYNTHETIC")
            rebuilt = runtime.validate_capture(path)
            self.assertEqual(rebuilt, value)
            with (path / "snapshot.json").open("ab") as stream:
                stream.write(b' ')
            with self.assertRaisesRegex(ValueError, "hash"):
                runtime.validate_capture(path)

    def test_hierarchy_change_prevents_baseline_confirmation(self):
        before = runtime.parse_registry_tree(b'+-o root <class IORegistryRoot, id 0x1>\n  +-o dcp <class AppleDCPExpert, id 0x2>\n')
        after = runtime.parse_registry_tree(b'+-o root <class IORegistryRoot, id 0x1>\n  +-o dcp <class AppleDCPExpert, id 0x3>\n')
        profiler = {"displays": [], "usb_hub_candidates": []}
        value, _, _ = runtime.build_snapshot(before, after, {}, profiler, {"boot_before": 1, "boot_after": 1}, "disconnected", "off", {})
        self.assertEqual(value["validation"]["status"], "INVALID")
        self.assertFalse(value["validation"]["disconnected_absence_confirmed"])

    def test_policy_mismatch_blocks_diff(self):
        before, after = snapshot("off", DEVICE), snapshot("on", DEVICE)
        after["capture_policy_sha256"] = "different"
        with self.assertRaises(ValueError):
            runtime.diff_snapshots(before, after)

    def test_missing_relevant_property_object_invalidates_snapshot(self):
        tree = runtime.parse_registry_tree(b'+-o root <class IORegistryRoot, id 0x1>\n  +-o dcp <class AppleDCPExpert, id 0x2>\n')
        properties = {"DCPDPDeviceProxy": [{"entry_id": "0x9", "properties": runtime.select_properties({"Unit": 0})}]}
        value, _, _ = runtime.build_snapshot(tree, tree, properties, {"displays": [], "usb_hub_candidates": []},
                                               {"boot_before": 1, "boot_after": 1}, "disconnected", "off", {})
        self.assertEqual(value["validation"]["status"], "INVALID")
        self.assertEqual(value["validation"]["unpaired_property_objects"], ["0x9"])

    def test_complete_capture_runs_only_fixed_mocked_queries(self):
        tree = ("+-o PRIVATE COMPUTER <class IORegistryRoot, id 0x1>\n"
                "  +-o arm-io <class AppleARMIO, id 0x2>\n"
                "    +-o dcpext0 <class AppleARMIODevice, id 0x3>\n" + DEVICE).encode()
        profiler = json.dumps({"SPDisplaysDataType": [{"spdisplays_ndrvs": [{"_name": "Color LCD",
                              "spdisplays_connection_type": "spdisplays_internal"}]}], "SPUSBDataType": []}).encode()
        def execute(argv):
            if argv[0].endswith("ioreg"):
                raw = plistlib.dumps([]) if "-a" in argv else tree
            elif argv[0].endswith("system_profiler"):
                raw = profiler
            elif argv[-1] == "-productVersion":
                raw = b"26.6.2\n"
            elif argv[-1] == "-buildVersion":
                raw = b"25G83\n"
            elif argv[-1] == "hw.model":
                raw = b"Mac17,2\n"
            elif argv[-1] == "machdep.cpu.brand_string":
                raw = b"Apple M5\n"
            else:
                raw = b"{ sec = 1000, usec = 0 } SYNTHETIC\n"
            return {"argv": list(argv), "status": "OK", "stdout_sha256": runtime.digest(raw)}, raw
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory).resolve()
            with mock.patch.object(runtime, "REPOSITORY", root), mock.patch.object(runtime, "execute_public", side_effect=execute) as runner, \
                    mock.patch.object(runtime, "tool_provenance", return_value={"synthetic": True}), contextlib.redirect_stdout(io.StringIO()):
                output = root / "artifacts/runtime/m5p3/disconnected"
                runtime.capture("disconnected", "off", output)
                self.assertEqual(runner.call_count, 42)
                self.assertTrue(runtime.validate_capture(output)["validation"]["disconnected_absence_confirmed"])
                self.assertFalse((root / "artifacts/runtime/m5p3/connected").exists())


if __name__ == "__main__":
    unittest.main()