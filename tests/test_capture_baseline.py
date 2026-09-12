import importlib.util
import pathlib
import unittest


SOURCE = pathlib.Path(__file__).resolve().parents[1] / "tools" / "capture_baseline.py"
SPEC = importlib.util.spec_from_file_location("capture_baseline", SOURCE)
capture = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(capture)


class CapturePrivacyTests(unittest.TestCase):
    def test_symbol_name_extraction_has_no_addresses_or_abi_claims(self):
        source = "exports: [ _IODPDeviceReadDPCD, _IOAVServiceReadI2C, _Unrelated ]\n_IODPDeviceReadDPCD 0xdeadbeef"
        self.assertEqual(capture.extract_display_symbol_names(source),
                         ["_IOAVServiceReadI2C", "_IODPDeviceReadDPCD"])

    def test_registry_keeps_raw_numbers_not_unique_identifiers(self):
        source = {"idVendor": 4660, "idProduct": 22136, "LinkRate": 30,
                  "USB Serial Number": "PRIVATE", "IOPlatformUUID": "PRIVATE",
                  "IODisplayEDID": b"PRIVATE", "EventLog": {"token": "PRIVATE"},
                  "UnknownField": "PRIVATE"}
        self.assertEqual(capture.select_registry_properties(source),
                         {"idVendor": 4660, "idProduct": 22136, "LinkRate": 30})

    def test_profiler_nested_identifiers_removed(self):
        source = {"SPDisplaysDataType": [{"_name": "Example GPU", "spdisplays_ndrvs": [
            {"_name": "Example Display", "_spdisplays_display-product-id": "1234",
             "_spdisplays_display-serial-number": "PRIVATE", "spdisplays_uuid": "PRIVATE"}]}],
                  "SPHardwareDataType": [{"chip_type": "Apple M5", "serial_number": "PRIVATE"}],
                  "UnrelatedData": {"token": "PRIVATE"}}
        result = capture.sanitize_profiler(source)
        self.assertNotIn("PRIVATE", str(result))
        self.assertEqual(result["SPHardwareDataType"], [{"chip_type": "Apple M5"}])
        self.assertEqual(result["SPDisplaysDataType"][0]["spdisplays_ndrvs"][0]["_name"], "Example Display")

    def test_thunderbolt_host_name_omitted(self):
        source = {"SPThunderboltDataType": [{"_name": "Personal Computer", "switch_uid": "PRIVATE",
                                            "_items": [{"vendor_id": "0x1234", "uid": "PRIVATE"}]}]}
        result = capture.sanitize_profiler(source)
        self.assertEqual(result, {"SPThunderboltDataType": [{"_items": [{"vendor_id": "0x1234"}]}]})

    def test_registry_tree_keeps_display_ancestry_only(self):
        source = "+-o Host  <class IORegistryRoot, id 0x1>\n  +-o arm-io  <class AppleARMIO, id 0x2>\n    +-o dcpext0  <class AppleARMIODevice, id 0x3>\n      +-o AppleDCPExpert  <class AppleDCPExpert, id 0x4>\n    +-o Unrelated  <class OtherDevice, id 0x5>"
        result = capture.select_registry_tree(source)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[1]["ancestors"], ["arm-io", "dcpext0"])
        self.assertNotIn("Unrelated", str(result))


if __name__ == "__main__":
    unittest.main()