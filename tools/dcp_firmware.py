import argparse
import ctypes
import hashlib
import json
import pathlib
import re
import struct

import kernel_image
import ipsw_dcp
import scan_mst


def bundle_layout(raw):
    if not 0x3b8 <= len(raw) <= 64 * 1024 * 1024 or raw[8:12] != b"DNUB" or struct.unpack_from("<H", raw, 14)[0] != 4:
        raise ValueError("Only bounded BUND type 4 is supported")
    range_count = struct.unpack_from("<Q", raw, 0x88)[0]
    if not 1 <= range_count <= 13:
        raise ValueError("Invalid BUND range count")
    ranges = []
    for index in range(13):
        kind, name_raw, offset, size = struct.unpack_from("<I4sQQ", raw, 0x280 + index * 24)
        name = name_raw[::-1].rstrip(b"\0").decode("ascii")
        if size:
            kernel_image.bounded_slice(raw, offset, size)
            if not name or any(record["name"] == name for record in ranges):
                raise ValueError("Missing or duplicate BUND range name")
        ranges.append({"index": index, "type": kind, "name": name, "offset": offset, "size": size})
    containers = [record for record in ranges if record["name"] == "nold" and record["size"]]
    if len(containers) != 1:
        raise ValueError("BUND lacks unique nold metadata range")
    container = containers[0]
    relative, padding, size = struct.unpack_from("<3Q", raw, 0x248)
    if not 0 < size <= 1024 * 1024 or relative + size > container["size"] or (padding and size > padding):
        raise ValueError("BUND nold metadata outside declared range")
    config_offset = container["offset"] + relative
    config = bytes(kernel_image.bounded_slice(raw, config_offset, size))
    nodes = parse_devicetree(config)
    return {"type": 4, "range_count_raw": range_count, "ranges": ranges,
            "config_format": "APPLE_DEVICETREE_NOLD", "config_offset": config_offset,
            "config_size": size, "config_sha256": ipsw_dcp.sha256(config),
            "config_nodes": [{"path": node["path"], "offset": node["offset"],
                              "property_names": list(node["properties"])} for node in nodes]}


def decode_im4p(raw, component, decoder=None):
    if not 0 < len(raw) <= 64 * 1024 * 1024:
        raise ValueError("IM4P exceeds bounded input size")
    tag, start, end = kernel_image.der_item(raw, 0)
    if tag != 0x30 or end != len(raw):
        raise ValueError("Expected one complete IM4P sequence")
    children = kernel_image.der_children(raw, start, end)
    if len(children) < 4 or [item[0] for item in children[:4]] != [0x16, 0x16, 0x16, 0x04]:
        raise ValueError("Unsupported IM4P field shape")
    if raw[children[0][1]:children[0][2]] != b"IM4P":
        raise ValueError("Not an IM4P container")
    payload_type = raw[children[1][1]:children[1][2]].decode("ascii")
    if payload_type not in ("dcpf", "dcp2", "dtre"):
        raise ValueError("Only normal DCP/DeviceTree payloads are in scope")
    description = raw[children[2][1]:children[2][2]].decode("ascii")
    payload_start, payload_end = children[3][1:]
    payload = raw[payload_start:payload_end]
    adjusted = bytearray(raw)
    requested_type = component["Info"].get("Img4PayloadType", payload_type)
    if requested_type not in ("dcpf", "dcp2", "dtre") or len(requested_type) != 4:
        raise ValueError("Unexpected normal firmware payload-type override")
    adjusted[children[1][1]:children[1][2]] = requested_type.encode("ascii")
    digest = component["Digest"]
    if isinstance(digest, dict):
        digest = bytes.fromhex(digest["hex"])
    if component.get("Trusted") is not True or len(digest) != 48 or hashlib.sha384(adjusted).digest() != digest:
        raise ValueError("IM4P does not match selected BuildManifest digest/type")
    expected_size = None
    compression_mode = None
    for field_tag, field_start, field_end in children[4:]:
        if field_tag == 0x04:
            raise ValueError("Public IM4P keybag present; no decryption or device-key access implemented")
        if field_tag != 0x30 or expected_size is not None:
            raise ValueError("Unrecognized IM4P metadata; cannot claim keybag absence")
        fields = kernel_image.der_children(raw, field_start, field_end)
        if len(fields) != 2 or any(kind != 0x02 for kind, _, _ in fields):
            raise ValueError("Unknown IM4P compression metadata")
        values = []
        for _, begin, finish in fields:
            value = raw[begin:finish]
            if not value or len(value) > 5 or value[0] & 0x80:
                raise ValueError("Invalid IM4P metadata integer")
            values.append(int.from_bytes(value, "big"))
        compression_mode, expected_size = values
        if compression_mode != 1 or not 0 < expected_size <= 64 * 1024 * 1024:
            raise ValueError("Unsupported compression mode or output size")
    compressed = payload[:4] in (b"bvx2", b"bvx1", b"bvxn", b"bvx-")
    if compressed:
        if expected_size is None:
            raise ValueError("Compressed IM4P lacks bounded decompressed-size metadata")
        if decoder is None:
            library = ctypes.CDLL("/usr/lib/libcompression.dylib")
            library.compression_decode_buffer.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_void_p,
                                                         ctypes.c_size_t, ctypes.c_void_p, ctypes.c_int]
            library.compression_decode_buffer.restype = ctypes.c_size_t
            output = ctypes.create_string_buffer(expected_size + 1)
            source = ctypes.create_string_buffer(payload)
            count = library.compression_decode_buffer(output, expected_size + 1, source, len(payload), None, 0x801)
            decoded = output[:count]
        else:
            decoded = decoder(payload, expected_size)
        if len(decoded) != expected_size:
            raise ValueError("IM4P decompressed size mismatch")
    else:
        if expected_size is not None:
            raise ValueError("Compression metadata without recognized LZFSE payload")
        decoded = payload
    return decoded, {"container_type": "IM4P", "raw_type": payload_type, "manifest_type": requested_type,
                     "description": description, "raw_size": len(raw), "raw_sha256": ipsw_dcp.sha256(raw),
                     "raw_sha384": hashlib.sha384(raw).hexdigest(), "manifest_digest_sha384": digest.hex(),
                     "digest_verification": "MATCH_AFTER_EXPLICIT_MANIFEST_TYPE_OVERRIDE" if requested_type != payload_type else "MATCH_RAW_IM4P",
                     "type_override_offset": children[1][1], "payload_offset": payload_start,
                     "compressed_payload_size": len(payload), "compressed_payload_sha256": ipsw_dcp.sha256(payload),
                     "compression": "LZFSE" if compressed else "NONE", "compression_mode_raw": compression_mode,
                     "keybag_status": "NO_KEYBAG_FIELD_PRESENT", "encryption_observation": "PUBLIC_PAYLOAD_DECODED_WITHOUT_KEYS",
                     "decoded_size": len(decoded), "decoded_sha256": ipsw_dcp.sha256(decoded),
                     "signature_validation": "NOT_PERFORMED; manifest digest is verified, not an Apple signature/TSS ticket"}


def runtime_view(raw):
    if raw.startswith(b"\xcf\xfa\xed\xfe"):
        if len(raw) > 64 * 1024 * 1024:
            raise ValueError("Standalone firmware exceeds input bound")
        header, commands = kernel_image.macho_commands(raw)
        segments = []
        for command, _, record in commands:
            if command == 0x19:
                name = bytes(record[8:24]).split(b"\0", 1)[0].decode("ascii")
                address, size, file_offset, file_size = struct.unpack_from("<4Q", record, 24)
                kernel_image.bounded_slice(raw, file_offset, file_size)
                if file_size > size:
                    raise ValueError("Standalone firmware segment file exceeds VM size")
                segments.append({"name": name, "address": address, "size": size, "file_offset": file_offset, "file_size": file_size})
        sections = kernel_image.macho_sections(raw, 0)
        mapped = []
        for section in sections:
            owners = [segment for segment in segments if segment["name"] == section["segment"] and
                      segment["address"] <= section["address"] <= section["address"] + section["size"] <= segment["address"] + segment["size"]]
            if len(owners) != 1:
                raise ValueError("Standalone firmware section lacks unique segment")
            if section["flags"] & 0xff in (1, 0xc, 0x12) or not section["size"]:
                continue
            owner = owners[0]
            if not owner["file_offset"] <= section["file_offset"] <= section["file_offset"] + section["size"] <= owner["file_offset"] + owner["file_size"]:
                raise ValueError("Standalone firmware section outside file-backed segment")
            mapped.append({**section, "raw": bytes(kernel_image.bounded_slice(raw, section["file_offset"], section["size"]))})
        identity = kernel_image.macho_uuid(raw)
        header_size = 32 + struct.unpack_from("<I", raw, 20)[0]
        symbols = [record for command, _, record in commands if command == 2]
        evidence = {"format": "STANDALONE_ARM64_MACHO", "architecture": header, "uuid": identity,
                    "header_offset": 0, "header_sha256": ipsw_dcp.sha256(raw[:header_size]), "segments": segments,
                    "all_sections": sections, "unmapped_sections": [],
                    "function_start_command_present": any(command == 0x26 for command, _, _ in commands),
                    "symbol_table_fields_raw": list(struct.unpack_from("<4I", symbols[0], 8)) if len(symbols) == 1 else None,
                    "symbol_table_status": "RECORDED_NOT_USED_FOR_FUNCTION_BOUNDARIES",
                    "chained_fixup_command_present": any(command == 0x80000034 for command, _, _ in commands),
                    "section_mapping": "Declared standalone Mach-O file and VM ranges; comparison input is not M5 identity evidence"}
        return {"image": "DCP_RUNTIME", "uuid": identity, "kind": "dcp_standalone_runtime", "symbols": [],
                "sections": mapped, "header_sha256": evidence["header_sha256"], "layout_evidence": evidence}
    layout = bundle_layout(raw)
    ranges = {record["name"]: record for record in layout["ranges"] if record["size"]}
    if not all(name in ranges for name in ("nold", "rtxt", "rdat")):
        raise ValueError("DCP runtime ranges are incomplete")
    directory = ranges["nold"]
    candidates = []
    cursor = directory["offset"]
    directory_end = cursor + min(directory["size"], layout["config_offset"] - cursor)
    while cursor < directory_end:
        cursor = raw.find(b"\xcf\xfa\xed\xfe", cursor, directory_end)
        if cursor < 0:
            break
        header, commands = kernel_image.macho_commands(raw, cursor)
        header_size = 32 + struct.unpack_from("<I", raw, cursor + 20)[0]
        if cursor + header_size > directory_end or len(candidates) >= 8:
            raise ValueError("Embedded Mach-O header exceeds directory bounds")
        segments = []
        sections = []
        section_index = 0
        for command, position, record in commands:
            if command != 0x19:
                continue
            name = bytes(record[8:24]).split(b"\0", 1)[0].decode("ascii")
            address, size, file_offset, file_size = struct.unpack_from("<4Q", record, 24)
            count = struct.unpack_from("<I", record, 64)[0]
            if 72 + count * 80 != len(record) or file_size > size or file_offset + file_size > 64 * 1024 * 1024:
                raise ValueError("Invalid runtime segment bounds")
            segments.append({"name": name, "address": address, "size": size, "file_offset": file_offset, "file_size": file_size})
            for index in range(count):
                section_index += 1
                section = record[72 + index * 80:152 + index * 80]
                section_name = bytes(section[:16]).split(b"\0", 1)[0].decode("ascii")
                section_address, section_size, section_offset = struct.unpack_from("<QQI", section, 32)
                relocation_offset, relocation_count, flags = struct.unpack_from("<III", section, 56)
                if not address <= section_address <= section_address + section_size <= address + size:
                    raise ValueError("Runtime section outside declared segment")
                if flags & 0xff not in (1, 0xc, 0x12) and not file_offset <= section_offset <= section_offset + section_size <= file_offset + file_size:
                    raise ValueError("Runtime section outside file-backed segment")
                sections.append({"segment": name, "section": section_name, "address": section_address,
                                 "size": section_size, "file_offset": section_offset, "flags": flags,
                                 "index": section_index, "relocation_offset": relocation_offset, "relocation_count": relocation_count,
                                 "reserved1": struct.unpack_from("<I", section, 68)[0]})
        texts = [segment for segment in segments if segment["name"] == "__TEXT"]
        if len(texts) != 1:
            raise ValueError("Embedded runtime lacks unique text segment")
        candidates.append({"header_offset": cursor, "header_size": header_size, "header": header,
                           "uuid": kernel_image.macho_uuid(raw, cursor), "segments": segments, "sections": sections,
                           "text_size": texts[0]["size"], "commands": commands})
        cursor += header_size
    if not candidates:
        raise ValueError("No valid runtime header in nold directory")
    candidates.sort(key=lambda item: item["text_size"], reverse=True)
    if len(candidates) > 1 and candidates[0]["text_size"] == candidates[1]["text_size"]:
        raise ValueError("Ambiguous main DCP runtime image")
    selected = candidates[0]
    text = next(segment for segment in selected["segments"] if segment["name"] == "__TEXT")
    data = next(segment for segment in selected["segments"] if segment["name"] == "__DATA")
    config = raw[layout["config_offset"]:layout["config_offset"] + layout["config_size"]]
    metadata_nodes = [node for node in parse_devicetree(config) if node["path"].endswith("/dcp_legacy/metadata")]
    segment_sources = {"__TEXT": ranges["rtxt"], "__DATA": ranges["rdat"]}
    associations = []
    for node in metadata_nodes:
        values = {key: int.from_bytes(value["raw"], "little") for key, value in node["properties"].items()
                  if key.startswith("%__MACHO") and len(value["raw"]) == 8}
        if values.get("%__MACHOHEADEROFF") != selected["header_offset"] or values.get("%__MACHOHEADERSZ") != selected["header_size"]:
            raise ValueError("Compartment header metadata disagrees with selected runtime")
        associations.append({"path": node["path"], "fields": values})
        for segment in selected["segments"]:
            prefix = "%__MACHO" + segment["name"]
            if prefix + "OFF" not in values or prefix + "SZ" not in values:
                continue
            offset, size = values[prefix + "OFF"], values[prefix + "SZ"]
            kernel_image.bounded_slice(raw, offset, size)
            if size != segment["size"]:
                raise ValueError("Compartment segment size mismatch")
            previous = segment_sources.get(segment["name"])
            if previous and previous["offset"] != offset:
                raise ValueError("Compartment segment mapping disagrees across instances")
            segment_sources[segment["name"]] = {"offset": offset, "size": size}
    log_segments = [segment for segment in selected["segments"] if segment["name"] == "__OS_LOG"]
    if len(log_segments) == 1 and "ubdl" in ranges and "__OS_LOG" not in segment_sources:
        if log_segments[0]["file_size"] > ranges["ubdl"]["size"]:
            raise ValueError("Runtime log segment exceeds declared ubdl range")
        segment_sources["__OS_LOG"] = ranges["ubdl"]
    sections = []
    unmapped = []
    for section in selected["sections"]:
        if section["flags"] & 0xff in (1, 0xc, 0x12) or not section["size"]:
            continue
        if section["segment"] not in segment_sources:
            unmapped.append({**section, "reason": "NO_COMPARTMENT_SEGMENT_MAPPING; not treated as zero-filled evidence"})
            continue
        source_range = segment_sources[section["segment"]]
        source_base = next(segment["file_offset"] for segment in selected["segments"] if segment["name"] == section["segment"])
        relative = section["file_offset"] - source_base
        if relative < 0 or relative + section["size"] > source_range["size"]:
            raise ValueError("Runtime section exceeds its BUND source range")
        offset = source_range["offset"] + relative
        sections.append({**section, "bundle_offset": offset,
                         "raw": bytes(kernel_image.bounded_slice(raw, offset, section["size"]))})
    commands = selected["commands"]
    symbol_records = [record for command, _, record in commands if command == 0x2]
    symbol_fields = list(struct.unpack_from("<4I", symbol_records[0], 8)) if len(symbol_records) == 1 else None
    evidence = {"bundle": layout, "header_offset": selected["header_offset"], "architecture": selected["header"],
                "uuid": selected["uuid"], "header_sha256": ipsw_dcp.sha256(raw[selected["header_offset"]:selected["header_offset"] + selected["header_size"]]),
                "segments": selected["segments"], "all_sections": selected["sections"],
                "directory_images": [{key: candidate[key] for key in ("header_offset", "header_size", "uuid", "text_size")} for candidate in candidates],
                "function_start_command_present": any(command == 0x26 for command, _, _ in commands),
                "symbol_table_fields_raw": symbol_fields,
                "symbol_table_status": "DECLARED_OFFSETS_NOT_RECONSTRUCTED; public runtime extractor discards stale LC_SYMTAB/LC_DYSYMTAB",
                "chained_fixup_command_present": any(command == 0x80000034 for command, _, _ in commands),
                "compartment_associations": associations, "unmapped_sections": unmapped,
                "section_mapping": "Main largest-text nold header, checked against dcp_legacy compartment metadata; explicit per-segment mappings; main __OS_LOG from bounded ubdl range with diagnostic-reference cross-check; unmapped sections excluded"}
    return {"image": "DCP_RUNTIME", "uuid": selected["uuid"], "kind": "dcp_bund_runtime", "symbols": [],
            "sections": sections, "header_sha256": evidence["header_sha256"], "layout_evidence": evidence}


def firmware_regions(section):
    raw, base = section["raw"], section["address"]
    if len(raw) % 4 or base % 4:
        raise ValueError("Unaligned firmware code section")
    boundaries = {base: "SECTION_START"}
    for index, (word,) in enumerate(struct.iter_unpack("<I", raw)):
        address = base + index * 4
        if word in (0xd503237f, 0xd503233f):
            boundaries[address] = "PAC_PROLOGUE_INFERRED_FUNCTION_START"
        target = scan_mst.direct_branch_target(raw[index * 4:index * 4 + 4], address)
        if word & 0xfc000000 == 0x94000000 and target is not None and base <= target < base + len(raw):
            boundaries.setdefault(target, "DIRECT_CALL_TARGET_INFERRED_FUNCTION_START")
    starts = sorted(boundaries)
    regions = []
    for index, start in enumerate(starts):
        end = starts[index + 1] if index + 1 < len(starts) else base + len(raw)
        for position in range(start, end, 65536):
            regions.append({"start": position, "end": min(end, position + 65536),
                            "boundary": boundaries[start] if position == start else "BOUNDED_CONTINUATION_NOT_FUNCTION_START"})
    return regions


class FirmwarePointers:
    def __init__(self, view):
        self.view = view
        sections = [section for section in view["sections"] if section["section"] == "__chain_starts"]
        if len(sections) != 1:
            raise ValueError("Firmware lacks unique chain-start section")
        section = sections[0]
        raw = section["raw"]
        pointer_format, count = struct.unpack("<II", kernel_image.bounded_slice(raw, 0, 8))
        if pointer_format != 7 or not 0 < count <= 4096 or section["reserved1"] != 2:
            raise ValueError("Only format-7 VM-offset firmware chains are supported")
        starts_raw = kernel_image.bounded_slice(raw, 8, count * 4)
        if any(raw[8 + count * 4:]):
            raise ValueError("Nonzero extra firmware chain-start data")
        bases = [segment["address"] for segment in view["layout_evidence"]["segments"] if segment["name"] == "__TEXT"]
        if len(bases) != 1:
            raise ValueError("Firmware lacks unique text VM base")
        self.base = bases[0]
        self.records = {}
        self.chain_sha256 = ipsw_dcp.sha256(raw)
        for chain_index, (relative,) in enumerate(struct.iter_unpack("<I", starts_raw)):
            address = self.base + relative
            hops = 0
            while True:
                if address % 4 or address in self.records or len(self.records) >= 200000:
                    raise ValueError("Misaligned, duplicate or excessive firmware pointer chain")
                word_raw = self.read(address, 8)
                word = int.from_bytes(word_raw, "little")
                if word & (1 << 62):
                    raise ValueError("Firmware bind pointer is unsupported")
                authenticated = bool(word >> 63)
                if authenticated:
                    target = self.base + (word & 0xffffffff)
                else:
                    target = self.base + (word & ((1 << 43) - 1))
                    target |= ((word >> 43) & 0xff) << 56
                next_bytes = ((word >> 51) & 0x7ff) * 4
                self.records[address] = {"slot_hex": hex(address), "raw_bytes_hex": word_raw.hex(),
                                         "target_hex": hex(target), "authenticated": authenticated,
                                         "next_bytes": next_bytes, "chain_index": chain_index, "chain_hops": hops,
                                         "chain_metadata_sha256": self.chain_sha256,
                                         "assessment": "DECLARED_CHAIN_MEMBER; receiver context and target role require separate proof"}
                if not next_bytes:
                    break
                address += next_bytes
                hops += 1

    def read(self, address, size):
        matches = [section for section in self.view["sections"] if section["address"] <= address and
                   address + size <= section["address"] + section["size"]]
        if len(matches) != 1:
            raise ValueError("Firmware pointer/read lacks unique mapped section")
        section = matches[0]
        offset = address - section["address"]
        return section["raw"][offset:offset + size]

    def pointer(self, address):
        if address not in self.records:
            raise ValueError("Firmware slot is not a declared chain member")
        return self.records[address]


def scan_runtime(view, oracle):
    candidates = []
    literals = []
    tables = []
    sections = []
    region_count = 0
    census = {entry["name"]: {"value_hex": hex(entry["address"]), "events": 0} for entry in oracle["registers"]}
    diagnostics = re.compile(r"(?i)dptx|displayport|\bdpcd\b|\bsst\b|\bmst\b|sideband|vcpi|\bpbn\b|payload|branch|topology|bandwidth|stream")
    for section in view["sections"]:
        evidence = {key: value for key, value in section.items() if key != "raw"}
        evidence["sha256"] = ipsw_dcp.sha256(section["raw"])
        sections.append(evidence)
        if section["flags"] & 0xff == 2:
            position = 0
            for value in section["raw"].split(b"\0"):
                if 3 <= len(value) <= 16384:
                    try:
                        text = value.decode("utf-8")
                    except UnicodeDecodeError:
                        text = ""
                    signatures = scan_mst.literal_matches(text, oracle)
                    if signatures or diagnostics.search(text):
                        literals.append({"address_hex": hex(section["address"] + position), "section": section["section"],
                                         "segment": section["segment"], "value": text, "sha256": ipsw_dcp.sha256(value),
                                         "signatures": signatures, "function_hex": None, "assessment": "UNQUALIFIED_FIRMWARE_STRING"})
                position += len(value) + 1
        if section["section"] == "__const":
            tables.extend({**hit, "section": section["section"], "segment": section["segment"]}
                          for hit in scan_mst.constant_table_hits(section["raw"], section["address"], oracle))
    targets = {int(hit["address_hex"], 16) for hit in literals}
    references = []
    for section in view["sections"]:
        if not section["flags"] & 0x80000000:
            continue
        refs = kernel_image.literal_address_references(section["raw"], section["address"], targets)
        for region in firmware_regions(section):
            region_count += 1
            start, end = region["start"], region["end"]
            body = section["raw"][start - section["address"]:end - section["address"]]
            receipt = scan_mst.function_receipt(body, start, [], oracle)
            receipt["boundary_evidence"] = region["boundary"]
            receipt["boundary_limit"] = "Inferred code region, not LC_FUNCTION_STARTS or proven complete function; next inferred start bounds it"
            receipt["literal_references"] = [reference for reference in refs if start <= int(reference["instruction_address_hex"], 16) < end]
            for reference in receipt["literal_references"]:
                references.append({**reference, "region_hex": hex(start), "boundary_evidence": region["boundary"]})
            for hit in receipt["dpcd_value_candidates"]:
                census[hit["register_name"]]["events"] += 1
            if receipt["constant_groups"] or receipt["literal_references"]:
                candidates.append(receipt)
    references_by_target = {}
    for reference in references:
        references_by_target.setdefault(reference["target_address_hex"], []).append(reference)
    for literal in literals:
        literal["code_references"] = references_by_target.get(literal["address_hex"], [])
        literal["image_uuid"] = view["uuid"]
    return {"image": view["image"], "uuid": view["uuid"], "layout": view["layout_evidence"],
            "sections": sections, "regions": region_count, "candidates": candidates, "literal_hits": literals,
            "literal_references": references, "constant_table_candidates": tables, "dpcd_value_census": census,
            "coverage_limit": "Declared file-backed executable sections scanned in inferred regions. No trusted function-start or symbol metadata; indirect constants/references and other bundle compartments can remain opaque."}


def detail_region(view, address, oracle, decoder):
    sections = [section for section in view["sections"] if section["flags"] & 0x80000000 and
                section["address"] <= address < section["address"] + section["size"]]
    if len(sections) != 1:
        raise ValueError("Detail address lacks unique executable section")
    section = sections[0]
    matches = [region for region in firmware_regions(section) if region["start"] == address]
    if len(matches) != 1 or matches[0]["end"] - address > 32768:
        raise ValueError("Detail must start at an inferred region within 32 KiB")
    region = matches[0]
    raw = section["raw"][address - section["address"]:region["end"] - section["address"]]
    result = scan_mst.function_receipt(raw, address, [], oracle)
    result.update(image_uuid=view["uuid"], boundary_evidence=region["boundary"],
                  boundary_limit="INFERRED, not declared function metadata; inspect entry/exit/control flow before qualification",
                  instructions=[decoder.decode(address + offset, raw[offset:offset + 4]) for offset in range(0, len(raw), 4)],
                  direct_callers=kernel_image.direct_call_references(section["raw"], section["address"], {address}))
    return result


def parse_devicetree(raw):
    if not 8 <= len(raw) <= 16 * 1024 * 1024:
        raise ValueError("DeviceTree exceeds bounded input size")
    nodes = []
    cursor = 0

    def node(parent, depth):
        nonlocal cursor
        if depth > 64 or len(nodes) >= 8192:
            raise ValueError("Excessive DeviceTree depth/node count")
        begin = cursor
        property_count, child_count = struct.unpack("<II", kernel_image.bounded_slice(raw, cursor, 8))
        cursor += 8
        if not 1 <= property_count <= 4096 or child_count > 4096:
            raise ValueError("Invalid DeviceTree property/child count")
        properties = {}
        for _ in range(property_count):
            name_bytes, size_field = struct.unpack("<32sI", kernel_image.bounded_slice(raw, cursor, 36))
            cursor += 36
            if b"\0" not in name_bytes:
                raise ValueError("Unterminated DeviceTree property name")
            name = name_bytes.split(b"\0", 1)[0].decode("ascii")
            size = size_field & 0x7fffffff
            if not name or name in properties or size > 1024 * 1024:
                raise ValueError("Duplicate/invalid DeviceTree property")
            value = bytes(kernel_image.bounded_slice(raw, cursor, size))
            properties[name] = {"offset": cursor, "size_raw": size_field, "raw": value}
            cursor += (size + 3) & ~3
            if cursor > len(raw):
                raise ValueError("DeviceTree padding extends beyond input")
        if "name" not in properties:
            raise ValueError("DeviceTree node lacks name")
        name = properties["name"]["raw"].rstrip(b"\0").decode("ascii")
        if not name or "/" in name:
            raise ValueError("Invalid DeviceTree node name")
        path = parent + "/" + name
        record = {"path": path, "offset": begin, "properties": properties, "child_count": child_count}
        nodes.append(record)
        for _ in range(child_count):
            node(path, depth + 1)
        record["end_offset"] = cursor
    node("", 0)
    if any(raw[cursor:]):
        raise ValueError("Nonzero data after complete DeviceTree")
    return nodes


def devicetree_evidence(raw):
    nodes = parse_devicetree(raw)
    result = []
    for node in nodes:
        matched_path = bool(re.search(r"dcp|dptx|display|disp[0-9]|dispext|dpin|dpphy|dpxbar|atc-phy", node["path"], re.IGNORECASE))
        identity_path = node["path"] in ("/device-tree", "/device-tree/arm-io")
        selected = {}
        for name, property_value in node["properties"].items():
            value = property_value["raw"]
            relevant_name = re.search(r"compat|firmware|generation|revision|stream|link|chip|board|product|model|target|name|reg$", name, re.IGNORECASE)
            relevant_value = re.search(rb"dcp|dcpext|dptx|display|H17G|j704|t8142", value, re.IGNORECASE)
            if not ((matched_path and relevant_name) or (identity_path and name in ("compatible", "model", "target-type", "product-name") and relevant_value)):
                continue
            decoded = None
            if value.endswith(b"\0") and all(character == 0 or 32 <= character < 127 for character in value):
                decoded = [item.decode("ascii") for item in value.rstrip(b"\0").split(b"\0")]
            selected[name] = {"offset": property_value["offset"], "size_raw": property_value["size_raw"],
                              "bytes": len(value), "sha256": ipsw_dcp.sha256(value), "raw_hex": value.hex() if len(value) <= 1024 else None,
                              "ascii_strings": decoded}
        if selected:
            result.append({"path": node["path"], "offset": node["offset"], "properties": selected})
    return {"total_nodes": len(nodes), "selected_nodes": result,
            "scope": "Offline Apple DeviceTree display-related names/compatibility/firmware fields only; no node executed or loaded"}


def main():
    parser = argparse.ArgumentParser(description="Decode identified public M3B DCP/DeviceTree files offline; no firmware execution.")
    parser.add_argument("--components", type=pathlib.Path, required=True)
    parser.add_argument("--output", type=pathlib.Path, required=True)
    parser.add_argument("--scan", action="store_true")
    parser.add_argument("--detail-address", type=lambda value: int(value, 0), action="append", default=[])
    parser.add_argument("--pointer-slot", type=lambda value: int(value, 0), action="append", default=[])
    args = parser.parse_args()
    if len(args.detail_address) > 48 or len(set(args.detail_address)) != len(args.detail_address) or (args.detail_address and not args.scan):
        parser.error("at most 48 unique detail addresses, requiring --scan")
    if len(args.pointer_slot) > 64 or len(set(args.pointer_slot)) != len(args.pointer_slot) or (args.pointer_slot and not args.scan):
        parser.error("at most 64 unique pointer slots, requiring --scan")
    root = pathlib.Path(__file__).resolve().parents[1] / "artifacts/sources/m3b"
    if not args.components.resolve().is_relative_to(root) or not args.output.resolve().is_relative_to(root) or args.output.exists():
        parser.error("inputs/output must be under artifacts/sources/m3b and output must be new")
    extraction_raw = (args.components / "extraction.json").read_bytes()
    extraction = json.loads(extraction_raw)
    if extraction.get("errors") or extraction.get("result") not in ("IDENTIFIED_DCP_AND_DEVICETREE_EXTRACTED", "IDENTIFIED_M4_COMPARISON_DCP_EXTRACTED"):
        raise ValueError("Missing successful component extraction receipt")
    mapping = extraction["mapping"]
    report = {"schema_version": 1, "started_utc": ipsw_dcp.utc_now(), "extraction_sha256": ipsw_dcp.sha256(extraction_raw),
              "mapping": mapping, "images": [], "errors": [], "selector_status": "RETIRED_ON_DAILY_USE_M5",
              "dpcd_gate": "NOT_READY_FOR_DPCD_TEST",
              "requested": {"scan": args.scan, "detail_addresses_hex": [hex(address) for address in args.detail_address],
                            "pointer_slots_hex": [hex(address) for address in args.pointer_slot]},
              "tool_sha256": {name: ipsw_dcp.sha256((pathlib.Path(__file__).parent / name).read_bytes())
                              for name in ("dcp_firmware.py", "ipsw_dcp.py", "scan_mst.py", "kernel_image.py", "dyld_cache.py", "inspect_iodp.py")}}
    args.output.mkdir(parents=True)
    try:
        for member in extraction["members"]:
            member_path = pathlib.PurePosixPath(member["path"])
            source = (args.components / member_path).resolve()
            if member_path.is_absolute() or ".." in member_path.parts or not source.is_relative_to(args.components.resolve()):
                raise ValueError("Component path leaves retained extraction directory")
            if not 0 < source.stat().st_size <= 64 * 1024 * 1024:
                raise ValueError("Retained IM4P exceeds input bound")
            raw = source.read_bytes()
            if ipsw_dcp.sha256(raw) != member["sha256"]:
                raise ValueError("Retained component hash mismatch")
            components = mapping["selected"]["display_components"]
            key = "DeviceTree" if member["path"] == mapping["devicetree_path"] else next(key for key in mapping["normal_dcp_components"] if components[key]["Info"]["Path"] == member["path"])
            decoded, evidence = decode_im4p(raw, components[key])
            evidence.update(component_key=key, path=member["path"])
            destination = args.output / (pathlib.PurePosixPath(member["path"]).name + ".payload")
            with destination.open("xb") as stream:
                stream.write(decoded)
            evidence["decoded_file"] = destination.name
            if key == "DeviceTree":
                evidence["devicetree"] = devicetree_evidence(decoded)
            else:
                evidence["payload_magic_hex"] = decoded[:32].hex()
                if decoded.startswith(b"\xcf\xfa\xed\xfe"):
                    header, commands = kernel_image.macho_commands(decoded)
                    evidence["macho_header"] = header
                    evidence["commands"] = [{"command_hex": hex(command), "offset": offset, "size": len(record)} for command, offset, record in commands]
                    evidence["sections"] = kernel_image.macho_sections(decoded, 0)
                if args.scan:
                    view = runtime_view(decoded)
                    oracle_file = pathlib.Path(__file__).resolve().parents[1] / "docs/research/mst-source-signatures.json"
                    oracle, oracle_hash = scan_mst.load_oracle(oracle_file)
                    report["oracle_sha256"] = oracle_hash
                    evidence["scan"] = scan_runtime(view, oracle)
                    if args.pointer_slot:
                        pointers = FirmwarePointers(view)
                        evidence["pointer_slots"] = [pointers.pointer(address) for address in args.pointer_slot]
                    if args.detail_address:
                        from inspect_iodp import LLVMDisassembler
                        decoder = LLVMDisassembler()
                        try:
                            evidence["details"] = [detail_region(view, address, oracle, decoder) for address in args.detail_address]
                        finally:
                            decoder.close()
                elif not decoded.startswith(b"\xcf\xfa\xed\xfe"):
                    evidence["format"] = "UNRESOLVED_NOT_A_SINGLE_MACHO"
            report["images"].append(evidence)
    except (ValueError, OSError, KeyError) as error:
        report["errors"].append(str(error))
    report["completed_utc"] = ipsw_dcp.utc_now()
    with (args.output / "decoded.json").open("x") as stream:
        json.dump(report, stream, indent=2)
        stream.write("\n")
    print(json.dumps({"output": str(args.output), "images": len(report["images"]), "errors": report["errors"]}))
    if report["errors"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()