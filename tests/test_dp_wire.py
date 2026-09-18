import copy
import hashlib
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tools"))
import dp_aux_decode as aux
import dp_mst_decode as mst
import dp_wire_analyze as wire
import dp_wire_synthetic as synthetic


def packet(raw, kind="request", timestamp=0, direction=None):
    return {"raw_hex": raw, "kind": kind, "timestamp_ns": timestamp,
            "direction": direction or ("source_to_sink" if kind == "request" else "sink_to_source"),
            "direction_basis": "synthetic_fixture", "loss_state": "none"}


def capture(records):
    return {"schema_version": 1, "capture_id": "synthetic-wire", "evidence_kind": "synthetic",
            "records": records}


class AuxPacketTests(unittest.TestCase):
    def test_native_read(self):
        event = aux.decode_packet(packet("90002100"), "test", 0)
        self.assertEqual((event["aux_command"], event["address"], event["length"]), (9, 0x21, 1))
        self.assertFalse(event["malformed"] or event["truncated"])

    def test_native_write(self):
        event = aux.decode_packet(packet("8001110007"), "test", 0)
        self.assertEqual(event["data_hex"], "07")

    def test_i2c_mot_read(self):
        event = aux.decode_packet(packet("5000500f"), "test", 0)
        self.assertEqual((event["aux_type"], event["address"], event["length"], event["mot"]),
                         ("i2c", 0x50, 16, True))

    def test_address_only(self):
        self.assertTrue(aux.decode_packet(packet("000050"), "test", 0)["address_only"])

    def test_reply_nibbles(self):
        for raw, native, i2c in (("00ff", "ACK", "ACK"), ("10", "NACK", "ACK"),
                                 ("20", "DEFER", "ACK"), ("40", "ACK", "NACK"),
                                 ("80", "ACK", "DEFER")):
            status = aux.decode_packet(packet(raw, "reply"), "test", 0)["reply_status"]
            self.assertEqual((status["native"], status["i2c"]), (native, i2c))

    def test_reserved_length(self):
        self.assertTrue(aux.decode_packet(packet("90002110"), "test", 0)["malformed"])

    def test_truncated_write(self):
        self.assertTrue(aux.decode_packet(packet("8001110107"), "test", 0)["truncated"])

    def test_excess_read_bytes(self):
        self.assertTrue(aux.decode_packet(packet("9000210001"), "test", 0)["malformed"])

    def test_ambiguous_direction_stays_unknown(self):
        record = packet("90002100", direction="unknown")
        event = aux.decode_packet(record, "test", 0)
        self.assertEqual(event["direction_confidence"], "unknown")

    def test_direction_requires_basis(self):
        record = packet("90002100")
        record.pop("direction_basis")
        with self.assertRaises(ValueError):
            aux.decode_packet(record, "test", 0)

    def test_unknown_packet_preserves_raw(self):
        event = aux.decode_packet(packet("eedd", "unknown", direction="unknown"), "test", 0)
        self.assertEqual(event["raw_hex"], "eedd")
        self.assertIsNone(event["aux_command"])

    def test_request_reply_reconstruction(self):
        result = aux.decode_capture(capture([packet("90002100"), packet("0001", "reply", 1000)]))
        self.assertTrue(result["transactions"][0]["accepted"])

    def test_missing_reply_not_invented(self):
        result = aux.decode_capture(capture([packet("90002100")]))
        self.assertIsNone(result["transactions"][0]["reply"])

    def test_wrong_reply_size(self):
        result = aux.decode_capture(capture([packet("90002100"), packet("00", "reply", 1000)]))
        self.assertFalse(result["transactions"][0]["complete"])

    def test_loss_breaks_pairing(self):
        lost = {"kind": "loss", "timestamp_ns": 500, "loss_state": "lost"}
        result = aux.decode_capture(capture([packet("90002100"), lost, packet("0001", "reply", 1000)]))
        self.assertFalse(any(item["accepted"] for item in result["transactions"]))

    def test_no_automatic_direction_alternation(self):
        records = [packet("90002100", direction="unknown"), packet("0001", "reply", 1000, "unknown")]
        self.assertFalse(aux.decode_capture(capture(records))["transactions"][0]["complete"])

    def test_raw_extensions_preserved(self):
        record = packet("90002100")
        record["vendor_extension"] = {"opaque": 42}
        before = copy.deepcopy(record)
        self.assertEqual(aux.decode_packet(record, "test", 0)["raw_record"], before)
        self.assertEqual(record, before)

    def test_bad_metadata(self):
        for key, value in (("timestamp_ns", -1), ("timestamp_ns", True), ("raw_hex", "zz"),
                           ("loss_state", "fine"), ("truncated", "false")):
            record = packet("90002100")
            record[key] = value
            with self.assertRaises(ValueError):
                aux.decode_packet(record, "test", 0)


def chunk(body, channel="down_request", sequence=0, start=True, end=True, rad=b""):
    lct = 1 if not rad else 2
    header = bytearray([(lct << 4) | (lct - 1)]) + rad
    header.extend([len(body) + 1, (0x80 if start else 0) | (0x40 if end else 0) | (sequence << 4)])
    header[-1] |= mst.crc(header, 4, 0x13, len(header) * 8 - 4)
    return bytes(header) + body + bytes([mst.crc(body, 8, 0xd5)])


def link_reply(count=2):
    return b"\x01" + bytes(range(16)) + bytes([count]) + b"".join(
        bytes([0x30 | port, 0x40, 0x14]) + bytes([port]) * 16 + b"\x11"
        for port in range(1, count + 1))


class MstTests(unittest.TestCase):
    def test_link_address(self):
        body = mst.decode_body(link_reply(), "down_reply")
        self.assertEqual([port["port"] for port in body["ports"]], [1, 2])
        self.assertTrue(all(port["ddps"] for port in body["ports"]))
        self.assertEqual(body["branch_guid"], bytes(range(16)).hex())

    def test_connection_notification(self):
        body = mst.decode_body(b"\x02\x20" + bytes(range(16)) + b"\x33", "up_request")
        self.assertEqual((body["port"], body["peer_type"], body["ddps"]), (2, 3, True))

    def test_resource_reply(self):
        body = mst.decode_body(bytes.fromhex("102104000300"), "down_reply")
        self.assertEqual((body["port"], body["full_pbn"], body["available_pbn"]), (2, 1024, 768))

    def test_allocation_request_and_reply(self):
        for channel, raw in (("down_request", "1120050200"), ("down_reply", "1120050200")):
            body = mst.decode_body(bytes.fromhex(raw), channel)
            self.assertEqual((body["port"], body["payload_id"], body["pbn"]), (2, 5, 512))
            self.assertIsNone(body["slot_count"])

    def test_query_reply_has_no_vcpi(self):
        body = mst.decode_body(bytes.fromhex("12200200"), "down_reply")
        self.assertEqual(body["pbn"], 512)
        self.assertIsNone(body["payload_id"])

    def test_clear_payload(self):
        self.assertEqual(mst.decode_body(b"\x14", "down_request")["message_type"], "CLEAR_PAYLOAD_ID_TABLE")

    def test_remote_dpcd(self):
        read = mst.decode_body(bytes.fromhex("2020002101"), "down_request")
        write = mst.decode_body(bytes.fromhex("212001110107"), "down_request")
        self.assertEqual((read["port"], read["address"], read["length"]), (2, 0x21, 1))
        self.assertEqual(write["data_hex"], "07")

    def test_remote_i2c(self):
        read = mst.decode_body(bytes.fromhex("2221500100105080"), "down_request")
        self.assertEqual((read["port"], read["i2c_device"], read["length"]), (2, 0x50, 128))
        self.assertEqual(read["preceding_i2c"][0]["data_hex"], "00")
        write = mst.decode_body(bytes.fromhex("2320500100"), "down_request")
        self.assertEqual(write["data_hex"], "00")

    def test_power_messages(self):
        for opcode in (0x24, 0x25):
            self.assertEqual(mst.decode_body(bytes([opcode, 0x20]), "down_request")["port"], 2)

    def test_crc_failure(self):
        raw = bytearray(chunk(b"\x01"))
        raw[-1] ^= 1
        decoded = mst.decode_chunk(raw, "down_request", "none")
        self.assertTrue(decoded["malformed"])
        self.assertFalse(decoded["body_crc_ok"])

    def test_header_crc(self):
        raw = bytearray(chunk(b"\x01"))
        raw[2] ^= 1
        self.assertFalse(mst.decode_chunk(raw, "down_request", "none")["header_crc_ok"])

    def test_unknown_opcode(self):
        body = mst.decode_body(bytes.fromhex("77aabb"), "down_request")
        self.assertTrue(body["unknown"])
        self.assertEqual(body["raw_body"], "77aabb")

    def test_truncated_body(self):
        self.assertTrue(mst.decode_body(b"\x11\x20", "down_request")["truncated"])

    def test_chunk_reassembly(self):
        raw = link_reply()
        chunks = [mst.decode_chunk(chunk(raw[:25], end=False), "down_reply", "none"),
                  mst.decode_chunk(chunk(raw[25:], start=False), "down_reply", "none")]
        message = mst.assemble(chunks)[0]
        self.assertTrue(message["complete"])
        self.assertEqual(message["raw_body"], raw.hex())

    def test_sequence_mismatch(self):
        chunks = [mst.decode_chunk(chunk(b"\x01", end=False), "down_request", "none"),
                  mst.decode_chunk(chunk(b"", start=False, sequence=1), "down_request", "none")]
        self.assertTrue(all(not item["complete"] for item in mst.assemble(chunks)))

    def test_partial_sideband(self):
        message = mst.assemble([mst.decode_chunk(chunk(b"\x01", end=False), "down_request", "none")])[0]
        self.assertTrue(message["truncated"])

    def test_bad_packet_then_valid_retransmission(self):
        raw = bytearray(chunk(b"\x01")); raw[-1] ^= 1
        chunks = [mst.decode_chunk(raw, "down_request", "none"),
                  mst.decode_chunk(chunk(b"\x01"), "down_request", "none")]
        messages = mst.assemble(chunks)
        self.assertFalse(messages[0]["complete"])
        self.assertTrue(messages[1]["complete"])

    def test_capture_loss_during_message(self):
        chunks = [mst.decode_chunk(chunk(b"\x01", end=False), "down_request", "none"),
                  mst.decode_chunk(b"", "down_request", "lost"),
                  mst.decode_chunk(chunk(b"", start=False), "down_request", "none")]
        self.assertTrue(all(not item["complete"] for item in mst.assemble(chunks)))


def waveform(raw, oversample=10, half_period=500, kind="request"):
    bits = "".join(f"{value:08b}" for value in bytes.fromhex(raw))
    symbols = "01" * 16 + "11110000" + "".join("10" if bit == "1" else "01" for bit in bits) + "11110000"
    record = packet(raw, kind)
    record.pop("raw_hex")
    record.update(representation="digital_samples", sample_period_ns=half_period // oversample,
                  samples=[int(symbol) for symbol in symbols for unused in range(oversample)])
    return record


class WaveformTests(unittest.TestCase):
    def test_sampled_request_timing_recovery(self):
        result = aux.decode_capture(capture([waveform("90002100")]))
        self.assertEqual(result["events"][0]["request_raw"], "90002100")
        self.assertEqual(result["events"][0]["raw_record"]["recovered_half_period_ns"], 500)

    def test_sampled_reply(self):
        result = aux.decode_capture(capture([waveform("0001", kind="reply")]))
        self.assertEqual(result["events"][0]["reply_raw"], "0001")

    def test_ideal_symbols(self):
        record = waveform("8001110001", oversample=1)
        record["representation"] = "ideal_symbols"
        record["symbols"] = record.pop("samples")
        self.assertEqual(aux.decode_capture(capture([record]))["events"][0]["request_raw"], "8001110001")

    def test_clock_rate_range(self):
        for half_period in (420, 500, 620):
            result = aux.decode_capture(capture([waveform("90002100", half_period=half_period)]))
            self.assertEqual(result["events"][0]["address"], 0x21)

    def test_waveform_direction_not_invented(self):
        record = waveform("90002100")
        record["direction"] = "unknown"
        self.assertEqual(aux.decode_capture(capture([record]))["events"][0]["direction"], "unknown")

    def test_missing_stop(self):
        record = waveform("90002100")
        record["samples"] = record["samples"][:-80]
        self.assertTrue(aux.decode_capture(capture([record]))["events"][0]["truncated"])

    def test_malformed_symbol(self):
        record = waveform("90002100")
        record["samples"][400:420] = [1] * 20
        self.assertTrue(aux.decode_capture(capture([record]))["events"][0]["malformed"])

    def test_no_sync_is_not_empty_success(self):
        record = waveform("90002100")
        record["samples"] = [0, 1] * 20
        self.assertTrue(aux.decode_capture(capture([record]))["events"][0]["truncated"])

    def test_raw_waveform_kept(self):
        record = waveform("90002100")
        self.assertEqual(aux.decode_capture(capture([record]))["raw_records"], [record])

    def test_slow_sampling_rejected(self):
        record = waveform("90002100")
        record["sample_period_ns"] = 200
        with self.assertRaises(ValueError):
            aux.decode_capture(capture([record]))

    def test_mixed_origin_rejected(self):
        record = packet("90002100")
        record["evidence_kind"] = "hardware"
        with self.assertRaises(ValueError):
            aux.decode_capture(capture([record]))

    def test_late_reply_not_paired(self):
        result = aux.decode_capture(capture([packet("90002100"), packet("0001", "reply", 2000000)]))
        self.assertFalse(result["transactions"][0]["complete"])


class WireScenarioTests(unittest.TestCase):
    def analyze(self, name):
        return wire.analyze(synthetic.scenario(name))["analysis"]

    def test_scenario_a(self):
        result = self.analyze("A")
        self.assertEqual(result["completeness"], "COMPLETE_FOR_INTERVAL")
        self.assertEqual(result["gates"]["W1.2"]["result"], "MST_ENABLE_ESTABLISHED")
        self.assertEqual(result["gates"]["W1.4"]["topologies"][0]["peer_count"], 2)
        self.assertEqual(result["gates"]["W1.5"]["edid_probed_path_count"], 2)
        self.assertTrue(result["gates"]["W1.7"]["only_one_payload_established"])

    def test_scenario_b(self):
        result = self.analyze("B")
        self.assertEqual(result["gates"]["W1.7"]["observed_payload_ids"], [1, 2])
        self.assertEqual(result["gates"]["W1.7"]["exclusive_max_concurrent_ids"], 2)
        self.assertTrue(result["gates"]["W1.8"]["completion_observed"])
        self.assertFalse(result["real_source_ownership_established"])

    def test_scenario_c(self):
        result = self.analyze("C")
        self.assertEqual(result["gates"]["W1.2"]["result"], "MST_ENABLE_NOT_OBSERVED_IN_COMPLETE_CAPTURE")

    def test_scenario_d(self):
        self.assertEqual(self.analyze("D")["gates"]["W1.4"]["topologies"][0]["peer_count"], 1)

    def test_scenario_e(self):
        result = self.analyze("E")
        self.assertEqual(result["gates"]["W1.4"]["topologies"][0]["peer_count"], 2)
        self.assertEqual(result["gates"]["W1.5"]["edid_probed_path_count"], 1)

    def test_scenario_f_no_one_payload_conclusion(self):
        result = self.analyze("F")
        self.assertEqual(result["completeness"], "CAPTURE_INCOMPLETE")
        self.assertFalse(result["gates"]["W1.7"]["only_one_payload_established"])
        self.assertIsNone(result["gates"]["W1.7"]["exclusive_max_concurrent_ids"])

    def test_scenario_g_retransmission_keeps_error(self):
        result = self.analyze("G")
        self.assertEqual(result["gates"]["W1.4"]["topologies"][0]["peer_count"], 2)
        self.assertEqual(result["completeness"], "CAPTURE_INCOMPLETE")
        self.assertGreater(result["gates"]["W1.3"]["rejected_or_partial_messages"], 0)

    def test_scenario_h_ambiguity(self):
        result = self.analyze("H")
        self.assertEqual(result["gates"]["W1.2"]["result"], "MST_ENABLE_UNRESOLVED")
        self.assertFalse(result["gates"]["W1.7"]["only_one_payload_established"])

    def test_negative_forbidden_for_manifest_loss(self):
        value = synthetic.scenario("C")
        value["loss_intervals"] = [{"start_ns": 0, "end_ns": 10}]
        self.assertEqual(wire.analyze(value)["analysis"]["gates"]["W1.2"]["result"], "MST_ENABLE_UNRESOLVED")

    def test_negative_forbidden_for_late_start(self):
        value = synthetic.scenario("C")
        value["coverage"]["armed_before_attach"] = False
        self.assertEqual(wire.analyze(value)["analysis"]["gates"]["W1.2"]["result"], "MST_ENABLE_UNRESOLVED")

    def test_unknown_initial_allocations_not_exclusive(self):
        value = synthetic.scenario("A")
        value["coverage"].pop("initial_payload_table_empty")
        self.assertFalse(wire.analyze(value)["analysis"]["gates"]["W1.7"]["only_one_payload_established"])

    def test_every_gate_has_completeness(self):
        for name in "ABCDEFGH":
            result = self.analyze(name)
            self.assertEqual(list(result["gates"]), [f"W1.{number}" for number in range(1, 10)])
            self.assertTrue(all(gate["completeness"] == result["completeness"] for gate in result["gates"].values()))

    def test_deterministic_scenarios(self):
        for name in "ABCDEFGH":
            self.assertEqual(wire.json_bytes(synthetic.scenario(name)), wire.json_bytes(synthetic.scenario(name)))

    def test_bundle_raw_and_hashes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = pathlib.Path(temporary).resolve()
            source = root / "input.json"
            original = wire.json_bytes(synthetic.scenario("A"))
            source.write_bytes(original)
            output = root / "capture"
            wire.write_bundle(source, output, "synthetic-test-commit")
            self.assertEqual((output / "raw/capture.json").read_bytes(), original)
            for name, checksum in json.loads((output / "hashes.json").read_bytes()).items():
                self.assertEqual(hashlib.sha256((output / name).read_bytes()).hexdigest(), checksum)
            with self.assertRaises(ValueError):
                wire.write_bundle(source, output)

    def test_cli_scenarios_and_bundle_refusal(self):
        tools = pathlib.Path(__file__).resolve().parents[1] / "tools"
        with tempfile.TemporaryDirectory() as temporary:
            root = pathlib.Path(temporary).resolve()
            for name in "ABCDEFGH":
                with self.subTest(scenario=name):
                    source = root / (name + ".json")
                    output = root / (name + "-bundle")
                    subprocess.run([sys.executable, str(tools / "dp_wire_synthetic.py"), name,
                                    "--output", str(source)], check=True, capture_output=True)
                    for decoder in ("dp_aux_decode.py", "dp_mst_decode.py"):
                        result = subprocess.run([sys.executable, str(tools / decoder), str(source)],
                                                check=True, capture_output=True)
                        self.assertEqual(json.loads(result.stdout)["evidence_kind"], "synthetic")
                    command = [sys.executable, str(tools / "dp_wire_analyze.py"), str(source),
                               "--bundle", str(output), "--decoder-commit", "0" * 40]
                    result = subprocess.run(command, check=True, capture_output=True)
                    self.assertFalse(json.loads(result.stdout)["hardware_authorized"])
                    manifest = json.loads((output / "manifest.json").read_bytes())
                    self.assertEqual(manifest["physical_link_id"], "synthetic-link-0")
                    self.assertEqual(manifest["interval"], synthetic.scenario(name)["interval"])
                    self.assertEqual((output / "raw/capture.json").read_bytes(), source.read_bytes())
                    hashes = (output / "hashes.json").read_bytes()
                    self.assertEqual(subprocess.run(command, capture_output=True).returncode, 2)
                    self.assertEqual((output / "hashes.json").read_bytes(), hashes)

    def test_counter_binding_stays_unresolved(self):
        self.assertEqual(self.analyze("B")["gates"]["W1.9"]["result"], "SOFTWARE_COUNTER_BINDING_UNRESOLVED")


class WireIntegrityTests(unittest.TestCase):
    def test_manifest_gap_does_not_invent_concurrency(self):
        value = synthetic.scenario("B")
        first = wire.analyze(value)["analysis"]["gates"]["W1.7"]["accepted"][0]
        gap = value["records"][first["reply_sequence"]]["timestamp_ns"] + 1
        value["loss_intervals"] = [{"start_ns": gap, "end_ns": gap}]
        result = wire.analyze(value)["analysis"]["gates"]["W1.7"]
        self.assertEqual(result["observed_payload_ids"], [1, 2])
        self.assertEqual(result["observed_max_concurrent_ids"], 1)
        self.assertIsNone(result["exclusive_max_concurrent_ids"])

    def test_slot_rules_require_observed_coding(self):
        value = synthetic.scenario("B")
        value["records"] = value["records"][2:]
        result = wire.analyze(value)["analysis"]["gates"]
        self.assertTrue(all(not slot["qualified"] for slot in result["W1.7"]["slots"]))
        self.assertIsNone(result["W1.8"]["completion_observed"])

    def test_unmatched_local_payload_blocks_exclusivity(self):
        value = synthetic.scenario("A")
        slot = next(record for record in value["records"] if record["raw_hex"].startswith("8001c0"))
        slot["raw_hex"] = "8001c00202010a"
        result = wire.analyze(value)["analysis"]["gates"]["W1.7"]
        self.assertFalse(result["only_one_payload_established"])
        self.assertIn("unmatched_local_payload_id", result["state_problems"])

    def test_query_conflict_blocks_exclusivity(self):
        value = synthetic.scenario("A")
        trace = synthetic.Trace()
        trace.records = value["records"]
        trace.timestamp = value["interval"]["end_ns"]
        trace.exchange(bytes.fromhex("122002"), bytes.fromhex("12200100"))
        value["interval"]["end_ns"] = trace.timestamp
        result = wire.analyze(value)["analysis"]["gates"]["W1.7"]
        self.assertEqual(result["observed_payload_ids"], [1, 2])
        self.assertFalse(result["only_one_payload_established"])
        self.assertIn("payload_query_conflicts_with_history", result["state_problems"])

    def test_resource_replies_are_independent_gate_evidence(self):
        result = wire.analyze(synthetic.scenario("A"))["analysis"]["gates"]["W1.6"]
        self.assertEqual([reply["available_pbn"] for reply in result["accepted_resources"]], [1024, 1024])

    def test_allocation_pbn_mismatch_is_not_accepted(self):
        trace = synthetic.Trace()
        trace.exchange(bytes.fromhex("1110010100"), bytes.fromhex("1110010080"))
        sideband = mst.from_aux(aux.decode_capture(capture(trace.records)))
        exchanges, unused = wire.qualify_messages(sideband["messages"])
        self.assertEqual(len(exchanges), 1)
        self.assertFalse(exchanges[0]["accepted"])

    def test_overflow_json_number_rejected(self):
        for number in (b"1e999", b"-1e999", b"Infinity", b"-Infinity"):
            with self.subTest(number=number), self.assertRaises(ValueError):
                aux.parse_capture(b'{"extension":' + number + b'}')

    def test_unhashable_metadata_rejected(self):
        for field in ("direction", "kind", "loss_state", "waveform_errors"):
            value = packet("90002100")
            value[field] = {}
            with self.subTest(field=field), self.assertRaises(ValueError):
                aux.decode_packet(value, "test", 0)

    def test_ideal_symbols_cannot_claim_hardware(self):
        value = capture([{"representation": "ideal_symbols", "symbols": [0, 1],
                          "timestamp_ns": 0, "sample_period_ns": 500}])
        value["evidence_kind"] = "hardware"
        with self.assertRaises(ValueError):
            aux.decode_capture(value)

    def test_ambiguous_capture_does_not_invent_loss(self):
        messages = wire.analyze(synthetic.scenario("H"))["mst"]["messages"]
        self.assertTrue(messages)
        self.assertTrue(all(message["loss_state"] == "unknown" for message in messages))

    def test_manifest_gap_breaks_aux_pairing(self):
        value = capture([packet("90002100"), packet("0001", "reply", 1000)])
        value["loss_intervals"] = [{"start_ns": 400, "end_ns": 600}]
        before = copy.deepcopy(value)
        decoded = aux.decode_capture(value)
        self.assertFalse(any(item["accepted"] for item in decoded["transactions"]))
        self.assertEqual([event["sequence"] for event in decoded["events"]], [0, 1, 2])
        self.assertEqual(value, before)

    def test_manifest_gap_covers_complete_transaction(self):
        value = capture([packet("90002100", timestamp=100), packet("0001", "reply", 200)])
        value["loss_intervals"] = [{"start_ns": 0, "end_ns": 300}]
        decoded = aux.decode_capture(value)
        self.assertFalse(any(item["accepted"] for item in decoded["transactions"]))
        self.assertTrue(all(event["loss_state"] == "lost" for event in decoded["events"]))

    def test_manifest_gap_breaks_sideband_exchange(self):
        trace = synthetic.Trace()
        trace.sideband(b"\x01")
        gap_start = trace.records[-1]["timestamp_ns"] + 1
        trace.sideband(link_reply(), reply=True)
        value = capture(trace.records)
        baseline, unused = wire.qualify_messages(mst.from_aux(aux.decode_capture(value))["messages"])
        self.assertEqual(len(baseline), 1)
        self.assertTrue(baseline[0]["accepted"])
        value["loss_intervals"] = [{"start_ns": gap_start, "end_ns": gap_start}]
        sideband = mst.from_aux(aux.decode_capture(value))
        exchanges, unpaired = wire.qualify_messages(sideband["messages"])
        self.assertFalse(any(exchange["accepted"] for exchange in exchanges))
        self.assertTrue(unpaired)

    def test_synthetic_cannot_be_promoted(self):
        value = synthetic.scenario("A"); value["evidence_kind"] = "hardware"
        with self.assertRaises(ValueError):
            wire.analyze(value)

    def test_known_loss_is_preserved_in_mst(self):
        result = wire.analyze(synthetic.scenario("F"))
        self.assertTrue(any(message["loss_state"] == "lost" for message in result["mst"]["messages"]))

    def test_mst_events_carry_capture_identity(self):
        result = wire.analyze(synthetic.scenario("A"))
        self.assertTrue(all(message["capture_id"] == "synthetic-A" and message["evidence_kind"] == "synthetic"
                            for message in result["mst"]["messages"]))

    def test_fixed_crc_vectors(self):
        self.assertEqual(mst.crc(b"\x01", 8, 0xd5), 0xd5)
        self.assertEqual(mst.crc(b"\x00", 8, 0xd5), 0)
        self.assertEqual(mst.crc(b"123456789", 8, 0xd5), 0xbc)

    def test_short_native_read_reply_incomplete(self):
        result = aux.decode_capture(capture([packet("90002101"), packet("0001", "reply", 1000)]))
        self.assertFalse(result["transactions"][0]["accepted"])

    def test_native_reply_cannot_have_i2c_status(self):
        result = aux.decode_capture(capture([packet("90002100"), packet("8001", "reply", 1000)]))
        self.assertFalse(result["transactions"][0]["accepted"])

    def test_stale_act_not_completion(self):
        value = synthetic.scenario("B")
        for record in value["records"][-4:]:
            if record["kind"] == "reply":
                record["raw_hex"] = "0003"
        self.assertFalse(wire.analyze(value)["analysis"]["gates"]["W1.8"]["completion_observed"])

    def test_loss_act_unknown(self):
        self.assertIsNone(wire.analyze(synthetic.scenario("F"))["analysis"]["gates"]["W1.8"]["completion_observed"])

    def test_missing_initial_coverage(self):
        value = synthetic.scenario("A")
        value["coverage"] = {}
        self.assertFalse(wire.analyze(value)["analysis"]["gates"]["W1.7"]["only_one_payload_established"])

    def test_unparsed_waveform_not_silent(self):
        record = waveform("90002100")
        record["samples"] += [value for value in (0, 1) * 20 for unused in range(10)]
        result = aux.decode_capture(capture([record]))
        self.assertTrue(any(event["truncated"] for event in result["events"]))

    def test_digital_jitter_recovery(self):
        record = waveform("90002100")
        record["samples"].insert(150, record["samples"][150])
        record["samples"].pop(250)
        self.assertEqual(aux.decode_capture(capture([record]))["events"][0]["request_raw"], "90002100")

    def test_duplicate_json_key(self):
        with self.assertRaises(ValueError):
            aux.parse_capture(b'{"schema_version":1,"schema_version":1}')

    def test_non_finite_json(self):
        with self.assertRaises(ValueError):
            aux.parse_capture(b'{"timestamp":NaN}')

    def test_boolean_version_rejected(self):
        value = capture([]); value["schema_version"] = True
        with self.assertRaises(ValueError):
            aux.decode_capture(value)

    def test_request_direction_conflict(self):
        self.assertTrue(aux.decode_packet(packet("90002100", direction="sink_to_source"), "test", 0)["malformed"])

    def test_oversized_chunk(self):
        with self.assertRaises(ValueError):
            mst.decode_chunk(bytes(513), "down_request")

    def test_incomplete_capture_no_empty_negative(self):
        value = synthetic.scenario("C"); value["records"] = []
        self.assertEqual(wire.analyze(value)["analysis"]["gates"]["W1.2"]["result"], "MST_ENABLE_UNRESOLVED")


if __name__ == "__main__":
    unittest.main()