import ctypes
import bisect
import hashlib
import plistlib
import re
import struct
import subprocess
import uuid

from dyld_cache import adrp_add_target, direct_branch_target


def decode_function_starts(raw, base):
    if not 0 <= base < 1 << 64:
        raise ValueError("Invalid function-start base")
    addresses = []
    cursor = 0
    runtime_offset = 0
    while cursor < len(raw):
        delta = 0
        shift = 0
        while True:
            if cursor >= len(raw) or shift >= 64:
                raise ValueError("Truncated or overflowing function-start ULEB128")
            value = raw[cursor]
            cursor += 1
            delta |= (value & 0x7f) << shift
            if delta >= 1 << 64:
                raise ValueError("Function-start ULEB128 exceeds uint64")
            if not value & 0x80:
                break
            shift += 7
        if delta == 0:
            if any(raw[cursor:]):
                raise ValueError("Nonzero trailing function-start data")
            return addresses
        runtime_offset = (runtime_offset + delta) & ((1 << 64) - 1)
        address = (base + runtime_offset) & ((1 << 64) - 1)
        if address % 4 or len(addresses) >= 1000000:
            raise ValueError("Invalid or excessive function-start address")
        addresses.append(address)
    raise ValueError("Missing function-start terminator")


def literal_address_references(raw, base, targets):
    if len(raw) % 4 or base % 4:
        raise ValueError("Unaligned code range")
    result = []
    for index, (word,) in enumerate(struct.iter_unpack("<I", raw)):
        offset = index * 4
        if word & 0x9f000000 != 0x90000000 or offset + 8 > len(raw) or word & 31 == 31:
            continue
        pair = raw[offset:offset + 8]
        try:
            target = adrp_add_target(pair, base + offset, word & 31)
        except ValueError:
            continue
        if target in targets:
            result.append({"instruction_address_hex": hex(base + offset), "instruction_bytes_hex": pair.hex(),
                           "target_address_hex": hex(target)})
    return result


def direct_call_references(raw, base, targets):
    if base < 0 or base % 4 or len(raw) % 4 or base + len(raw) > 1 << 64:
        raise ValueError("Invalid or unaligned direct-call code range")
    result = []
    for index, (word,) in enumerate(struct.iter_unpack("<I", raw)):
        if word & 0x7c000000 != 0x14000000:
            continue
        offset = index * 4
        instruction = raw[offset:offset + 4]
        target = direct_branch_target(instruction, base + offset)
        if target not in targets:
            continue
        if len(result) >= 4096:
            raise ValueError("Excessive direct-call references")
        result.append({"instruction_address_hex": hex(base + offset), "instruction_bytes_hex": instruction.hex(),
                       "target_address_hex": hex(target), "branch_kind": "BL" if word & 0x80000000 else "B"})
    return result


def rpc_memory_or_wait_symbol(name):
    groups = (
        ("OSData", ("withCapacity", "initWithCapacity", "ensureCapacity", "appendBytes", "getCapacity", "getLength", "getBytesNoCopy", "4freeE")),
        ("IOCommandGate", ("commandSleep", "commandWakeup", "runAction", "attemptAction", "disable", "enable")),
        ("IOAVCommandGate", ("commandSleep", "commandWakeup", "runAction", "attemptAction", "commandGate")),
        ("IOEventSource", ("sleepGate", "wakeupGate")),
        ("IOWorkLoop", ("sleepGate", "wakeupGate", "closeGate", "openGate")),
    )
    return any(kind in name and any(method in name for method in methods) for kind, methods in groups)


def rpc_endpoint_symbol(name):
    kinds = ("20AFKEndpointInterface", "20AFKEPInterfaceKextV2", "16AFKEPInterfaceV2",
             "27AFKEPInterfaceEventSourceV2", "17AFKEPCommandLocal", "26AFKEndpointInterfaceClient",
             "16AFKEPSendOptions", "13AFKEPSendOpts", "11AFKWorkloop")
    methods = ("enqueueCommand", "abortCommand", "deliverResponse", "handleClientResponse", "dispatchResponse",
               "removeCommand", "createErrorResponses", "acquireCommand", "releaseCommand", "validateCommand",
               "4openE", "5closeE", "4stopE", "4freeE", "terminate", "Timeout", "timeout", "parseResponse",
               "create", "release", "handleResponse", "Disconnect", "getEPICForIOService", "defCommandResponseOpt",
               "setBlockPower", "setChangePower", "setUnreliable", "Synchronous", "sleep", "wake", "wait", "runAction",
               "getCmdHeaders", "sendMessage")
    owner = re.match(r"^_+Z(?:Thn[0-9]+_)?NK?(" + "|".join(kinds) + r")(?=[0-9])", name)
    return owner is not None and any(method in name for method in methods)


def user_client_lifecycle_symbol(name):
    if name in {"_iokit_task_terminate", "_iokit_task_terminate_phase1", "_iokit_task_terminate_phase2",
                "_iokit_connect_no_senders", "_is_io_service_close", "_iokit_client_died",
                "_iokit_client_retain", "_iokit_client_release", "_iokit_destroy_object_port"}:
        return True
    if "IOUserClient" in name:
        return any(method in name for method in ("clientDied", "clientClose", "noMoreSenders",
                   "4freeE", "registerOwner", "ipcEnter", "ipcExit", "destroyUserReferences"))
    if "IOMachPort" in name:
        return any(method in name for method in ("noMoreSenders", "4freeE", "releasePortForObject"))
    return False


def function_record_key(symbol, selected):
    addresses = {item["address"] for item in selected if item["name"] == symbol["name"]}
    return symbol["name"] if len(addresses) == 1 else symbol["name"] + " [" + hex(symbol["address"]) + "]"


def der_item(data, offset):
    if offset < 0 or offset + 2 > len(data):
        raise ValueError("Truncated DER item")
    tag, first = data[offset:offset + 2]
    start = offset + 2
    if first & 0x80:
        count = first & 0x7f
        if not 1 <= count <= 4 or start + count > len(data):
            raise ValueError("Unsupported or truncated DER length")
        if data[start] == 0:
            raise ValueError("Noncanonical DER length")
        size = int.from_bytes(data[start:start + count], "big")
        if size < 128:
            raise ValueError("Noncanonical long DER length")
        start += count
    else:
        size = first
    end = start + size
    if end > len(data):
        raise ValueError("DER item extends beyond input")
    return tag, start, end


def der_children(data, start, end):
    children = []
    cursor = start
    while cursor < end:
        tag, body, next_offset = der_item(data, cursor)
        if next_offset > end or len(children) >= 32:
            raise ValueError("Invalid DER sequence bounds")
        children.append((tag, body, next_offset))
        cursor = next_offset
    return children


def kernel_payload(data):
    tag, start, end = der_item(data, 0)
    if tag != 0x30 or end != len(data):
        raise ValueError("Expected a single complete IMG4/IM4P DER sequence")
    children = der_children(data, start, end)
    if not children or children[0][0] != 0x16:
        raise ValueError("Missing image container name")
    name = data[children[0][1]:children[0][2]]
    if name == b"IMG4":
        containers = [item for item in children[1:] if item[0] == 0x30]
        if len(containers) != 1:
            raise ValueError("Ambiguous IM4P container")
        children = der_children(data, containers[0][1], containers[0][2])
        name = data[children[0][1]:children[0][2]] if children else b""
    if name != b"IM4P" or len(children) < 4 or [item[0] for item in children[:4]] != [0x16, 0x16, 0x16, 0x04]:
        raise ValueError("Unsupported IM4P fields")
    image_type = data[children[1][1]:children[1][2]]
    if image_type != b"krnl":
        raise ValueError("Only a kernel collection payload may be inspected")
    payload_start, payload_end = children[3][1:]
    return data[payload_start:payload_end], {"container_type": "IM4P", "payload_type": "krnl",
        "description": data[children[2][1]:children[2][2]].decode("ascii"),
        "payload_offset": payload_start, "payload_size": payload_end - payload_start,
        "signature_validation": "NOT_PERFORMED_BY_THIS_READER"}


def decompress_kernel(payload):
    if payload.startswith(b"\xcf\xfa\xed\xfe"):
        return payload
    if payload[:4] not in (b"bvx2", b"bvx1", b"bvxn", b"bvx-"):
        raise ValueError("Unsupported or encrypted kernel payload; no fallback")
    library = ctypes.CDLL("/usr/lib/libcompression.dylib")
    library.compression_decode_buffer.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_void_p,
                                                 ctypes.c_size_t, ctypes.c_void_p, ctypes.c_int]
    library.compression_decode_buffer.restype = ctypes.c_size_t
    capacity = 256 * 1024 * 1024
    output = ctypes.create_string_buffer(capacity)
    source = ctypes.create_string_buffer(payload)
    count = library.compression_decode_buffer(output, capacity, source, len(payload), None, 0x801)
    if not 0 < count < capacity:
        raise ValueError("Kernel decompression failed or reached bounded capacity")
    data = output[:count]
    if not data.startswith(b"\xcf\xfa\xed\xfe"):
        raise ValueError("Decoded kernel payload is not a 64-bit Mach-O")
    return data


def bounded_slice(data, offset, size):
    if offset < 0 or size < 0 or offset + size > len(data):
        raise ValueError("Mach-O field extends outside input")
    return memoryview(data)[offset:offset + size]


def macho_commands(data, offset=0):
    header = bounded_slice(data, offset, 32)
    magic, cpu, subtype, filetype, count, size, flags, reserved = struct.unpack("<8I", header)
    if magic != 0xfeedfacf or cpu != 0x0100000c or count > 16384:
        raise ValueError("Unsupported Mach-O architecture or command count")
    bounded_slice(data, offset + 32, size)
    commands = []
    cursor = offset + 32
    for index in range(count):
        command, length = struct.unpack("<II", bounded_slice(data, cursor, 8))
        if length < 8 or length % 8 or cursor + length > offset + 32 + size:
            raise ValueError("Invalid Mach-O command length")
        commands.append((command, cursor, bounded_slice(data, cursor, length)))
        cursor += length
    if cursor != offset + 32 + size:
        raise ValueError("Mach-O command lengths do not match header")
    return {"cpu_type": cpu, "cpu_subtype": subtype, "filetype": filetype}, commands


def cstring(data, offset):
    if not 0 <= offset < len(data):
        raise ValueError("String offset out of bounds")
    tail = bytes(data[offset:min(len(data), offset + 4096)])
    if b"\0" not in tail:
        raise ValueError("Unterminated or excessive string")
    return tail.split(b"\0", 1)[0].decode("utf-8")


def fileset_entries(data):
    header, commands = macho_commands(data)
    if header["filetype"] != 0xc:
        raise ValueError("Kernel collection is not a Mach-O fileset")
    result = {}
    for command, offset, raw in commands:
        if command != 0x80000035:
            continue
        if len(raw) < 32:
            raise ValueError("Truncated fileset entry")
        address, file_offset, name_offset, reserved = struct.unpack_from("<QQII", raw, 8)
        if name_offset < 32:
            raise ValueError("Invalid fileset name offset")
        name = cstring(raw, name_offset)
        if name in result:
            raise ValueError("Duplicate fileset image")
        bounded_slice(data, file_offset, 32)
        result[name] = {"address": address, "file_offset": file_offset}
    return result


def macho_symbols(data, offset):
    header, commands = macho_commands(data, offset)
    tables = [raw for command, command_offset, raw in commands if command == 0x2]
    if len(tables) != 1 or len(tables[0]) != 24:
        raise ValueError("Missing or ambiguous symbol table")
    symbol_offset, count, string_offset, string_size = struct.unpack_from("<4I", tables[0], 8)
    if count > 2000000:
        raise ValueError("Excessive symbol count")
    table = bounded_slice(data, symbol_offset, count * 16)
    strings = bounded_slice(data, string_offset, string_size)
    result = []
    for index in range(count):
        name_offset, symbol_type, section, descriptor, address = struct.unpack_from("<IBBHQ", table, index * 16)
        if name_offset:
            result.append({"name": cstring(strings, name_offset), "address": address,
                           "type": symbol_type, "section": section})
    return result


def macho_uuid(data, offset=0):
    _, commands = macho_commands(data, offset)
    records = [raw for command, command_offset, raw in commands if command == 0x1b]
    if len(records) != 1 or len(records[0]) != 24:
        raise ValueError("Missing or ambiguous Mach-O UUID")
    return str(uuid.UUID(bytes=bytes(records[0][8:24]))).upper()


def macho_function_starts(data, offset):
    _, commands = macho_commands(data, offset)
    starts = [raw for command, command_offset, raw in commands if command == 0x26]
    bases = [struct.unpack_from("<Q", raw, 24)[0] for command, command_offset, raw in commands
             if command == 0x19 and bytes(raw[8:24]).split(b"\0", 1)[0] == b"__TEXT"]
    if len(starts) != 1 or len(starts[0]) != 16 or len(bases) != 1:
        raise ValueError("Missing or ambiguous function starts or text base")
    file_offset, size = struct.unpack_from("<II", starts[0], 8)
    raw = bytes(bounded_slice(data, file_offset, size))
    addresses = decode_function_starts(raw, bases[0])
    executable = [section for section in macho_sections(data, offset) if section["flags"] & 0x80000000]
    for address in addresses:
        matches = [section for section in executable if section["address"] <= address < section["address"] + section["size"]]
        if len(matches) != 1:
            raise ValueError("Function start has no unique executable section")
    return sorted(set(addresses)), {"file_offset": file_offset, "size": size, "text_base_hex": hex(bases[0]),
                                   "count": len(addresses), "uint64_backward_deltas": sum(
                                       following < previous for previous, following in zip(addresses, addresses[1:])),
                                   "bytes_sha256": hashlib.sha256(raw).hexdigest()}


def macho_sections(data, offset):
    _, commands = macho_commands(data, offset)
    sections = []
    for command, command_offset, raw in commands:
        if command != 0x19:
            continue
        if len(raw) < 72:
            raise ValueError("Truncated segment command")
        segment = bytes(raw[8:24]).split(b"\0", 1)[0].decode("ascii")
        count = struct.unpack_from("<I", raw, 64)[0]
        if 72 + count * 80 != len(raw):
            raise ValueError("Section count does not match segment command")
        for index in range(count):
            section = raw[72 + index * 80:72 + (index + 1) * 80]
            name = bytes(section[:16]).split(b"\0", 1)[0].decode("ascii")
            address, size, file_offset = struct.unpack_from("<QQI", section, 32)
            flags = struct.unpack_from("<I", section, 64)[0]
            if flags & 0xff not in (1, 0xc, 0x12):
                bounded_slice(data, file_offset, size)
            sections.append({"segment": segment, "section": name, "address": address,
                             "size": size, "file_offset": file_offset, "flags": flags})
    return sections


def decode_kernel_pointer8(word, base):
    if not 0 <= word < 1 << 64 or not 0 <= base < 1 << 64:
        raise ValueError("Invalid kernel pointer word or base")
    if (word >> 30) & 3:
        raise ValueError("Only pointers within the boot collection are supported")
    target = base + (word & ((1 << 30) - 1))
    if target >= 1 << 64:
        raise ValueError("Kernel pointer target overflows")
    return {"target_address_hex": hex(target), "authenticated": bool(word >> 63),
            "diversity": (word >> 32) & 0xffff, "address_diversity": bool((word >> 48) & 1),
            "key": ("IA", "IB", "DA", "DB")[(word >> 49) & 3],
            "next_bytes": ((word >> 51) & 0xfff) * 4, "cache_level": 0}


def verify_kernel_chain8(page, start, requested, base):
    if start == 0xffff or start & 0x8000 or start % 4 or requested % 4:
        raise ValueError("Unsupported or absent kernel page chain")
    cursor = start
    hops = 0
    while cursor <= requested:
        word = struct.unpack("<Q", bounded_slice(page, cursor, 8))[0]
        decoded = decode_kernel_pointer8(word, base)
        if cursor == requested:
            return {**decoded, "chain_hops": hops, "raw_word_hex": hex(word)}
        if not decoded["next_bytes"]:
            break
        cursor += decoded["next_bytes"]
        hops += 1
    raise ValueError("Kernel pointer slot is not a member of its declared chain")


class KernelCachePointers:
    def __init__(self, data):
        self.data = data
        _, commands = macho_commands(data)
        self.segments = []
        for command, offset, raw in commands:
            if command == 0x19:
                if len(raw) < 72:
                    raise ValueError("Truncated kernel segment")
                address, size, file_offset, file_size = struct.unpack_from("<4Q", raw, 24)
                bounded_slice(data, file_offset, file_size)
                self.segments.append({"address": address, "size": size, "file_offset": file_offset,
                                      "file_size": file_size})
        bases = [segment["address"] for segment in self.segments
                 if segment["file_offset"] == 0 and segment["file_size"] >= 32]
        if len(bases) != 1:
            raise ValueError("Missing or ambiguous boot collection base")
        self.base = bases[0]
        fixups = [raw for command, offset, raw in commands if command == 0x80000034]
        if len(fixups) != 1 or len(fixups[0]) != 16:
            raise ValueError("Missing or ambiguous kernel chained fixups")
        offset, size = struct.unpack_from("<II", fixups[0], 8)
        self.blob = bounded_slice(data, offset, size)
        version, starts, imports, symbols, count, import_format, symbol_format = struct.unpack(
            "<7I", bounded_slice(self.blob, 0, 28))
        if version != 0 or count != 0 or symbol_format != 0:
            raise ValueError("Unsupported kernel fixup header")
        segment_count = struct.unpack("<I", bounded_slice(self.blob, starts, 4))[0]
        if segment_count != len(self.segments):
            raise ValueError("Kernel fixup segment count mismatch")
        self.starts = {}
        for index in range(segment_count):
            relative = struct.unpack("<I", bounded_slice(self.blob, starts + 4 + index * 4, 4))[0]
            if not relative:
                continue
            position = starts + relative
            length, page_size, pointer_format, segment_offset, maximum, pages = struct.unpack(
                "<IHHQIH", bounded_slice(self.blob, position, 22))
            if pointer_format != 8 or page_size not in (4096, 16384) or length < 22 + pages * 2:
                raise ValueError("Unsupported kernel chained-pointer format")
            bounded_slice(self.blob, position, length)
            if self.base + segment_offset != self.segments[index]["address"]:
                raise ValueError("Kernel chain segment address mismatch")
            self.starts[index] = {"page_size": page_size, "page_count": pages,
                                  "page_table": position + 22}

    def read(self, address, size):
        matches = [segment for segment in self.segments if segment["address"] <= address
                   and address + size <= segment["address"] + segment["file_size"]]
        if size < 0 or len(matches) != 1:
            raise ValueError("Missing or ambiguous kernel virtual-address mapping")
        segment = matches[0]
        offset = segment["file_offset"] + address - segment["address"]
        return bytes(bounded_slice(self.data, offset, size))

    def pointer(self, address):
        matches = [(index, segment) for index, segment in enumerate(self.segments)
                   if segment["address"] <= address and address + 8 <= segment["address"] + segment["file_size"]]
        if len(matches) != 1 or matches[0][0] not in self.starts:
            raise ValueError("Pointer has no unique kernel fixup segment")
        index, segment = matches[0]
        info = self.starts[index]
        page_index, page_offset = divmod(address - segment["address"], info["page_size"])
        if page_index >= info["page_count"]:
            raise ValueError("Kernel fixup page index exceeds table")
        start = struct.unpack("<H", bounded_slice(self.blob, info["page_table"] + page_index * 2, 2))[0]
        file_offset = segment["file_offset"] + page_index * info["page_size"]
        page_length = min(info["page_size"], segment["file_size"] - page_index * info["page_size"])
        page = bounded_slice(self.data, file_offset, page_length)
        decoded = verify_kernel_chain8(page, start, page_offset, self.base)
        self.read(int(decoded["target_address_hex"], 16), 1)
        return {**decoded, "slot_address_hex": hex(address), "file_offset": file_offset + page_offset,
                "pointer_format": 8, "collection_base_hex": hex(self.base), "page_index": page_index,
                "page_offset": page_offset, "page_start": start,
                "page_sha256": hashlib.sha256(page).hexdigest(),
                "raw_bytes_hex": bytes(page[page_offset:page_offset + 8]).hex()}


def collect_server_evidence(file, decoder, extra_symbols=(), extra_vtables=(), extra_images=(), extra_strings=(), extra_addresses=(), callers_of=(), lifecycle=False):
    if file.stat().st_size > 64 * 1024 * 1024:
        raise ValueError("Kernel container exceeds static inspection limit")
    original = file.read_bytes()
    payload, container = kernel_payload(original)
    data = decompress_kernel(payload)
    entries = fileset_entries(data)
    pointers = KernelCachePointers(data)
    kernel = entries.get("com.apple.kernel")
    if kernel is None:
        raise ValueError("Missing kernel image identity")
    active_uuid = subprocess.check_output(["/usr/sbin/sysctl", "-n", "kern.uuid"], text=True).strip().upper()
    kernel_uuid = macho_uuid(data, kernel["file_offset"])
    if active_uuid != kernel_uuid:
        raise ValueError("Static kernel image UUID does not match the running kernel")
    families = tuple(dict.fromkeys(("com.apple.kernel", "com.apple.iokit.IOAVFamily", "com.apple.iokit.IODisplayPortFamily",
                                   "com.apple.driver.DCPAVFamilyProxy", "com.apple.driver.DCPDPFamilyProxy",
                                   "com.apple.driver.AppleFirmwareKit", *extra_images)))
    if any(family not in entries for family in families):
        raise ValueError("Requested kernel image is absent from the matched fileset")
    inventories = {family: macho_symbols(data, entries[family]["file_offset"]) for family in families}
    names_by_address = {}
    for symbols in inventories.values():
        for symbol in symbols:
            if symbol["address"]:
                names_by_address.setdefault(symbol["address"], set()).add(symbol["name"])
    defined_names = {symbol["name"] for symbols in inventories.values() for symbol in symbols
                     if symbol["address"] and symbol["section"]}
    missing = (set(extra_symbols) | set(extra_vtables) | set(callers_of)) - defined_names
    if missing:
        raise ValueError("Requested kernel definitions not found: " + ", ".join(sorted(missing)))
    call_targets = {symbol["address"] for symbols in inventories.values() for symbol in symbols
                    if symbol["address"] and symbol["section"] and symbol["name"] in callers_of}
    images = []
    requested_addresses = set(extra_addresses)
    if any(address < 0 or address >= 1 << 64 or address % 4 for address in requested_addresses):
        raise ValueError("Invalid explicit kernel function address")
    matched_addresses = set()
    relevant_classes = ("IODPDevice", "DCPDPDeviceProxy", "IOAVUserClient", "DCPAVProxy",
                        "DCPAVDeviceProxy", "IOAVDevice")
    methods = ("readDPCD", "ReadDPCD", "_readBytes", "_writeBytes", "newUserClient", "externalMethod",
               "clientClose", "initWithTask", "5startE", "4stopE", "4freeE", "MethodCount", "MethodFor",
               "sMethods", "MethodsE", "getProvider", "__sendMessage", "performCommandGated", "handleResponse",
               "C2EPK11OSMetaClass")
    for family in families:
        offset = entries[family]["file_offset"]
        sections = macho_sections(data, offset)
        starts, starts_evidence = macho_function_starts(data, offset)
        symbols = inventories[family]
        selected = [symbol for symbol in symbols if symbol["address"] and symbol["section"]
                and ((any(kind in symbol["name"] for kind in relevant_classes)
                  and any(method in symbol["name"] for method in methods))
                 or "IOService13newUserClient" in symbol["name"]
                         or "IOUserClient12initWithTask" in symbol["name"]
                 or "IOUserClient14externalMethod" in symbol["name"]
                         or rpc_memory_or_wait_symbol(symbol["name"])
                         or rpc_endpoint_symbol(symbol["name"])
                         or (lifecycle and user_client_lifecycle_symbol(symbol["name"]))
                         or symbol["name"] in extra_symbols)]
        for section_index, section in enumerate(sections, 1):
            if section["section"] != "__text":
                continue
            for address in sorted(requested_addresses):
                if section["address"] <= address < section["address"] + section["size"]:
                    if address in matched_addresses or address not in starts:
                        raise ValueError("Explicit address is ambiguous or not a declared function start")
                    matched_addresses.add(address)
                    if not any(symbol["address"] == address for symbol in selected):
                        selected.append({"name": "address@" + hex(address), "address": address,
                                         "section": section_index, "type": 0xe})
        literals = {}
        for section in sections:
            if section["section"] != "__cstring":
                continue
            raw = bytes(bounded_slice(data, section["file_offset"], section["size"]))
            position = 0
            for value in raw.split(b"\0"):
                text = value.decode("utf-8", errors="replace")
                if text in extra_strings:
                    literals[section["address"] + position] = {"value": text, "bytes_hex": value.hex()}
                position += len(value) + 1
        references = []
        for section_index, section in enumerate(sections, 1):
            if section["section"] != "__text" or not literals:
                continue
            raw = bytes(bounded_slice(data, section["file_offset"], section["size"]))
            references.extend(literal_address_references(raw, section["address"], literals))
            for reference in references:
                address = int(reference["instruction_address_hex"], 16)
                if not section["address"] <= address < section["address"] + section["size"]:
                    continue
                index = bisect.bisect_right(starts, address) - 1
                if index < 0:
                    raise ValueError("Literal reference is outside declared functions")
                start = starts[index]
                reference["containing_function_hex"] = hex(start)
                if not any(symbol["address"] == start for symbol in selected):
                    selected.append({"name": "literal-reference@" + hex(start), "address": start,
                                     "section": section_index, "type": 0xe})
        call_references = []
        for section_index, section in enumerate(sections, 1):
            if section["section"] != "__text" or not call_targets:
                continue
            raw = bytes(bounded_slice(data, section["file_offset"], section["size"]))
            for reference in direct_call_references(raw, section["address"], call_targets):
                address = int(reference["instruction_address_hex"], 16)
                index = bisect.bisect_right(starts, address) - 1
                if index < 0 or starts[index] < section["address"]:
                    raise ValueError("Direct caller is outside a declared function in its section")
                start = starts[index]
                reference["containing_function_hex"] = hex(start)
                reference["exact_target_symbols"] = sorted(names_by_address[int(reference["target_address_hex"], 16)])
                reference["exact_caller_symbols"] = sorted(names_by_address.get(start, ()))
                call_references.append(reference)
                if not any(symbol["address"] == start for symbol in selected):
                    selected.append({"name": "direct-caller@" + hex(start), "address": start,
                                     "section": section_index, "type": 0xe})
        functions = {}
        for symbol in selected:
            if symbol["section"] > len(sections):
                raise ValueError("Symbol references nonexistent section")
            section = sections[symbol["section"] - 1]
            if section["section"] != "__text":
                continue
            start = symbol["address"]
            index = bisect.bisect_left(starts, start)
            if index >= len(starts) or starts[index] != start:
                raise ValueError("Selected symbol is not a declared function start: " + symbol["name"])
            end = min(starts[index + 1] if index + 1 < len(starts) else section["address"] + section["size"],
                      section["address"] + section["size"])
            if start < section["address"] or end > section["address"] + section["size"] or not 0 < end - start <= 32768 or (end - start) % 4:
                raise ValueError("Function range is invalid or excessive")
            file_offset = section["file_offset"] + start - section["address"]
            raw = bytes(bounded_slice(data, file_offset, end - start))
            instructions = []
            for index in range(0, len(raw), 4):
                instruction = decoder.decode(start + index, raw[index:index + 4])
                target = instruction["direct_branch_target_hex"]
                instruction["exact_symbol_matches"] = sorted(names_by_address.get(int(target, 16), ())) if target else []
                instructions.append(instruction)
            functions[function_record_key(symbol, selected)] = {"address_hex": hex(start), "file_offset": file_offset,
                                          "size": len(raw), "bytes_sha256": hashlib.sha256(raw).hexdigest(),
                                          "instructions": instructions,
                                          "undecoded_instruction_addresses": [item["address_hex"] for item in instructions
                                                                              if item["instruction"] == "UNDECODED"]}
        images.append({"bundle_id": family, "uuid": macho_uuid(data, offset), "fileset_header_offset": offset,
                       "sections": sections, "relevant_symbols": selected, "functions": functions,
                       "function_starts_evidence": starts_evidence,
                       "selected_literals": {hex(address): item for address, item in literals.items()},
                       "literal_references": references, "direct_call_references": call_references})
    if matched_addresses != requested_addresses:
        raise ValueError("Explicit kernel address not found in the requested images")
    tables = [symbol for symbols in inventories.values() for symbol in symbols
              if "IODPDeviceUserClient5start" in symbol["name"] and symbol["name"].endswith("E7methods")]
    if len(tables) != 1:
        raise ValueError("Missing or ambiguous DP device dispatch table")
    dispatch = []
    for selector in range(6):
        address = tables[0]["address"] + selector * 24
        raw = pointers.read(address, 24)
        pointer = pointers.pointer(address)
        matches = sorted(names_by_address.get(int(pointer["target_address_hex"], 16), ()))
        dispatch.append({"selector": selector, "address_hex": hex(address), "raw_bytes_hex": raw.hex(),
                         "function_pointer": pointer, "exact_symbol_matches": matches,
                         "checks": dict(zip(("scalar_input_count", "structure_input_size", "scalar_output_count",
                                             "structure_output_size"), struct.unpack_from("<4I", raw, 8)))})
    vtables = []
    symbols = [symbol for inventory in inventories.values() for symbol in inventory]
    virtual_methods = ("newUserClient", "initWithTask", "clientClose", "externalMethod", "readDPCD",
                       "writeDPCD", "9terminateE", "4stopE", "4freeE", "5startE", "getWorkLoop")
    for symbol in symbols:
        if not symbol["address"] or not symbol["section"]:
            continue
        if symbol["name"] not in ("__ZTV16DCPDPDeviceProxy", "__ZTV26DCPDPDeviceProxyUserClient",
                       "__ZTV6OSData", "__ZTV13IOCommandGate", "__ZTV15IOAVCommandGate",
                       "__ZTV20AFKEndpointInterface", "__ZTV20AFKEPInterfaceKextV2",
                       "__ZTV16AFKEPInterfaceV2", *extra_vtables):
            continue
        start = symbol["address"]
        end = min(item["address"] for item in symbols
                  if item["address"] > start)
        if not 16 < end - start <= 8192:
            raise ValueError("Invalid or excessive DP proxy vtable range")
        raw = pointers.read(start, end - start)
        bindings = []
        unbound = []
        for address in range(start + 16, end, 8):
            try:
                pointer = pointers.pointer(address)
            except ValueError:
                unbound.append(hex(address))
                continue
            matches = sorted(names_by_address.get(int(pointer["target_address_hex"], 16), ()))
            selected_binding = any(method in name for method in virtual_methods for name in matches)
            selected_binding = selected_binding or any(rpc_memory_or_wait_symbol(name) for name in matches)
            selected_binding = selected_binding or any(rpc_endpoint_symbol(name) for name in matches)
            selected_binding = selected_binding or symbol["name"] in extra_vtables
            if selected_binding:
                bindings.append({"offset_from_primary_address_point": address - start - 16,
                                 "pointer": pointer, "exact_symbol_matches": matches})
        vtables.append({"symbol": symbol["name"], "address_hex": hex(start), "raw_bytes_hex": raw.hex(),
                        "bindings": bindings, "nonpointer_or_unresolved_slots": unbound})
    command = ["/usr/sbin/ioreg", "-a", "-r", "-c", "DCPDPDeviceProxy", "-d", "1"]
    observed = plistlib.loads(subprocess.check_output(command))
    routing = select_external_client_routing(observed)
    return {"container": container, "container_sha256": hashlib.sha256(original).hexdigest(),
            "decompressed_sha256": hashlib.sha256(data).hexdigest(), "decompressed_size": len(data),
            "file_selection": "unique */boot/*/System/Library/Caches/com.apple.kernelcaches/kernelcache in Preboot",
            "active_kernel_uuid": active_uuid, "image_kernel_uuid": kernel_uuid,
            "kernel_uuid_matches": True, "images": images, "dp_device_dispatch": dispatch,
            "proxy_virtual_bindings": vtables,
            "requested_symbols": sorted(set(extra_symbols)), "requested_vtables": sorted(set(extra_vtables)),
            "requested_images": sorted(set(extra_images)),
            "requested_strings": sorted(set(extra_strings)),
            "requested_addresses_hex": [hex(address) for address in sorted(requested_addresses)],
            "requested_callers_of": sorted(set(callers_of)),
            "user_client_lifecycle_selection": lifecycle,
            "direct_caller_scope": "Direct B/BL references in selected images only; absent references do not rule out indirect callbacks.",
            "observed_external_client_routing": {"command": command, "entries": routing},
            "scope": "Read-only decompression and static instruction analysis; no inspected kernel code is executed or loaded."}


def select_external_client_routing(nodes):
    if not isinstance(nodes, list):
        raise ValueError("Expected a structured registry root list")
    allowed = {"IORegistryEntryID", "Location", "Unit", "IOUserClientClass",
               "IODPDeviceUserInterfaceSupported", "IOAVDeviceUserInterfaceSupported"}
    return [{key: value for key, value in node.items() if key in allowed
             and isinstance(value, (str, int, bool))}
            for node in nodes if isinstance(node, dict) and node.get("Location") == "External"]