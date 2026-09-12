import argparse
import ctypes
import datetime
import hashlib
import json
import pathlib
import plistlib
import re
import subprocess
import sys

from dyld_cache import DyldCache, adrp_add_target, authenticated_stub_slot, direct_branch_target
from kernel_image import collect_server_evidence


IOKIT_IMAGE = "/System/Library/Frameworks/IOKit.framework/Versions/A/IOKit"
COREFOUNDATION_IMAGE = "/System/Library/Frameworks/CoreFoundation.framework/Versions/A/CoreFoundation"
CALLER_IMAGES = ("/usr/lib/updaters/libPS190Updater.dylib", "/usr/lib/libdpfu.dylib")
FOCUS = frozenset({
    "_IODPDeviceCreate", "_IODPDeviceCreateWithLocation", "_IODPDeviceCreateWithService",
    "_IODPDeviceReadDPCD", "_IODPDeviceWriteDPCD", "_IODPDeviceGetAVDevice",
    "_IODPDeviceGetController", "_IODPDeviceGetTypeID", "___IODPDeviceRegister",
    "_IODPServiceCreateWithService", "_IODPServiceGetDevice", "_IOAVObjectConformsTo",
    "_IOAVDeviceCreateWithService", "_IOAVDeviceCopyProperty",
    "_IODPServiceCreate", "_IODPServiceCreateWithLocation", "_IODPServiceGetAVService",
    "___IODPDeviceFree", "___IODPServiceRegister", "___IODPServiceFree",
    "___IOAVDeviceRegister", "___IOAVDeviceFree", "___IODPControllerRegister", "___IODPControllerFree",
    "_IOServiceOpen", "_IOServiceClose", "_IOConnectCallMethod", "_IOObjectRetain",
    "_IOObjectRelease", "_IORegistryEntryCreateCFProperty",
})
CALLER_METHODS = frozenset({
    "+[PS190IODPDevice allDevices]",
    "-[PS190IODPDevice initWithService:rootPath:]",
    "-[PS190IODPDevice readRegisterAddress:buffer:length:]",
    "-[PS190IODPDevice dealloc]",
})


def parse_signing_evidence(metadata, entitlement_bytes):
    if len(metadata) > 65536 or len(entitlement_bytes) > 1024 * 1024:
        raise ValueError("Excessive code-signing metadata")
    allowed = {"Identifier", "Format", "CodeDirectory", "Signature", "TeamIdentifier", "CDHash"}
    identity = {}
    for line in metadata.splitlines():
        key, separator, value = line.partition("=")
        if separator and key in allowed:
            if key in identity or not value or len(value) > 512:
                raise ValueError("Ambiguous or invalid code-signing identity field")
            identity[key] = value
    if not {"Identifier", "Format", "Signature", "CDHash"} <= identity.keys():
        raise ValueError("Missing code-signing identity fields")
    if not re.fullmatch(r"(?:[0-9a-fA-F]{40}|[0-9a-fA-F]{64})", identity["CDHash"]):
        raise ValueError("Invalid code-directory hash")
    if not re.fullmatch(r"[A-Za-z0-9._-]+", identity["Identifier"]):
        raise ValueError("Unsupported executable identifier")
    entitlements = plistlib.loads(entitlement_bytes) if entitlement_bytes.strip() else {}
    if not isinstance(entitlements, dict):
        raise ValueError("Entitlements are not a property-list dictionary")
    sandbox = entitlements.get("com.apple.security.app-sandbox")
    if sandbox is not None and not isinstance(sandbox, bool):
        raise ValueError("App Sandbox entitlement is not boolean")
    return {"identity": identity, "entitlement_key_count": len(entitlements),
            "entitlement_output_status": "PLIST_REPORTED" if entitlement_bytes.strip() else "NO_DATA_REPORTED",
            "entitlement_output_sha256": hashlib.sha256(entitlement_bytes).hexdigest(),
            "app_sandbox_entitlement": sandbox,
            "authorization": "UNRESOLVED_NOT_TESTED",
            "privacy": "Executable path, authority details and entitlement names/values omitted except App Sandbox boolean."}


def collect_probe_signing(executable, repository):
    executable = pathlib.Path(executable).resolve()
    repository = pathlib.Path(repository).resolve()
    if not executable.is_relative_to(repository) or not executable.is_file() or executable.stat().st_size > 16 * 1024 * 1024:
        raise ValueError("Signing inspection requires a bounded local probe executable")
    before = hashlib.sha256(executable.read_bytes()).hexdigest()
    command = ["/usr/bin/codesign", "--display", "--verbose=4", "--entitlements", "-", str(executable)]
    result = subprocess.run(command, capture_output=True, timeout=30, check=False)
    if result.returncode:
        raise RuntimeError("Code-signing display failed; no signing or authorization fallback")
    evidence = parse_signing_evidence(result.stderr.decode("utf-8"), result.stdout)
    if hashlib.sha256(executable.read_bytes()).hexdigest() != before:
        raise ValueError("Probe executable changed during signing inspection")
    return {**evidence, "probe_relative_path": str(executable.relative_to(repository)),
            "probe_sha256": before, "command": command[:-1] + [str(executable.relative_to(repository))],
            "exit_code": result.returncode}


def reference_source_evidence(root):
    root = pathlib.Path(root).resolve()
    records = []
    for file in sorted(root.rglob("*")):
        if not file.is_file() or file.suffix not in (".c", ".h", ".cpp", ".py"):
            continue
        if not file.resolve().is_relative_to(root) or file.stat().st_size > 2 * 1024 * 1024 or len(records) >= 64:
            raise ValueError("Reference source escapes root or exceeds capture bounds")
        raw = file.read_bytes()
        records.append({"path": str(file.relative_to(root)), "size": len(raw),
                        "sha256": hashlib.sha256(raw).hexdigest(),
                        "git_blob_sha1": hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()})
    if not records:
        raise ValueError("No reference source files found")
    return records


def parse_exports(text):
    return {match[2]: match[1] for match in re.finditer(
        r"^\s*(0x[0-9A-Fa-f]+)\s+(_IODP[A-Za-z0-9_]+)\b", text, re.MULTILINE)}


def parse_export_addresses(exports, segments):
    bases = re.findall(r"^\s*(0x[0-9a-fA-F]+)\s+__TEXT\s", segments, re.MULTILINE)
    if len(bases) != 1:
        raise ValueError("Image base does not resolve uniquely")
    base = int(bases[0], 16)
    result = {}
    for match in re.finditer(r"^\s*(0x[0-9a-fA-F]+)\s+(_[^\s]+)\s*$", exports, re.MULTILINE):
        name = match[2]
        if name in result:
            raise ValueError("Duplicate exported symbol")
        result[name] = base + int(match[1], 16)
    return result


def resolve_call_bindings(cache, functions, stubs, export_addresses):
    result = []
    for name, function in sorted(functions.items()):
        for instruction in function["raw_byte_llvm_crosscheck"]:
            target_text = instruction["direct_branch_target_hex"]
            if target_text not in stubs:
                continue
            address = int(target_text, 16)
            raw = cache.read(address, 16)
            recorded = b"".join(bytes.fromhex(item["bytes_hex"]) for item in stubs[target_text])
            if raw != recorded:
                raise ValueError("Disk stub bytes differ from dyld_info evidence")
            slot = authenticated_stub_slot(raw, address)
            pointer = cache.pointer(slot)
            symbols = sorted(symbol for symbol, target in export_addresses.items() if target == pointer["target"])
            result.append({"caller": name, "call_address_hex": instruction["address_hex"],
                           "call_bytes_hex": instruction["bytes_hex"], "stub_address_hex": target_text,
                           "stub_bytes_hex": raw.hex(), "pointer": pointer, "exact_export_matches": symbols,
                           "binding_status": "EXACT_EXPORT" if len(symbols) == 1 else "UNRESOLVED_OR_ALIASED"})
    return result


def resolve_cf_lifecycle(cache, functions, all_blocks):
    result = []
    for kind in ("IODPDevice", "IODPService", "IOAVDevice", "IODPController"):
        register_name = "___" + kind + "Register"
        if register_name not in functions:
            continue
        instructions = functions[register_name]["raw_byte_llvm_crosscheck"]
        addresses = []
        for index, instruction in enumerate(instructions[:-1]):
            if instruction["bytes_hex"] is None or instructions[index + 1]["bytes_hex"] is None:
                continue
            raw = bytes.fromhex(instruction["bytes_hex"] + instructions[index + 1]["bytes_hex"])
            try:
                target = adrp_add_target(raw, int(instruction["address_hex"], 16), 0)
            except ValueError:
                continue
            addresses.append((target, instruction["address_hex"], raw.hex()))
        if len(addresses) != 1:
            raise ValueError("CF runtime class address is ambiguous")
        class_address, instruction_address, instruction_bytes = addresses[0]
        header = cache.read(class_address, 40)
        if int.from_bytes(header[:8], "little") != 0:
            raise ValueError("Unsupported CF runtime class version")
        name_pointer = cache.pointer(class_address + 8)
        class_name = cache.read(name_pointer["target"], 64).split(b"\0", 1)[0].decode("ascii")
        if class_name != kind:
            raise ValueError("CF class name does not match registration function")
        callback = cache.pointer(class_address + 32)
        matches = []
        for name, block in all_blocks.items():
            first = re.search(r"^(0x[0-9a-fA-F]+)\s", block, re.MULTILINE)
            if first and int(first[1], 16) == callback["target"]:
                matches.append(name)
        if len(matches) != 1:
            raise ValueError("CF finalizer function does not resolve uniquely")
        result.append({"class_name": kind, "registration_function": register_name,
                       "class_address_hex": hex(class_address), "class_header_bytes_hex": header.hex(),
                       "class_reference_instruction_address_hex": instruction_address,
                       "class_reference_instruction_bytes_hex": instruction_bytes,
                       "class_name_pointer": name_pointer, "finalize_offset": 32,
                       "finalizer_pointer": callback, "finalizer_symbol": matches[0]})
    return result


def disassembly_blocks(text):
    blocks = {}
    occurrences = {}
    current = None
    for line in text.splitlines():
        match = re.fullmatch(r"([^\s][^\n]*):", line)
        if match:
            current = match[1]
            occurrences[current] = occurrences.get(current, 0) + 1
            if current in FOCUS and occurrences[current] > 1:
                raise ValueError("Duplicate disassembly heading; architecture/scope is ambiguous")
            if occurrences[current] > 1:
                current += " [occurrence " + str(occurrences[current]) + "]"
            blocks[current] = [line]
        elif current is not None:
            blocks[current].append(line)
    return {name: "\n".join(lines).rstrip() + "\n" for name, lines in blocks.items()}


def read_calls(blocks):
    call = re.compile(r"\b(?:bl|b)\s+_IODPDevice(?:ReadDPCD|CreateWithService|Create)\s*(?:;.*)?$", re.MULTILINE)
    return {name: text for name, text in blocks.items() if call.search(text)}


def selected_strings(text):
    return [line for line in text.splitlines()
            if any(value in line for value in ("IODPDevice", "IODPService", "IOAVDevice",
                                               "UserInterfaceSupported", "IOService", "IOAVPlane"))]


def section_bytes(text):
    result = {}
    for line in text.splitlines():
        match = re.fullmatch(r"(0x[0-9a-fA-F]+):\s+((?:[0-9a-fA-F]{2}\s*)+)", line)
        if match:
            address = int(match[1], 16)
            for offset, value in enumerate(bytes.fromhex(match[2])):
                if address + offset in result:
                    raise ValueError("Overlapping raw byte addresses")
                result[address + offset] = value
    return result


def raw_strings(values):
    result = []
    start = None
    previous = None
    buffer = bytearray()
    for address, value in sorted(values.items()):
        if previous is not None and address != previous + 1:
            buffer.clear()
            start = None
        previous = address
        if value == 0:
            if start is not None:
                try:
                    text = buffer.decode("utf-8")
                    if any(name in text for name in ("IODPDevice", "IODPService", "IOAVDevice", "UserInterfaceSupported")) or text in ("%s%s", "IOService"):
                        result.append({"address_hex": hex(start), "value": text})
                except UnicodeDecodeError:
                    pass
            buffer.clear()
            start = None
        else:
            if start is None:
                start = address
            buffer.append(value)
    return result


def raw_instruction(values, address):
    if not all(address + offset in values for offset in range(4)):
        return None
    return bytes(values[address + offset] for offset in range(4))


class LLVMDisassembler:
    def __init__(self):
        clang = pathlib.Path(subprocess.check_output(["/usr/bin/xcrun", "--find", "clang"], text=True).strip())
        self.path = clang.parent.parent / "lib/libLTO.dylib"
        self.library = ctypes.CDLL(str(self.path))
        self.library.lto_initialize_disassembler.argtypes = []
        self.library.lto_initialize_disassembler.restype = None
        self.library.lto_initialize_disassembler()
        self.library.LLVMCreateDisasmCPUFeatures.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p,
                                                            ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p]
        self.library.LLVMCreateDisasmCPUFeatures.restype = ctypes.c_void_p
        self.features = "+pauth,+lse"
        self.context = self.library.LLVMCreateDisasmCPUFeatures(b"arm64-apple-macosx", b"generic", self.features.encode(), None, 0, None, None)
        if not self.context:
            raise RuntimeError("Installed LLVM cannot initialize the arm64 disassembler")
        self.library.LLVMDisasmInstruction.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint64,
                                                      ctypes.c_uint64, ctypes.c_char_p, ctypes.c_size_t]
        self.library.LLVMDisasmInstruction.restype = ctypes.c_size_t
        self.library.LLVMDisasmDispose.argtypes = [ctypes.c_void_p]
        self.library.LLVMDisasmDispose.restype = None

    def decode(self, address, instruction):
        buffer = ctypes.create_string_buffer(instruction)
        output = ctypes.create_string_buffer(256)
        size = self.library.LLVMDisasmInstruction(self.context, buffer, len(instruction), address, output, len(output))
        target = direct_branch_target(instruction, address)
        return {"address_hex": hex(address), "bytes_hex": instruction.hex(),
                "instruction": output.value.decode().strip() if size == 4 else "UNDECODED",
                "direct_branch_target_hex": hex(target) if target is not None else None}

    def close(self):
        self.library.LLVMDisasmDispose(self.context)


def main():
    parser = argparse.ArgumentParser(description="Static IODP inspection; no private function is invoked.")
    parser.add_argument("--baseline", required=True, type=pathlib.Path,
                        help="Existing capture containing sdk-surface.json and environment provenance.")
    parser.add_argument("--output", type=pathlib.Path)
    parser.add_argument("--cache", type=pathlib.Path, default=pathlib.Path(
        "/System/Volumes/Preboot/Cryptexes/OS/System/Library/dyld/dyld_shared_cache_arm64e"),
        help="Read-only primary arm64e shared-cache file for authenticated binding evidence.")
    parser.add_argument("--server", action="store_true",
                        help="Statically inspect the uniquely identified local arm64 boot image; never load it.")
    parser.add_argument("--kernel-symbol", action="append", default=[], help="Additional exact kernel symbol to capture; requires --server.")
    parser.add_argument("--kernel-vtable", action="append", default=[], help="Additional exact kernel vtable to resolve; requires --server.")
    parser.add_argument("--kernel-image", action="append", default=[], help="Additional exact fileset bundle ID to inspect; requires --server.")
    parser.add_argument("--kernel-string", action="append", default=[], help="Capture declared functions referencing this exact kernel C string; requires --server.")
    parser.add_argument("--kernel-address", action="append", default=[], type=lambda value: int(value, 0),
                        help="Capture this exact declared function start in the matched image; requires --server.")
    parser.add_argument("--kernel-callers-of", action="append", default=[],
                        help="Capture declared functions with a direct B/BL to this exact defined symbol; requires --server.")
    parser.add_argument("--kernel-lifecycle", action="store_true",
                        help="Capture bounded IOUserClient task-death/close ownership methods; requires --server.")
    parser.add_argument("--kernel-graph-root", action="append", default=[], type=lambda value: int(value, 0),
                        help="Export bounded direct-call paths from this declared function start; requires --server.")
    parser.add_argument("--kernel-graph-sink", action="append", default=[], type=lambda value: int(value, 0),
                        help="Stop graph traversal at this exact sink address; requires --kernel-graph-root.")
    parser.add_argument("--kernel-graph-vtable-edge", nargs=3, action="append", default=[],
                        metavar=("CALLSITE", "VTABLE", "OFFSET"),
                        help="Follow a declared vtable slot in a selected receiver context; context remains a proof gap. Requires a graph root.")
    parser.add_argument("--reference-root", type=pathlib.Path,
                        help="Hash reference source files already downloaded under artifacts/sources; never execute them.")
    parser.add_argument("--signing-probe", type=pathlib.Path,
                        help="Statically record allowlisted codesign identity for a local probe executable; never run or sign it.")
    args = parser.parse_args()
    if (args.kernel_symbol or args.kernel_vtable or args.kernel_image or args.kernel_string or args.kernel_address or args.kernel_callers_of or args.kernel_lifecycle or args.kernel_graph_root or args.kernel_graph_sink or args.kernel_graph_vtable_edge) and not args.server:
        parser.error("kernel selection options require --server")
    if (args.kernel_graph_sink or args.kernel_graph_vtable_edge) and not args.kernel_graph_root:
        parser.error("kernel graph sinks require a graph root")
    try:
        graph_virtual_edges = [(int(callsite, 0), symbol, int(offset, 0))
                               for callsite, symbol, offset in args.kernel_graph_vtable_edge]
    except ValueError:
        parser.error("graph callsite and vtable offset must be integers")
    if sys.platform != "darwin":
        parser.error("requires macOS dyld_info")
    repository = pathlib.Path(__file__).resolve().parents[1]
    root = repository / "artifacts/probes"
    signing_evidence = collect_probe_signing(args.signing_probe, repository) if args.signing_probe else None
    references = []
    if args.reference_root is not None:
        if not args.reference_root.resolve().is_relative_to((repository / "artifacts/sources").resolve()):
            parser.error("reference root must be under artifacts/sources")
        references = reference_source_evidence(args.reference_root)
    timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output = args.output or root / ("iodp-static-" + timestamp)
    if not output.resolve().is_relative_to(root.resolve()) or output.resolve() == root.resolve():
        parser.error("output must be a new child directory under artifacts/probes")
    baseline = args.baseline.resolve()
    if not baseline.is_relative_to(root.resolve()):
        parser.error("baseline must be under artifacts/probes")
    sdk = json.loads((baseline / "sdk-surface.json").read_text())
    cache = DyldCache(args.cache)
    output.mkdir(parents=True, exist_ok=False)
    commands = []

    def inspect(arguments):
        argv = ["/usr/bin/dyld_info", *arguments]
        result = subprocess.run(argv, capture_output=True, text=True, timeout=120, check=False)
        commands.append({"argv": argv, "exit_code": result.returncode,
                         "stdout_sha256": hashlib.sha256(result.stdout.encode()).hexdigest(),
                         "stderr": result.stderr.replace(str(pathlib.Path.home()), "~")})
        if result.returncode:
            raise RuntimeError("dyld_info failed; no private API fallback permitted")
        return result.stdout

    exported = parse_exports(inspect(["-exports", IOKIT_IMAGE]))
    export_addresses = {}
    export_evidence = []
    for image in (IOKIT_IMAGE, COREFOUNDATION_IMAGE):
        export_text = inspect(["-exports", image])
        segment_text = inspect(["-segments", image])
        addresses = parse_export_addresses(export_text, segment_text)
        export_addresses.update(addresses)
        export_evidence.append({"image": image, "image_identity": inspect(["-uuid", image]),
                                "segments": segment_text,
                                "relevant_exports": {name: hex(address) for name, address in addresses.items()
                                                     if name.startswith("_IODP") or name in ("_CFRelease", "_CFRetain", "_IOServiceClose", "_IOObjectRelease")}})
    library = ctypes.CDLL(IOKIT_IMAGE)
    symbols = []
    sdk_symbols = {symbol for symbol in sdk["symbol_name_matches"] if symbol.startswith("_IODP")}
    for symbol in sorted(sdk_symbols | exported.keys()):
        try:
            getattr(library, symbol[1:])
            runtime = "PRESENT_NOT_INVOKED"
        except AttributeError:
            runtime = "NOT_FOUND"
        symbols.append({"name": symbol, "sdk_declared": symbol in sdk_symbols,
                        "cached_export_offset_hex": exported.get(symbol), "runtime": runtime})

    images = []
    server_evidence = None
    decoder = LLVMDisassembler()
    try:
        for image in (IOKIT_IMAGE, *CALLER_IMAGES):
            identity = inspect(["-uuid", image])
            blocks = disassembly_blocks(inspect(["-disassemble", image]))
            selected = {name: text for name, text in blocks.items() if name in FOCUS} if image == IOKIT_IMAGE else {
                **read_calls(blocks), **{name: text for name, text in blocks.items()
                                       if name in CALLER_METHODS or re.search(r"read.*dpcd|dpcd.*read", name, re.I)}}
            raw = section_bytes(inspect(["-section_bytes", "__TEXT", "__text", image]))
            functions = {}
            for name, text in selected.items():
                instructions = []
                for match in re.finditer(r"^(0x[0-9a-fA-F]+)\s+", text, re.MULTILINE):
                    address = int(match[1], 16)
                    instruction = raw_instruction(raw, address)
                    if instruction is None:
                        instructions.append({"address_hex": hex(address), "bytes_hex": None,
                                             "instruction": "OUTSIDE_CAPTURED_TEXT", "direct_branch_target_hex": None})
                    else:
                        instructions.append(decoder.decode(address, instruction))
                functions[name] = {"disassembly": text, "sha256": hashlib.sha256(text.encode()).hexdigest(),
                                   "raw_byte_llvm_crosscheck": instructions,
                                   "raw_byte_crosscheck_complete": bool(instructions) and all(item["bytes_hex"] is not None for item in instructions)}
            imports = inspect(["-imports", image])
            image_data = {"path": image, "image_identity": identity, "functions": functions,
                          "relevant_imports": [line for line in imports.splitlines()
                                               if any(symbol in line for symbol in ("IODP", "IOConnectCallMethod", "CFRelease", "CFRetain"))],
                          "callsite_limit": "dyld_info external branch labels can be incorrect; only disk-chain pointers with a unique exact export match establish binding. This is static binding, not invocation."}
            if image == IOKIT_IMAGE:
                image_data["cf_lifecycle"] = resolve_cf_lifecycle(cache, functions, blocks)
                image_data["missing_focus_symbols"] = sorted(FOCUS - selected.keys())
                strings = section_bytes(inspect(["-section_bytes", "__TEXT", "__cstring", image]))
                image_data["relevant_cstrings_raw"] = raw_strings(strings)
            stubs = section_bytes(inspect(["-section_bytes", "__TEXT", "__auth_stubs", image]))
            targets = {int(item["direct_branch_target_hex"], 16) for function in functions.values()
                       for item in function["raw_byte_llvm_crosscheck"] if item["direct_branch_target_hex"]}
            image_data["referenced_auth_stubs"] = {
                hex(target): [decoder.decode(target + offset, bytes(stubs[target + offset + index] for index in range(4)))
                              for offset in range(0, 16, 4)] for target in sorted(targets)
                if all(target + index in stubs for index in range(16))}
            image_data["authenticated_call_bindings"] = resolve_call_bindings(
                cache, functions, image_data["referenced_auth_stubs"], export_addresses)
            images.append(image_data)
            print(pathlib.Path(image).name + ": " + str(len(selected)) + " selected function/caller blocks")
        if args.server:
            files = sorted(pathlib.Path("/System/Volumes/Preboot").glob(
                "*/boot/*/System/Library/Caches/com.apple.kernelcaches/kernelcache"))
            if len(files) != 1:
                raise ValueError("Boot image selection is ambiguous; provide evidence rather than guessing")
            server_evidence = collect_server_evidence(files[0], decoder, args.kernel_symbol, args.kernel_vtable,
                                                      args.kernel_image, args.kernel_string, args.kernel_address,
                                                      args.kernel_callers_of, args.kernel_lifecycle,
                                                      args.kernel_graph_root, args.kernel_graph_sink, graph_virtual_edges)
            print("Kernel UUID matched; captured selected static server methods.")
    finally:
        decoder.close()
    report = {
        "schema_version": 1, "captured_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "baseline": str(baseline.relative_to(repository)),
        "sdk_evidence_sha256": hashlib.sha256((baseline / "sdk-surface.json").read_bytes()).hexdigest(),
        "tool_source_sha256": hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),
        "cache_parser_source_sha256": hashlib.sha256(pathlib.Path(__file__).with_name("dyld_cache.py").read_bytes()).hexdigest(),
        "kernel_parser_source_sha256": hashlib.sha256(pathlib.Path(__file__).with_name("kernel_image.py").read_bytes()).hexdigest(),
        "call_graph_source_sha256": hashlib.sha256(pathlib.Path(__file__).with_name("call_graph.py").read_bytes()).hexdigest(),
        "cache_components": cache.components, "export_binding_evidence": export_evidence,
        "server_evidence": server_evidence,
        "probe_signing_evidence": signing_evidence,
        "reference_root": str(args.reference_root.resolve().relative_to(repository)) if args.reference_root else None,
        "reference_sources": references,
        "llvm_library": str(decoder.path),
        "llvm_features": decoder.features,
        "llvm_library_sha256": hashlib.sha256(decoder.path.read_bytes()).hexdigest(),
        "symbols": symbols, "images": images, "commands": commands,
        "safety": "Static image reads, public LLVM/libcompression calls and public registry/identity queries only. No private transport, updater or inspected kernel code invoked.",
        "scope": "Local arm64e client and optional UUID-matched host-kernel static evidence; not executed hardware or DCP firmware behavior. Each hash field identifies its own input scope.",
    }
    destination = output / "iodp-static.json"
    with destination.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2, sort_keys=True)
        stream.write("\n")
    with (output / "manifest.json").open("x", encoding="utf-8") as stream:
        json.dump({"schema_version": 1, "artifacts": {destination.name: hashlib.sha256(destination.read_bytes()).hexdigest()}}, stream, indent=2)
        stream.write("\n")
    print(f"Static evidence: {output.name}; {len(symbols)} IODP names; no private calls.")
    return 0


if __name__ == "__main__":
    sys.exit(main())