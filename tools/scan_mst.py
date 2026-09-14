import argparse
import bisect
import datetime
import hashlib
import json
import pathlib
import re
import struct
import subprocess
import uuid

from dyld_cache import DyldCache, direct_branch_target
import kernel_image


def load_oracle(file):
    raw = pathlib.Path(file).read_bytes()
    if len(raw) > 131072:
        raise ValueError("MST oracle exceeds 128 KiB")
    oracle = json.loads(raw)
    if oracle.get("schema_version") != 1 or not re.fullmatch(r"[0-9a-f]{40}", oracle.get("linux_revision", "")):
        raise ValueError("Unsupported MST oracle identity")
    for group in oracle["constant_groups"]:
        values = group["values"]
        if any(type(value) is not int or not 0 <= value < 1 << 32 for value in values):
            raise ValueError("Invalid MST signature constant")
        if type(group["minimum_distinct"]) is not int or not 1 < group["minimum_distinct"] <= len(set(values)):
            raise ValueError("Invalid MST co-occurrence threshold")
    for pattern in oracle["literal_patterns"]:
        re.compile(pattern["pattern"])
    return oracle, hashlib.sha256(raw).hexdigest()


def logical_immediate(word):
    width = 64 if word & (1 << 31) else 32
    nbit, rotation, imms = (word >> 22) & 1, (word >> 16) & 63, (word >> 10) & 63
    length = ((nbit << 6) | ((~imms) & 63)).bit_length() - 1
    if length < 1 or (width == 32 and nbit):
        return None
    levels = (1 << length) - 1
    if imms & levels == levels:
        return None
    element_width = 1 << length
    rotation &= levels
    ones = (1 << ((imms & levels) + 1)) - 1
    element_mask = (1 << element_width) - 1
    element = ((ones >> rotation) | (ones << (element_width - rotation))) & element_mask
    return sum(element << offset for offset in range(0, width, element_width))


def immediate_events(raw, base):
    if base < 0 or base % 4 or len(raw) % 4 or len(raw) > 65536 or base + len(raw) > 1 << 64:
        raise ValueError("Invalid bounded A64 function range")
    previous = None
    events = []
    for offset, (word,) in enumerate(struct.iter_unpack("<I", raw)):
        value = None
        kind = None
        register = word & 31
        width = 64 if word & (1 << 31) else 32
        if word & 0x1f800000 == 0x12800000:
            operation, shift = (word >> 29) & 3, ((word >> 21) & 3) * 16
            immediate = (word >> 5) & 0xffff
            if register != 31 and shift < width:
                if operation == 2:
                    value = immediate << shift
                elif operation == 0:
                    value = (~(immediate << shift)) & ((1 << width) - 1)
                elif operation == 3 and previous and previous[:2] == (register, width):
                    value = (previous[2] & ~(0xffff << shift)) | (immediate << shift)
                kind = "MOVE_WIDE_CONSTANT" if value is not None else None
        elif word & 0x1f800000 == 0x12000000:
            value = logical_immediate(word)
            kind = "LOGICAL_IMMEDIATE_MASK" if value is not None else None
        elif word & 0x1f000000 == 0x11000000 and word & (1 << 29) and register == 31:
            value = ((word >> 10) & 0xfff) << (12 if word & (1 << 22) else 0)
            kind = "COMPARE_IMMEDIATE"
        previous = (register, width, value) if kind == "MOVE_WIDE_CONSTANT" else None
        if value is not None:
            events.append({"address_hex": hex(base + offset * 4), "bytes_hex": word.to_bytes(4, "little").hex(),
                           "value": value, "value_hex": hex(value), "kind": kind})
    return events


def constant_groups(events, oracle):
    values = {event["value"] for event in events}
    return [{"id": group["id"], "values_hex": [hex(value) for value in group["values"] if value in values],
             "assessment": group["assessment"]} for group in oracle["constant_groups"]
            if len(values.intersection(group["values"])) >= group["minimum_distinct"]]


def literal_matches(text, oracle):
    return [pattern["id"] for pattern in oracle["literal_patterns"] if re.search(pattern["pattern"], text)]


def string_hits(raw, base, oracle):
    if len(raw) > 64 * 1024 * 1024 or base < 0 or base + len(raw) > 1 << 64:
        raise ValueError("Invalid string section range")
    result = []
    position = 0
    for value in raw.split(b"\0"):
        if 3 <= len(value) <= 2048:
            try:
                text = value.decode("utf-8")
            except UnicodeDecodeError:
                text = ""
            matches = literal_matches(text, oracle)
            if matches:
                result.append({"address_hex": hex(base + position), "value": text,
                               "sha256": hashlib.sha256(value).hexdigest(), "signatures": matches,
                               "assessment": "UNQUALIFIED_LITERAL_CANDIDATE"})
        position += len(value) + 1
    return result


def constant_table_hits(raw, base, oracle):
    if len(raw) > 64 * 1024 * 1024 or base < 0 or base + len(raw) > 1 << 64:
        raise ValueError("Invalid constant section range")
    groups = [group for group in oracle["constant_groups"]
              if group["id"] in ("mst_sideband_windows", "mst_payload_registers")]
    values = {value for group in groups for value in group["values"]}
    matches = [(offset, struct.unpack_from("<I", raw, offset)[0]) for offset in range(0, len(raw) - 3, 4)
               if struct.unpack_from("<I", raw, offset)[0] in values]
    result = []
    used = set()
    for index, (offset, _) in enumerate(matches):
        local = [(position, value) for position, value in matches[index:index + 16] if position < offset + 64]
        present = {value for position, value in local}
        qualified = [group for group in groups if len(present.intersection(group["values"])) >= group["minimum_distinct"]]
        if not qualified or offset in used:
            continue
        size = min(64, len(raw) - offset)
        result.append({"address_hex": hex(base + offset), "size": size,
                       "bytes_sha256": hashlib.sha256(raw[offset:offset + size]).hexdigest(),
                       "matches": [{"address_hex": hex(base + position), "value_hex": hex(value)} for position, value in local],
                       "signatures": [group["id"] for group in qualified], "function_hex": None,
                       "assessment": "UNQUALIFIED_DATA_TABLE_NOT_PROVEN_DP_ADDRESSES"})
        used.update(position for position, value in local)
    return result


def function_bounds(address, starts, section_start, section_size):
    if not starts or starts != sorted(set(starts)) or section_size <= 0:
        raise ValueError("Invalid declared function starts")
    position = bisect.bisect_right(starts, address) - 1
    if position < 0:
        return None
    start = starts[position]
    end = min(starts[position + 1] if position + 1 < len(starts) else section_start + section_size,
              section_start + section_size)
    if not section_start <= start <= address < end:
        return None
    return start, end


def function_receipt(raw, base, names, oracle):
    events = immediate_events(raw, base)
    groups = constant_groups(events, oracle)
    signatures = sorted({match for name in names for match in literal_matches(name, oracle)})
    registers = {entry["address"]: entry for entry in oracle["registers"]}
    address_hits = [{**event, "register_name": registers[event["value"]]["name"],
                     "category": registers[event["value"]]["category"],
                     "assessment": "VALUE_MATCH_NOT_PROVEN_DPCD_ADDRESS"}
                    for event in events if event["value"] in registers]
    interesting = {value for group in oracle["constant_groups"] for value in group["values"]}
    interesting.update(entry["address"] for entry in oracle["registers"])
    calls = []
    for offset in range(0, len(raw), 4):
        target = direct_branch_target(raw[offset:offset + 4], base + offset)
        if target is not None and not base <= target < base + len(raw):
            calls.append({"callsite_hex": hex(base + offset), "target_hex": hex(target),
                          "kind": "CALL" if raw[offset + 3] & 0x80 else "TAIL_BRANCH"})
    return {"address_hex": hex(base), "size": len(raw), "bytes_sha256": hashlib.sha256(raw).hexdigest(),
            "symbols": names, "symbol_signatures": signatures, "constant_groups": groups,
            "constant_events": [event for event in events if event["value"] in interesting],
            "dpcd_value_candidates": address_hits, "direct_calls": calls,
            "assessment": "UNQUALIFIED_STATIC_CANDIDATE_NOT_IMPLEMENTATION_PROOF"}


def cache_image_inventory(cache):
    header = cache.read_disk(cache.main_file, 0, 152)
    offset, count = struct.unpack_from("<QQ", header, 136)
    if not 0 < count <= 32768:
        raise ValueError("Invalid cache image-text table count")
    table = cache.read_disk(cache.main_file, offset, count * 32)
    images = []
    seen = set()
    for position in range(count):
        identity, address, size, path_offset = struct.unpack_from("<16sQII", table, position * 32)
        path_bytes = cache.read_disk(cache.main_file, path_offset, min(4096, cache.main_file.stat().st_size - path_offset))
        if b"\0" not in path_bytes or size == 0:
            raise ValueError("Invalid cache image text/path record")
        path = path_bytes.split(b"\0", 1)[0].decode("utf-8")
        parsed_path = pathlib.PurePosixPath(path)
        if not parsed_path.is_absolute() or ".." in parsed_path.parts or any(ord(character) < 32 for character in path) or path in seen:
            raise ValueError("Unexpected or duplicate cached image path")
        seen.add(path)
        images.append({"image": path, "address": address, "uuid": str(uuid.UUID(bytes=identity)).upper(),
                       "text_segment_size": size})
    return images, hashlib.sha256(table).hexdigest()


def cache_range(cache, address, size):
    if not 0 <= size <= 64 * 1024 * 1024:
        raise ValueError("Excessive cached image section")
    return b"".join(cache.read(address + offset, min(1024 * 1024, size - offset))
                    for offset in range(0, size, 1024 * 1024))


def cached_symbols(table, string_size, read_string):
    if len(table) % 16 or len(table) > 16000000 or not 0 < string_size <= 1 << 32:
        raise ValueError("Invalid cached symbol/string table bounds")
    symbols = []
    for name_offset, symbol_type, section, _, address in struct.iter_unpack("<IBBHQ", table):
        if not name_offset or symbol_type & 0xe != 0xe:
            continue
        if name_offset >= string_size:
            raise ValueError("Cached symbol name outside string pool")
        raw = read_string(name_offset, min(4096, string_size - name_offset))
        symbols.append({"name": kernel_image.cstring(raw, 0), "address": address, "section": section})
    return symbols


def cached_image(cache, entry):
    header = cache.read(entry["address"], 32)
    command_size = struct.unpack_from("<I", header, 20)[0]
    if command_size > 1024 * 1024 - 32:
        raise ValueError("Excessive cached Mach-O commands")
    data = cache.read(entry["address"], 32 + command_size)
    _, commands = kernel_image.macho_commands(data)
    identity = kernel_image.macho_uuid(data)
    if identity != entry["uuid"]:
        raise ValueError("Cached image UUID differs from image table")
    segments = []
    sections = []
    for command, _, record in commands:
        if command != 0x19:
            continue
        if len(record) < 72:
            raise ValueError("Truncated cached segment")
        name = bytes(record[8:24]).split(b"\0", 1)[0].decode("ascii")
        address, size, file_offset, file_size = struct.unpack_from("<QQQQ", record, 24)
        count = struct.unpack_from("<I", record, 64)[0]
        if 72 + count * 80 != len(record):
            raise ValueError("Invalid cached section count")
        segments.append({"name": name, "address": address, "size": size, "file_offset": file_offset, "file_size": file_size})
        for index in range(count):
            section = record[72 + index * 80:152 + index * 80]
            section_name = bytes(section[:16]).split(b"\0", 1)[0].decode("ascii")
            section_address, section_size = struct.unpack_from("<QQ", section, 32)
            flags = struct.unpack_from("<I", section, 64)[0]
            if section_address < address or section_address + section_size > address + size:
                raise ValueError("Cached section outside segment")
            sections.append({"segment": name, "section": section_name, "address": section_address,
                             "size": section_size, "flags": flags})

    def file_bytes(offset, size):
        matches = [segment for segment in segments if segment["file_offset"] <= offset and
                   offset + size <= segment["file_offset"] + segment["file_size"]]
        if len(matches) != 1:
            raise ValueError("Cached file offset lacks unique segment mapping")
        segment = matches[0]
        return cache_range(cache, segment["address"] + offset - segment["file_offset"], size)

    start_records = [record for command, _, record in commands if command == 0x26]
    text_bases = [segment["address"] for segment in segments if segment["name"] == "__TEXT"]
    if len(start_records) != 1 or len(text_bases) != 1:
        raise ValueError("Cached image lacks unique function-start metadata")
    offset, size = struct.unpack_from("<II", start_records[0], 8)
    start_bytes = file_bytes(offset, size)
    starts = sorted(set(kernel_image.decode_function_starts(start_bytes, text_bases[0])))
    symbols = []
    symbol_records = [record for command, _, record in commands if command == 0x2]
    if len(symbol_records) == 1:
        symbol_offset, count, string_offset, string_size = struct.unpack_from("<4I", symbol_records[0], 8)
        if count > 1000000:
            raise ValueError("Excessive cached symbol table")
        if count:
            table = file_bytes(symbol_offset, count * 16)
            symbols = cached_symbols(table, string_size, lambda offset, size: file_bytes(string_offset + offset, size))
    selected = [section for section in sections if section["section"] in ("__text", "__cstring", "__objc_methname", "__objc_classname", "__os_log", "__const")]
    return {"image": entry["image"], "uuid": identity, "kind": "dyld_shared_cache", "symbols": symbols,
            "starts": starts, "function_starts_sha256": hashlib.sha256(start_bytes).hexdigest(),
            "sections": [{**section, "raw": cache_range(cache, section["address"], section["size"])} for section in selected],
            "header_sha256": hashlib.sha256(data).hexdigest()}


def scan_image(image, oracle):
    sections = image["sections"]
    text_sections = [section for section in sections if section["section"] == "__text"]
    if not text_sections:
        raise ValueError("No text section in selected image")
    declared_starts = image["starts"]
    if not declared_starts or any(type(start) is not int or start < 0 or start % 4 for start in declared_starts):
        raise ValueError("Invalid or empty declared function starts")
    if declared_starts != sorted(set(declared_starts)):
        raise ValueError("Function starts must be unique and sorted")
    for section in sections:
        if section["size"] != len(section["raw"]) or section["address"] < 0:
            raise ValueError("Section bytes do not match their declared range")
    for section in text_sections:
        if section["address"] % 4 or section["size"] % 4:
            raise ValueError("Unaligned A64 text section")
    names = {}
    symbol_hits = []
    for symbol in image["symbols"]:
        names.setdefault(symbol["address"], []).append(symbol["name"])
        matches = literal_matches(symbol["name"], oracle)
        if matches:
            symbol_hits.append({"address_hex": hex(symbol["address"]), "name": symbol["name"], "signatures": matches,
                                "assessment": "UNQUALIFIED_SYMBOL_CANDIDATE"})
    literals = []
    data_tables = []
    section_evidence = []
    for section in sections:
        raw = section["raw"]
        section_evidence.append({key: value for key, value in section.items() if key != "raw"})
        section_evidence[-1]["sha256"] = hashlib.sha256(raw).hexdigest()
        if section["section"] in ("__cstring", "__objc_methname", "__objc_classname", "__os_log"):
            literals.extend({**hit, "section": section["section"]} for hit in string_hits(raw, section["address"], oracle))
        if section["section"] == "__const":
            data_tables.extend({**hit, "segment": section["segment"], "section": section["section"]}
                               for hit in constant_table_hits(raw, section["address"], oracle))
    targets = {int(hit["address_hex"], 16) for hit in literals}
    references = []
    candidates = []
    census = {entry["name"]: {"value_hex": hex(entry["address"]), "category": entry["category"], "functions": 0, "events": 0}
              for entry in oracle["registers"]}
    address_sites = []
    skipped = [{"address_hex": hex(start), "reason": "START_OUTSIDE_SCANNED_TEXT"} for start in declared_starts
               if not any(section["address"] <= start < section["address"] + section["size"] for section in text_sections)]
    unassigned_text_bytes = 0
    function_count = 0
    for section in text_sections:
        base, raw = section["address"], section["raw"]
        starts = [start for start in image["starts"] if base <= start < base + len(raw)]
        if not starts:
            raise ValueError("Text section lacks declared function coverage")
        unassigned_text_bytes += starts[0] - base
        refs = kernel_image.literal_address_references(raw, base, targets)
        by_function = {}
        for reference in refs:
            bounds = function_bounds(int(reference["instruction_address_hex"], 16), starts, base, len(raw))
            reference["function_hex"] = hex(bounds[0]) if bounds else None
            references.append(reference)
            if bounds:
                by_function.setdefault(bounds[0], []).append(reference)
        for index, start in enumerate(starts):
            end = starts[index + 1] if index + 1 < len(starts) else base + len(raw)
            function_count += 1
            if end - start > 65536:
                skipped.append({"address_hex": hex(start), "size": end - start, "reason": "FUNCTION_OVER_64K_BOUND"})
                continue
            receipt = function_receipt(raw[start - base:end - base], start, names.get(start, []), oracle)
            receipt["literal_references"] = by_function.get(start, [])
            touched = set()
            for hit in receipt["dpcd_value_candidates"]:
                census[hit["register_name"]]["events"] += 1
                touched.add(hit["register_name"])
                if hit["value"] > 2 and hit["kind"] == "MOVE_WIDE_CONSTANT":
                    address_sites.append({**hit, "function_hex": receipt["address_hex"], "symbols": receipt["symbols"],
                                          "function_sha256": receipt["bytes_sha256"]})
            for name in touched:
                census[name]["functions"] += 1
            dpcd_named = any(re.search(r"(?i)dpcd|read.*aux|write.*aux", name) for name in receipt["symbols"])
            if receipt["constant_groups"] or receipt["symbol_signatures"] or receipt["literal_references"] or dpcd_named:
                candidates.append(receipt)
    evidence_hash = hashlib.sha256(json.dumps(section_evidence, sort_keys=True).encode()).hexdigest()
    for candidate in candidates:
        candidate.update(image=image["image"], image_uuid=image["uuid"], image_sections_sha256=evidence_hash)
    for hit in literals + symbol_hits + data_tables:
        hit.update(image=image["image"], image_uuid=image["uuid"], image_sections_sha256=evidence_hash)
    for hit in address_sites:
        hit.update(image=image["image"], image_uuid=image["uuid"], image_sections_sha256=evidence_hash)
    surface_symbols = [{"name": symbol["name"], "address_hex": hex(symbol["address"])} for symbol in image["symbols"]
                       if re.search(r"(?i)dpcd|stream|displayport|tunnel|payload|sideband|vcpi|packet|train|timing|port|link", symbol["name"])]
    return {"image": image["image"], "uuid": image["uuid"], "kind": image["kind"],
            "header_sha256": image["header_sha256"], "image_sections_sha256": evidence_hash,
            "hash_scope": "Exact scanned section descriptors and SHA-256 values; not a full dyld cache file hash",
            "sections": section_evidence, "function_starts_sha256": image["function_starts_sha256"],
            "declared_functions": function_count, "symbol_count": len(image["symbols"]), "skipped_functions": skipped,
            "unassigned_text_prefix_bytes": unassigned_text_bytes,
            "literal_hits": literals, "symbol_hits": symbol_hits, "literal_references": references,
            "constant_table_candidates": data_tables,
            "dpcd_value_census": census, "dpcd_move_sites": address_sites, "surface_symbols": surface_symbols,
            "symbol_inventory_sha256": hashlib.sha256(json.dumps(image["symbols"], sort_keys=True).encode()).hexdigest(),
            "candidates": candidates,
            "coverage_limit": "Move-wide/compare/logical immediates, aligned 32-bit payload/window tables within 64 bytes, and adjacent ADRP+ADD literals; dynamic constants, jump tables and indirect strings can be missed. All hits require manual DP attribution."}


def detail_function(image, address, decoder, oracle):
    if address not in image["starts"]:
        raise ValueError("Detail address is not a declared function start")
    sections = [section for section in image["sections"] if section["section"] == "__text" and
                section["address"] <= address < section["address"] + section["size"]]
    if len(sections) != 1:
        raise ValueError("Detail function lacks a unique text section")
    section = sections[0]
    start, end = function_bounds(address, image["starts"], section["address"], section["size"])
    if end - start > 32768:
        raise ValueError("Detail function exceeds 32 KiB")
    raw = section["raw"][start - section["address"]:end - section["address"]]
    names = {}
    for symbol in image["symbols"]:
        names.setdefault(symbol["address"], []).append(symbol["name"])
    receipt = function_receipt(raw, start, names.get(start, []), oracle)
    receipt.update(image=image["image"], image_uuid=image["uuid"],
                   instructions=[decoder.decode(start + offset, raw[offset:offset + 4]) for offset in range(0, len(raw), 4)])
    for call in receipt["direct_calls"]:
        call["target_symbols"] = names.get(int(call["target_hex"], 16), [])
    callers = kernel_image.direct_call_references(section["raw"], section["address"], {address})
    for caller in callers:
        bounds = function_bounds(int(caller["instruction_address_hex"], 16), image["starts"], section["address"], section["size"])
        caller["containing_function_hex"] = hex(bounds[0]) if bounds else None
        caller["symbols"] = names.get(bounds[0], []) if bounds else []
    receipt["direct_callers_in_image"] = callers
    receipt["caller_limit"] = "Direct calls in this image only; not an indirect or cross-image caller closure"
    return receipt


def kernel_inputs():
    files = sorted(pathlib.Path("/System/Volumes/Preboot").glob("*/boot/*/System/Library/Caches/com.apple.kernelcaches/kernelcache"))
    if len(files) != 1 or files[0].stat().st_size > 64 * 1024 * 1024:
        raise ValueError("No unique bounded kernel container")
    original = files[0].read_bytes()
    payload, container = kernel_image.kernel_payload(original)
    data = kernel_image.decompress_kernel(payload)
    entries = kernel_image.fileset_entries(data)
    identity = kernel_image.macho_uuid(data, entries["com.apple.kernel"]["file_offset"])
    active = subprocess.check_output(["/usr/sbin/sysctl", "-n", "kern.uuid"], text=True).strip().upper()
    if identity != active:
        raise ValueError("Kernel image does not match current kernel")
    return data, entries, {"kernel_uuid": identity, "container": container,
                           "container_sha256": hashlib.sha256(original).hexdigest(),
                           "decompressed_sha256": hashlib.sha256(data).hexdigest()}


def kernel_view(data, name, entry):
    offset = entry["file_offset"]
    starts, start_evidence = kernel_image.macho_function_starts(data, offset)
    sections = [section for section in kernel_image.macho_sections(data, offset)
                if section["section"] in ("__text", "__cstring", "__os_log", "__const")]
    command_size = struct.unpack_from("<I", data, offset + 20)[0]
    return {"image": name, "kind": "kernel_fileset", "uuid": kernel_image.macho_uuid(data, offset),
            "header_sha256": hashlib.sha256(data[offset:offset + 32 + command_size]).hexdigest(),
            "starts": starts, "function_starts_sha256": start_evidence["bytes_sha256"],
            "symbols": kernel_image.macho_symbols(data, offset),
            "sections": [{**section, "raw": bytes(kernel_image.bounded_slice(data, section["file_offset"], section["size"]))} for section in sections]}


def public_registry_evidence(baseline_file):
    from inspect_userserver import RegistryReader
    baseline_file = pathlib.Path(baseline_file)
    raw = baseline_file.read_bytes()
    baseline = json.loads(raw)
    candidates = baseline.get("external_dp_candidates", [])
    if len(candidates) != 1 or baseline.get("public_displayport_interface", {}).get("active_external_display_count") != 1:
        raise ValueError("Public evidence requires a healthy single-external baseline")
    paths = candidates[0]["active_transport_paths"]
    reader = RegistryReader()
    records = {}
    for class_name in ("DCPDPDeviceProxy", "DCPDPServiceProxy", "AppleDCPDPTXRemotePortProxy",
                       "IOPortTransportStateDisplayPort", "IOMobileFramebuffer"):
        with reader.entries(class_name=class_name) as (result, handles):
            if result != 0:
                raise ValueError("Public class enumeration failed: " + class_name)
            records[class_name] = [reader.record(handle) for handle in handles]
    active = [record for record in records["IOPortTransportStateDisplayPort"]
              if (record.get("properties") or {}).get("values", {}).get("Active") is True]
    if len(active) != 1 or active[0]["path"] not in paths:
        raise ValueError("Public active transport changed since baseline")
    values = active[0]["properties"]["values"]
    if values.get("HPD_State") != 2 or values.get("LinkRate", 0) == 0 or values.get("LaneCount", 0) == 0:
        raise ValueError("Public link is no longer healthy")
    if any(record.get("properties") is None for entries in records.values() for record in entries):
        raise ValueError("Incomplete public property-name evidence")
    return {"baseline_sha256": hashlib.sha256(raw).hexdigest(), "classes": records, "calls": reader.calls,
            "scope": "Public matching/class identity/property names and existing allowlisted values only; no userServer analysis, client open or transaction",
            "property_value_limit": "Unallowlisted property values remain unrepresented; absence of a value is not absence of a property"}


def main():
    parser = argparse.ArgumentParser(description="Read-only, candidate-only MST source scan; no transport code or private API invocation.")
    parser.add_argument("--inventory", action="store_true")
    parser.add_argument("--kernel-image", action="append", default=[])
    parser.add_argument("--userspace-image", action="append", default=[])
    parser.add_argument("--detail-address", action="append", type=lambda value: int(value, 0), default=[])
    parser.add_argument("--public-baseline", type=pathlib.Path)
    parser.add_argument("--output", type=pathlib.Path, required=True)
    args = parser.parse_args()
    repository = pathlib.Path(__file__).resolve().parents[1]
    root = (repository / "artifacts/probes").resolve()
    if not args.output.resolve().is_relative_to(root) or args.output.resolve() == root or args.output.exists():
        parser.error("output must be a new file under artifacts/probes")
    if not args.inventory and not (args.kernel_image or args.userspace_image or args.public_baseline):
        parser.error("select exact image names or inventory")
    if len(args.detail_address) > 64 or len(set(args.detail_address)) != len(args.detail_address):
        parser.error("at most 64 unique detail addresses")
    oracle, oracle_hash = load_oracle(repository / "docs/research/mst-source-signatures.json")
    report = {"schema_version": 1, "timestamp_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
              "oracle_sha256": oracle_hash, "linux_revision": oracle["linux_revision"],
              "selector0_status": "RETIRED_ON_DAILY_USE_M5", "dpcd_gate": "NOT_READY_FOR_DPCD_TEST",
              "safety": "Static file parsing and optional public registry reads only; no private interface opened or invoked.", "images": [], "errors": [], "details": []}
    detail_matches = set()

    def collect(image):
        report["images"].append(scan_image(image, oracle))
        selected = [address for address in args.detail_address if address in image["starts"]]
        if selected:
            from inspect_iodp import LLVMDisassembler
            decoder = LLVMDisassembler()
            try:
                for address in selected:
                    if address in detail_matches:
                        raise ValueError("Detail address maps to more than one image")
                    report["details"].append(detail_function(image, address, decoder, oracle))
                    detail_matches.add(address)
            finally:
                decoder.close()
    if args.inventory or args.kernel_image:
        data, entries, metadata = kernel_inputs()
        report["kernel"] = metadata
        if args.inventory:
            report["kernel_image_names"] = sorted(entries)
        for name in args.kernel_image:
            if name not in entries:
                raise ValueError("Requested kernel image is absent: " + name)
            collect(kernel_view(data, name, entries[name]))
    if args.inventory or args.userspace_image:
        cache = DyldCache("/System/Volumes/Preboot/Cryptexes/OS/System/Library/dyld/dyld_shared_cache_arm64e")
        inventory, table_hash = cache_image_inventory(cache)
        report["cache"] = {"components": cache.components, "image_table_sha256": table_hash}
        by_name = {entry["image"]: entry for entry in inventory}
        if args.inventory:
            report["userspace_image_names"] = sorted(by_name)
        for name in args.userspace_image:
            if name not in by_name:
                raise ValueError("Requested cached image is absent: " + name)
            try:
                collect(cached_image(cache, by_name[name]))
            except ValueError as error:
                report["errors"].append({"image": name, "uuid": by_name[name]["uuid"], "error": str(error)})
    if set(args.detail_address) != detail_matches:
        raise ValueError("Some requested detail addresses were not captured")
    if args.public_baseline:
        if not args.public_baseline.resolve().is_relative_to(root):
            parser.error("public baseline must be retained under artifacts/probes")
        report["public_registry"] = public_registry_evidence(args.public_baseline)
    report["tool_sha256"] = {name: hashlib.sha256((repository / "tools" / name).read_bytes()).hexdigest()
                             for name in ("scan_mst.py", "kernel_image.py", "dyld_cache.py", "inspect_iodp.py", "inspect_userserver.py")}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x") as stream:
        json.dump(report, stream, indent=2)
        stream.write("\n")
    print(json.dumps({"output": str(args.output), "images": len(report["images"]), "errors": report["errors"],
                      "candidates": sum(len(image["candidates"]) for image in report["images"])}))


if __name__ == "__main__":
    main()