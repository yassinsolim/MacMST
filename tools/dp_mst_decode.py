#!/usr/bin/env python3
"""Offline MST sideband reconstruction using the pinned public Linux wire oracle."""

import argparse
import json
import pathlib

import dp_aux_decode as aux


DECODER_VERSION = "macmst-mst-1"
ORACLE = "238650ef6c7c7cca08e032527329424c9fbd70e5"
MESSAGES = {0x01: "LINK_ADDRESS", 0x02: "CONNECTION_STATUS_NOTIFY",
            0x10: "ENUM_PATH_RESOURCES", 0x11: "ALLOCATE_PAYLOAD", 0x12: "QUERY_PAYLOAD",
            0x14: "CLEAR_PAYLOAD_ID_TABLE", 0x20: "REMOTE_DPCD_READ",
            0x21: "REMOTE_DPCD_WRITE", 0x22: "REMOTE_I2C_READ", 0x23: "REMOTE_I2C_WRITE",
            0x24: "POWER_UP_PHY", 0x25: "POWER_DOWN_PHY"}
BUFFERS = {0x1000: "down_request", 0x1200: "up_reply", 0x1400: "down_reply", 0x1600: "up_request"}


def crc(data, width, polynomial, bit_count=None):
    count = len(data) * 8 if bit_count is None else bit_count
    aux.integer(count, "CRC bit count", 0, len(data) * 8)
    value = int.from_bytes(data, "big") >> (len(data) * 8 - count)
    value <<= width
    divisor = (1 << width) | polynomial
    while value.bit_length() > width:
        value ^= divisor << (value.bit_length() - width - 1)
    return value


class BodyReader:
    def __init__(self, raw):
        self.raw = raw
        self.offset = 0

    def take(self, count):
        if self.offset + count > len(self.raw):
            raise EOFError("truncated_body")
        result = self.raw[self.offset:self.offset + count]
        self.offset += count
        return result

    def byte(self):
        return self.take(1)[0]

    def word(self):
        return int.from_bytes(self.take(2), "big")


def decode_body(raw, channel):
    result = {"request_id": None, "message_type": "UNKNOWN", "raw_body": raw.hex(),
              "port": None, "peer_type": None, "branch_guid": None, "payload_id": None,
              "pbn": None, "slot_count": None, "malformed": False, "truncated": False,
              "unknown": False, "errors": []}
    reader = BodyReader(raw)
    try:
        first = reader.byte()
        opcode = first & 0x7f
        reply = channel.endswith("reply")
        result.update(request_id=opcode, message_type=MESSAGES.get(opcode, "UNKNOWN"),
                      reply_type=("NAK" if first & 0x80 else "ACK") if reply else None)
        if not reply and first & 0x80:
            result["errors"].append("reserved_request_bit")
        if reply and first & 0x80:
            result.update(branch_guid=reader.take(16).hex(), nak_reason=reader.byte(), nak_data=reader.byte())
        elif opcode not in MESSAGES:
            result["unknown"] = True
            result["unknown_body"] = reader.take(len(raw) - reader.offset).hex()
        elif reply:
            if opcode == 0x01:
                result["branch_guid"] = reader.take(16).hex()
                count = reader.byte()
                if count & 0xf0:
                    result["errors"].append("reserved_port_count_bits")
                ports = []
                for unused in range(count & 15):
                    descriptor = reader.byte()
                    flags = reader.byte()
                    port = {"port": descriptor & 15, "input": bool(descriptor & 0x80),
                            "peer_type": (descriptor >> 4) & 7, "mcs": bool(flags & 0x80),
                            "ddps": bool(flags & 0x40), "legacy_present": bool(flags & 0x20),
                            "descriptor_raw": descriptor, "flags_raw": flags}
                    if not port["input"]:
                        port.update(dpcd_revision=reader.byte(), peer_guid=reader.take(16).hex())
                        streams = reader.byte()
                        port.update(streams=streams >> 4, stream_sinks=streams & 15)
                    ports.append(port)
                result["ports"] = ports
                if len({port["port"] for port in ports}) != len(ports):
                    result["errors"].append("duplicate_port")
            elif opcode == 0x10:
                descriptor = reader.byte()
                result.update(port=descriptor >> 4, fec_capable=bool(descriptor & 1),
                              full_pbn=reader.word(), available_pbn=reader.word())
            elif opcode == 0x11:
                result.update(port=reader.byte() >> 4, payload_id=reader.byte(), pbn=reader.word())
            elif opcode == 0x12:
                result.update(port=reader.byte() >> 4, pbn=reader.word())
            elif opcode in (0x20, 0x22):
                result["port"] = reader.byte() & 15
                result["data_hex"] = reader.take(reader.byte()).hex()
            elif opcode == 0x21:
                result["port"] = reader.byte() & 15
            elif opcode in (0x24, 0x25):
                result["port"] = reader.byte() >> 4
        else:
            if opcode in (0x10, 0x24, 0x25):
                result["port"] = reader.byte() >> 4
            elif opcode == 0x02:
                result["port"] = reader.byte() >> 4
                result["branch_guid"] = reader.take(16).hex()
                flags = reader.byte()
                result.update(peer_type=flags & 7, input=bool(flags & 8), mcs=bool(flags & 16),
                              ddps=bool(flags & 32), legacy_present=bool(flags & 64), flags_raw=flags)
            elif opcode == 0x11:
                descriptor = reader.byte()
                result.update(port=descriptor >> 4, number_sdp_streams=descriptor & 15,
                              payload_id=reader.byte(), pbn=reader.word())
                sinks = reader.take(((descriptor & 15) + 1) // 2)
                result["sdp_stream_sinks"] = [
                    (sinks[index // 2] >> (0 if index % 2 else 4)) & 15
                    for index in range(descriptor & 15)]
            elif opcode == 0x12:
                result.update(port=reader.byte() >> 4, payload_id=reader.byte())
            elif opcode in (0x20, 0x21):
                descriptor = reader.byte()
                address = ((descriptor & 15) << 16) | reader.word()
                result.update(port=descriptor >> 4, address=address, length=reader.byte())
                if opcode == 0x21:
                    result["data_hex"] = reader.take(result["length"]).hex()
            elif opcode == 0x22:
                descriptor = reader.byte()
                result["port"] = descriptor >> 4
                writes = []
                for unused in range(descriptor & 3):
                    device = reader.byte()
                    data = reader.take(reader.byte())
                    control = reader.byte()
                    writes.append({"i2c_device": device, "data_hex": data.hex(), "control_raw": control})
                result.update(preceding_i2c=writes, i2c_device=reader.byte(), length=reader.byte())
            elif opcode == 0x23:
                result.update(port=reader.byte() >> 4, i2c_device=reader.byte())
                result["data_hex"] = reader.take(reader.byte()).hex()
        if reader.offset != len(raw):
            result["errors"].append("excess_body_bytes")
        if result["payload_id"] is not None and result["payload_id"] > 0x7f:
            result["errors"].append("reserved_payload_id_bit")
    except EOFError:
        result["truncated"] = True
        result["errors"].append("truncated_body")
    result["malformed"] = bool(result["errors"])
    return result


def decode_chunk(raw, channel, loss_state="unknown"):
    if channel not in BUFFERS.values() or len(raw) > 512:
        raise ValueError("Invalid sideband chunk")
    result = {"raw_hex": raw.hex(), "raw_header": "", "raw_body": "", "channel": channel,
              "lct": None, "lcr": None, "rad": None, "sequence_number": None,
              "broadcast": None, "path": None, "somt": False, "eomt": False,
              "header_crc_ok": False, "body_crc_ok": False, "malformed": False,
              "truncated": False, "loss_state": loss_state, "errors": []}
    if not raw:
        result["truncated"] = True
        return result
    lct = raw[0] >> 4
    header_size = 3 + lct // 2
    if len(raw) < header_size:
        result["truncated"] = True
        return result
    control = raw[header_size - 1]
    length = raw[header_size - 2] & 63
    result.update(raw_header=raw[:header_size].hex(), lct=lct, lcr=raw[0] & 15,
                  rad=raw[1:header_size - 2].hex(), broadcast=bool(raw[header_size - 2] & 0x80),
                  path=bool(raw[header_size - 2] & 0x40), somt=bool(control & 0x80),
                  eomt=bool(control & 0x40), sequence_number=(control >> 4) & 1,
                  header_crc_ok=crc(raw[:header_size], 4, 0x13, header_size * 8 - 4) == (control & 15))
    if not lct or not length or control & 0x20 or header_size + length > 48:
        result["errors"].append("invalid_header")
    if not result["broadcast"] and result["lcr"] >= lct:
        result["errors"].append("invalid_route_count")
    if len(raw) < header_size + length:
        result["truncated"] = True
    elif length:
        body = raw[header_size:header_size + length - 1]
        result.update(raw_body=body.hex(), body_crc_ok=crc(body, 8, 0xd5) == raw[header_size + length - 1])
        if len(raw) != header_size + length:
            result["errors"].append("excess_chunk_bytes")
    if not result["header_crc_ok"]:
        result["errors"].append("header_crc_failure")
    if not result["truncated"] and not result["body_crc_ok"]:
        result["errors"].append("body_crc_failure")
    result["malformed"] = bool(result["errors"])
    return result


def assemble(chunks):
    messages = []
    pending = {}

    def emit(items, incomplete=False, reason=None):
        first = items[0]
        body = b"".join(bytes.fromhex(item["raw_body"]) for item in items)
        result = decode_body(body, first["channel"])
        result.update(schema_version=1, decoder_version=DECODER_VERSION, oracle_revision=ORACLE,
                      channel=first["channel"], timestamp=first.get("timestamp"),
                      end_sequence=max(item.get("end_sequence", -1) for item in items),
                      raw_header=first["raw_header"], lct=first["lct"], lcr=first["lcr"],
                      rad=first["rad"], sequence_number=first["sequence_number"],
                      broadcast=first["broadcast"], path=first["path"], chunks=items,
                      crc_result=all(item["header_crc_ok"] and item["body_crc_ok"] for item in items),
                      loss_state=("lost" if any(item["loss_state"] == "lost" for item in items) else
                                  "none" if all(item["loss_state"] == "none" for item in items) else "unknown"))
        result["malformed"] |= any(item["malformed"] for item in items)
        result["truncated"] |= incomplete or any(item["truncated"] for item in items)
        if reason:
            result["errors"].append(reason)
        result["complete"] = not (result["malformed"] or result["truncated"] or result["unknown"])
        result["complete"] &= result["crc_result"] and result["loss_state"] == "none"
        messages.append(result)

    for chunk in chunks:
        channel = chunk["channel"]
        key = (channel, chunk["lct"], chunk["rad"], chunk["sequence_number"], chunk["path"], chunk["broadcast"])
        if chunk["malformed"] or chunk["truncated"] or chunk["loss_state"] != "none":
            for pending_key in list(pending):
                if pending_key[0] == channel:
                    emit(pending.pop(pending_key), True, "invalid_chunk_interrupted_message")
            emit([chunk], True, "invalid_chunk")
            continue
        if chunk["somt"]:
            for pending_key in list(pending):
                if pending_key[0] == channel:
                    emit(pending.pop(pending_key), True, "new_start_before_end")
            pending[key] = []
        elif key not in pending:
            emit([chunk], True, "orphan_continuation")
            continue
        pending[key].append(chunk)
        if sum(len(bytes.fromhex(item["raw_body"])) for item in pending[key]) > 256:
            emit(pending.pop(key), True, "message_too_large")
        elif chunk["eomt"]:
            emit(pending.pop(key))
    for items in pending.values():
        emit(items, True, "missing_end")
    return messages


def from_aux(decoded):
    chunks = []
    buffers = {}

    def flush(base, incomplete=True):
        state = buffers.pop(base)
        chunk = decode_chunk(bytes(state["data"]), BUFFERS[base], state["loss_state"])
        chunk.update(timestamp=state["timestamp"], aux_sequences=state["sequences"],
                     end_sequence=max(state["sequences"]))
        chunk["truncated"] |= incomplete
        chunks.append(chunk)

    for transaction in decoded["transactions"]:
        request, reply = transaction["request"], transaction["reply"]
        if not transaction["complete"]:
            for base in list(buffers):
                flush(base)
            loss = "lost" if any(item and item["loss_state"] == "lost" for item in (request, reply)) else "unknown"
            for base, channel in BUFFERS.items():
                gap = decode_chunk(b"", channel, loss)
                item = request or reply
                gap.update(timestamp=item["timestamp"], aux_sequences=[item["sequence"]], end_sequence=item["sequence"])
                chunks.append(gap)
            continue
        if not transaction["accepted"] or not request or request.get("aux_type") != "native":
            continue
        address = request["address"]
        base = next((candidate for candidate in BUFFERS if candidate <= address < candidate + 0x200), None)
        if base is None:
            continue
        command = request["aux_command"]
        if ((base in (0x1000, 0x1200) and command != 8) or
                (base in (0x1400, 0x1600) and command != 9)):
            continue
        data = bytes.fromhex((request if command == 8 else reply)["data_hex"])
        offset = address - base
        if offset == 0 and base in buffers:
            flush(base)
        if base not in buffers:
            buffers[base] = {"data": bytearray(), "timestamp": request["timestamp"], "sequences": [],
                             "loss_state": "none" if offset == 0 else "unknown"}
        state = buffers[base]
        state["sequences"].extend([request["sequence"], reply["sequence"]])
        if offset != len(state["data"]):
            state["loss_state"] = "unknown"
        state["data"].extend(data)
        raw = state["data"]
        if raw:
            header_size = 3 + (raw[0] >> 4) // 2
            if len(raw) >= header_size:
                total = header_size + (raw[header_size - 2] & 63)
                if len(raw) >= total:
                    if command == 9:
                        state["data"] = raw[:total]
                    flush(base, False)
    for base in list(buffers):
        flush(base)
    messages = assemble(chunks)
    for message in messages:
        message.update(capture_id=decoded["capture_id"], evidence_kind=decoded["evidence_kind"])
    return {"schema_version": 1, "capture_id": decoded["capture_id"],
            "evidence_kind": decoded["evidence_kind"], "decoder_version": DECODER_VERSION,
            "chunks": chunks, "messages": messages}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("capture", type=pathlib.Path)
    arguments = parser.parse_args()
    try:
        print(json.dumps(from_aux(aux.decode_capture(aux.load_capture(arguments.capture))), sort_keys=True))
    except (ValueError, OSError) as error:
        parser.exit(2, str(error) + "\n")


if __name__ == "__main__":
    main()