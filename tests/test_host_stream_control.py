import importlib.util
import pathlib
import struct
import sys
import unittest
from unittest import mock


ROOT = pathlib.Path(__file__).resolve().parents[1]
with mock.patch.object(sys, 'path', [str(ROOT / 'tools')] + sys.path):
    SPEC = importlib.util.spec_from_file_location('host_stream_control', ROOT / 'tools/host_stream_control.py')
    host = importlib.util.module_from_spec(SPEC)
    SPEC.loader.exec_module(host)


def image():
    return {'image': 'synthetic-host-image', 'uuid': 'SYNTHETIC', 'starts': [0x1000, 0x1008],
            'symbols': [{'name': '_create', 'address': 0x1000}, {'name': '_undefined', 'address': 0}],
            'sections': [{'section': '__text', 'address': 0x1000, 'size': 16,
                          'raw': struct.pack('<4I', 0x94000002, 0xd65f03c0, 0xd503201f, 0xd65f03c0)}]}


class HostReceiptTests(unittest.TestCase):
    def test_exact_declared_extent(self):
        raw, end = host.declared_bounds(image(), 0x1000)
        self.assertEqual(end, 0x1008)
        self.assertEqual(len(raw), 8)

    def test_interior_address_is_not_a_function(self):
        with self.assertRaises(ValueError):
            host.declared_bounds(image(), 0x1004)

    def test_truncated_function_rejected(self):
        value = image()
        value['sections'][0]['raw'] = b'\0' * 4
        with self.assertRaises(ValueError):
            host.declared_bounds(value, 0x1000)

    def test_duplicate_or_unsorted_starts_rejected(self):
        for starts in ([0x1000, 0x1000], [0x1008, 0x1000]):
            value = image()
            value['starts'] = starts
            with self.assertRaises(ValueError):
                host.declared_bounds(value, 0x1000)

    def test_symbol_owner_has_no_zero_address_import(self):
        self.assertEqual(host.symbol_names([image()]), {0x1000: ['_create']})

    def test_text_owner_does_not_classify_data(self):
        self.assertEqual(host.text_owner(image(), 0x1004), 0x1000)
        self.assertIsNone(host.text_owner(image(), 0x2000))

    def test_receipt_raw_hash_and_direct_edges(self):
        decoder = mock.Mock()
        decoder.decode.side_effect = lambda address, raw: {'address_hex': hex(address), 'bytes_hex': raw.hex(), 'instruction': 'synthetic'}
        value = image()
        result = host.function_receipt(value, 0x1000, decoder, host.symbol_names([value]), [value])
        self.assertEqual(result['raw_hex'], value['sections'][0]['raw'][:8].hex())
        self.assertEqual(result['edges'][0]['target_hex'], '0x1008')
        self.assertEqual(result['size'], 8)

    def test_output_cannot_overwrite_or_escape(self):
        for path in (ROOT / 'README.md', ROOT / 'artifacts/probes/m5p2', ROOT / 'artifacts/probes/m5p2/../../outside.json'):
            with self.assertRaises(ValueError):
                host.output_path(path)

    def test_no_firmware_input_or_mst_scan_in_entrypoint(self):
        source = (ROOT / 'tools/host_stream_control.py').read_text()
        self.assertNotIn('scan_image(', source)
        self.assertNotIn('dcp_firmware', source)
        self.assertNotIn('public_registry_evidence(', source)

    def test_explicit_data_ranges_are_bounded(self):
        self.assertEqual(host.data_range('0x1000:8'), (0x1000, 8))
        for value in ('0x1000:0', '0x1000:257', '-1:8', '0xffffffffffffffff:8'):
            with self.assertRaises(ValueError):
                host.data_range(value)

    def test_metadata_uses_only_fixed_host_files(self):
        with mock.patch.object(pathlib.Path, 'is_file', return_value=False), \
                mock.patch.object(pathlib.Path, 'read_bytes', return_value=b'not-a-host-container'):
            with self.assertRaisesRegex(ValueError, 'WindowServer'):
                host.host_file_metadata()

    def test_plist_data_remains_typed_raw_bytes(self):
        value = {'IOPropertyMatch': [{'port-type': b'\x00\xff'}], 'flag': True}
        self.assertEqual(host.plist_json(value), {'IOPropertyMatch': [{'port-type': {
            'plist_type': 'data', 'raw_hex': '00ff'}}], 'flag': True})


if __name__ == '__main__':
    unittest.main()