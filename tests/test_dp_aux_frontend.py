import math
import json
import pathlib
import re
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tools"))
import dp_aux_frontend_model as model
import dp_aux_decode as aux


class LoadingTests(unittest.TestCase):
    def test_scope_resistance_can_disturb_idle_detection_bias(self):
        result = model.dc_bias_loading(200000)
        self.assertEqual(result["relative_bias"], 0.5)
        self.assertAlmostEqual(result["retained_bias_difference_v"], 1.35)

    def test_dc_loading_target_is_separate_from_active_termination(self):
        result = model.dc_bias_loading(200000000)
        self.assertGreater(result["relative_bias"], 0.999)
        self.assertLess(result["observer_current_ua"], 0.014)

    def test_pair_matches_symmetric_differential_half_circuit(self):
        parameters = model.load_design()["parameters"]
        for frequency in (100000, 1000000, 10000000):
            pair = model.pair_transfer(parameters, parameters, frequency)
            half = model.ac_transfer(parameters, frequency)
            self.assertAlmostEqual(abs(pair["sink"] - half["sink"]), 0)
            self.assertAlmostEqual(abs(pair["sense"] - half["sense"]), 0)

    def test_common_mode_rejected_by_symmetric_network(self):
        parameters = model.load_design()["parameters"]
        pair = model.pair_transfer(parameters, parameters, 1000000, common_mode=True)
        self.assertAlmostEqual(abs(pair["sense"]), 0)
        self.assertAlmostEqual(abs(pair["sink"]), 0)

    def test_design_is_non_authorizing(self):
        design = model.load_design()
        self.assertIs(design["hardware_authorized"], False)
        self.assertEqual(design["parameter_classification"], "ASSUMED_FOR_SIMULATION")

    def test_no_observer_reference_is_unity(self):
        observations = model.loading_sweep(model.load_design())["S0"]
        self.assertTrue(all(abs(item["sink_relative_amplitude"] - 1) < 1e-12 for item in observations))

    def test_unpowered_clamp_has_capacitance_bound(self):
        observations = model.loading_sweep(model.load_design())["S2"]
        self.assertGreater(observations[1]["sink_relative_amplitude"], 0.999)
        self.assertLess(observations[-1]["sense_per_loaded_differential"], 0.02)

    def test_component_imbalance_converts_common_mode(self):
        cases = model.loading_sweep(model.load_design())
        self.assertEqual(cases["S1"][1]["common_to_differential_gain"], 0)
        self.assertGreater(cases["S4"][1]["common_to_differential_gain"], 0.04)

    def test_source_and_coupling_sensitivity(self):
        parameters = model.load_design()["parameters"]
        for source in (25, 50, 75):
            for coupling in (75, 100, 200):
                corner = {**parameters, "source_leg_ohm": source, "source_coupling_nf": coupling,
                          "sink_coupling_nf": coupling}
                baseline = model.pair_transfer(corner, corner, 10000000, attached=False)
                loaded = model.pair_transfer(corner, corner, 10000000, off=True)
                self.assertGreater(abs(loaded["sink"] / baseline["sink"]), 0.99)

    def test_capacitor_bounds_off_charge_not_backfeed(self):
        result = model.transient_bounds(model.load_design()["parameters"])
        self.assertAlmostEqual(result["maximum_coupled_charge_pc"], 7.92)
        self.assertAlmostEqual(result["off_input_capacitance_bound_pf"], 3.2)
        self.assertFalse(result["supply_backfeed_excluded"])

    def test_protection_placement_removes_bias_resistor_leakage_path(self):
        result = model.transient_bounds(model.load_design()["parameters"])
        self.assertEqual(result["leakage_offset_if_protection_after_cap_mv"], 10)
        self.assertEqual(result["protection_leakage_drop_before_cap_uv"], 10)

    def test_power_off_resistance_conflicts_with_speed(self):
        result = model.series_sense(3300000, 4)
        self.assertAlmostEqual(result["off_clamp_current_ua"], 1)
        self.assertGreater(result["rise_10_90_ns"], 28000)

    def test_fast_series_path_does_not_limit_off_current(self):
        result = model.series_sense(1000, 4)
        self.assertLess(result["rise_10_90_ns"], 10)
        self.assertGreater(result["off_clamp_current_ua"], 3000)

    def test_shunt_model_matches_resistive_limit(self):
        result = model.shunt_loading(100, 100, 1000, 1e-9, 1)
        self.assertAlmostEqual(result["relative_amplitude"], 2 / 2.1)

    def test_capacitance_costs_high_frequency_margin(self):
        low = model.shunt_loading(100, 100, 1000000, 5, 1000000)
        high = model.shunt_loading(100, 100, 1000000, 50, 100000000)
        self.assertGreater(low["relative_amplitude"], high["relative_amplitude"])

    def test_invalid_values_rejected(self):
        for value in (True, 0, -1, math.inf, math.nan):
            with self.subTest(value=value), self.assertRaises(ValueError):
                model.series_sense(value, 4)


class ConditionedSignalTests(unittest.TestCase):
    def decode(self, **parameters):
        record, metrics = model.conditioned_record(**parameters)
        result = aux.decode_capture({"schema_version": 1, "capture_id": "synthetic-frontend",
                                     "evidence_kind": "synthetic", "records": [record]})
        return result, metrics

    def test_nominal_conditioning_decodes(self):
        result, metrics = self.decode()
        self.assertEqual(result["events"][0]["request_raw"], "90002100")
        self.assertFalse(result["events"][0]["malformed"] or result["events"][0]["truncated"])
        self.assertFalse(metrics["hardware_authorized"])

    def test_constant_delay_does_not_change_bytes(self):
        result, unused = self.decode(rise_delay_ns=100, fall_delay_ns=100)
        self.assertEqual(result["events"][0]["request_raw"], "90002100")

    def test_modest_asymmetry_and_jitter_decodes(self):
        result, unused = self.decode(rise_delay_ns=50, fall_delay_ns=30, jitter_ns=10)
        self.assertEqual(result["events"][0]["request_raw"], "90002100")

    def test_threshold_error_margin(self):
        for threshold in (-0.008, 0.008):
            with self.subTest(threshold=threshold):
                result, unused = self.decode(threshold_v=threshold)
                self.assertEqual(result["events"][0]["request_raw"], "90002100")

    def test_worst_capacitance_with_bounded_threshold(self):
        parameters = {**model.load_design()["parameters"], "input_pf": 8, "sense_pf": 2.1}
        for threshold in (-0.008, 0.008):
            with self.subTest(threshold=threshold):
                result, unused = self.decode(parameters=parameters, threshold_v=threshold, sample_period_ns=25)
                self.assertEqual(result["events"][0]["request_raw"], "90002100")

    def test_capacitance_plus_leakage_offset_exposes_risk(self):
        parameters = {**model.load_design()["parameters"], "input_pf": 8}
        result, unused = self.decode(parameters=parameters, threshold_v=0.020, sample_period_ns=25)
        self.assertTrue(all(event["malformed"] or event["truncated"] for event in result["events"]))

    def test_short_glitch_is_not_silent_success(self):
        result, unused = self.decode(glitch_at=(2200, 10))
        self.assertTrue(any(event["malformed"] or event["truncated"] for event in result["events"]))

    def test_half_cell_timing_range_at_40msps(self):
        for half_period in (400, 500, 600):
            with self.subTest(half_period=half_period):
                result, unused = self.decode(half_period_ns=half_period, sample_period_ns=25)
                self.assertEqual(result["events"][0]["request_raw"], "90002100")

    def test_invalid_zero_sample_period_rejected(self):
        with self.assertRaises(ValueError):
            model.conditioned_record(sample_period_ns=0)

    def test_excess_threshold_is_not_valid_packet(self):
        result, unused = self.decode(threshold_v=0.15)
        self.assertFalse(any(event["request_raw"] == "90002100" and not event["malformed"] and
                             not event["truncated"] for event in result["events"]))

    def test_inversion_is_not_silently_corrected(self):
        result, unused = self.decode(invert=True)
        self.assertTrue(all(event["malformed"] or event["truncated"] for event in result["events"]))

    def test_missed_edge_is_detected(self):
        result, unused = self.decode(missed_edge=45)
        self.assertTrue(any(event["malformed"] or event["truncated"] for event in result["events"]))


class SpiceArtifactTests(unittest.TestCase):
    def test_model_cli_outputs_are_deterministic_and_non_overwriting(self):
        script = model.DESIGN.parents[2] / "tools/dp_aux_frontend_model.py"
        with tempfile.TemporaryDirectory() as temporary:
            output = pathlib.Path(temporary).resolve() / "nominal.json"
            command = [sys.executable, str(script), "--capture", "--output", str(output)]
            subprocess.run(command, check=True, capture_output=True)
            original = output.read_bytes()
            value = json.loads(original)
            self.assertEqual(value["evidence_kind"], "synthetic")
            self.assertEqual(value["records"][0]["sample_period_ns"], 25)
            self.assertEqual(aux.decode_capture(value)["events"][0]["request_raw"], "90002100")
            self.assertEqual(subprocess.run(command, capture_output=True).returncode, 2)
            self.assertEqual(output.read_bytes(), original)

    def test_generic_tvs_model_is_bidirectional(self):
        text = model.DESIGN.with_name("aux-sense.cir").read_text()
        for node in ("PROTP", "PROTN"):
            self.assertIn(f"max(V({node},AGND)-6.4,0)/0.57+min(V({node},AGND)+6.4,0)/0.57", text)
        for voltage in (0, 3.6, 6.97, 15):
            positive_current = max(voltage - 6.4, 0) / 0.57 + min(voltage + 6.4, 0) / 0.57
            negative_current = max(-voltage - 6.4, 0) / 0.57 + min(-voltage + 6.4, 0) / 0.57
            self.assertAlmostEqual(positive_current, -negative_current)

    def test_six_cases_have_distinct_configuration(self):
        design = model.load_design()
        decks = {case: model.spice_deck(design, case) for case in ("S0", "S1", "S2", "S3", "S4", "S5")}
        self.assertNotIn("XOBSERVER", decks["S0"])
        self.assertIn("VPOWER VDD 0 0", decks["S2"])
        self.assertIn("CIN=8p", decks["S3"])
        self.assertIn("MISMATCH=0.01", decks["S4"])
        self.assertIn("CAPDELTA=0.1p", decks["S4"])
        self.assertIn("INDELTA=-0.125p", decks["S4"])
        self.assertIn("PULSE(0 0.3 12u 10n 10n 2u 16u)", decks["S4"])
        self.assertIn("RTERM SINKP SINKN {2*RTERM}", decks["S1"])
        self.assertTrue(all("PWL(" in deck and deck.endswith(".end\n") for deck in decks.values()))

    def test_design_parameters_match_subcircuit(self):
        text = model.DESIGN.with_name("aux-sense.cir").read_text()
        values = dict(re.findall(r"\b([A-Z]+)=([0-9.]+(?:k|Meg|p)?)", text))
        parameters = model.load_design()["parameters"]
        scales = {"k": 1000, "Meg": 1000000, "p": 1e-12, "": 1}
        for spice_name, model_name, scale in (("RBRANCH", "sense_series_ohm", 1),
                                             ("RLIMIT", "input_series_ohm", 1),
                                             ("CSENSE", "sense_pf", 1e-12),
                                             ("RBIAS", "bias_ohm", 1), ("CIN", "input_pf", 1e-12),
                                             ("CPROT", "protection_pf", 1e-12), ("CSTRAY", "bus_stray_pf", 1e-12)):
            number, unit = re.fullmatch(r"([0-9.]+)(k|Meg|p)?", values[spice_name]).groups()
            self.assertAlmostEqual(float(number) * scales[unit or ""] / scale, parameters[model_name])

    def test_subcircuit_has_no_aux_driver(self):
        text = model.DESIGN.with_name("aux-sense.cir").read_text()
        elements = [line.split() for line in text.splitlines() if line and line[0] not in "*. +"]
        for element in elements:
            if element[0][0] in "BEGIV":
                self.assertNotIn("AUXP", element[1:3])
                self.assertNotIn("AUXN", element[1:3])
            if "RXD" in element[1:3]:
                self.assertEqual(element[0], "BISOLATE")
        self.assertNotIn("HPD", text)
        self.assertNotIn("DP_PWR", text)


if __name__ == "__main__":
    unittest.main()