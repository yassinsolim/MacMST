import importlib.util
import hashlib
import json
import pathlib
import plistlib
import struct
import sys
import tempfile
import unittest
from unittest import mock


SOURCE = pathlib.Path(__file__).resolve().parents[1] / "tools/inspect_iodp.py"
sys.path.insert(0, str(SOURCE.parent))
import dyld_cache
import kernel_image
import call_graph
import inspect_userserver
import scan_mst
import ipsw_dcp
import dcp_firmware

SPEC = importlib.util.spec_from_file_location("inspect_iodp", SOURCE)
analysis = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(analysis)


class StaticAnalysisParserTests(unittest.TestCase):
    def test_m3c_explicit_detail_requires_referenced_entry_and_bounds(self):
        raw = struct.pack("<4I", 0xb4000041, 0xd503237f, 0xd65f0fff, 0xd65f03c0)
        view = {"uuid": "fixture", "sections": [{"address": 0x1000, "size": len(raw), "raw": raw, "flags": 0x80000400}]}
        pointers = mock.Mock()
        pointers.records = {0x2000: {"target_hex": "0x1000", "slot_hex": "0x2000"}}
        oracle, _ = scan_mst.load_oracle(SOURCE.parents[1] / "docs/research/mst-source-signatures.json")
        decoder = mock.Mock()
        decoder.decode.side_effect = lambda address, value: {"address_hex": hex(address), "bytes_hex": value.hex()}
        result = dcp_firmware.detail_exact_range(view, 0x1000, 12, oracle, decoder, pointers)
        self.assertEqual(result["size"], 12)
        self.assertEqual(len(result["instructions"]), 3)
        self.assertEqual(len(result["entry_pointer_references"]), 1)
        for address, size in ((0x1004, 4), (0x1000, 20), (0x1000, 3), (0x1000, 32772)):
            with self.assertRaises(ValueError):
                dcp_firmware.detail_exact_range(view, address, size, oracle, decoder, pointers)
        view["sections"][0]["raw"] = struct.pack("<4I", 0x94000003, 0xd503237f, 0xd65f0fff, 0xd65f03c0)
        pointers.records = {}
        result = dcp_firmware.detail_exact_range(view, 0x100c, 4, oracle, decoder, pointers)
        self.assertEqual(result["entry_pointer_references"], [])
        self.assertEqual(len(result["direct_callers"]), 1)

    def test_m3c_details_only_rejects_broad_or_empty_selection(self):
        for arguments in (("--scan", "--details-only", "--detail-address", "0x4000000"),
                          ("--details-only",),
                          ("--details-only", "--detail-range", "0x1000:4:8"),
                          ("--scan", "--detail-range", "0x1000:4"),
                          ("--details-only", "--detail-address", "0x1000", "--detail-range", "0x1000:4")):
            with mock.patch.object(sys, "argv", ["dcp_firmware", "--components", "unused", "--output", "unused", *arguments]):
                with mock.patch.object(pathlib.Path, "read_bytes") as reader:
                    with mock.patch("argparse.ArgumentParser.error", side_effect=ValueError("invalid selection")):
                        with self.assertRaises(ValueError):
                            dcp_firmware.main()
                    reader.assert_not_called()

    def test_m3c_details_only_skips_devicetree_and_broad_scan(self):
        with tempfile.TemporaryDirectory() as directory:
            repository = pathlib.Path(directory)
            tools = repository / "tools"
            tools.mkdir()
            for name in ("dcp_firmware.py", "ipsw_dcp.py", "scan_mst.py", "kernel_image.py", "dyld_cache.py", "inspect_iodp.py"):
                (tools / name).write_bytes(b"synthetic tool identity")
            components = repository / "artifacts/sources/m3b/components"
            components.mkdir(parents=True)
            raw = b"synthetic retained DCP"
            (components / "dcp.im4p").write_bytes(raw)
            mapping = {"dcp_path": "dcp.im4p", "devicetree_path": "absent-tree.im4p",
                       "normal_dcp_components": ["Ap,DCP2"],
                       "selected": {"display_components": {"Ap,DCP2": {"Info": {"Path": "dcp.im4p"}}}}}
            extraction = {"result": "IDENTIFIED_DCP_AND_DEVICETREE_EXTRACTED", "mapping": mapping,
                          "members": [{"path": "absent-tree.im4p"},
                                      {"path": "dcp.im4p", "sha256": hashlib.sha256(raw).hexdigest()}]}
            (components / "extraction.json").write_text(json.dumps(extraction))
            output = repository / "artifacts/probes/m3c/receipt"
            arguments = ["dcp_firmware", "--components", str(components), "--output", str(output),
                         "--details-only", "--pointer-slot", "0x2000"]
            with mock.patch.object(dcp_firmware, "__file__", str(tools / "dcp_firmware.py")), \
                    mock.patch.object(sys, "argv", arguments), \
                    mock.patch.object(dcp_firmware, "decode_im4p", return_value=(b"decoded fixture", {})) as decode, \
                    mock.patch.object(dcp_firmware, "runtime_view", return_value={"layout_evidence": {"fixture": True}}), \
                    mock.patch.object(scan_mst, "load_oracle", return_value=({}, "fixture")), \
                    mock.patch.object(dcp_firmware, "FirmwarePointers") as pointers, \
                    mock.patch.object(dcp_firmware, "scan_runtime") as broad_scan, \
                    mock.patch.object(dcp_firmware, "devicetree_evidence") as tree_scan, \
                    mock.patch("builtins.print"):
                pointers.return_value.pointer.return_value = {"slot_hex": "0x2000", "target_hex": "0x1000"}
                dcp_firmware.main()
                decode.assert_called_once()
                pointers.return_value.pointer.assert_called_once_with(0x2000)
                broad_scan.assert_not_called()
                tree_scan.assert_not_called()
            report = json.loads((output / "decoded.json").read_text())
            self.assertEqual(report["errors"], [])
            self.assertEqual(len(report["images"]), 1)
            self.assertNotIn("scan", report["images"][0])
            self.assertEqual(report["images"][0]["layout"], {"fixture": True})
            self.assertTrue(report["requested"]["details_only"])

    def test_m3b_m4_comparison_never_substitutes_for_m5_identity(self):
        record = {"fields": {"Ap,ProductType": "Mac16,1", "Ap,Target": "J604AP", "ApChipID": "0x8132", "ApBoardID": "0x22"},
                  "display_components": {"Ap,DCP2": {"Info": {"Path": "Firmware/dcp/t8132dcp.im4p"}}}}
        mapping = {"comparison": [record], "selected": {"identity_binary_plist_sha256": "m5-fixture"}}
        result = ipsw_dcp.m4_comparison_mapping(mapping)
        self.assertEqual(result["dcp_path"], "Firmware/dcp/t8132dcp.im4p")
        self.assertIsNone(result["devicetree_path"])
        self.assertIn("NOT_M5", result["purpose"])
        with self.assertRaises(ValueError):
            ipsw_dcp.m4_comparison_mapping({**mapping, "comparison": [record, record]})
        with self.assertRaises(ValueError):
            ipsw_dcp.m4_comparison_mapping({**mapping, "comparison": []})

    def test_m3b_firmware_pointers_require_declared_vm_chain_membership(self):
        word = (1 << 63) | (2 << 51) | 0x200
        values = word.to_bytes(8, "little") + (0x300).to_bytes(8, "little")
        chain = struct.pack("<3I", 7, 1, 0x100)
        view = {"sections": [{"section": "__chain_starts", "address": 0x1000, "size": 12, "raw": chain, "reserved1": 2},
                             {"section": "__const", "address": 0x1100, "size": 16, "raw": values}],
                "layout_evidence": {"segments": [{"name": "__TEXT", "address": 0x1000}]}}
        pointers = dcp_firmware.FirmwarePointers(view)
        self.assertEqual(pointers.pointer(0x1100)["target_hex"], "0x1200")
        self.assertEqual(pointers.pointer(0x1108)["target_hex"], "0x1300")
        self.assertEqual(pointers.pointer(0x1108)["chain_hops"], 1)
        with self.assertRaises(ValueError):
            pointers.pointer(0x1104)
        view["sections"][0]["reserved1"] = 1
        with self.assertRaises(ValueError):
            dcp_firmware.FirmwarePointers(view)

    def test_m3b_runtime_maps_sections_from_declared_bundle_ranges(self):
        def segment(name, address, file_offset, section_name, flags):
            command = struct.pack("<II16s4Q4I", 0x19, 152, name.encode(), address, 16, file_offset, 16, 7, 5, 1, 0)
            section = struct.pack("<16s16sQQ8I", section_name.encode(), name.encode(), address, 16, file_offset, 2, 0, 0, flags, 0, 0, 0)
            return command + section
        commands = segment("__TEXT", 0x4000000, 0x1000, "__text", 0x80000400)
        commands += segment("__DATA", 0x4001000, 0x2000, "__const", 0)
        commands += segment("__OS_LOG", 0x4002000, 0x3000, "__string", 2)
        commands += struct.pack("<II16s", 0x1b, 24, bytes(range(16)))
        header = struct.pack("<8I", 0xfeedfacf, 0x0100000c, 2, 5, 4, len(commands), 0, 0) + commands
        tree = struct.pack("<II32sI", 1, 0, b"name", 5) + b"root\0\0\0\0"
        raw = bytearray(8192)
        raw[8:12] = b"DNUB"
        struct.pack_into("<H", raw, 14, 4)
        struct.pack_into("<Q", raw, 0x88, 4)
        for index, (name, offset, size) in enumerate(((b"dlon", 2048, 2048), (b"txtr", 4096, 16), (b"tadr", 8192 - 16, 16), (b"ldbu", 6000, 16))):
            struct.pack_into("<I4sQQ", raw, 0x280 + index * 24, 1, name, offset, size)
        struct.pack_into("<3Q", raw, 0x248, 1024, 1024, len(tree))
        raw[2048:2048 + len(header)] = header
        raw[3072:3072 + len(tree)] = tree
        raw[4096:4112] = bytes(range(16))
        raw[-16:] = bytes(range(16, 32))
        raw[6000:6016] = b"MST log fixture\0"
        view = dcp_firmware.runtime_view(raw)
        self.assertEqual(view["sections"][0]["raw"], bytes(range(16)))
        self.assertEqual(view["sections"][1]["raw"], bytes(range(16, 32)))
        self.assertEqual(view["sections"][0]["bundle_offset"], 4096)
        self.assertEqual(view["sections"][2]["bundle_offset"], 6000)
        self.assertEqual(view["sections"][2]["raw"], b"MST log fixture\0")
        self.assertEqual(view["layout_evidence"]["header_offset"], 2048)
        self.assertFalse(view["layout_evidence"]["function_start_command_present"])
        standalone = bytearray(0x3010)
        standalone[:len(header)] = header
        standalone[0x1000:0x1010] = bytes(range(16))
        standalone[0x2000:0x2010] = bytes(range(16, 32))
        standalone[0x3000:0x3010] = b"MST log fixture\0"
        standalone_view = dcp_firmware.runtime_view(standalone)
        self.assertEqual(standalone_view["kind"], "dcp_standalone_runtime")
        self.assertEqual([section["raw"] for section in standalone_view["sections"]], [section["raw"] for section in view["sections"]])
        struct.pack_into("<Q", raw, 0x290 + 24, 8)
        with self.assertRaises(ValueError):
            dcp_firmware.runtime_view(raw)

    def test_m3b_firmware_regions_preserve_inferred_boundaries(self):
        words = [0xd503237f, 0x94000003, 0x52800000 | (0x1c0 << 5), 0xd65f0fff, 0xd503237f, 0xd65f0fff]
        raw = struct.pack("<6I", *words)
        section = {"raw": raw, "address": 0x4000000}
        regions = dcp_firmware.firmware_regions(section)
        self.assertEqual([(item["start"], item["end"]) for item in regions], [(0x4000000, 0x4000010), (0x4000010, 0x4000018)])
        self.assertTrue(all("INFERRED" in item["boundary"] for item in regions))
        with self.assertRaises(ValueError):
            dcp_firmware.firmware_regions({"raw": b"x", "address": 0})
        oracle, _ = scan_mst.load_oracle(SOURCE.parents[1] / "docs/research/mst-source-signatures.json")
        section.update(section="__text", segment="__TEXT", flags=0x80000400, size=len(raw))
        view = {"image": "synthetic", "uuid": "fixture", "sections": [section], "layout_evidence": {}}
        result = dcp_firmware.scan_runtime(view, oracle)
        self.assertEqual(result["dpcd_value_census"]["DP_PAYLOAD_ALLOCATE_SET"]["events"], 1)
        self.assertEqual(result["regions"], 2)
        decoder = mock.Mock()
        decoder.decode.side_effect = lambda address, value: {"address_hex": hex(address), "bytes_hex": value.hex()}
        detail = dcp_firmware.detail_region(view, 0x4000000, oracle, decoder)
        self.assertEqual(detail["size"], 16)
        self.assertIn("INFERRED", detail["boundary_evidence"])
        self.assertEqual(len(detail["instructions"]), 4)
        with self.assertRaises(ValueError):
            dcp_firmware.detail_region(view, 0x4000004, oracle, decoder)

    def test_m3b_bundle_config_uses_declared_ranges(self):
        config = struct.pack("<II32sI", 1, 0, b"name", 5) + b"root\0\0\0\0"
        raw = bytearray(4096)
        raw[8:12] = b"DNUB"
        struct.pack_into("<H", raw, 14, 4)
        struct.pack_into("<Q", raw, 0x88, 1)
        struct.pack_into("<I4sQQ", raw, 0x280, 1, b"dlon", 2048, 2048)
        struct.pack_into("<3Q", raw, 0x248, 0, 1024, len(config))
        raw[2048:2048 + len(config)] = config
        layout = dcp_firmware.bundle_layout(raw)
        self.assertEqual(layout["config_format"], "APPLE_DEVICETREE_NOLD")
        self.assertEqual(layout["config_nodes"][0]["path"], "/root")
        self.assertEqual(layout["config_offset"], 2048)
        for offset, value in ((0x88, 14), (0x258, 4096), (0x288, 4096)):
            invalid = bytearray(raw)
            struct.pack_into("<Q", invalid, offset, value)
            with self.assertRaises(ValueError):
                dcp_firmware.bundle_layout(invalid)
        raw[0x284:0x288] = b"tsru"
        with self.assertRaises(ValueError):
            dcp_firmware.bundle_layout(raw)

    def test_m3b_im4p_digest_type_override_and_decompression_bounds(self):
        def field(kind, value):
            return bytes([kind, len(value)]) + value
        content = field(0x16, b"IM4P") + field(0x16, b"dcpf") + field(0x16, b"1") + field(4, b"bvx2fixture")
        content += field(0x30, field(2, b"\1") + field(2, b"\x10"))
        raw = field(0x30, content)
        adjusted = raw.replace(b"dcpf", b"dcp2", 1)
        component = {"Trusted": True, "Info": {"Img4PayloadType": "dcp2"}, "Digest": hashlib.sha384(adjusted).digest()}
        decoded, receipt = dcp_firmware.decode_im4p(raw, component, lambda value, size: bytes(size))
        self.assertEqual(len(decoded), 16)
        self.assertEqual(receipt["raw_type"], "dcpf")
        self.assertEqual(receipt["manifest_type"], "dcp2")
        self.assertEqual(receipt["keybag_status"], "NO_KEYBAG_FIELD_PRESENT")
        with self.assertRaises(ValueError):
            dcp_firmware.decode_im4p(raw, component, lambda value, size: bytes(size + 1))
        with self.assertRaises(ValueError):
            dcp_firmware.decode_im4p(raw, {**component, "Digest": bytes(48)})
        keybag_raw = field(0x30, content + field(4, b"keybag"))
        component["Digest"] = hashlib.sha384(keybag_raw.replace(b"dcpf", b"dcp2", 1)).digest()
        with self.assertRaisesRegex(ValueError, "keybag present"):
            dcp_firmware.decode_im4p(keybag_raw, component)

    def test_m3b_devicetree_preserves_display_properties_and_bounds(self):
        def node(properties, children=()):
            raw = struct.pack("<II", len(properties), len(children))
            for name, value in properties:
                raw += struct.pack("<32sI", name.encode("ascii"), len(value)) + value
                raw += bytes((-len(value)) % 4)
            return raw + b"".join(children)
        child = node([("name", b"dcp\0"), ("compatible", b"t8142-dcp\0AppleDCP\0")])
        unrelated = node([("name", b"gpu\0"), ("compatible", b"gpu,t8142\0")])
        raw = node([("name", b"device-tree\0"), ("model", b"J704AP\0")], [child, unrelated])
        nodes = dcp_firmware.parse_devicetree(raw)
        self.assertEqual(len(nodes), 3)
        self.assertEqual(nodes[1]["properties"]["compatible"]["raw"], b"t8142-dcp\0AppleDCP\0")
        evidence = dcp_firmware.devicetree_evidence(raw)
        self.assertEqual(evidence["total_nodes"], 3)
        self.assertEqual([entry["path"] for entry in evidence["selected_nodes"]], ["/device-tree", "/device-tree/dcp"])
        for invalid in (raw[:-1], raw + b"x", struct.pack("<II", 0xffffffff, 0)):
            with self.assertRaises(ValueError):
                dcp_firmware.parse_devicetree(invalid)
        with self.assertRaises(ValueError):
            dcp_firmware.parse_devicetree(node([("name", b"root\0"), ("name", b"other\0")]))

    def test_m3b_identity_selection_is_board_variant_and_product_exact(self):
        identity = {"Ap,ProductType": "Mac17,2", "Ap,Target": "J704AP", "ApChipID": "0x8142", "ApBoardID": "0x22",
                    "Info": {"DeviceClass": "j704ap", "Variant": "macOS Customer", "RestoreBehavior": "Erase",
                             "BuildNumber": "25G83", "VariantContents": {"DCP": "macOSProduction"}}}
        manifest = {"ProductBuildVersion": "25G83", "ProductVersion": "26.6.2", "BuildIdentities": [identity]}
        self.assertEqual(ipsw_dcp.select_identity(manifest), (0, identity))
        for key, value in (("Ap,Target", "J999AP"), ("Ap,ProductType", "Mac16,1"), ("ApBoardID", "0x23")):
            with self.assertRaises(ValueError):
                ipsw_dcp.select_identity({**manifest, "BuildIdentities": [{**identity, key: value}]})
        with self.assertRaises(ValueError):
            ipsw_dcp.select_identity({**manifest, "BuildIdentities": [identity, identity]})
        for key, value in (("Variant", "Customer Upgrade Install (IPSW)"), ("RestoreBehavior", "Update"), ("VariantContents", {"DCP": "Development"})):
            with self.assertRaises(ValueError):
                ipsw_dcp.select_identity({**manifest, "BuildIdentities": [{**identity, "Info": {**identity["Info"], key: value}}]})

    def test_m3b_partial_zip_manifest_and_range_budget(self):
        import io
        import zipfile
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("BuildManifest.plist", b"synthetic manifest")
            archive.writestr("unrelated.dmg", bytes(65536))
        raw = buffer.getvalue()
        calls = []

        def opener(request, timeout):
            self.assertEqual(timeout, 30)
            self.assertTrue(request.headers["Range"].startswith("bytes="))
            start, end = [int(value) for value in request.headers["Range"][6:].split("-")]
            calls.append((start, end))
            response = mock.MagicMock()
            response.__enter__.return_value = response
            response.status = 206
            response.geturl.return_value = request.full_url
            response.headers = {"Content-Range": f"bytes {start}-{end}/{len(raw)}", "Content-Length": str(end - start + 1), "ETag": '"fixture"'}
            response.read.return_value = raw[start:end + 1]
            return response

        remote = ipsw_dcp.RemoteIPSW("https://updates.cdn-apple.com/test.ipsw", len(raw), opener)
        with zipfile.ZipFile(remote) as archive:
            data, receipt = ipsw_dcp.extract_member(archive, "BuildManifest.plist")
        self.assertEqual(data, b"synthetic manifest")
        self.assertEqual(receipt["sha256"], hashlib.sha256(data).hexdigest())
        self.assertEqual(remote.transferred, sum(end - start + 1 for start, end in calls))
        self.assertTrue(all(request["status"] == 206 for request in remote.requests))
        with self.assertRaises(ValueError):
            remote.read(16 * 1024 * 1024 + 1)
        with self.assertRaises(ValueError):
            remote.seek(len(raw) + 1)

    def test_m3b_range_refuses_full_body_and_mismatched_range(self):
        response = mock.MagicMock()
        response.__enter__.return_value = response
        response.geturl.return_value = "https://updates.cdn-apple.com/test.ipsw"
        for response_status, content_range in ((200, "bytes 0-3/100"), (206, "bytes 4-7/100")):
            response.status = response_status
            response.headers = {"Content-Range": content_range}
            remote = ipsw_dcp.RemoteIPSW(response.geturl(), 100, mock.Mock(return_value=response))
            with self.assertRaises(ValueError):
                remote.read(4)
            response.read.assert_not_called()
        with self.assertRaises(ValueError):
            ipsw_dcp.RemoteIPSW("http://updates.cdn-apple.com/test.ipsw", 100)

    def test_m3b_metadata_requires_exact_board_signed_build(self):
        firmware = {"identifier": "Mac17,2", "version": "26.6.2", "buildid": "25G83", "signed": True,
                    "url": "https://updates.cdn-apple.com/UniversalMac_26.6.2_25G83_Restore.ipsw"}
        board = {"boardconfig": "J704AP", "platform": "t8142", "cpid": 0x8142, "bdid": 0x22}
        device = {"identifier": "Mac17,2", "boards": [board], "firmwares": [firmware]}
        self.assertEqual(ipsw_dcp.select_metadata(device, firmware)["bdid_hex"], "0x22")
        for altered in ({**board, "bdid": 0x23}, {**board, "boardconfig": "J999AP"}):
            with self.assertRaises(ValueError):
                ipsw_dcp.select_metadata({**device, "boards": [altered]}, firmware)
        with self.assertRaises(ValueError):
            ipsw_dcp.select_metadata({**device, "boards": [board, board]}, firmware)
        with self.assertRaises(ValueError):
            ipsw_dcp.select_metadata(device, {**firmware, "signed": False})

    def test_mst_data_tables_are_bounded_unqualified_candidates(self):
        oracle, _ = scan_mst.load_oracle(SOURCE.parents[1] / "docs/research/mst-source-signatures.json")
        raw = struct.pack("<4I", 0x1000, 0x1200, 0, 0x1400)
        hits = scan_mst.constant_table_hits(raw, 0x2000, oracle)
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0]["signatures"], ["mst_sideband_windows"])
        self.assertIsNone(hits[0]["function_hex"])
        self.assertIn("NOT_PROVEN", hits[0]["assessment"])
        self.assertEqual(scan_mst.constant_table_hits(struct.pack("<2I", 0x1000, 0x1000), 0, oracle), [])
        spread = struct.pack("<I", 0x1000) + bytes(64) + struct.pack("<I", 0x1200)
        self.assertEqual(scan_mst.constant_table_hits(spread, 0, oracle), [])

    def test_mst_public_names_capture_refuses_unhealthy_baseline_before_enumeration(self):
        with tempfile.TemporaryDirectory() as directory:
            baseline = pathlib.Path(directory) / "baseline.json"
            baseline.write_text('{"external_dp_candidates": []}')
            with mock.patch.object(inspect_userserver, "RegistryReader") as reader:
                with self.assertRaises(ValueError):
                    scan_mst.public_registry_evidence(baseline)
                reader.assert_not_called()

    def test_mst_cached_symbols_read_bounded_names_from_shared_string_pool(self):
        table = struct.pack("<IBBHQ", 400000000, 0x0f, 1, 0, 0x180001000)
        reader = mock.Mock(return_value=b"_DPSource\0")
        symbols = scan_mst.cached_symbols(table, 406729643, reader)
        reader.assert_called_once_with(400000000, 4096)
        self.assertEqual(symbols, [{"name": "_DPSource", "address": 0x180001000, "section": 1}])
        with self.assertRaises(ValueError):
            scan_mst.cached_symbols(table, 300000000, reader)
        with self.assertRaises(ValueError):
            scan_mst.cached_symbols(table, 406729643, lambda offset, size: b"x" * size)

    def test_mst_scan_image_keeps_hashes_and_unqualified_census(self):
        oracle, _ = scan_mst.load_oracle(SOURCE.parents[1] / "docs/research/mst-source-signatures.json")
        raw = struct.pack("<3I", 0x52800000 | (0x1c0 << 5), 0x52800001 | (0x2c0 << 5), 0xd65f03c0)
        image = {"image": "test.DP", "uuid": "fixture", "kind": "fixture", "header_sha256": "fixture",
                 "starts": [0x1000], "function_starts_sha256": "fixture", "symbols": [{"address": 0x1000, "name": "MSTPayload"}],
                 "sections": [{"section": "__text", "segment": "__TEXT", "address": 0x1000, "size": len(raw), "raw": raw}]}
        result = scan_mst.scan_image(image, oracle)
        self.assertEqual(result["declared_functions"], 1)
        self.assertEqual(result["dpcd_value_census"]["DP_PAYLOAD_ALLOCATE_SET"]["functions"], 1)
        self.assertEqual(result["candidates"][0]["image_uuid"], "fixture")
        self.assertEqual(result["candidates"][0]["bytes_sha256"], hashlib.sha256(raw).hexdigest())
        self.assertIn("NOT_IMPLEMENTATION_PROOF", result["candidates"][0]["assessment"])
        self.assertEqual(result["dpcd_move_sites"][0]["function_hex"], "0x1000")
        self.assertEqual(result["dpcd_move_sites"][0]["image_uuid"], "fixture")
        decoder = mock.Mock()
        decoder.decode.side_effect = lambda address, value: {"address_hex": hex(address), "bytes_hex": value.hex()}
        detail = scan_mst.detail_function(image, 0x1000, decoder, oracle)
        self.assertEqual(len(detail["instructions"]), 3)
        self.assertEqual(detail["direct_callers_in_image"], [])
        with self.assertRaises(ValueError):
            scan_mst.detail_function(image, 0x1004, decoder, oracle)
        self.assertEqual(result["unassigned_text_prefix_bytes"], 0)
        for starts in ([], [0x1001], [0x1004, 0x1000], [0x1000, 0x1000]):
            with self.assertRaises(ValueError):
                scan_mst.scan_image({**image, "starts": starts}, oracle)
        prefix = scan_mst.scan_image({**image, "starts": [0x1004]}, oracle)
        self.assertEqual(prefix["unassigned_text_prefix_bytes"], 4)
        outside = scan_mst.scan_image({**image, "starts": [0x1000, 0x2000]}, oracle)
        self.assertEqual(outside["skipped_functions"][0]["reason"], "START_OUTSIDE_SCANNED_TEXT")

    def test_mst_cache_inventory_rejects_excessive_count(self):
        cache = mock.Mock()
        header = bytearray(152)
        struct.pack_into("<QQ", header, 136, 4096, 32769)
        cache.read_disk.return_value = header
        with self.assertRaises(ValueError):
            scan_mst.cache_image_inventory(cache)

    def test_mst_cache_inventory_accepts_iossupport_and_rejects_traversal(self):
        cache = mock.Mock()
        cache.main_file.stat.return_value.st_size = 16384
        header = bytearray(152)
        struct.pack_into("<QQ", header, 136, 4096, 1)
        record = struct.pack("<16sQII", bytes(16), 0x180000000, 4096, 8192)
        for path, valid in ((b"/System/iOSSupport/System/Library/Test", True), (b"/System/../Test", False)):
            cache.read_disk.side_effect = [header, record, path + b"\0"]
            if valid:
                entries, _ = scan_mst.cache_image_inventory(cache)
                self.assertEqual(entries[0]["image"], path.decode())
            else:
                with self.assertRaises(ValueError):
                    scan_mst.cache_image_inventory(cache)

    def test_mst_oracle_and_constant_groups_require_distinct_values(self):
        oracle, digest = scan_mst.load_oracle(SOURCE.parents[1] / "docs/research/mst-source-signatures.json")
        self.assertEqual(len(digest), 64)
        self.assertEqual(len(oracle["registers"]), 29)
        events = [{"value": 0x1000}, {"value": 0x1000}]
        self.assertEqual(scan_mst.constant_groups(events, oracle), [])
        events.append({"value": 0x1200})
        self.assertEqual(scan_mst.constant_groups(events, oracle)[0]["id"], "mst_sideband_windows")

    def test_mst_immediates_do_not_treat_stack_offsets_as_register_addresses(self):
        words = [0x52800000 | (0x1c0 << 5), 0x52800001 | (0x2c0 << 5), 0xd1000000 | (0x1c0 << 10) | (31 << 5) | 31]
        events = scan_mst.immediate_events(struct.pack("<3I", *words), 0x1000)
        self.assertEqual([event["value"] for event in events], [0x1c0, 0x2c0])
        self.assertEqual(events[0]["bytes_hex"], words[0].to_bytes(4, "little").hex())

    def test_mst_move_wide_only_combines_adjacent_matching_registers(self):
        words = [0x52800000 | (0x1234 << 5), 0x72a00000 | (0x5 << 5), 0xd65f03c0, 0x72a00000 | (0x7 << 5)]
        events = scan_mst.immediate_events(struct.pack("<4I", *words), 0x1000)
        self.assertEqual([event["value"] for event in events], [0x1234, 0x51234])
        self.assertEqual(scan_mst.immediate_events(struct.pack("<I", 0x52c00000), 0x1000), [])

    def test_mst_logical_masks_preserve_width_and_invalid_encoding(self):
        self.assertEqual(scan_mst.logical_immediate(0x32001c00), 0xff)
        self.assertEqual(scan_mst.logical_immediate(0xb2401c00), 0xff)
        self.assertIsNone(scan_mst.logical_immediate(0x3200fc00))
        self.assertIsNone(scan_mst.logical_immediate(0x32401c00))

    def test_mst_literal_candidates_are_not_substring_act_or_implementation_proof(self):
        oracle, _ = scan_mst.load_oracle(SOURCE.parents[1] / "docs/research/mst-source-signatures.json")
        self.assertEqual(scan_mst.literal_matches("action activation radio", oracle), [])
        for name in ("DPMSTTopology", "calculatePBN", "sendACT", "buildRAD", "RemoteDPCDRead", "MultiStream"):
            self.assertTrue(scan_mst.literal_matches(name, oracle), name)
        hits = scan_mst.string_hits(b"nothing\0DP MST payload table\0", 0x1000, oracle)
        self.assertEqual(hits[0]["address_hex"], "0x1008")
        self.assertEqual(hits[0]["assessment"], "UNQUALIFIED_LITERAL_CANDIDATE")
        self.assertEqual(scan_mst.string_hits(b"\xffVCPI\0", 0x1000, oracle), [])

    def test_mst_function_receipt_preserves_bounds_hash_and_candidate_only_status(self):
        oracle, _ = scan_mst.load_oracle(SOURCE.parents[1] / "docs/research/mst-source-signatures.json")
        raw = struct.pack("<3I", 0x52800000 | (0x1c0 << 5), 0x52800001 | (0x2c0 << 5), 0x94000040)
        receipt = scan_mst.function_receipt(raw, 0x1000, ["DPTest"], oracle)
        self.assertEqual(receipt["bytes_sha256"], hashlib.sha256(raw).hexdigest())
        self.assertEqual(receipt["constant_groups"][0]["id"], "mst_payload_registers")
        self.assertEqual(receipt["direct_calls"][0]["target_hex"], "0x1108")
        self.assertTrue(all(hit["assessment"] == "VALUE_MATCH_NOT_PROVEN_DPCD_ADDRESS" for hit in receipt["dpcd_value_candidates"]))
        self.assertIn("NOT_IMPLEMENTATION_PROOF", receipt["assessment"])
        self.assertEqual(scan_mst.function_bounds(0x1010, [0x1000, 0x1020], 0x1000, 0x40), (0x1000, 0x1020))
        self.assertIsNone(scan_mst.function_bounds(0xffc, [0x1000], 0x1000, 0x40))
        for raw_bytes, address in ((b"x", 0x1000), (b"\0" * 4, 3), (b"\0" * 65540, 0x1000)):
            with self.assertRaises(ValueError):
                scan_mst.immediate_events(raw_bytes, address)

    @staticmethod
    def graph_function(address, words):
        raw = b"".join(word.to_bytes(4, "little") for word in words)
        return {"address_hex": hex(address), "size": len(raw), "bytes_sha256": hashlib.sha256(raw).hexdigest(),
                "instructions": [{"address_hex": hex(address + index * 4), "bytes_hex": raw[index * 4:index * 4 + 4].hex(),
                                  "instruction": "ret" if word == 0xd65f03c0 else "blraa x8, x16" if word == 0xd73f0910 else "decoded"}
                                 for index, word in enumerate(words)]}

    def test_userserver_properties_preserve_names_not_sensitive_values(self):
        properties = {"IOUserClasses": ["DCPDPDeviceProxy"], "IOAssociatedServices": [4294970467],
                      "IOUserServerName": "com.apple.example", "Unit": 0, "IODPDeviceUserInterfaceSupported": True,
                      "serial-number": "sensitive-serial", "EDID": b"sensitive-edid", "private-token": "secret"}
        result = inspect_userserver.select_properties(properties)
        self.assertEqual(result["property_names"], sorted(properties))
        self.assertTrue(result["property_names_complete"])
        self.assertEqual(result["values"]["IOAssociatedServices"], [4294970467])
        self.assertNotIn("sensitive", str(result))
        self.assertNotIn("secret", str(result))
        for field, value in (("IOAssociatedServices", [True]), ("IOUserClasses", [b"blob"]),
                             ("IOUserServerName", "/private/personal/path"), ("Unit", -1)):
            result = inspect_userserver.select_properties({field: value})
            self.assertEqual(result["values"], {})
            self.assertEqual(result["relevant_values_unrepresented"], [field])
        with self.assertRaises(ValueError):
            inspect_userserver.select_properties({"bad\nname": 1})

    def test_userserver_selection_requires_fresh_exact_external_provider(self):
        target = {"entry_id_raw": 1234, "path": "IOService:/RTBuddy(DCPEXT0)/endpoint/DCPDPDeviceProxy",
                  "properties": {"values": {"Location": "External", "Unit": 0, "IODPDeviceUserInterfaceSupported": True}}}
        flag = "IODPDeviceUserInterfaceSupported"
        self.assertEqual(inspect_userserver.select_exact([target], 1234, target["path"], flag), 0)
        for records, entry_id in (([], 1234), ([target, target], 1234), ([target], 9999),
                      ([{**target, "properties": None}], 1234)):
            with self.assertRaises(ValueError):
                inspect_userserver.select_exact(records, entry_id, target["path"], flag)
        for field, value in (("Location", "Embedded"), ("Unit", False), (flag, False)):
            changed = {**target, "properties": {"values": {**target["properties"]["values"], field: value}}}
            with self.assertRaises(ValueError):
                inspect_userserver.select_exact([changed], 1234, target["path"], flag)

    def test_userserver_reader_preserves_errors_and_releases_partial_properties(self):
        reader = inspect_userserver.RegistryReader.__new__(inspect_userserver.RegistryReader)
        reader.calls = []
        reader.iokit = mock.Mock()
        reader.cf = mock.Mock()
        def failed_copy(handle, properties, allocator, options):
            properties._obj.value = 123
            return -536870207
        reader.iokit.IORegistryEntryCreateCFProperties.side_effect = failed_copy
        result, properties = reader.properties(42)
        self.assertEqual(result, -536870207)
        self.assertIsNone(properties)
        self.assertEqual(reader.calls[0]["ioreturn_hex"], "0xe00002c1")
        reader.cf.CFRelease.assert_called_once()
        self.assertEqual(reader.cf.CFRelease.call_args.args[0].value, 123)

    def test_userserver_reader_only_serializes_allowlisted_values(self):
        reader = inspect_userserver.RegistryReader.__new__(inspect_userserver.RegistryReader)
        reader.dictionary_items = mock.Mock(return_value=[("EDID", 111), ("serial-number", 222),
                                                         ("IOUserClasses", 333), ("IOClass", 444)])
        reader.property_value = mock.Mock(side_effect=[None, "DCPDPDeviceProxy"])
        properties = reader.property_dictionary(999)
        self.assertEqual(reader.property_value.call_args_list, [mock.call(333), mock.call(444)])
        selected = inspect_userserver.select_properties(properties)
        self.assertEqual(selected["property_names"], ["EDID", "IOClass", "IOUserClasses", "serial-number"])
        self.assertEqual(selected["relevant_values_unrepresented"], ["IOUserClasses"])
        self.assertEqual(selected["values"], {"IOClass": "DCPDPDeviceProxy"})

    def test_userserver_personality_retains_only_matching_technical_values(self):
        properties = {"CFBundleIdentifier": "com.apple.driver.DCPDPFamilyProxy", "IOKitPersonalities": {
            "DCPDPDeviceProxy": {"IOClass": "DCPDPDeviceProxy", "IOProviderClass": "AFKEndpointInterface",
                                 "IOPropertyMatch": {"EPICName": "dcpdp-device-epic"}, "serial-number": "sensitive"},
            "Other": {"IOClass": "Other", "private-token": "secret"}}}
        with tempfile.TemporaryDirectory() as directory:
            file = pathlib.Path(directory) / "Info.plist"
            raw = plistlib.dumps(properties)
            file.write_bytes(raw)
            report = inspect_userserver.driver_personality(file)
            self.assertEqual(report["sha256"], hashlib.sha256(raw).hexdigest())
            self.assertEqual(list(report["personalities"]), ["DCPDPDeviceProxy"])
            self.assertNotIn("sensitive", str(report))
            self.assertNotIn("secret", str(report))
            file.write_bytes(plistlib.dumps({**properties, "CFBundleIdentifier": "wrong"}))
            with self.assertRaises(ValueError):
                inspect_userserver.driver_personality(file)
        selected = inspect_userserver.select_properties({"IOPropertyMatch": {"serial-number": "sensitive"}})
        self.assertEqual(selected["values"], {})
        self.assertEqual(selected["relevant_values_unrepresented"], ["IOPropertyMatch"])

    def test_userserver_inspector_binds_only_public_registry_apis(self):
        iokit = mock.Mock()
        core_foundation = mock.Mock()
        with mock.patch.object(inspect_userserver.ctypes, "CDLL", side_effect=[iokit, core_foundation]) as load:
            inspect_userserver.RegistryReader()
        self.assertEqual(load.call_args_list, [
            mock.call("/System/Library/Frameworks/IOKit.framework/IOKit"),
            mock.call("/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation")])
        self.assertEqual(set(iokit._mock_children), {
            "IOServiceMatching", "IOServiceGetMatchingServices", "IOIteratorNext", "IOObjectRelease",
            "IORegistryEntryGetRegistryEntryID", "IORegistryEntryGetPath", "IORegistryEntryCreateCFProperties",
            "IORegistryEntryGetParentIterator", "IORegistryEntryGetChildIterator", "IORegistryEntryInPlane",
            "IORegistryGetRootEntry", "IOObjectCopyClass", "IOObjectCopyBundleIdentifierForClass",
            "IOObjectCopySuperclassForClass"})

    def test_call_graph_exports_exact_direct_sink_path(self):
        functions = {0x1000: self.graph_function(0x1000, [0x94000004, 0xd65f03c0]),
                     0x1010: self.graph_function(0x1010, [0x14000004]),
                     0x1020: self.graph_function(0x1020, [0xd65f03c0])}
        result = call_graph.bounded_call_graph(functions.__getitem__, [0x1000], {0x1020})["roots"][0]
        self.assertTrue(result["complete"])
        self.assertEqual(result["status"], "SINK_PATH_PRESENT")
        self.assertEqual([edge["callsite_hex"] for edge in result["sink_paths"][0]["path"]], ["0x1000", "0x1010"])

    def test_call_graph_keeps_indirect_calls_and_unknown_boundaries_open(self):
        functions = {0x1000: self.graph_function(0x1000, [0xd73f0910, 0x94000003, 0xd65f03c0])}
        result = call_graph.bounded_call_graph(functions.__getitem__, [0x1000], set())["roots"][0]
        self.assertFalse(result["complete"])
        self.assertEqual({gap["reason"] for gap in result["gaps"]},
                         {"UNRESOLVED_INDIRECT_CONTROL_FLOW", "MISSING_OR_INVALID_FUNCTION"})

    def test_call_graph_bounds_cycles_and_keeps_conditional_paths(self):
        functions = {0x1000: self.graph_function(0x1000, [0x54000080, 0x97ffffff, 0xd65f03c0]),
                 0x1010: self.graph_function(0x1010, [0xd65f03c0])}
        result = call_graph.bounded_call_graph(functions.__getitem__, [0x1000], {0x1010})["roots"][0]
        self.assertTrue(result["complete"])
        self.assertEqual(result["sink_paths"][0]["path"][0]["kind"], "CONDITIONAL_TAIL")
        limited = call_graph.bounded_call_graph(functions.__getitem__, [0x1000], set(), depth_limit=0)["roots"][0]
        self.assertEqual(limited["gaps"][0]["reason"], "TRAVERSAL_LIMIT")

    def test_call_graph_ignores_unreachable_bytes_not_missing_bytes(self):
        function = self.graph_function(0x1000, [0xd65f03c0, 0xd73f0910])
        self.assertEqual(call_graph.function_edges(function)["unresolved"], [])
        for field, value in (("size", 4), ("bytes_sha256", "0" * 64), ("address_hex", "0x1001")):
            with self.assertRaises(ValueError):
                call_graph.function_edges({**function, field: value})
        function["instructions"][0]["instruction"] = "UNDECODED"
        self.assertEqual(call_graph.function_edges(function)["unresolved"][0]["reason"], "UNDECODED_INSTRUCTION")

    def test_call_graph_fallthrough_and_unsupported_control_fail_closed(self):
        function = self.graph_function(0x1000, [0xd503201f])
        self.assertEqual(call_graph.function_edges(function)["unresolved"][0]["reason"], "FALLTHROUGH_OUTSIDE_FUNCTION")
        with self.assertRaises(ValueError):
            call_graph.bounded_call_graph(lambda address: function, [], set())
        with self.assertRaises(ValueError):
            call_graph.bounded_call_graph(lambda address: function, [0x1001], set())

    def test_graph_vtable_receipt_rejects_ambiguity_and_bad_fixups(self):
        pointer = {"pointer_format": 8, "slot_address_hex": "0x3010", "target_address_hex": "0x1020",
                   "raw_bytes_hex": "2000000000000080"}
        table = {"symbol": "__ZTVExample", "address_hex": "0x3000", "raw_bytes_hex": "00" * 16 + pointer["raw_bytes_hex"],
                 "bindings": [{"offset_from_primary_address_point": 0, "pointer": pointer, "exact_symbol_matches": ["target"]}]}
        receipt = call_graph.resolve_vtable_slot([table], "__ZTVExample", 0)
        self.assertEqual(receipt["target_hex"], "0x1020")
        functions = {0x1000: self.graph_function(0x1000, [0xd73f0910, 0xd65f03c0]),
                 0x1020: self.graph_function(0x1020, [0xd65f03c0])}
        result = call_graph.bounded_call_graph(functions.__getitem__, [0x1000], {0x1020}, virtual_edges={0x1000: receipt})["roots"][0]
        self.assertFalse(result["complete"])
        self.assertEqual(result["gaps"][0]["reason"], "RECEIVER_CONTEXT_REQUIRES_PROOF")
        self.assertEqual(result["sink_paths"][0]["path"][0]["kind"], "CONTEXTUAL_VTABLE")
        for tables, offset in (([table, table], 0), ([table], 8), ([table], 1)):
            with self.assertRaises(ValueError):
                call_graph.resolve_vtable_slot(tables, "__ZTVExample", offset)
        for field, value in (("pointer_format", 9), ("slot_address_hex", "0x3018"), ("raw_bytes_hex", "00" * 8)):
            with self.assertRaises(ValueError):
                call_graph.resolve_vtable_slot([{**table, "bindings": [{**table["bindings"][0], "pointer": {**pointer, field: value}}]}], "__ZTVExample", 0)

    def test_graph_rejects_undeclared_sink_and_retains_conditional_kinds(self):
        for word in (0x54000080, 0x54000090, 0x34000080, 0x36000080):
            functions = {0x1000: self.graph_function(0x1000, [word, 0xd65f03c0])}
            result = call_graph.bounded_call_graph(functions.__getitem__, [0x1000], {0x1010})["roots"][0]
            self.assertFalse(result["complete"])
            self.assertEqual(result["sink_paths"], [])
            self.assertEqual(result["gaps"][0]["reason"], "MISSING_OR_INVALID_FUNCTION")
        function = self.graph_function(0x1000, [0x94000004, 0xd65f03c0])
        result = call_graph.bounded_call_graph(lambda address: function, [0x1000], {0x1010})["roots"][0]
        self.assertFalse(result["complete"])
        self.assertEqual(result["gaps"][0]["detail"], "Target is not an exact function start")

    def test_graph_records_owner_and_gate_branch_predicates(self):
        cases = (
            (0x34000043, {"kind": "COMPARE_ZERO", "register": 3, "width_bits": 32, "branch_if": "ZERO"}),
            (0xb5000049, {"kind": "COMPARE_ZERO", "register": 9, "width_bits": 64, "branch_if": "NONZERO"}),
            (0x3400005f, {"kind": "COMPARE_ZERO", "register": 31, "width_bits": 32, "branch_if": "ZERO"}),
            (0x37000043, {"kind": "TEST_BIT", "register": 3, "bit_index": 0, "branch_if": "BIT_SET"}),
            (0xb6f80049, {"kind": "TEST_BIT", "register": 9, "bit_index": 63, "branch_if": "BIT_CLEAR"}),
            (0x54000041, {"kind": "CONDITION_FLAGS", "condition_code": 1, "consistent_branch": False}),
            (0x54000051, {"kind": "CONDITION_FLAGS", "condition_code": 1, "consistent_branch": True}),
        )
        for word, predicate in cases:
            with self.subTest(word=hex(word)):
                function = self.graph_function(0x1000, [word, 0xd65f03c0, 0xd65f03c0])
                result = call_graph.function_edges(function)
                self.assertEqual(result["reachable_instruction_count"], 3)
                self.assertEqual(result["conditions"], [{"callsite_hex": "0x1000",
                    "bytes_hex": word.to_bytes(4, "little").hex(), "instruction": "decoded",
                    "predicate": predicate, "taken_hex": "0x1008", "fallthrough_hex": "0x1004"}])

    def test_graph_predicates_preserve_backward_targets_and_unreachable_code(self):
        for word in (0x54ffffe0, 0x34ffffe2, 0x3607ffe3):
            function = self.graph_function(0x1000, [0xd503201f, word, 0xd65f03c0])
            result = call_graph.function_edges(function)
            self.assertEqual(result["reachable_instruction_count"], 3)
            self.assertEqual(result["conditions"][0]["taken_hex"], "0x1000")
            self.assertEqual(result["conditions"][0]["fallthrough_hex"], "0x1008")
        function = self.graph_function(0x1000, [0xd65f03c0, 0x34000040])
        self.assertEqual(call_graph.function_edges(function)["conditions"], [])

    def test_frontier_scope_keeps_unknowns_and_original_completeness(self):
        functions = {0x1000: self.graph_function(0x1000, [0x94000004, 0xd65f03c0]),
                     0x1010: self.graph_function(0x1010, [0xd73f0910, 0xd65f03c0])}
        graph = call_graph.bounded_call_graph(functions.__getitem__, [0x1000], set())
        graph["function_bodies"] = {hex(address): body for address, body in functions.items()}
        call_graph.classify_frontiers(graph, None, "kernel-identity")
        self.assertEqual(graph["roots"][0]["gaps"][0]["relevance"], "UNKNOWN")
        scope = {"schema_version": 1, "kernel_uuid": "kernel-identity", "functions": [{
            "address_hex": "0x1000", "bytes_sha256": functions[0x1000]["bytes_sha256"],
            "classification": "RESOURCE_MANAGEMENT_ONLY", "include_descendants": True,
            "evidence": "Synthetic reviewed allocation-only context."}]}
        call_graph.classify_frontiers(graph, scope, "kernel-identity")
        root = graph["roots"][0]
        self.assertEqual(root["gaps"][0]["relevance"], "RESOURCE_MANAGEMENT_ONLY")
        self.assertEqual(root["relevant_or_unknown_frontier_count"], 0)
        self.assertFalse(root["complete"])
        self.assertEqual(root["status"], "CALL_GRAPH_INCOMPLETE")
        scope["functions"].append({"address_hex": "0x1010", "callsite_hex": "0x1010",
            "bytes_sha256": functions[0x1010]["bytes_sha256"], "classification": "RELEVANT_TO_PROVIDER_OWNERSHIP",
            "evidence": "Synthetic specific provider callback supersedes ancestor classification."})
        call_graph.classify_frontiers(graph, scope, "kernel-identity")
        self.assertEqual(root["gaps"][0]["relevance"], "RELEVANT_TO_PROVIDER_OWNERSHIP")
        self.assertEqual(root["relevant_or_unknown_frontier_count"], 1)

    def test_frontier_scope_rejects_stale_and_ambiguous_receipts(self):
        function = self.graph_function(0x1000, [0xd73f0910, 0xd65f03c0])
        graph = call_graph.bounded_call_graph(lambda address: function, [0x1000], set())
        graph["function_bodies"] = {"0x1000": function}
        receipt = {"address_hex": "0x1000", "bytes_sha256": function["bytes_sha256"],
                   "classification": "UNKNOWN", "evidence": "Unresolved synthetic callback."}
        scope = {"schema_version": 1, "kernel_uuid": "kernel-identity", "functions": [receipt]}
        for malformed in ({**scope, "kernel_uuid": "other-kernel"}, {**scope, "schema_version": True},
                          {**scope, "functions": [receipt, receipt]}, {**scope, "extra": "ignored"}):
            with self.assertRaises(ValueError):
                call_graph.classify_frontiers(graph, malformed, "kernel-identity")
        for field, value in (("address_hex", "0x1010"), ("bytes_sha256", "0" * 64),
                             ("callsite_hex", "0x1001"), ("classification", "HARMLESS"),
                             ("evidence", ""), ("include_descendants", 1),
                             ("address_hex", 4096), ("callsite_hex", []), ("classification", [])):
            with self.assertRaises(ValueError):
                call_graph.classify_frontiers(graph, {**scope, "functions": [{**receipt, field: value}]}, "kernel-identity")

    def test_frontier_scope_does_not_transfer_state_between_roots(self):
        functions = {0x1000: self.graph_function(0x1000, [0x94000004, 0xd65f03c0]),
                     0x1010: self.graph_function(0x1010, [0xd73f0910, 0xd65f03c0])}
        graph = call_graph.bounded_call_graph(functions.__getitem__, [0x1000, 0x1010], set())
        graph["function_bodies"] = {hex(address): body for address, body in functions.items()}
        receipt = {"address_hex": "0x1010", "bytes_sha256": functions[0x1010]["bytes_sha256"],
                   "classification": "RESOURCE_MANAGEMENT_ONLY", "evidence": "Synthetic unused-state context only.",
                   "root_addresses_hex": ["0x1000"]}
        scope = {"schema_version": 1, "kernel_uuid": "kernel-identity", "functions": [receipt]}
        call_graph.classify_frontiers(graph, scope, "kernel-identity")
        self.assertEqual(graph["roots"][0]["gaps"][0]["relevance"], "RESOURCE_MANAGEMENT_ONLY")
        self.assertEqual(graph["roots"][1]["gaps"][0]["relevance"], "UNKNOWN")
        specific = {**receipt, "callsite_hex": "0x1010", "classification": "RELEVANT_TO_PROVIDER_OWNERSHIP",
                "root_addresses_hex": ["0x1010"]}
        call_graph.classify_frontiers(graph, {**scope, "functions": [receipt, specific]}, "kernel-identity")
        self.assertEqual(graph["roots"][0]["gaps"][0]["relevance"], "RESOURCE_MANAGEMENT_ONLY")
        self.assertEqual(graph["roots"][1]["gaps"][0]["relevance"], "RELEVANT_TO_PROVIDER_OWNERSHIP")
        for roots in ([], ["0x9990"], ["0x1000", "0x1000"], [4096]):
            with self.assertRaises(ValueError):
                call_graph.classify_frontiers(graph, {**scope, "functions": [{**receipt, "root_addresses_hex": roots}]}, "kernel-identity")

    def test_graph_scope_cli_fails_closed_before_collection(self):
        for arguments in (["--kernel-graph-scope", "unused"], ["--server", "--kernel-graph-scope", "unused"]):
            with mock.patch.object(sys, "argv", ["inspect_iodp.py", "--baseline", "unused", *arguments]), mock.patch("sys.stderr"):
                with self.assertRaises(SystemExit) as raised:
                    analysis.main()
                self.assertEqual(raised.exception.code, 2)
        with tempfile.TemporaryDirectory() as directory:
            scope = pathlib.Path(directory) / "scope.json"
            for content in (b"not-json", b"null", b" " * 262145):
                scope.write_bytes(content)
                arguments = ["inspect_iodp.py", "--baseline", "unused", "--server", "--kernel-graph-root", "0x1000",
                             "--kernel-graph-scope", str(scope)]
                with mock.patch.object(sys, "argv", arguments), mock.patch("sys.stderr"), mock.patch.object(analysis, "collect_server_evidence") as collect:
                    with self.assertRaises(SystemExit) as raised:
                        analysis.main()
                    self.assertEqual(raised.exception.code, 2)
                    collect.assert_not_called()

    def test_graph_virtual_options_fail_closed_before_capture(self):
        for arguments in (
            ["--kernel-graph-vtable-edge", "0x1000", "__ZTVExample", "0"],
            ["--server", "--kernel-graph-vtable-edge", "0x1000", "__ZTVExample", "0"],
            ["--server", "--kernel-graph-root", "0x1000", "--kernel-graph-vtable-edge", "invalid", "__ZTVExample", "0"],
        ):
            with mock.patch.object(sys, "argv", ["inspect_iodp.py", "--baseline", "unused", *arguments]), mock.patch("sys.stderr"):
                with self.assertRaises(SystemExit) as raised:
                    analysis.main()
                self.assertEqual(raised.exception.code, 2)

    def test_user_client_lifecycle_selection_is_scoped(self):
        for name in ("_iokit_task_terminate", "_iokit_connect_no_senders", "_is_io_service_close",
                     "__ZN12IOUserClient10clientDiedEv", "__ZN12IOUserClient13noMoreSendersEv",
                     "__ZN10IOMachPort13noMoreSendersEP8ipc_portjj"):
            self.assertTrue(kernel_image.user_client_lifecycle_symbol(name), name)
        for name in ("__ZN8IOService14externalMethodEv", "_task_terminate_internal",
                     "__ZN12OtherService10clientDiedEv", "__ZN12IOUserClient17setPropertiesImplEv"):
            self.assertFalse(kernel_image.user_client_lifecycle_symbol(name), name)

    def test_lifecycle_selection_requires_static_server_mode(self):
        with mock.patch.object(sys, "argv", ["inspect_iodp.py", "--baseline", "unused", "--kernel-lifecycle"]), mock.patch("sys.stderr"):
            with self.assertRaises(SystemExit) as raised:
                analysis.main()
            self.assertEqual(raised.exception.code, 2)

    def test_signing_identity_omits_paths_and_entitlement_values(self):
        metadata = "Identifier=macmst\nFormat=Mach-O thin (arm64)\nSignature=adhoc\nCDHash=" + "a" * 40
        metadata += "\nExecutable=/private-machine-path/macmst\nAuthority=private authority\n"
        raw = plistlib.dumps({"com.apple.security.app-sandbox": False, "private-entitlement": "secret fixture"})
        evidence = analysis.parse_signing_evidence(metadata, raw)
        self.assertEqual(evidence["identity"]["Identifier"], "macmst")
        self.assertFalse(evidence["app_sandbox_entitlement"])
        self.assertEqual(evidence["entitlement_key_count"], 2)
        self.assertEqual(evidence["authorization"], "UNRESOLVED_NOT_TESTED")
        for omitted in ("private-machine-path", "private authority", "private-entitlement", "secret fixture"):
            self.assertNotIn(omitted, str(evidence))

    def test_signing_identity_rejects_ambiguous_or_malformed_input(self):
        metadata = "Identifier=macmst\nFormat=Mach-O thin (arm64)\nSignature=adhoc\nCDHash=" + "a" * 40
        evidence = analysis.parse_signing_evidence(metadata, b"")
        self.assertEqual(evidence["entitlement_output_status"], "NO_DATA_REPORTED")
        self.assertIsNone(evidence["app_sandbox_entitlement"])
        for text, raw in ((metadata + "\nIdentifier=other", b""), ("", b""),
                          (metadata.replace("a" * 40, "a" * 41), b""),
                          (metadata, plistlib.dumps([])),
                          (metadata, plistlib.dumps({"com.apple.security.app-sandbox": "true"})),
                          (metadata, b"x" * (1024 * 1024 + 1))):
            with self.assertRaises(ValueError):
                analysis.parse_signing_evidence(text, raw)

    def test_direct_call_references_preserve_calls_and_tail_branches(self):
        raw = bytes.fromhex("04000094 ffffff17 20000054")
        result = kernel_image.direct_call_references(raw, 0x1000, {0x1010, 0x1000})
        self.assertEqual([(item["instruction_address_hex"], item["target_address_hex"], item["branch_kind"])
                          for item in result], [("0x1000", "0x1010", "BL"), ("0x1004", "0x1000", "B")])
        self.assertEqual(kernel_image.direct_call_references(raw, 0x1000, {0x100c}), [])

    def test_direct_call_references_reject_invalid_ranges_and_excess(self):
        for raw, base in ((b"\0", 0x1000), (bytes(4), -4), (bytes(4), 0x1001), (bytes(8), (1 << 64) - 4)):
            with self.assertRaises(ValueError):
                kernel_image.direct_call_references(raw, base, set())
        with self.assertRaises(ValueError):
            kernel_image.direct_call_references(bytes.fromhex("00000094") * 4097, 0,
                                                set(range(0, 4097 * 4, 4)))

    def test_reference_sources_reject_escaping_symlinks(self):
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as external:
            root = pathlib.Path(directory)
            outside = pathlib.Path(external) / "outside.h"
            outside.write_bytes(b"external fixture")
            (root / "linked.h").symlink_to(outside)
            with self.assertRaises(ValueError):
                analysis.reference_source_evidence(root)

    def test_reference_sources_reject_oversized_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            with (root / "oversized.c").open("wb") as stream:
                stream.truncate(2 * 1024 * 1024 + 1)
            with self.assertRaises(ValueError):
                analysis.reference_source_evidence(root)

    def test_reference_source_hashes_are_sorted_and_bounded(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            (root / "second.c").write_bytes(b"int second;\n")
            (root / "first.h").write_bytes(b"int first;\n")
            (root / "ignored.json").write_bytes(b"{}")
            records = analysis.reference_source_evidence(root)
            self.assertEqual([item["path"] for item in records], ["first.h", "second.c"])
            self.assertEqual(records, analysis.reference_source_evidence(root))
            self.assertEqual(len(records[0]["sha256"]), 64)
            self.assertEqual(len(records[0]["git_blob_sha1"]), 40)
            with self.assertRaises(ValueError):
                analysis.reference_source_evidence(root / "missing")

    def test_kernel_selection_requires_static_server_mode(self):
        for option, value in (("--kernel-symbol", "_example"), ("--kernel-vtable", "__ZTVExample"),
                              ("--kernel-image", "example"), ("--kernel-string", "example"),
                              ("--kernel-address", "0x1000"), ("--kernel-callers-of", "_example"),
                              ("--kernel-graph-root", "0x1000"), ("--kernel-graph-sink", "0x1000")):
            with mock.patch.object(sys, "argv", ["inspect_iodp.py", "--baseline", "unused", option, value]), mock.patch("sys.stderr"):
                with self.assertRaises(SystemExit) as raised:
                    analysis.main()
                self.assertEqual(raised.exception.code, 2)

    def test_graph_sink_requires_root(self):
        with mock.patch.object(sys, "argv", ["inspect_iodp.py", "--baseline", "unused", "--server", "--kernel-graph-sink", "0x1000"]), mock.patch("sys.stderr"):
            with self.assertRaises(SystemExit) as raised:
                analysis.main()
            self.assertEqual(raised.exception.code, 2)

    def test_function_starts_are_bounded_and_terminated(self):
        self.assertEqual(kernel_image.decode_function_starts(bytes.fromhex("801004080000"), 0x1000), [0x1800, 0x1804, 0x180c])
        backwards = bytes.fromhex("0810f8ffffffffffffffff0100")
        self.assertEqual(kernel_image.decode_function_starts(backwards, 0x1000), [0x1008, 0x1018, 0x1010])
        for malformed in (b"\x80", b"\x04", b"\x00\x01", b"\x01\x00", b"\x80" * 11, b"\xff" * 9 + b"\x02\x00"):
            with self.assertRaises(ValueError):
                kernel_image.decode_function_starts(malformed, 0x1000)

    def test_literal_reference_requires_exact_address_pair(self):
        raw = bytes.fromhex("71250a90 31621991 300240f9 110a1fd7")
        matches = kernel_image.literal_address_references(raw, 0x286086068, {0x29a532658})
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]["target_address_hex"], "0x29a532658")
        self.assertEqual(kernel_image.literal_address_references(raw, 0x286086068, {0x29a532660}), [])
        with self.assertRaises(ValueError):
            kernel_image.literal_address_references(raw[:-1], 0x286086068, {})

    def test_rpc_endpoint_selection_excludes_unrelated_clients(self):
        self.assertTrue(kernel_image.rpc_endpoint_symbol("__ZN20AFKEndpointInterface12abortCommandEPv"))
        self.assertTrue(kernel_image.rpc_endpoint_symbol("__ZN16AFKEPInterfaceV220handleClientResponseEyh"))
        self.assertTrue(kernel_image.rpc_endpoint_symbol("__ZN17AFKEPCommandLocal13parseResponseEP21CommandResponseHeader"))
        self.assertTrue(kernel_image.rpc_endpoint_symbol("__ZNK16AFKEPSendOptions14getSynchronousEv"))
        self.assertFalse(kernel_image.rpc_endpoint_symbol("__ZN30AFKEndpointInterfaceUserClient14enqueueCommandEj"))
        self.assertFalse(kernel_image.rpc_endpoint_symbol("__ZN25AFKEndpointInterfaceRelay14enqueueCommandEP20AFKEndpointInterface"))
        self.assertFalse(kernel_image.rpc_endpoint_symbol("__ZN20AFKEPInterfaceKextV29serializeEPv"))

    def test_duplicate_kernel_function_names_preserve_addresses(self):
        first = {"name": "abortCommand", "address": 0x1000}
        second = {"name": "abortCommand", "address": 0x2000}
        self.assertEqual(kernel_image.function_record_key(first, [first]), "abortCommand")
        self.assertEqual(kernel_image.function_record_key(first, [first, second]), "abortCommand [0x1000]")
        self.assertEqual(kernel_image.function_record_key(second, [second, first]), "abortCommand [0x2000]")

    def test_rpc_memory_and_wait_selection_is_scoped(self):
        for name in ("__ZN6OSData11appendBytesEPKvj", "__ZN13IOCommandGate12commandSleepEPvj",
                     "__ZN15IOAVCommandGate11commandGateEP9IOService"):
            self.assertTrue(kernel_image.rpc_memory_or_wait_symbol(name))
        for name in ("__ZN6OSData9serializeEP11OSSerialize", "__ZN16DCPDPDeviceProxy9writeDPCDEjPKhjj",
                     "__ZN14UnrelatedClass12commandSleepEPvj"):
            self.assertFalse(kernel_image.rpc_memory_or_wait_symbol(name))

    def test_static_client_routing_is_external_and_allowlisted(self):
        nodes = [{"Location": "External", "Unit": 0, "IOUserClientClass": "DCPDPDeviceProxyUserClient",
                  "IODPDeviceUserInterfaceSupported": True, "SerialNumber": "private", "IORegistryEntryChildren": []},
                 {"Location": "Embedded", "Unit": 0, "IOUserClientClass": "InternalClient"}]
        selected = kernel_image.select_external_client_routing(nodes)
        self.assertEqual(len(selected), 1)
        self.assertEqual(selected[0]["IOUserClientClass"], "DCPDPDeviceProxyUserClient")
        self.assertNotIn("SerialNumber", selected[0])
        self.assertNotIn("IORegistryEntryChildren", selected[0])
        with self.assertRaises(ValueError):
            kernel_image.select_external_client_routing({})

    def test_kernel_pointer8_fields_and_cache_level(self):
        base = 0xfffffe0007004000
        word = 0x8030bcad037a865c
        decoded = kernel_image.decode_kernel_pointer8(word, base)
        self.assertEqual(decoded["target_address_hex"], "0xfffffe000a7ac65c")
        self.assertTrue(decoded["authenticated"])
        self.assertEqual(decoded["next_bytes"], 24)
        self.assertEqual(decoded["diversity"], 0xbcad)
        with self.assertRaises(ValueError):
            kernel_image.decode_kernel_pointer8(word | (1 << 30), base)
        with self.assertRaises(ValueError):
            kernel_image.decode_kernel_pointer8(word, (1 << 64) - 1)

    def test_kernel_pointer8_requires_chain_membership(self):
        page = bytearray(64)
        struct.pack_into("<Q", page, 8, (6 << 51) | 0x100)
        struct.pack_into("<Q", page, 32, 0x200)
        decoded = kernel_image.verify_kernel_chain8(page, 8, 32, 0xfffffe0007004000)
        self.assertEqual(decoded["chain_hops"], 1)
        self.assertEqual(decoded["target_address_hex"], "0xfffffe0007004200")
        for start, requested in ((8, 16), (0xffff, 32), (0x8000, 32), (8, 33), (8, 64)):
            with self.assertRaises(ValueError):
                kernel_image.verify_kernel_chain8(page, start, requested, 0xfffffe0007004000)

    def test_macho_uuid_is_exact_and_unique(self):
        identity = bytes(range(16))
        header = struct.pack("<8I", 0xfeedfacf, 0x0100000c, 2, 0xc, 1, 24, 0, 0)
        data = header + struct.pack("<II", 0x1b, 24) + identity
        self.assertEqual(kernel_image.macho_uuid(data), "00010203-0405-0607-0809-0A0B0C0D0E0F")
        with self.assertRaises(ValueError):
            kernel_image.macho_uuid(struct.pack("<8I", 0xfeedfacf, 0x0100000c, 2, 0xc, 0, 0, 0, 0))

    def test_fileset_entry_bounds_and_identity(self):
        entry = struct.pack("<IIQQII", 0x80000035, 40, 0xfffffe0007000000, 72, 32, 0) + b"kernel\0\0"
        header = struct.pack("<8I", 0xfeedfacf, 0x0100000c, 2, 0xc, 1, 40, 0, 0)
        data = header + entry + bytes(32)
        self.assertEqual(kernel_image.fileset_entries(data)["kernel"]["file_offset"], 72)
        with self.assertRaises(ValueError):
            kernel_image.fileset_entries(data[:72])

    def test_kernel_container_rejects_ambiguous_or_non_kernel_input(self):
        def field(tag, value):
            return bytes((tag, len(value))) + value
        body = field(0x16, b"IM4P") + field(0x16, b"krnl") + field(0x16, b"test") + field(0x04, b"bvx2data")
        encoded = field(0x30, body)
        payload, metadata = kernel_image.kernel_payload(encoded)
        self.assertEqual(payload, b"bvx2data")
        self.assertEqual(metadata["payload_type"], "krnl")
        for invalid in (encoded[:-1], encoded + b"extra", encoded.replace(b"krnl", b"dcpf"), b"\x30\x80"):
            with self.assertRaises(ValueError):
                kernel_image.kernel_payload(invalid)

    def test_macho_command_bounds_and_architecture(self):
        header = struct.pack("<8I", 0xfeedfacf, 0x0100000c, 2, 0xc, 1, 16, 0, 0)
        data = header + struct.pack("<IIQ", 0x2a, 16, 0)
        self.assertEqual(len(kernel_image.macho_commands(data)[1]), 1)
        for invalid in (data[:-1], data[:32] + struct.pack("<IIQ", 0x2a, 24, 0),
                        data[:4] + struct.pack("<I", 0x01000007) + data[8:]):
            with self.assertRaises(ValueError):
                kernel_image.macho_commands(invalid)

    def test_macho_strings_fail_closed(self):
        self.assertEqual(kernel_image.cstring(b"\0method\0", 1), "method")
        for raw, offset in ((b"bad", 0), (b"ok\0", 8), (b"ok\0", -1)):
            with self.assertRaises(ValueError):
                kernel_image.cstring(raw, offset)

    def test_export_matches_require_exact_unambiguous_base(self):
        exports = "  0x10 _IODPDeviceReadDPCD\n  0x20 _CFRelease\n"
        segments = "  0x180000000 __TEXT   32KB\n  0x999999999    __text 128\n"
        self.assertEqual(analysis.parse_export_addresses(exports, segments),
                         {"_IODPDeviceReadDPCD": 0x180000010, "_CFRelease": 0x180000020})
        for malformed in ("", segments + segments):
            with self.assertRaises(ValueError):
                analysis.parse_export_addresses(exports, malformed)

    def test_authenticated_stub_uses_raw_address_calculation(self):
        stub = bytes.fromhex("71250a90 31621991 300240f9 110a1fd7")
        self.assertEqual(dyld_cache.authenticated_stub_slot(stub, 0x286086068), 0x29a532658)
        for malformed in (stub[:12], stub[:12] + bytes(4), bytes(16)):
            with self.assertRaises(ValueError):
                dyld_cache.authenticated_stub_slot(malformed, 0x286086068)

    def test_slide5_authentication_fields_and_plain_high_bits(self):
        base = 0x180000000
        word = (1 << 63) | (3 << 52) | (1 << 50) | (0x1234 << 34) | 0x487eeb0
        result = dyld_cache.decode_slide_pointer5(word, base)
        self.assertEqual(result, {"authenticated": True, "next_bytes": 24, "diversity": 0x1234,
                                  "address_diversity": True, "key": "IA", "target": 0x18487eeb0})
        regular = dyld_cache.decode_slide_pointer5((0xab << 34) | 0x42, base)
        self.assertEqual(regular["target"], 0xab00000180000042)
        self.assertFalse(regular["authenticated"])
        with self.assertRaises(ValueError):
            dyld_cache.decode_slide_pointer5(1 << 42, base)

    def test_slide5_requires_actual_chain_membership(self):
        page = bytearray(4096)
        struct.pack_into("<Q", page, 8, (2 << 52) | 0x100)
        struct.pack_into("<Q", page, 24, (1 << 63) | 0x200)
        word, result, hops = dyld_cache.verify_chain5(page, 8, 24, 0x180000000)
        self.assertEqual((word, result["target"], hops), ((1 << 63) | 0x200, 0x180000200, 1))
        for start, target in ((0xffff, 24), (8, 16), (8, 32), (4096, 4096), (9, 24)):
            with self.assertRaises(ValueError):
                dyld_cache.verify_chain5(page, start, target, 0x180000000)

    def test_cache_mapping_translation_is_bounded(self):
        header = bytearray(88)
        header[:16] = b"dyld_v1  arm64e\0\0"
        struct.pack_into("<II", header, 16, 24, 2)
        struct.pack_into("<QQQII", header, 24, 0x180000000, 0x1000, 0, 5, 5)
        struct.pack_into("<QQQII", header, 56, 0x190000000, 0x1000, 0x1000, 3, 3)
        mappings = dyld_cache.cache_mappings(header, 0x2000)
        self.assertEqual(dyld_cache.file_location(mappings, 0x190000080, 8)[1], 0x1080)
        for address, size in ((0x190000fff, 8), (0, 8), (0x190000000, 0)):
            with self.assertRaises(ValueError):
                dyld_cache.file_location(mappings, address, size)
        with self.assertRaises(ValueError):
            dyld_cache.file_location([mappings[0], mappings[0]], 0x180000000, 8)

    def test_cache_mapping_rejects_truncation_and_overflow(self):
        for raw in (b"", b"not a cache" + bytes(64)):
            with self.assertRaises(ValueError):
                dyld_cache.cache_mappings(raw, len(raw))
        header = bytearray(56)
        header[:16] = b"dyld_v1  arm64e\0\0"
        struct.pack_into("<II", header, 16, 24, 1)
        struct.pack_into("<QQQII", header, 24, 0xfffffffffffffff0, 0x100, 0, 3, 3)
        with self.assertRaises(ValueError):
            dyld_cache.cache_mappings(header, 0x1000)
        struct.pack_into("<QQQII", header, 24, 0x1000, 0x1000, 0x1000, 3, 3)
        with self.assertRaises(ValueError):
            dyld_cache.cache_mappings(header, 0x1000)

    def test_missing_raw_instruction_is_not_fabricated(self):
        self.assertIsNone(analysis.raw_instruction({0x1000: 0}, 0x1000))
        self.assertEqual(analysis.raw_instruction({0x1000 + offset: offset for offset in range(4)}, 0x1000), b"\x00\x01\x02\x03")

    def test_raw_bytes_and_exact_cstring_addresses(self):
        values = analysis.section_bytes("header:\n0x1000: 49 4f 44 50 44 65 76 69 63 65 00\n")
        self.assertEqual(analysis.raw_strings(values), [{"address_hex": "0x1000", "value": "IODPDevice"}])
        self.assertEqual(analysis.raw_strings({4096: 73, 4097: 79}), [])

    def test_raw_bytes_reject_overlap(self):
        with self.assertRaises(ValueError):
            analysis.section_bytes("0x1000: 01 02\n0x1001: 02\n")

    def test_a64_direct_branches_preserve_signed_offsets(self):
        self.assertEqual(analysis.direct_branch_target(bytes.fromhex("04000094"), 0x1000), 0x1010)
        self.assertEqual(analysis.direct_branch_target(bytes.fromhex("ffffff97"), 0x1000), 0xffc)
        self.assertEqual(analysis.direct_branch_target(bytes.fromhex("01000014"), 0x1000), 0x1004)
        self.assertIsNone(analysis.direct_branch_target(bytes.fromhex("20000054"), 0x1000))
        with self.assertRaises(ValueError):
            analysis.direct_branch_target(b"\x00", 0x1000)

    def test_exports_are_names_and_image_offsets_only(self):
        self.assertEqual(analysis.parse_exports("  0x00020EB0 _IODPDeviceReadDPCD\n  0x123 _Unrelated\n"),
                         {"_IODPDeviceReadDPCD": "0x00020EB0"})

    def test_function_boundaries_and_actual_calls(self):
        source = "_caller:\n0x1000   bl       _IODPDeviceReadDPCD\n0x1004   ret\n_other:\n0x1008   bl _IODPDeviceWriteDPCD\n_reference:\n0x100c   adrp x1, 1 ; _IODPDeviceReadDPCD\n"
        blocks = analysis.disassembly_blocks(source)
        self.assertEqual(set(blocks), {"_caller", "_other", "_reference"})
        self.assertEqual(set(analysis.read_calls(blocks)), {"_caller"})
        self.assertNotIn("_other:", blocks["_caller"])

    def test_tail_call_is_recorded_not_prefix_match(self):
        blocks = {"tail": "0x1000   b _IODPDeviceCreateWithService\n",
                  "different": "0x1000   bl _IODPDeviceReadDPCDExtra\n"}
        self.assertEqual(set(analysis.read_calls(blocks)), {"tail"})

    def test_duplicate_local_labels_preserve_both_occurrences(self):
        blocks = analysis.disassembly_blocks("_OUTLINED_FUNCTION_0:\n0x1000 ret\n_OUTLINED_FUNCTION_0:\n0x2000 ret\n")
        self.assertEqual(len(blocks), 2)
        self.assertIn("0x1000", blocks["_OUTLINED_FUNCTION_0"])
        self.assertIn("0x2000", blocks["_OUTLINED_FUNCTION_0 [occurrence 2]"])

    def test_duplicate_focus_symbols_fail_closed(self):
        with self.assertRaises(ValueError):
            analysis.disassembly_blocks("_IODPDeviceReadDPCD:\n0x1000 ret\n_IODPDeviceReadDPCD:\n0x2000 ret\n")

    def test_string_selection_does_not_capture_unrelated_fields(self):
        self.assertEqual(analysis.selected_strings("0x100 IODPDevice\n0x200 unrelated\n"), ["0x100 IODPDevice"])


if __name__ == "__main__":
    unittest.main()