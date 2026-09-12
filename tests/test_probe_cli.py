import json
import pathlib
import subprocess
import sys
import unittest


EXECUTABLE = str(pathlib.Path(sys.argv[1]).resolve())
HARDWARE = "--hardware" in sys.argv[2:]
MOCK_EXECUTABLES = tuple(str(pathlib.Path(value).resolve()) for value in sys.argv[3:]) if sys.argv[2:3] == ["--mock-executables"] else ()


class CLIContractTests(unittest.TestCase):
    @unittest.skipUnless(MOCK_EXECUTABLES, "Mock targets supplied by the CTest unit entry")
    def test_mock_imports_have_no_display_or_dynamic_transport(self):
        self.assertEqual(len(MOCK_EXECUTABLES), 2)
        for executable in MOCK_EXECUTABLES:
            with self.subTest(executable=pathlib.Path(executable).name):
                result = subprocess.run(["/usr/bin/nm", "-u", executable], capture_output=True, text=True, timeout=10)
                self.assertEqual(result.returncode, 0, result.stderr)
                imports = {line.split()[-1] for line in result.stdout.splitlines() if line.split()}
                self.assertFalse(any(symbol.startswith(("_IO", "_CG")) for symbol in imports))
                self.assertEqual(imports & {"_dlopen", "_dlsym"}, set())

    def test_display_api_imports_are_enumeration_only(self):
        result = subprocess.run(["/usr/bin/nm", "-u", EXECUTABLE], capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        imports = {line.split()[-1] for line in result.stdout.splitlines() if line.split()}
        self.assertTrue({"_CGDisplayIOServicePort", "_IOFBGetI2CInterfaceCount",
                         "_IOFBCopyI2CInterfaceForBus"} <= imports)
        forbidden = {"_IOI2CSendRequest", "_IOI2CInterfaceOpen", "_IOI2CInterfaceClose",
                     "_IOServiceOpen", "_IOConnectCallMethod", "_IOConnectCallScalarMethod",
                     "_IOConnectCallStructMethod", "_IODPDeviceCreateWithService",
                     "_IODPDeviceReadDPCD", "_IODPDeviceWriteDPCD"}
        self.assertEqual(imports & forbidden, set())

    def test_help(self):
        result = subprocess.run([EXECUTABLE, "--help"], capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0)
        self.assertIn("macmst probe [--json]", result.stdout)
        self.assertEqual(result.stderr, "")

    def test_reject_invalid_arguments_without_probing(self):
        for arguments in ([], ["enable-mst"], ["--json"], ["probe", "--write"],
                          ["probe", "--json", "extra"], ["probe", "probe"],
                          ["experimental", "dpdv-open-check"],
                          ["experimental", "dpcd-read", "--address", "0x000", "--length", "1"]):
            with self.subTest(arguments=arguments):
                result = subprocess.run([EXECUTABLE, *arguments], capture_output=True, text=True, timeout=10)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stdout, "")
                self.assertIn("Usage:", result.stderr)


class HardwareProbeTests(unittest.TestCase):
    def test_public_read_only_snapshot(self):
        result = subprocess.run([EXECUTABLE, "probe", "--json"], capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["schema_version"], 1)
        self.assertTrue(report["display_enumeration_ok"])
        self.assertEqual(report["errors"], [])
        self.assertIsNone(report["physical_downstream_displays"])
        self.assertEqual(set(report["capabilities"].values()), {"UNKNOWN"})
        self.assertNotEqual(report["host"]["soc"], "UNKNOWN")
        self.assertFalse(report["snapshot_atomic"])
        self.assertEqual(report["dpcd_transport"], {"read_capability": "UNVERIFIED", "private_object_acquired": False})
        public = report["public_displayport_interface"]
        self.assertEqual(public["scope"], "PUBLIC_ENUMERATION_ONLY")
        self.assertEqual(public["dpcd_access"], "UNKNOWN")
        self.assertFalse(public["interface_open_attempted"])
        self.assertFalse(public["request_attempted"])
        self.assertIn(public["result"], {"PUBLIC_DP_NATIVE_CANDIDATE", "PUBLIC_INTERFACE_PRESENT_NO_DP_NATIVE",
                                         "PUBLIC_IOFRAMEBUFFER_PATH_UNAVAILABLE", "PUBLIC_PATH_UNRESOLVED"})
        observation = public["enumeration"]
        if observation is not None:
            external = [display for display in report["displays"] if not display["built_in"] and display["active"]]
            self.assertEqual(len(external), 1)
            self.assertEqual(public["external_display_id_raw"], external[0]["display_id_raw"])
            if observation["count_attempted"]:
                self.assertTrue(observation["framebuffer_conforms"])
                self.assertIs(type(observation["count_status_code_raw"]), int)
                self.assertEqual(observation["count_status_hex"], f"0x{observation['count_status_code_raw'] & 0xffffffff:08x}")
                self.assertIs(type(observation["bus_count_raw"]), int)
            else:
                self.assertIsNone(observation["count_status_code_raw"])
                self.assertIsNone(observation["count_status_hex"])
                self.assertIsNone(observation["bus_count_raw"])
                self.assertEqual(observation["buses"], [])
            for bus in observation["buses"]:
                self.assertEqual(bus["copy_status_hex"], f"0x{bus['copy_status_code_raw'] & 0xffffffff:08x}")
                interface = bus["interface"]
                if interface is not None:
                    for key in interface["properties"]:
                        self.assertFalse(any(part in key.lower() for part in ("serial", "uuid", "edid", "token", "password")))
        for candidate in report["external_dp_candidates"]:
            self.assertEqual(candidate["location"], "External")
            self.assertEqual(candidate["evidence_class"], "INFERRED")
            self.assertFalse(candidate["private_object_acquired"])
            self.assertFalse(candidate["safe_to_invoke_private_api"])
        for query in report["registry"].values():
            self.assertEqual(query["query_status_code_raw"], 0)
            for entry in query["entries"]:
                self.assertEqual(entry["property_status_code_raw"], 0)
                self.assertEqual(entry["relationships"]["parent_status_code_raw"], 0)
                self.assertEqual(entry["relationships"]["children_status_code_raw"], 0)
                self.assertIn("class", entry["relationships"]["parent"])
                for key in entry["properties"]:
                    self.assertFalse(any(part in key.lower() for part in ("serial", "uuid", "edid", "token", "password")))


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(HardwareProbeTests if HARDWARE else CLIContractTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)