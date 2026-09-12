import importlib.util
import hashlib
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

SPEC = importlib.util.spec_from_file_location("inspect_iodp", SOURCE)
analysis = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(analysis)


class StaticAnalysisParserTests(unittest.TestCase):
    @staticmethod
    def graph_function(address, words):
        raw = b"".join(word.to_bytes(4, "little") for word in words)
        return {"address_hex": hex(address), "size": len(raw), "bytes_sha256": hashlib.sha256(raw).hexdigest(),
                "instructions": [{"address_hex": hex(address + index * 4), "bytes_hex": raw[index * 4:index * 4 + 4].hex(),
                                  "instruction": "ret" if word == 0xd65f03c0 else "blraa x8, x16" if word == 0xd73f0910 else "decoded"}
                                 for index, word in enumerate(words)]}

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