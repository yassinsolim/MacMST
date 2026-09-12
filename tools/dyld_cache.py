import hashlib
import pathlib
import struct


def direct_branch_target(instruction, address):
    if len(instruction) != 4:
        raise ValueError("A64 instruction must be four bytes")
    word = int.from_bytes(instruction, "little")
    if word & 0x7c000000 != 0x14000000:
        return None
    immediate = word & 0x03ffffff
    if immediate & 0x02000000:
        immediate -= 0x04000000
    return address + immediate * 4


def cache_mappings(data, file_size):
    if len(data) < 24 or data[:16].rstrip(b"\0") not in (b"dyld_v1  arm64e", b"dyld_v1   arm64e"):
        raise ValueError("Unsupported or truncated arm64e cache header")
    table_offset, count = struct.unpack_from("<II", data, 16)
    if count > 64 or table_offset < 24 or table_offset + count * 32 > len(data):
        raise ValueError("Invalid cache mapping table bounds")
    mappings = []
    for index in range(count):
        address, size, offset, maximum, initial = struct.unpack_from("<QQQII", data, table_offset + index * 32)
        if size == 0 or address + size > 1 << 64 or offset + size > file_size:
            raise ValueError("Invalid cache mapping range")
        mappings.append({"address": address, "size": size, "file_offset": offset,
                         "maximum_protection": maximum, "initial_protection": initial})
    return mappings


def file_location(mappings, address, size):
    if address < 0 or size <= 0 or address + size > 1 << 64:
        raise ValueError("Invalid virtual address range")
    matches = [mapping for mapping in mappings
               if mapping["address"] <= address and address + size <= mapping["address"] + mapping["size"]]
    if len(matches) != 1:
        raise ValueError("Virtual address does not map uniquely to a cache file")
    mapping = matches[0]
    return mapping, mapping["file_offset"] + address - mapping["address"]


def decode_slide_pointer5(word, value_add):
    if not 0 <= word < 1 << 64 or not 0 <= value_add < 1 << 64:
        raise ValueError("Invalid encoded pointer or base")
    authenticated = bool(word >> 63)
    target = value_add + (word & ((1 << 34) - 1))
    if target >= 1 << 56:
        raise ValueError("Decoded cache pointer exceeds supported address range")
    result = {"authenticated": authenticated, "next_bytes": ((word >> 52) & 0x7ff) * 8}
    if authenticated:
        result.update(diversity=(word >> 34) & 0xffff, address_diversity=bool((word >> 50) & 1),
                      key="DA" if (word >> 51) & 1 else "IA")
    else:
        if (word >> 42) & 0x3ff:
            raise ValueError("Reserved regular-pointer bits are not zero")
        target |= ((word >> 34) & 0xff) << 56
    result["target"] = target
    return result


def verify_chain5(page, start, requested_offset, value_add):
    if start == 0xffff:
        raise ValueError("Page has no fixup chain")
    offset = start
    hops = 0
    while True:
        if offset % 8 != 0 or offset + 8 > len(page):
            raise ValueError("Fixup chain points outside its page or is unaligned")
        word = struct.unpack_from("<Q", page, offset)[0]
        decoded = decode_slide_pointer5(word, value_add)
        if offset == requested_offset:
            return word, decoded, hops
        if decoded["next_bytes"] == 0 or offset > requested_offset:
            raise ValueError("Requested slot is not a member of the fixup chain")
        offset += decoded["next_bytes"]
        hops += 1


def adrp_add_target(raw, address, register):
    if len(raw) != 8 or address % 4 or not 0 <= register <= 30:
        raise ValueError("Expected aligned ADRP/ADD instruction pair")
    adrp, add = struct.unpack("<II", raw)
    if (adrp & 0x9f00001f) != 0x90000000 | register or (add & 0xffc003ff) != 0x91000000 | (register << 5) | register:
        raise ValueError("Unsupported ADRP/ADD address calculation")
    immediate = ((adrp >> 5) & 0x7ffff) << 2 | ((adrp >> 29) & 3)
    if immediate & (1 << 20):
        immediate -= 1 << 21
    slot = (address & ~0xfff) + immediate * 4096 + ((add >> 10) & 0xfff)
    if not 0 <= slot < 1 << 64:
        raise ValueError("Invalid ADRP/ADD target")
    return slot


def authenticated_stub_slot(raw, address):
    if len(raw) != 16:
        raise ValueError("Expected four A64 stub instructions")
    load, branch = struct.unpack_from("<II", raw, 8)
    if load != 0xf9400230 or branch != 0xd71f0a11:
        raise ValueError("Unsupported authenticated-stub load or branch")
    slot = adrp_add_target(raw[:8], address, 17)
    if slot % 8:
        raise ValueError("Unaligned authenticated-stub slot")
    return slot


class DyldCache:
    def __init__(self, main_file):
        self.main_file = pathlib.Path(main_file)
        self.mappings = []
        self.components = []
        main_header = self.read_disk(self.main_file, 0, 552)
        if main_header[:16].rstrip(b"\0") != b"dyld_v1  arm64e":
            raise ValueError("Only the inspected arm64e cache format is supported")
        self.shared_base = struct.unpack_from("<Q", main_header, 224)[0]
        offset, count = struct.unpack_from("<II", main_header, 392)
        if not 0 < count <= 64:
            raise ValueError("Unsupported cache component count")
        entries = self.read_disk(self.main_file, offset, count * 56)
        files = [(self.main_file, main_header[88:104])]
        for index in range(count):
            record = entries[index * 56:(index + 1) * 56]
            suffix = record[24:56].split(b"\0", 1)[0].decode("ascii")
            if not suffix.startswith(".") or "/" in suffix or "\\" in suffix or ".." in suffix:
                raise ValueError("Invalid cache component suffix")
            files.append((self.main_file.with_name(self.main_file.name + suffix), record[:16]))
        for file, expected_uuid in files:
            size = file.stat().st_size
            header = self.read_disk(file, 0, min(size, 8192))
            if header[88:104] != expected_uuid:
                raise ValueError("Cache component UUID does not match primary header")
            ordinary = cache_mappings(header, size)
            table, mapping_count = struct.unpack_from("<II", header, 312)
            if mapping_count != len(ordinary) or table < 320:
                raise ValueError("Cache slide mapping table does not match ordinary mappings")
            slide_records = self.read_disk(file, table, mapping_count * 56)
            for index in range(mapping_count):
                address, length, file_offset, slide_offset, slide_size, flags, maximum, initial = struct.unpack_from(
                    "<QQQQQQII", slide_records, index * 56)
                if (address, length, file_offset) != (ordinary[index]["address"], ordinary[index]["size"], ordinary[index]["file_offset"]):
                    raise ValueError("Inconsistent cache mappings")
                if slide_offset + slide_size > size:
                    raise ValueError("Slide metadata extends outside component")
                self.mappings.append({**ordinary[index], "file": file, "uuid_hex": expected_uuid.hex(),
                                      "slide_offset": slide_offset, "slide_size": slide_size, "flags": flags})
            self.components.append({"name": file.name, "uuid_hex": expected_uuid.hex(), "size": size,
                                    "header_sha256": hashlib.sha256(header[:552]).hexdigest()})

    @staticmethod
    def read_disk(file, offset, count):
        if offset < 0 or not 0 < count <= 1024 * 1024 or offset + count > file.stat().st_size:
            raise ValueError("Invalid or excessive static file read")
        with file.open("rb") as stream:
            stream.seek(offset)
            data = stream.read(count)
        if len(data) != count:
            raise ValueError("Truncated static file read")
        return data

    def read(self, address, count):
        mapping, offset = file_location(self.mappings, address, count)
        return self.read_disk(mapping["file"], offset, count)

    def pointer(self, address):
        mapping, offset = file_location(self.mappings, address, 8)
        if mapping["slide_size"] < 24:
            raise ValueError("Pointer has no supported slide metadata")
        header = self.read_disk(mapping["file"], mapping["slide_offset"], 24)
        version, page_size, page_count = struct.unpack_from("<III", header)
        value_add = struct.unpack_from("<Q", header, 16)[0]
        if version != 5 or page_size not in (4096, 16384) or value_add != self.shared_base:
            raise ValueError("Unsupported slide version/page size/base; no guessed pointer decoding")
        page_index, page_offset = divmod(address - mapping["address"], page_size)
        if page_index >= page_count or 24 + page_count * 2 > mapping["slide_size"]:
            raise ValueError("Pointer page is outside slide metadata")
        page_start_raw = self.read_disk(mapping["file"], mapping["slide_offset"] + 24 + page_index * 2, 2)
        start = struct.unpack("<H", page_start_raw)[0]
        page = self.read(mapping["address"] + page_index * page_size, page_size)
        word, decoded, hops = verify_chain5(page, start, page_offset, value_add)
        file_location(self.mappings, decoded["target"], 1)
        return {"slot_address_hex": hex(address), "cache_file": mapping["file"].name,
                "cache_uuid_hex": mapping["uuid_hex"], "file_offset_hex": hex(offset),
                "raw_pointer_hex": f"{word:016x}", "raw_bytes_hex": self.read(address, 8).hex(),
                "slide_version": version, "slide_header_hex": header.hex(), "page_start_raw_hex": page_start_raw.hex(),
                "page_index": page_index, "page_offset": page_offset, "chain_hops": hops,
                "chain_membership_verified": True, "page_sha256": hashlib.sha256(page).hexdigest(),
                **decoded, "target_address_hex": hex(decoded["target"])}