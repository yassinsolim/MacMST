#!/usr/bin/env python3
"""Bounded current macOS host-image receipts; no display or firmware access."""

import argparse
import bisect
import datetime
import hashlib
import json
import pathlib
import plistlib
import re
import struct
import sys

import kernel_image
from call_graph import function_edges
from dyld_cache import DyldCache
from scan_mst import cache_image_inventory, cached_image, kernel_inputs, kernel_view


REPOSITORY = pathlib.Path(__file__).resolve().parents[1]
CACHE = pathlib.Path("/System/Volumes/Preboot/Cryptexes/OS/System/Library/dyld/dyld_shared_cache_arm64e")
MAX_FUNCTION_BYTES = 32768


def declared_bounds(image, address):
    starts = image["starts"]
    if starts != sorted(set(starts)) or address not in starts:
        raise ValueError("Requested address is not a unique declared function start")
    matches = [section for section in image["sections"] if section["section"] == "__text" and
               section["address"] <= address < section["address"] + section["size"]]
    if len(matches) != 1:
        raise ValueError("Function lacks a unique text section")
    section = matches[0]
    index = bisect.bisect_left(starts, address)
    end = min(starts[index + 1] if index + 1 < len(starts) else section["address"] + section["size"],
              section["address"] + section["size"])
    if not 0 < end - address <= MAX_FUNCTION_BYTES or (end - address) % 4 or address % 4:
        raise ValueError("Invalid or excessive declared function extent")
    offset = address - section["address"]
    raw = section["raw"][offset:offset + end - address]
    if len(raw) != end - address:
        raise ValueError("Incomplete declared function bytes")
    return raw, end


def text_owner(image, address):
    for section in image["sections"]:
        if section["section"] == "__text" and section["address"] <= address < section["address"] + section["size"]:
            index = bisect.bisect_right(image["starts"], address) - 1
            if index >= 0 and image["starts"][index] >= section["address"]:
                return image["starts"][index]
    return None


def symbol_names(images):
    names = {}
    for image in images:
        for symbol in image["symbols"]:
            if symbol["address"]:
                names.setdefault(symbol["address"], set()).add(symbol["name"])
    return {address: sorted(values) for address, values in names.items()}


def selected_symbols(image, pattern):
    starts = set(image["starts"])
    return [{"name": symbol["name"], "address_hex": hex(symbol["address"]),
             "declared_function": symbol["address"] in starts,
             "defined": bool(symbol["address"])}
            for symbol in image["symbols"] if pattern.search(symbol["name"])]


def selected_strings(image, pattern):
    strings = []
    for section in image["sections"]:
        if section["section"] not in ("__cstring", "__os_log", "__objc_methname", "__objc_classname"):
            continue
        offset = 0
        for value in section["raw"].split(b"\0"):
            if value and len(value) <= 4096:
                decoded = value.decode("utf-8", errors="replace")
                if pattern.search(decoded):
                    strings.append({"address_hex": hex(section["address"] + offset),
                                    "section": section["section"], "text": decoded,
                                    "raw_hex": value.hex(), "bytes_sha256": hashlib.sha256(value).hexdigest()})
            offset += len(value) + 1
    return strings


def describe_image(image, symbol_pattern, string_pattern, names):
    strings = selected_strings(image, string_pattern) if string_pattern else []
    targets = {int(value["address_hex"], 16) for value in strings}
    references = []
    if targets:
        for section in image["sections"]:
            if section["section"] != "__text":
                continue
            for reference in kernel_image.literal_address_references(section["raw"], section["address"], targets):
                address = int(reference["instruction_address_hex"], 16)
                owner = text_owner(image, address)
                references.append({**reference, "containing_function_hex": hex(owner) if owner is not None else None,
                                   "symbols": names.get(owner, [])})
    return {key: image[key] for key in ("image", "uuid", "kind", "header_sha256", "function_starts_sha256")} | {
        "declared_function_count": len(image["starts"]), "symbol_count": len(image["symbols"]),
        "sections": [{key: value for key, value in section.items() if key != "raw"} |
                     {"bytes_sha256": hashlib.sha256(section["raw"]).hexdigest()} for section in image["sections"]],
        "symbols": selected_symbols(image, symbol_pattern), "strings": strings,
        "literal_xrefs": references,
        "xref_limit": "Adjacent ADRP/ADD references only, not an exhaustive string/indirect reference closure"}


def function_receipt(image, address, decoder, names, images):
    raw, end = declared_bounds(image, address)
    record = {"image": image["image"], "image_uuid": image["uuid"], "address_hex": hex(address),
              "end_hex": hex(end), "size": len(raw), "raw_hex": raw.hex(),
              "bytes_sha256": hashlib.sha256(raw).hexdigest(), "symbols": names.get(address, []),
              "boundary": "LC_FUNCTION_STARTS to next declared start or text end; not runtime attestation",
              "instructions": [decoder.decode(address + offset, raw[offset:offset + 4]) for offset in range(0, len(raw), 4)]}
    graph = function_edges(record)
    for edge in graph["edges"]:
        edge["target_symbols"] = names.get(int(edge.get("target_hex", "0"), 16), [])
    record.update(graph)
    callers = []
    for other in images:
        for section in other["sections"]:
            if section["section"] != "__text":
                continue
            for reference in kernel_image.direct_call_references(section["raw"], section["address"], {address}):
                owner = text_owner(other, int(reference["instruction_address_hex"], 16))
                callers.append({**reference, "image": other["image"], "containing_function_hex": hex(owner) if owner else None,
                                "symbols": names.get(owner, [])})
    record["direct_callers"] = callers
    record["caller_limit"] = "Direct calls in selected host images only; excludes indirect/ObjC and unselected-image closure"
    return record


def output_path(path):
    root = (REPOSITORY / "artifacts/probes/m5p2").resolve()
    destination = path.resolve()
    if not destination.is_relative_to(root) or destination == root or destination.exists():
        raise ValueError("Output must be a new file under artifacts/probes/m5p2")
    return destination


def data_range(value):
    address, length = value.split(":", 1)
    address, length = int(address, 0), int(length, 0)
    if not 0 <= address < 1 << 64 or not 0 < length <= 256 or address + length > 1 << 64:
        raise ValueError("Static data range must be 1..256 bytes within one address space")
    return address, length


def plist_json(value):
    if isinstance(value, bytes):
        return {"plist_type": "data", "raw_hex": value.hex()}
    if isinstance(value, dict):
        return {key: plist_json(item) for key, item in value.items()}
    if isinstance(value, list):
        return [plist_json(item) for item in value]
    return value


def host_file_metadata():
    bundles = ("AppleDisplayCrossbar", "AppleDCP", "DCPDPFamilyProxy", "DCPAVFamilyProxy",
               "AppleDCPDPTXProxy", "IOAVFamily", "IODisplayPortFamily", "IOGraphicsFamily",
               "AppleMobileDispH17G-DCP", "IOMobileGraphicsFamily-DCP")
    records = []
    for name in bundles:
        path = pathlib.Path("/System/Library/Extensions") / (name + ".kext") / "Contents/Info.plist"
        if not path.is_file():
            records.append({"path": str(path), "present": False})
            continue
        raw = path.read_bytes()
        if len(raw) > 4 * 1024 * 1024:
            raise ValueError("Excessive static host bundle metadata")
        value = plist_json(plistlib.loads(raw))
        records.append({"path": str(path), "present": True, "size": len(raw),
                        "bytes_sha256": hashlib.sha256(raw).hexdigest(),
                        "bundle_identifier": value.get("CFBundleIdentifier"), "bundle_version": value.get("CFBundleVersion"),
                        "personalities": {key: {field: item[field] for field in
                                                ("IOClass", "IOProviderClass", "IONameMatch", "IOPropertyMatch", "IOUserClass", "IOUserServerName")
                                                if field in item}
                                          for key, item in value.get("IOKitPersonalities", {}).items()}})
    path = pathlib.Path("/System/Library/PrivateFrameworks/SkyLight.framework/Versions/A/Resources/WindowServer")
    raw = path.read_bytes()
    if len(raw) > 16 * 1024 * 1024 or raw[:4] != b"\xca\xfe\xba\xbe":
        raise ValueError("Unexpected standalone WindowServer container")
    count = struct.unpack_from(">I", raw, 4)[0]
    if not 0 < count <= 8 or 8 + count * 20 > len(raw):
        raise ValueError("Invalid WindowServer fat architecture count")
    slices = []
    for cpu, subtype, offset, size, alignment in struct.iter_unpack(">5I", raw[8:8 + count * 20]):
        if cpu != 0x0100000c:
            continue
        body = bytes(kernel_image.bounded_slice(raw, offset, size))
        _, commands = kernel_image.macho_commands(body)
        dependencies = [kernel_image.cstring(record, struct.unpack_from("<I", record, 8)[0])
                        for command, _, record in commands if command in (0xc, 0x80000018, 0x8000001f)]
        slices.append({"cpu_type": cpu, "cpu_subtype": subtype, "offset": offset, "size": size,
                       "uuid": kernel_image.macho_uuid(body), "bytes_sha256": hashlib.sha256(body).hexdigest(),
                       "dependencies": dependencies})
    if len(slices) != 1:
        raise ValueError("WindowServer has no unique arm64 slice")
    records.append({"path": str(path), "present": True, "size": len(raw),
                    "bytes_sha256": hashlib.sha256(raw).hexdigest(), "arm64_slices": slices})
    return records


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory", action="store_true", help="list host kernel/cache image metadata")
    parser.add_argument("--kernel-image", action="append", default=[])
    parser.add_argument("--userspace-image", action="append", default=[])
    parser.add_argument("--symbols", default=r"DCPDPVirtualDevice|DCPDPDeviceProxy|DCPDPServiceProxy")
    parser.add_argument("--strings", default=None)
    parser.add_argument("--function", action="append", type=lambda value: int(value, 0), default=[])
    parser.add_argument("--pointer", action="append", type=lambda value: int(value, 0), default=[])
    parser.add_argument("--data", action="append", type=data_range, default=[], help="explicit host constant address:length, at most 256 bytes")
    parser.add_argument("--output", required=True, type=pathlib.Path)
    arguments = parser.parse_args(argv)
    destination = output_path(arguments.output)
    if len(arguments.kernel_image) + len(arguments.userspace_image) > 16 or len(arguments.function) > 48 or len(arguments.pointer) > 128 or len(arguments.data) > 32:
        raise ValueError("Host-image/region selection exceeds bounded budget")
    if not arguments.inventory and not (arguments.kernel_image or arguments.userspace_image):
        raise ValueError("Select host images or metadata inventory")
    if len(arguments.symbols) > 1024 or (arguments.strings and len(arguments.strings) > 1024):
        raise ValueError("Excessive search expression")
    os_info = plistlib.loads(pathlib.Path('/System/Library/CoreServices/SystemVersion.plist').read_bytes())
    if (os_info["ProductVersion"], os_info["ProductBuildVersion"]) != ("26.6.2", "25G83"):
        raise ValueError("M5P2 exact host build differs from the approved 26.6.2/25G83 baseline")
    report = {"schema_version": 1, "milestone": "M5P2", "timestamp_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
              "os_version": os_info["ProductVersion"], "os_build": os_info["ProductBuildVersion"],
              "arguments": vars(arguments) | {"output": str(destination.relative_to(REPOSITORY))},
              "safety": "Host files only; no firmware payload analysis, registry enumeration, private/display call or m1n1 access",
              "images": [], "functions": [], "pointers": [], "data": [], "errors": []}
    images = []
    pointers = None
    cache = None
    if arguments.inventory or arguments.kernel_image:
        data, entries, metadata = kernel_inputs()
        report["kernel"] = metadata
        if metadata["kernel_uuid"] != "447D769E-1CB7-3086-A0B4-32226837B587":
            raise ValueError("Current kernel UUID differs from the target baseline")
        if arguments.inventory:
            report["kernel_image_names"] = sorted(entries)
        for name in arguments.kernel_image:
            images.append(kernel_view(data, name, entries[name]))
        pointers = kernel_image.KernelCachePointers(data) if arguments.pointer or arguments.data else None
    if arguments.inventory or arguments.userspace_image:
        cache = DyldCache(CACHE)
        inventory, table_hash = cache_image_inventory(cache)
        report["cache"] = {"components": cache.components, "image_table_sha256": table_hash}
        by_name = {entry["image"]: entry for entry in inventory}
        if arguments.inventory:
            report["userspace_image_names"] = sorted(by_name)
        for name in arguments.userspace_image:
            images.append(cached_image(cache, by_name[name]))
    names = symbol_names(images)
    if arguments.inventory:
        report["host_files"] = host_file_metadata()
    symbol_pattern = re.compile(arguments.symbols, re.I)
    string_pattern = re.compile(arguments.strings, re.I) if arguments.strings else None
    report["images"] = [describe_image(image, symbol_pattern, string_pattern, names) for image in images]
    if arguments.function:
        from inspect_iodp import LLVMDisassembler
        decoder = LLVMDisassembler()
        try:
            for address in arguments.function:
                owners = [image for image in images if address in image["starts"]]
                if len(owners) != 1:
                    raise ValueError("Function does not have a unique declared owner in selected images")
                report["functions"].append(function_receipt(owners[0], address, decoder, names, images))
        finally:
            decoder.close()
    for address in arguments.pointer:
        try:
            pointer = pointers.pointer(address) if address >= 0xffff000000000000 and pointers else cache.pointer(address)
            target = int(pointer["target_address_hex"], 16)
            report["pointers"].append(pointer | {"target_symbols": names.get(target, [])})
        except (ValueError, AttributeError) as error:
            report["errors"].append({"pointer": hex(address), "error": str(error)})
    for address, length in arguments.data:
        raw = pointers.read(address, length) if address >= 0xffff000000000000 and pointers else cache.read(address, length)
        report["data"].append({"address_hex": hex(address), "length": length, "raw_hex": raw.hex(),
                               "bytes_sha256": hashlib.sha256(raw).hexdigest(), "symbols": names.get(address, [])})
    report["tool_sha256"] = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in
                             (pathlib.Path(__file__), REPOSITORY / 'tools/scan_mst.py', REPOSITORY / 'tools/kernel_image.py',
                              REPOSITORY / 'tools/dyld_cache.py', REPOSITORY / 'tools/call_graph.py', REPOSITORY / 'tools/inspect_iodp.py')}
    content = json.dumps(report, indent=2, sort_keys=True) + '\n'
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open('x', encoding='utf-8') as stream:
        stream.write(content)
    print(json.dumps({"output": str(destination.relative_to(REPOSITORY)), "images": len(images),
                      "functions": len(report["functions"]), "pointers": len(report["pointers"]),
                      "errors": report["errors"], "sha256": hashlib.sha256(destination.read_bytes()).hexdigest()}))
    return 1 if report["errors"] else 0


if __name__ == '__main__':
    raise SystemExit(main())