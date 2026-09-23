import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tools"))
import dp_aux_differential as differential
import dp_aux_receiver as receiver


def cap_term(name, typical, maximum=None, verified=False):
    return {"name": name, "coefficient": 1, "typical_pf": typical, "maximum_pf": maximum,
            "maximum_basis": "VERIFIED_FROM_DATASHEET" if verified else "UNKNOWN",
            "covers_required_envelope": verified, "source": "synthetic_test_specification"}


class ElectricalEvidenceTests(unittest.TestCase):
    def test_negative_input_capacitance_is_not_silently_omitted(self):
        parameters = differential.case_parameters("N1")
        parameters.update(input_differential_pf=-2, protection_cross_pf=0)
        with self.assertRaises(ValueError):
            differential.direct_network(parameters)

    def test_missing_receiver_bound_does_not_erase_known_protection_term(self):
        terms = [cap_term("unknown", 1), cap_term("known", 0.2, 0.3, True)]
        self.assertEqual(receiver.capacitance_accounting(terms)["unknown_or_unqualified_terms"], ["unknown"])

    def test_all_required_architectures_are_concrete(self):
        items = receiver.catalog()["candidates"]
        self.assertTrue(set("ABCDE") <= {item["architecture"] for item in items})
        self.assertTrue(all(item["parts"] and item["source"] in receiver.catalog()["sources"] for item in items))

    def test_candidate_budget_includes_protection_and_board(self):
        result = receiver.candidate_budget("B_OPA810_BUFFERED")
        self.assertAlmostEqual(result["representative_pf_per_leg"], 3.4)
        self.assertIsNone(result["guaranteed_maximum_pf_per_leg"])

    def test_discrete_maximum_does_not_fit_complete_budget(self):
        result = receiver.candidate_budget("C_MMBF4416_FOLLOWERS")
        self.assertAlmostEqual(result["representative_pf_per_leg"], 4.9)
        self.assertIsNone(result["guaranteed_maximum_pf_per_leg"])

    def test_no_protection_does_not_supply_receiver_guarantees(self):
        result = receiver.candidate_budget("B_OPA810_BUFFERED", "BENCH_NONE")
        self.assertAlmostEqual(result["representative_pf_per_leg"], 3)
        self.assertEqual(result["loading_gate"], "UNKNOWN")

    def test_all_current_profiles_block_construction(self):
        for item in receiver.catalog()["candidates"]:
            with self.subTest(candidate=item["id"]):
                result = receiver.candidate_gates(item["id"])
                self.assertEqual(result["frontend_gate"], "AUX_FRONTEND_PROTOTYPE_STILL_BLOCKED")
                self.assertFalse(result["hardware_authorized"])

    def test_unknown_candidate_fails_closed(self):
        with self.assertRaises(ValueError):
            receiver.candidate_budget("invented")

    def test_typical_cannot_become_maximum(self):
        result = receiver.capacitance_accounting([cap_term("receiver", 0.45)])
        self.assertEqual(result["representative_pf_per_leg"], 0.45)
        self.assertIsNone(result["guaranteed_maximum_pf_per_leg"])
        self.assertEqual(result["loading_gate"], "UNKNOWN")

    def test_unknown_value_is_not_zero(self):
        result = receiver.capacitance_accounting([cap_term("receiver", None), cap_term("pcb", 0.5)])
        self.assertIsNone(result["representative_pf_per_leg"])

    def test_test_point_is_not_whole_envelope(self):
        term = cap_term("protection", 0.2, 0.27, True)
        term["covers_required_envelope"] = False
        result = receiver.capacitance_accounting([term])
        self.assertEqual(result["sum_of_stated_test_point_maxima_pf"], 0.27)
        self.assertIsNone(result["guaranteed_maximum_pf_per_leg"])

    def test_mutual_capacitance_counted_twice(self):
        term = {**cap_term("mutual", 0.1, 0.14, True), "coefficient": 2}
        result = receiver.capacitance_accounting([term, cap_term("ground", 1, 2, True)])
        self.assertAlmostEqual(result["guaranteed_maximum_pf_per_leg"], 2.28)

    def test_guaranteed_excess_rejected(self):
        result = receiver.capacitance_accounting([cap_term("receiver", 4, 4.1, True)])
        self.assertEqual(result["loading_gate"], "FAIL")

    def test_nonfinite_or_negative_values_rejected(self):
        for value in (-1, float("nan"), float("inf"), True):
            with self.subTest(value=value), self.assertRaises(ValueError):
                receiver.capacitance_accounting([cap_term("bad", value)])

    def test_one_unknown_blocks_build(self):
        gates = dict.fromkeys(receiver.REQUIRED_GATES, "PASS")
        gates["powered_off"] = "UNKNOWN"
        result = receiver.release_gate(gates)
        self.assertEqual(result["frontend_gate"], "AUX_FRONTEND_PROTOTYPE_STILL_BLOCKED")
        self.assertFalse(result["hardware_authorized"])

    def test_electrical_pass_is_not_hardware_authorization(self):
        result = receiver.release_gate(dict.fromkeys(receiver.REQUIRED_GATES, "PASS"))
        self.assertEqual(result["frontend_gate"], "AUX_FRONTEND_PROTOTYPE_BUILD_WARRANTED")
        self.assertFalse(result["hardware_authorized"])
        self.assertEqual(result["w1_gate"], "W1_CAPTURE_SYSTEM_NOT_READY")

    def test_missing_gate_rejected(self):
        with self.assertRaises(ValueError):
            receiver.release_gate({"receive_only": "PASS"})


class PoweredOffTests(unittest.TestCase):
    def test_input_diode_and_feedback_path_is_not_output_isolation(self):
        result = receiver.off_dc("input_feedback_clamped")
        self.assertGreater(result["aux_pin_current_na"]["n"], 100)
        self.assertLess(result["nodes_v"]["inputn"], 1)

    def test_negative_voltage_defeats_positive_failsafe_contract(self):
        result = receiver.off_dc("positive_failsafe", input_voltages=(-0.5, 3))
        self.assertGreater(abs(result["aux_pin_current_na"]["p"]), 100)

    def test_every_candidate_has_explicit_off_network(self):
        for item in receiver.catalog()["candidates"]:
            with self.subTest(candidate=item["id"]):
                result = receiver.candidate_off_sweep(item["id"])
                self.assertEqual(len(result["rows"]), 16)
                self.assertIsNone(result["guaranteed_maximum_rail_injection_ua"])
                self.assertEqual(result["powered_off_classification"], "POWERED_OFF_BEHAVIOR_UNRESOLVED")

    def test_follower_feedback_capacitance_is_in_equivalent(self):
        kind, parameters = receiver.candidate_off_parameters("B_OPA810_BUFFERED")
        circuit, unused, known = receiver.off_equivalent(kind, **parameters)
        self.assertIn(("inputp", "followerp", 0.5e-12), circuit.capacitors)

    def test_off_transient_is_not_a_steady_state_proof(self):
        result = receiver.off_transient("B_OPA810_BUFFERED", retain=False)
        steady = receiver.off_dc("rail_clamped")
        self.assertLess(result["maximum_rail_v"], steady["rail_v"])
        self.assertEqual(result["powered_off_classification"], "POWERED_OFF_BEHAVIOR_UNRESOLVED")

    def test_only_negative_supply_alive_does_not_fix_upper_clamp(self):
        result = receiver.off_dc("rail_clamped", negative_supply_v=-5, rail_discharge_ohm=1)
        self.assertGreater(result["aux_pin_current_na"]["n"], 100)

    def test_only_positive_supply_alive_does_not_fix_negative_input(self):
        result = receiver.off_dc("rail_clamped", positive_supply_v=5, input_voltages=(-0.5, 3), rail_discharge_ohm=1)
        self.assertGreater(abs(result["aux_pin_current_na"]["p"]), 100)

    def test_mutual_current_is_retained_not_declared_zero(self):
        result = receiver.off_transient("A_TLV9031_DIRECT", source_ohm=50, retain=False)
        self.assertGreater(result["maximum_input_mutual_current_ua"], 0)

    def test_upper_clamp_backpowers_rail(self):
        result = receiver.off_dc("rail_clamped")
        self.assertGreater(result["rail_v"], 0.1)
        self.assertGreater(result["rail_injection_ua"], 1)

    def test_clamped_off_supply_loads_aux(self):
        result = receiver.off_dc("rail_clamped", rail_discharge_ohm=1)
        self.assertLess(result["rail_v"], 0.1)
        self.assertGreater(result["aux_pin_current_na"]["n"], 100)

    def test_positive_failsafe_does_not_invent_upper_clamp(self):
        result = receiver.off_dc("positive_failsafe")
        self.assertAlmostEqual(result["rail_v"], 0)
        self.assertLess(result["aux_pin_current_na"]["n"], 1)
        self.assertEqual(result["powered_off_classification"], "POWERED_OFF_BEHAVIOR_UNRESOLVED")

    def test_jfet_gate_forward_path_loads_aux(self):
        result = receiver.off_dc("jfet_gate")
        self.assertGreater(result["aux_pin_current_na"]["n"], 100)

    def test_differential_resistance_bridges_aux(self):
        result = receiver.off_dc("resistive_receiver")
        self.assertGreater(abs(result["positive_to_negative_current_ua"]), 1)

    def test_output_backdrive_raises_supply(self):
        result = receiver.off_dc("positive_failsafe", output_backdrive_v=3.3)
        self.assertGreater(result["rail_v"], 2)

    def test_input_leakage_changes_weak_bias(self):
        result = receiver.off_dc("positive_failsafe", input_leakage_a=1e-6)
        self.assertGreater(result["aux_pin_current_na"]["p"], 900)
        self.assertLess(result["nodes_v"]["busp"], 0.21)

    def test_protection_conduction_loads_source(self):
        result = receiver.off_dc("positive_failsafe", protection_threshold_v=2)
        self.assertGreater(result["aux_source_current_na"]["n"], 100)

    def test_off_equivalent_cannot_authorize_hardware(self):
        self.assertFalse(receiver.off_dc("rail_clamped")["hardware_authorized"])


class CandidatePipelineTests(unittest.TestCase):
    def test_profile_summary_does_not_hide_off_current(self):
        result = receiver.simulate_candidate("B_OPA810_BUFFERED", step_ns=20, retain=False)
        off = receiver.candidate_off_sweep("B_OPA810_BUFFERED")
        summary = receiver.profile_summary(result, off, "COMPLETE_FOR_INTERVAL")
        self.assertGreater(summary["maximum_rail_injection_ua"], 1)
        self.assertEqual(summary["powered_proxy_rail_injection_ua"], 0)
        self.assertIsNone(summary["guaranteed_maximum_rail_injection_ua"])

    def test_tlv9031_conditioning_preserves_legacy_failure(self):
        result = receiver.tlv9031_conditioning_comparison()
        combined = next(item for item in result["legacy_ac_coupling"] if item["case"] == "E8")
        self.assertLess(combined["residual_margin_mv"], 10)
        self.assertGreater(combined["common_mode_conversion_v_per_v"], 0.005)
        self.assertFalse(result["hardware_authorized"])

    def test_buffered_candidate_recovers_only_conditionally(self):
        result = receiver.simulate_candidate("B_OPA810_BUFFERED", retain=False)
        self.assertTrue(result["packet_recovered"])
        self.assertIsNone(result["guaranteed_residual_margin_mv"])
        self.assertFalse(result["hardware_authorized"])

    def test_tlv9031_direct_does_not_remove_dc_bias(self):
        result = receiver.simulate_candidate("A_TLV9031_DIRECT", step_ns=20, retain=False)
        self.assertFalse(result["packet_recovered"])


class MatchingTests(unittest.TestCase):
    def test_off_range_conflict_does_not_depend_on_guessed_iv_curve(self):
        result = receiver.off_range_conflict()
        self.assertAlmostEqual(result["minimum_current_to_keep_pin_in_range_ua"], 24.97502497502498)
        self.assertFalse(result["range_and_loading_can_coexist"])

    def test_capacitance_and_resistance_mismatch_are_separate(self):
        rows = receiver.matching_sweep("B_OPA810_BUFFERED")
        values = {row["case"]: row for row in rows if row["frequency_hz"] == 1000000}
        self.assertGreater(values["input_0.1pf"]["external_common_mode_gain"], values["resistors_0.1pct"]["external_common_mode_gain"])

    def test_ratio_network_has_realistic_conditional_bound(self):
        self.assertLess(receiver.difference_stage_ratio_error()["maximum_cm_gain_from_four_resistors"], 0.00201)

    def test_jfet_gm_spread_cannot_be_wished_away(self):
        self.assertGreater(receiver.jfet_matching_example()["cm_conversion_from_gain_spread"], 0.005)

    def test_off_current_limit_destroys_mhz_bandwidth(self):
        for row in receiver.current_limit_tradeoff()["rows"]:
            self.assertGreater(row["series_ohm_for_100na"], 20000000)
            self.assertLess(row["received_mv_for_90mv"], 1)
    def test_direct_tlv3601_retains_real_dc_loading(self):
        parameters = differential.case_parameters("N1")
        parameters.update(receiver.model_parameters("A_TLV3601_DIRECT"))
        circuit, injections = differential.direct_network(parameters)
        voltage, unused = circuit.solve({"ground": 0, "drivep": 0, "driven": 0, "biasp": 0.3, "biasn": 3}, injections=injections)
        self.assertLess(abs(voltage["inputp"] - voltage["inputn"]), 1)

    def test_optional_parameters_reach_continuous_pipeline(self):
        parameters = {"input_common_pf": 0.45, "input_differential_pf": 0,
                      "protection_pf": 0.27, "protection_cross_pf": 0.14}
        capture, analysis = differential.pipeline_capture(extra=parameters)
        self.assertEqual(capture["acquisition"]["candidate_parameters"], parameters)
        self.assertEqual(analysis["completeness"], "COMPLETE_FOR_INTERVAL")
        self.assertFalse(capture["acquisition"]["hardware_authorized"])
        self.assertFalse(capture["acquisition"]["component_guarantees_established"])


class RetainedRegressionTests(unittest.TestCase):
    def test_every_retained_m5p10_result_and_manifest(self):
        with tempfile.TemporaryDirectory() as temporary:
            result = receiver.verify_m5p10_replay(pathlib.Path(temporary).resolve() / "replay")
        self.assertEqual(result["result_files_identical"], 68)
        self.assertTrue(result["manifest_identical_except_model_source_hash"])


if __name__ == "__main__":
    unittest.main()