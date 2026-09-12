import json
import pathlib
import subprocess
import sys
import unittest


EXECUTABLE = str(pathlib.Path(sys.argv[1]).resolve())
HARDWARE = "--hardware" in sys.argv[2:]


class CLIContractTests(unittest.TestCase):
    def test_help(self):
        result = subprocess.run([EXECUTABLE, "--help"], capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0)
        self.assertIn("macmst probe [--json]", result.stdout)
        self.assertEqual(result.stderr, "")

    def test_reject_invalid_arguments_without_probing(self):
        for arguments in ([], ["enable-mst"], ["--json"], ["probe", "--write"],
                          ["probe", "--json", "extra"], ["probe", "probe"]):
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