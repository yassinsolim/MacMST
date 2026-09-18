#!/usr/bin/env python3
"""Deterministic synthetic AUX/MST vectors, never an electrical transmitter."""

import argparse
import json
import pathlib

import dp_mst_decode as mst


def frame(body, sequence=0, start=True, end=True):
    header = bytearray([0x10, len(body) + 1,
                        (0x80 if start else 0) | (0x40 if end else 0) | (sequence << 4)])
    header[-1] |= mst.crc(header, 4, 0x13, 20)
    return bytes(header) + body + bytes([mst.crc(body, 8, 0xd5)])


class Trace:
    def __init__(self):
        self.records = []
        self.timestamp = 0
        self.sequence = 0

    def packet(self, raw, kind):
        self.records.append({"timestamp_ns": self.timestamp, "kind": kind, "raw_hex": raw.hex(),
                             "direction": "source_to_sink" if kind == "request" else "sink_to_source",
                             "direction_basis": "synthetic_fixture", "loss_state": "none"})
        self.timestamp += 250000

    def transaction(self, address, data, read=False):
        header = bytes([((9 if read else 8) << 4) | (address >> 16), (address >> 8) & 255, address & 255, len(data) - 1])
        self.packet(header if read else header + data, "request")
        self.packet(b"\x00" + data if read else b"\x00", "reply")

    def sideband(self, body, reply=False, corrupt=False):
        pieces = [body[offset:offset + 32] for offset in range(0, len(body), 32)]
        for index, piece in enumerate(pieces):
            raw = bytearray(frame(piece, self.sequence, index == 0, index == len(pieces) - 1))
            if corrupt:
                raw[-1] ^= 1
            for offset in range(0, len(raw), 16):
                self.transaction((0x1400 if reply else 0x1000) + offset, bytes(raw[offset:offset + 16]), reply)

    def exchange(self, request, reply):
        self.sideband(request)
        self.sideband(reply, True)
        self.sequence ^= 1


def scenario(name):
    if name not in "ABCDEFGH" or len(name) != 1:
        raise ValueError("Unknown scenario")
    trace = Trace()
    trace.transaction(0x108, b"\x01")
    trace.transaction(0x21, b"\x01", True)
    trace.transaction(0x111, b"\x00" if name == "C" else b"\x07")
    if name != "C":
        if name == "G":
            trace.sideband(b"\x01", corrupt=True)
        peers = 1 if name == "D" else 2
        topology = b"\x01" + bytes(range(16)) + bytes([peers])
        for port in range(1, peers + 1):
            topology += bytes([0x30 | port, 0x40, 0x14]) + bytes([port]) * 16 + b"\x11"
        trace.exchange(b"\x01", topology)
        for port in range(1, (1 if name in "DE" else 2) + 1):
            edid = bytearray(128)
            edid[:8] = bytes.fromhex("00ffffffffffff00")
            edid[127] = (-sum(edid)) & 255
            trace.exchange(bytes([0x22, (port << 4) | 1, 0x50, 1, 0, 0x10, 0x50, 128]),
                           bytes([0x22, port, 128]) + edid)
            trace.exchange(bytes([0x10, port << 4]), bytes([0x10, port << 4, 4, 0, 4, 0]))
        allocations = 2 if name == "B" else 1
        for payload in range(1, allocations + 1):
            body = bytes([0x11, payload << 4, payload, 1, 0])
            trace.exchange(body, body)
            trace.transaction(0x1c0, bytes([payload, 1 + (payload - 1) * 10, 10]))
        if name == "F":
            trace.records.append({"kind": "loss", "timestamp_ns": trace.timestamp, "loss_state": "lost", "reason": "allocation_interval_gap"})
            trace.timestamp += 250000
        trace.transaction(0x2c0, b"\x01", True)
        trace.transaction(0x2c0, b"\x03", True)
    if name == "H":
        for record in trace.records:
            record["direction"] = "unknown"
            record["direction_basis"] = None
    return {"schema_version": 1, "capture_id": "synthetic-" + name, "evidence_kind": "synthetic",
            "capture_generation": "synthetic-generation-" + name, "physical_link_id": "synthetic-link-0",
            "interval": {"start_ns": 0, "end_ns": trace.timestamp},
            "coverage": {"complete": True, "armed_before_attach": True, "filters_disabled": True,
                         "initial_payload_table_empty": True, "loss_state": "lost" if name == "F" else "none"},
            "acquisition": {"hardware": "none-synthetic", "firmware": "none", "sample_rate_hz": None,
                            "clock_source": "deterministic_counter", "frontend_revision": "none",
                            "timestamp_resolution_ns": 1, "input_configuration": "framed_raw_bytes"},
            "records": trace.records}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scenario", choices=list("ABCDEFGH"))
    parser.add_argument("--output", type=pathlib.Path)
    arguments = parser.parse_args()
    data = json.dumps(scenario(arguments.scenario), sort_keys=True, indent=2) + "\n"
    if arguments.output is None:
        print(data, end="")
    else:
        if any(path.is_symlink() for path in (arguments.output, *arguments.output.absolute().parents)):
            parser.exit(2, "Output must not use symlinks\n")
        try:
            arguments.output.parent.mkdir(parents=True, exist_ok=True)
            with arguments.output.open("x", encoding="ascii") as stream:
                stream.write(data)
        except OSError as error:
            parser.exit(2, str(error) + "\n")


if __name__ == "__main__":
    main()