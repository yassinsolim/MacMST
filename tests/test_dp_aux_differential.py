import pathlib
import copy
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tools"))
import dp_aux_differential as differential


class LegacyAndTopologyTests(unittest.TestCase):
    def test_legacy_original_error_preserved(self):
        self.assertAlmostEqual(differential.legacy.matching_decomposition()[-1]["full_network_error_mv"], 14.210133691040062)

    def test_legacy_perfect_resistor_error_preserved(self):
        self.assertAlmostEqual(differential.legacy.precision_sweep()[-1]["combined_error_mv"], 14.208157935157194)

    def test_criteria_hash_matches_legacy(self):
        value, criteria = differential.design()
        self.assertEqual(criteria["maximum_common_mode_conversion_v_per_v"], 0.005)
        self.assertEqual(criteria["minimum_residual_differential_margin_mv"], 10)
        self.assertFalse(value["construction_released"])

    def test_direct_network_improves_assumed_cm_conversion(self):
        parameters = differential.design()[0]["parameters"]
        result = differential.direct_ac(parameters, 1000000, 0.25, 0.1)
        self.assertLess(result["external_common_mode_gain"], 0.005)
        self.assertFalse(result["component_guarantees_established"])

    def test_direct_comparator_sees_dc_bias(self):
        parameters = differential.design()[0]["parameters"]
        circuit, unused = differential.direct_network(parameters)
        voltage, unused = circuit.solve({"ground": 0, "drivep": 0, "driven": 0,
                                          "biasp": 0.3, "biasn": 3, "power": 3.3})
        self.assertLess(voltage["inputp"] - voltage["inputn"], -2.6)

    def test_high_resistance_attenuator_loses_bandwidth(self):
        example = differential.attenuation_example()
        self.assertGreaterEqual(example["dc_input_ohm"], 100000000)
        self.assertLess(example["received_mv_for_90mv_input"], 0.1)


class ThresholdTests(unittest.TestCase):
    def test_unknown_bounds_cannot_establish_threshold(self):
        result = differential.threshold_interval(None, 0.0015, 0.002, 0.001, 0.001)
        self.assertEqual(result["classification"], "FIXED_THRESHOLD_NOT_ESTABLISHED")

    def test_conditional_threshold_inequality(self):
        result = differential.threshold_interval(0.09, 0.0015, 0.002, 0.001, 0.001)
        self.assertAlmostEqual(result["lower_v"], 0.0055)
        self.assertAlmostEqual(result["upper_v"], 0.0745)
        self.assertFalse(result["component_guarantees_established"])

    def test_empty_interval_rejected(self):
        result = differential.threshold_interval(0.01, 0.01, 0.002, 0.001, 0.001)
        self.assertEqual(result["classification"], "EMPTY_THRESHOLD_INTERVAL")

    def test_two_bit_states(self):
        self.assertEqual([differential.differential_state(*pair) for pair in ((1, 0), (0, 1), (0, 0), (1, 1))],
                         ["POSITIVE", "NEGATIVE", "IDLE", "INVALID"])

    def test_physical_local_ladder_remains_conditional(self):
        example = differential.threshold_reference_example()
        self.assertGreater(example["conditional_minimum_v"], 0.020)
        self.assertLess(example["conditional_maximum_v"], 0.021)
        self.assertIsNone(example["complete_worst_case_bound_v"])
        self.assertFalse(example["construction_released"])


def window_record(raw_hex="90002100", kind="request"):
    binary = differential.legacy.baseline.manchester(raw_hex, 20, 500)
    return {"representation": "differential_window_samples", "samples": [0] * 100 +
            [1 if sample else 2 for sample in binary] + [0] * 100,
            "timestamp_ns": 0, "sample_period_ns": 20, "kind": kind,
            "direction": "source_to_sink" if kind == "request" else "sink_to_source",
            "direction_basis": "synthetic_window_fixture", "loss_state": "none"}


class WindowAdapterTests(unittest.TestCase):
    def capture(self, record):
        return {"schema_version": 1, "capture_id": "window-test", "evidence_kind": "synthetic", "records": [record]}

    def test_positive_negative_reconstruct_packet(self):
        result = differential.adapt_window_capture(self.capture(window_record()))
        events = differential.aux.decode_capture(result)["events"]
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["request_raw"], "90002100")
        self.assertFalse(events[0]["malformed"] or events[0]["truncated"])

    def test_reply_reconstruction(self):
        result = differential.adapt_window_capture(self.capture(window_record("0001", "reply")))
        self.assertEqual(differential.aux.decode_capture(result)["events"][0]["reply_raw"], "0001")

    def test_short_deadband_is_annotated(self):
        record = window_record()
        record["samples"][125] = 0
        result = differential.adapt_window_capture(self.capture(record))
        self.assertTrue(any(item["kind"] == "bounded_opposite_polarity_deadband"
                            for item in result["window_adapter"]["annotations"]))
        self.assertEqual(differential.aux.decode_capture(result)["events"][0]["request_raw"], "90002100")
        self.assertEqual(result["raw_window_records"][0]["samples"][125], 0)

    def test_impossible_dual_assert_cannot_be_filtered(self):
        record = window_record()
        record["samples"][2100] = 3
        result = differential.adapt_window_capture(self.capture(record))
        events = differential.aux.decode_capture(result)["events"]
        self.assertTrue(any("impossible_dual_assertion" in event["errors"] for event in events))
        self.assertFalse(any(event["request_raw"] == "90002100" and not event["malformed"] and
                             not event["truncated"] for event in events))

    def test_short_same_polarity_gap_is_not_filtered(self):
        record = window_record()
        record["samples"][110] = 0
        result = differential.adapt_window_capture(self.capture(record))
        self.assertTrue(any("unexplained_window_gap" in event["errors"]
                            for event in differential.aux.decode_capture(result)["events"]))

    def test_idle_has_no_false_packet(self):
        record = {**window_record(), "samples": [0] * 1000}
        result = differential.adapt_window_capture(self.capture(record))
        self.assertEqual(differential.aux.decode_capture(result)["events"], [])
        self.assertEqual(result["raw_window_records"][0], record)

    def test_idle_cannot_hide_invalid_metadata(self):
        record = {**window_record(), "samples": [0] * 20, "direction": "fabricated"}
        with self.assertRaises(ValueError):
            differential.adapt_window_capture(self.capture(record))

    def test_idle_cannot_promote_synthetic_provenance(self):
        capture = self.capture({**window_record(), "samples": [0] * 20})
        capture["evidence_kind"] = "hardware"
        with self.assertRaises(ValueError):
            differential.adapt_window_capture(capture)

    def test_idle_cannot_mix_evidence_origins(self):
        record = {**window_record(), "samples": [0] * 20, "evidence_kind": "hardware"}
        with self.assertRaises(ValueError):
            differential.adapt_window_capture(self.capture(record))

    def test_idle_unknown_loss_is_not_complete_silence(self):
        record = {**window_record(), "samples": [0] * 20, "loss_state": "unknown"}
        normalized = differential.adapt_window_capture(self.capture(record))
        events = differential.aux.decode_capture(normalized)["events"]
        self.assertEqual(events[0]["loss_state"], "unknown")
        self.assertIn("unknown_window_loss", events[0]["errors"])
        self.assertFalse(normalized["coverage"]["complete"])

    def test_unknown_direction_stays_unknown(self):
        record = {**window_record(), "direction": "unknown", "direction_basis": None, "kind": "unknown"}
        events = differential.aux.decode_capture(differential.adapt_window_capture(self.capture(record)))["events"]
        self.assertEqual(events[0]["direction"], "unknown")
        self.assertEqual(events[0]["kind"], "unknown")

    def test_raw_capture_is_not_mutated(self):
        capture = self.capture(window_record())
        original = copy.deepcopy(capture)
        differential.adapt_window_capture(capture)
        self.assertEqual(capture, original)

    def test_malformed_samples_rejected(self):
        for samples in ([], [True], [4], [-1], [1.0], "12"):
            with self.subTest(samples=samples), self.assertRaises(ValueError):
                differential.adapt_window_record({**window_record(), "samples": samples})

    def test_synthetic_provenance_cannot_become_hardware(self):
        capture = {**self.capture(window_record()), "evidence_kind": "hardware"}
        with self.assertRaises(ValueError):
            differential.adapt_window_capture(capture)

    def test_threshold_boundaries_are_deadband(self):
        self.assertEqual(differential.slice_value(0.020, 0.020), 0)
        self.assertEqual(differential.slice_value(-0.020, 0.020), 0)
        self.assertEqual(differential.slice_value(0.020001, 0.020), 1)
        self.assertEqual(differential.slice_value(-0.020001, 0.020), 2)

    def test_reference_error_changes_actual_threshold(self):
        self.assertEqual(differential.slice_value(0.0205, 0.020, reference_error_v=0.001), 0)
        self.assertEqual(differential.slice_value(0.0205, 0.020, reference_error_v=-0.001), 1)

    def test_overlapping_records_rejected(self):
        capture = self.capture(window_record())
        capture["records"].append(window_record())
        with self.assertRaises(ValueError):
            differential.adapt_window_capture(capture)

    def test_missing_samples_are_loss_not_idle(self):
        capture = self.capture(window_record())
        capture["records"][0]["timestamp_ns"] = 1000
        normalized = differential.adapt_window_capture(capture)
        self.assertEqual(normalized["loss_intervals"][0]["start_ns"], 0)
        self.assertEqual(normalized["loss_intervals"][0]["end_ns"], 1000)

    def test_input_loss_intervals_survive(self):
        capture = self.capture(window_record())
        capture["loss_intervals"] = [{"start_ns": 50000, "end_ns": 50020}]
        result = differential.adapt_window_capture(capture)
        self.assertEqual(result["loss_intervals"], capture["loss_intervals"])
        self.assertTrue(any(event["kind"] == "loss" for event in differential.aux.decode_capture(result)["events"]))


class NumericalReceiverTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.nominal = differential.simulate_case("N1", step_ns=5, retain=False)

    def test_nominal_conditioned_request(self):
        self.assertTrue(self.nominal["packet_recovered"])
        self.assertGreater(self.nominal["residual_margin_mv"], 10)
        self.assertEqual(self.nominal["invalid_samples"], 0)
        self.assertEqual(self.nominal["idle_asserted_samples"], 0)

    def test_nominal_is_not_qualified_part(self):
        self.assertFalse(self.nominal["component_guarantees_established"])
        self.assertGreater(self.nominal["effective_differential_capacitance_pf_per_leg"], 4)

    def test_direct_comparator_cannot_receive_dc_biased_packet(self):
        result, unused = differential.simulate_record(conditioning="direct", step_ns=20, retain=False)
        self.assertFalse(result["packet_recovered"])

    def test_common_mode_only_has_no_false_packet(self):
        result = differential.simulate_case("N12", step_ns=20, retain=False)
        self.assertEqual(result["decoded_events"], [])
        self.assertEqual(result["idle_asserted_samples"], 0)

    def test_idle_deadband_stays_quiet(self):
        result = differential.simulate_case("N11", step_ns=20, retain=False)
        self.assertEqual(result["decoded_events"], [])

    def test_continuous_turnaround_accepts_reply(self):
        result = differential.simulate_case("N10", step_ns=5, retain=False)
        self.assertTrue(result["packet_recovered"] and result["reply_recovered"] and result["transaction_accepted"])
        self.assertTrue(result["continuous_turnaround_state"])

    def test_powered_off_clamp_witness_fails_rail_target(self):
        result = differential.simulate_case("N7", step_ns=20, retain=False)
        self.assertFalse(result["packet_recovered"])
        self.assertGreater(result["maximum_rail_v"], 0.1)

    def test_capacitance_protection_offset_reference_corners(self):
        for case in ("N2", "N3", "N4", "N5", "N6"):
            with self.subTest(case=case):
                result = differential.simulate_case(case, step_ns=5, retain=False)
                self.assertTrue(result["packet_recovered"])
                self.assertGreater(result["residual_margin_mv"], 10)
                self.assertLess(result["common_mode_conversion_bound_v_per_v"], 0.005)

    def test_deterministic_repetition(self):
        self.assertEqual(self.nominal, differential.simulate_case("N1", step_ns=5, retain=False))

    def test_long_request_and_reverse_driven_reply(self):
        for case in ("N8", "N9"):
            with self.subTest(case=case):
                self.assertTrue(differential.simulate_case(case, step_ns=20, retain=False)["packet_recovered"])

    def test_bench_without_tvs_still_fails_input_capacitance(self):
        result, unused = differential.simulate_record(step_ns=20, retain=False,
                                                      extra={"protection_pf": 0, "protection_cross_pf": 0})
        self.assertTrue(result["packet_recovered"])
        self.assertEqual(result["effective_differential_capacitance_pf_per_leg"], 7.5)

    def test_channel_delay_skew_is_not_suppressed(self):
        result, unused = differential.simulate_record(step_ns=5, retain=False,
                                                      extra={"negative_delay_ns": 100})
        self.assertGreater(result["invalid_samples"], 0)
        self.assertTrue(any(event["errors"] for event in result["decoded_events"]))


class PipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.capture, cls.analysis = differential.pipeline_capture("N1", step_ns=20)

    def test_nominal_complete_frozen_pipeline(self):
        self.assertEqual(self.analysis["completeness"], "COMPLETE_FOR_INTERVAL")
        self.assertEqual(self.analysis["gates"]["W1.2"]["result"], "MST_ENABLE_ESTABLISHED")
        self.assertEqual(self.analysis["gates"]["W1.7"]["observed_payload_ids"], [1])
        self.assertTrue(self.capture["acquisition"]["continuous_analog_state"])

    def test_combined_assumed_corner_complete(self):
        unused, analysis = differential.pipeline_capture("N6", step_ns=20)
        self.assertEqual(analysis["completeness"], "COMPLETE_FOR_INTERVAL")

    def test_invalid_state_blocks_pipeline(self):
        capture = copy.deepcopy(self.capture)
        capture["records"][4]["samples"][2100] = 3
        analysis = differential.wire.analyze(differential.adapt_window_capture(capture))["analysis"]
        self.assertEqual(analysis["completeness"], "CAPTURE_INCOMPLETE")

    def test_acquisition_loss_blocks_pipeline(self):
        capture = copy.deepcopy(self.capture)
        capture["loss_intervals"] = [{"start_ns": 1050000, "end_ns": 1051000}]
        analysis = differential.wire.analyze(differential.adapt_window_capture(capture))["analysis"]
        self.assertEqual(analysis["completeness"], "CAPTURE_INCOMPLETE")

    def test_unknown_direction_is_not_inferred(self):
        capture = copy.deepcopy(self.capture)
        for record in capture["records"]:
            record.update(kind="unknown", direction="unknown", direction_basis=None)
        analysis = differential.wire.analyze(differential.adapt_window_capture(capture))["analysis"]
        self.assertEqual(analysis["completeness"], "CAPTURE_INCOMPLETE")

    def test_rate_budget_does_not_assume_sparse_edges(self):
        rates = differential.backend_rates()
        self.assertEqual(rates["packed_raw_total_bytes"], 2250000000)
        self.assertEqual(rates["eight_byte_event_total_bytes"], 7200000000)
        self.assertGreater(rates["eight_byte_event_bytes_per_second"], rates["packed_raw_bytes_per_second"])


class ReviewScopeTests(unittest.TestCase):
    def test_all_original_rows_survive(self):
        review = differential.review_summary()
        self.assertEqual(len(review["rows"]), 30)
        self.assertEqual(sum(row["m5p9_result"] is not None for row in review["rows"]), 22)
        self.assertEqual(review["counts"], {"PASS": 10, "FAIL": 1, "UNRESOLVED": 19})

    def test_backend_and_live_dp_are_not_frontend_blockers(self):
        blockers = differential.review_summary()["frontend_blockers"]
        self.assertTrue({"P8-07", "P8-09", "P8-12", "P8-13"}.isdisjoint(blockers))
        self.assertIn("P10-30", blockers)
        self.assertIn("P8-06", blockers)

    def test_compound_model_construction_item_stays_unresolved(self):
        rows = {row["id"]: row for row in differential.review_summary()["rows"]}
        self.assertEqual(rows["P8-16"]["result"], "UNRESOLVED")
        self.assertEqual(rows["P9-22"]["result"], "UNRESOLVED")
        self.assertEqual(rows["P10-26"]["result"], "PASS")


if __name__ == "__main__":
    unittest.main()