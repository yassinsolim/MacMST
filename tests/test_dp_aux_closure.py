import collections
import json
import math
import pathlib
import re
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tools"))
import dp_aux_closure as closure


class CircuitSolverTests(unittest.TestCase):
    def test_resistive_divider(self):
        circuit = closure.RcCircuit(["sense"], [("supply", "sense", 1000), ("sense", "ground", 1000)], [])
        result, metrics = circuit.solve({"supply": 3.3, "ground": 0})
        self.assertAlmostEqual(result["sense"], 1.65)
        self.assertLess(metrics["residual_a"], 1e-12)

    def test_rc_step_matches_analytic_solution(self):
        circuit = closure.RcCircuit(["sense"], [("supply", "sense", 1000)], [("sense", "ground", 1e-9)])
        previous, unused = circuit.solve({"supply": 0, "ground": 0})
        for unused in range(1000):
            previous, metrics = circuit.solve({"supply": 1, "ground": 0}, previous, 1e-9)
        self.assertAlmostEqual(previous["sense"], 1 - math.exp(-1), delta=0.0002)

    def test_power_off_diode_current_has_explicit_path(self):
        circuit = closure.RcCircuit(["input", "rail"],
                                    [("source", "input", 1000), ("rail", "ground", 10000)], [],
                                    [("input", "rail", 0.3, 10)])
        result, metrics = circuit.solve({"source": 3.3, "ground": 0})
        self.assertAlmostEqual(metrics["diode_currents_a"][0], 3 / 11010)
        self.assertGreater(result["rail"], 2.7)

    def test_capacitor_blocks_dc(self):
        circuit = closure.RcCircuit(["sense"], [("sense", "ground", 1000000)], [("source", "sense", 2.2e-12)])
        result, unused = circuit.solve({"source": 3.6, "ground": 0})
        self.assertEqual(result["sense"], 0)

    def test_current_injection_matches_ohms_law(self):
        circuit = closure.RcCircuit(["sense"], [("sense", "ground", 1000000)], [])
        result, unused = circuit.solve({"ground": 0}, injections={"sense": 1e-9})
        self.assertAlmostEqual(result["sense"], 0.001)

    def test_singular_circuit_rejected(self):
        circuit = closure.RcCircuit(["floating"], [], [])
        with self.assertRaises(ValueError):
            circuit.solve({"ground": 0})

    def test_ac_rc_matches_analytic_transfer(self):
        circuit = closure.RcCircuit(["sense"], [("supply", "sense", 1000)], [("sense", "ground", 1e-9)])
        result = circuit.ac({"supply": 1}, 1000000)
        expected = 1 / (1 + 2j * math.pi)
        self.assertAlmostEqual(abs(result["sense"] - expected), 0)


class NetworkTests(unittest.TestCase):
    def test_numerical_waveforms_are_reproducible(self):
        first = closure.simulate_packet(step_ns=25, extra={"offset_v": 0.002})
        second = closure.simulate_packet(step_ns=25, extra={"offset_v": 0.002})
        self.assertEqual(first, second)

    def test_fixed_delay_is_not_edge_dispersion(self):
        result = closure.simulate_packet(step_ns=25, extra={"offset_v": 0.002, "comparator_delay_ns": 1000}, retain=False)
        self.assertTrue(result["request_recovered"])
        self.assertLessEqual(result["edge_dispersion_ns"], 25)

    def test_large_delay_asymmetry_does_not_pass(self):
        result = closure.simulate_packet(step_ns=25, extra={"offset_v": 0.002, "rise_delay_ns": 350,
                                                          "fall_delay_ns": 100}, retain=False)
        self.assertFalse(result["request_recovered"])

    def test_negative_off_excursion_leaves_failsafe_contract(self):
        result = closure.simulate_packet(case="E7", step_ns=25, retain=False)
        self.assertLess(result["minimum_input_v"], 0)
        self.assertGreater(result["maximum_diode_current_ma"], 0)
        self.assertFalse(result["component_limits_guaranteed"])

    def test_higher_standoff_protection_still_has_loading(self):
        original = closure.simulate_packet(step_ns=25, retain=False)
        higher_cap = closure.simulate_packet(step_ns=25, extra={"protection_pf": 0.95}, retain=False)
        self.assertLess(higher_cap["sink_peak_v"], original["sink_peak_v"])

    def test_decode_does_not_override_failed_margin(self):
        result = closure.simulate_packet(case="E8", step_ns=25, retain=False)
        reference = closure.simulate_packet(case="E0", step_ns=25, retain=False)
        verdict = closure.evaluate_model(result, reference)
        self.assertFalse(verdict["checks"]["margin"])
        self.assertFalse(verdict["checks"]["common_mode"])
        self.assertFalse(verdict["build_release"])

    def test_nominal_circuit_decodes(self):
        result = closure.simulate_packet(step_ns=25, retain=False)
        self.assertTrue(result["request_recovered"])
        self.assertFalse(result["hardware_authorized"] or result["component_limits_guaranteed"])
        self.assertLess(result["maximum_kcl_residual_a"], 1e-7)

    def test_powered_off_circuit_cannot_create_valid_packet(self):
        result = closure.simulate_packet(case="E7", step_ns=25, retain=False)
        self.assertFalse(result["request_recovered"])
        self.assertIsNone(result["residual_margin_mv"])

    def test_turnaround_recovers_both_directions(self):
        result = closure.simulate_packet(case="E10", step_ns=25, extra={"offset_v": 0.002}, retain=False)
        self.assertTrue(result["request_recovered"])
        self.assertTrue(result["reply_recovered"])
        self.assertTrue(result["transaction_accepted"])

    def test_zero_threshold_numerical_sensitivity_is_explicit(self):
        result = closure.simulate_packet(step_ns=25, extra={"offset_v": 0})
        self.assertTrue(result["zero_threshold_numerical_sensitivity"])
        quiet = [voltage for timestamp, voltage in zip(result["waveforms"]["time_ns"],
                                                       result["waveforms"]["observer_differential_v"]) if timestamp < 4000]
        self.assertLess(max(map(abs, quiet)), 1e-10)

    def test_idle_region_errors_are_not_removed(self):
        result = closure.simulate_packet(step_ns=25, retain=False)
        self.assertTrue(result["request_recovered"])
        self.assertTrue(any(event["truncated"] for event in result["decoded_events"]))

    def test_time_step_convergence(self):
        coarse = closure.simulate_packet(step_ns=5, retain=False)
        fine = closure.simulate_packet(step_ns=1, retain=False)
        self.assertTrue(coarse["request_recovered"] and fine["request_recovered"])
        self.assertAlmostEqual(coarse["sink_peak_v"], fine["sink_peak_v"], delta=0.001)
        self.assertAlmostEqual(coarse["residual_margin_mv"], fine["residual_margin_mv"], delta=0.1)

    def test_network_has_no_upper_clamp_in_fail_safe_model(self):
        parameters = json.loads(closure.CRITERIA.read_bytes())["numerical_assumptions"]
        self.assertEqual(parameters["comparator_hysteresis_v"], 0)
        circuit, unused = closure.network(parameters)
        self.assertFalse(any(second == "rail" for first, second, threshold, resistance in circuit.diodes))
        clamped, unused = closure.network(parameters, upper_clamp=True)
        self.assertEqual(sum(second == "rail" for first, second, threshold, resistance in clamped.diodes), 2)

    def test_unknown_scenario_rejected(self):
        with self.assertRaises(ValueError):
            closure.simulate_packet(case="E11")


class MatchingTests(unittest.TestCase):
    def test_larger_caps_trade_matching_for_off_loading(self):
        rows = closure.alternative_coupling()
        self.assertTrue(any(row["matching_target_met_in_approximation"] for row in rows))
        self.assertFalse(any(row["matching_target_met_in_approximation"] and row["off_capacitance_target_met"] for row in rows))

    def test_error_budget_never_fills_unknown_with_zero(self):
        result = closure.error_budget()
        self.assertIsNone(result["guaranteed_total_worst_case_mv"])
        self.assertFalse(result["worst_case_closed"])

    def test_sensitivity_sweep_is_deterministic(self):
        result = closure.sensitivity_sweep()
        self.assertEqual(result, closure.sensitivity_sweep())
        self.assertEqual(len(result["rows"]), 35)
        self.assertFalse(result["monte_carlo_used"])
        self.assertGreater(result["ranking"][0]["maximum_contribution_mv"], 5)

    def test_exact_m5p8_failure_reproduced(self):
        rows = {row["case"]: row for row in closure.matching_decomposition()}
        self.assertAlmostEqual(rows["combined"]["full_network_error_mv"], 14.210133691040062)
        self.assertEqual(rows["nominal"]["full_network_error_mv"], 0)

    def test_capacitors_not_resistors_dominate(self):
        rows = {row["case"]: row for row in closure.matching_decomposition()}
        self.assertLess(rows["resistors_only"]["full_network_error_mv"], 0.5)
        self.assertGreater(rows["sense_caps_only"]["full_network_error_mv"], 6)
        self.assertGreater(rows["input_caps_only"]["full_network_error_mv"], 6)

    def test_perfect_resistors_do_not_close_matching(self):
        self.assertTrue(all(row["combined_error_mv"] > 14 for row in closure.precision_sweep()))

    def test_analytical_plateau_matches_full_network(self):
        row = closure.matching_decomposition()[-1]
        self.assertLess(abs(row["full_network_error_mv"] - row["capacitive_plateau_error_mv"]), 0.1)

    def test_transfer_has_expected_highpass_and_plateau(self):
        low = abs(closure.leg_transfer(2.2, 2.5, 1000000, 3200, 1))
        middle = abs(closure.leg_transfer(2.2, 2.5, 1000000, 3200, 1000000))
        self.assertLess(low, 0.0001)
        self.assertAlmostEqual(middle, closure.capacitive_gain(2.2, 2.5), delta=0.001)


class ClosureTableTests(unittest.TestCase):
    def test_existing_output_refused_before_simulation(self):
        with tempfile.TemporaryDirectory() as temporary, self.assertRaises(ValueError):
            closure.run_evidence(pathlib.Path(temporary).resolve())

    def test_all_m5p8_items_preserved(self):
        value = json.loads(closure.CRITERIA.read_bytes())
        self.assertFalse(value["hardware_authorized"])
        self.assertTrue(value["criteria_frozen_before_e_scenarios"])
        report = (closure.ROOT / "docs/research/m5-aux-frontend.md").read_text()
        review = report.split("## Design Review\n")[1].split("## Prototype Gate\n")[0]
        rows = re.findall(r"^\| ([^|]+) \| (PASS|FAIL|UNRESOLVED) \|", review, re.M)
        original = [(item["requirement"], item["m5p8_state"]) for item in value["review"] if item["id"].startswith("P8-")]
        self.assertEqual(original, [(name.strip(), state) for name, state in rows])
        self.assertEqual(collections.Counter(state for unused, state in original), {"PASS": 5, "FAIL": 1, "UNRESOLVED": 10})


class PipelineTests(unittest.TestCase):
    def test_circuit_output_reaches_mst_and_w1(self):
        capture, result = closure.pipeline_capture("accepted_envelope")
        self.assertEqual(result["gates"]["W1.2"]["result"], "MST_ENABLE_ESTABLISHED")
        self.assertTrue(result["gates"]["W1.4"]["topologies"])
        self.assertEqual(result["gates"]["W1.7"]["observed_payload_ids"], [1])
        self.assertFalse(result["hardware_authorized"] or result["real_source_ownership_established"])
        self.assertFalse(capture["acquisition"]["continuous_analog_state"])

    def test_powered_off_pipeline_does_not_invent_enable(self):
        unused, result = closure.pipeline_capture("powered_off")
        self.assertEqual(result["gates"]["W1.2"]["result"], "MST_ENABLE_UNRESOLVED")
        self.assertEqual(result["completeness"], "CAPTURE_INCOMPLETE")

    def test_nominal_idle_errors_block_complete_w1(self):
        unused, result = closure.pipeline_capture("nominal")
        self.assertEqual(result["completeness"], "CAPTURE_INCOMPLETE")
        self.assertFalse(result["gates"]["W1.7"]["only_one_payload_established"])


if __name__ == "__main__":
    unittest.main()