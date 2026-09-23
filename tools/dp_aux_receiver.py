#!/usr/bin/env python3
"""Evidence-qualified receiver profiles extending the offline M5P10 model."""

import argparse
import copy
import csv
import hashlib
import json
import math
import pathlib

import dp_aux_differential as differential


CATALOG = differential.ROOT / "hardware/aux-observer/receivers.json"


def catalog():
    value = json.loads(CATALOG.read_bytes())
    if value["criteria_sha256"] != differential.design()[0]["criteria_sha256"] or value["hardware_authorized"] is not False:
        raise ValueError("Frozen criteria and offline authorization must be preserved")
    return value


def candidate(identifier):
    return next((copy.deepcopy(item) for item in catalog()["candidates"] if item["id"] == identifier), None)


def candidate_budget(identifier, protection="ESD122DMXR"):
    item = candidate(identifier)
    if item is None or protection not in catalog()["protection"]:
        raise ValueError("Unknown candidate or protection profile")
    terms = item["capacitance"]
    diode = catalog()["protection"][protection]
    protection_terms = () if protection == "BENCH_NONE" else (("protection line", 1, "line_pf"), ("protection mutual", 2, "mutual_pf"))
    for name, coefficient, field in protection_terms:
        terms.append({"name": name, "coefficient": coefficient, "typical_pf": diode[field]["typical"],
                      "maximum_pf": diode[field]["maximum"], "maximum_basis": "VERIFIED_FROM_DATASHEET",
                      "covers_required_envelope": protection == "BENCH_NONE", "source": diode["source"]})
    terms.append({"name": "PCB and input pads", "coefficient": 1,
                  "typical_pf": catalog()["assumptions"]["pcb_pf_per_leg"], "maximum_pf": None,
                  "maximum_basis": "ASSUMED", "covers_required_envelope": False, "source": "layout_not_released"})
    return {"candidate": identifier, "protection": protection, "terms": terms, **capacitance_accounting(terms)}


def model_parameters(identifier, protection="ESD122DMXR"):
    item = candidate(identifier)
    if item is None or protection not in catalog()["protection"]:
        raise ValueError("Unknown candidate or protection profile")
    diode = catalog()["protection"][protection]
    parameters = copy.deepcopy(item["model"])
    parameters.update(protection_pf=diode["line_pf"]["typical"], protection_cross_pf=diode["mutual_pf"]["typical"],
                      board_pf=0.5, input_delta_pf=0, protection_delta_pf=0,
                      receiver_cm_gain=0.001, offset_v=0.002, reference_error_v=0.001, noise_v=0.001,
                      comparator_delay_ns=100, comparator_rise_delay_ns=115, comparator_fall_delay_ns=100)
    return parameters


def candidate_gates(identifier, protection="ESD122DMXR"):
    item = candidate(identifier)
    if item is None:
        raise ValueError("Unknown candidate")
    gates = dict.fromkeys(REQUIRED_GATES, "UNKNOWN")
    gates.update(receive_only="PASS", reproducible_model="PASS")
    for name in item["known_failures"]:
        gates[name] = "FAIL"
    gates["input_capacitance"] = candidate_budget(identifier, protection)["loading_gate"]
    return {"gates": gates, **release_gate(gates)}


def capacitance_accounting(terms):
    if not terms:
        raise ValueError("An explicit capacitance budget is required")
    representative = 0.0
    test_point_maximum = 0.0
    qualified_maximum = 0.0
    unknown = []
    for term in terms:
        coefficient = term["coefficient"]
        if type(coefficient) not in (int, float) or not math.isfinite(coefficient) or coefficient <= 0:
            raise ValueError("Invalid capacitance coefficient")
        for name in ("typical_pf", "maximum_pf"):
            value = term.get(name)
            if value is not None and (type(value) not in (int, float) or not math.isfinite(value) or value < 0):
                raise ValueError("Invalid capacitance specification")
        typical, maximum = term.get("typical_pf"), term.get("maximum_pf")
        example = typical if typical is not None else maximum
        representative = representative + coefficient * example if representative is not None and example is not None else None
        test_point_maximum = test_point_maximum + coefficient * maximum if test_point_maximum is not None and maximum is not None else None
        applicable = (maximum is not None and term.get("maximum_basis") == "VERIFIED_FROM_DATASHEET"
                      and term.get("covers_required_envelope") is True and bool(term.get("source")))
        if not applicable:
            qualified_maximum = None
            unknown.append(term["name"])
        elif qualified_maximum is not None:
            qualified_maximum += coefficient * maximum
    limit = differential.design()[1]["maximum_added_capacitance_pf_per_leg"]
    return {"representative_pf_per_leg": representative,
            "sum_of_stated_test_point_maxima_pf": test_point_maximum,
            "guaranteed_maximum_pf_per_leg": qualified_maximum,
            "unknown_or_unqualified_terms": unknown,
            "representative_classification": "INFERRED" if representative is not None else "UNKNOWN",
            "loading_gate": "UNKNOWN" if qualified_maximum is None else "PASS" if qualified_maximum <= limit else "FAIL"}


def off_equivalent(kind, source_ohm=100000, branch_ohm=100, rail_discharge_ohm=1000000,
                   input_leakage_a=0, input_pf=1, cross_pf=0, protection_pf=0,
                   protection_threshold_v=None, output_backdrive_v=None, input_voltages=(0.3, 3),
                   clamp_threshold_v=0.3, follower_feedback_pf=0, differential_resistance_ohm=None,
                   positive_supply_v=0, negative_supply_v=0):
    if kind not in ("positive_failsafe", "rail_clamped", "jfet_gate", "resistive_receiver", "input_feedback_clamped"):
        raise ValueError("Unknown powered-off equivalent")
    values = (source_ohm, branch_ohm, rail_discharge_ohm, input_pf, cross_pf, protection_pf, follower_feedback_pf)
    if any(type(value) not in (int, float) or not math.isfinite(value) or value < 0 for value in values):
        raise ValueError("Invalid off-state model parameter")
    if min(source_ohm, branch_ohm, rail_discharge_ohm) <= 0:
        raise ValueError("Positive resistances required")
    if len(input_voltages) != 2 or any(type(value) not in (int, float) or not math.isfinite(value) for value in input_voltages):
        raise ValueError("Two finite input voltages required")
    if any(not math.isfinite(value) for value in (input_leakage_a, positive_supply_v, negative_supply_v)) or clamp_threshold_v <= 0:
        raise ValueError("Invalid leakage or clamp threshold")
    nodes = ["busp", "busn", "inputp", "inputn", "rail", "output"]
    resistors = [("rail", "rail_supply", rail_discharge_ohm), ("output", "ground", 1000000)]
    capacitors = [("rail", "ground", 1.1e-6), ("inputp", "inputn", cross_pf * 1e-12)]
    diodes = [("output", "rail", 0.3, 10), ("negative_supply", "output", 0.3, 10)]
    injections = {}
    for suffix in ("p", "n"):
        bus, pin = "bus" + suffix, "input" + suffix
        resistors.extend([("drive" + suffix, bus, source_ohm), (bus, pin, branch_ohm),
                          (pin, "ground", 1e12)])
        capacitors.extend([(pin, "ground", input_pf * 1e-12), (bus, "ground", protection_pf * 1e-12)])
        injections[pin] = -input_leakage_a
        if kind in ("positive_failsafe", "rail_clamped"):
            diodes.append(("negative_supply", pin, clamp_threshold_v, 10))
        if kind in ("rail_clamped", "jfet_gate"):
            diodes.append((pin, "rail", clamp_threshold_v if kind == "rail_clamped" else 0.6, 10))
        if kind == "jfet_gate":
            source = "source" + suffix
            nodes.append(source)
            resistors.append((source, "ground", 10000))
            diodes.append((pin, source, 0.6, 10))
        if kind == "input_feedback_clamped":
            feedback, amplifier_output = "feedback" + suffix, "amplifier_output" + suffix
            nodes.extend((feedback, amplifier_output))
            resistors.extend([(feedback, "ground", 75), (feedback, amplifier_output, 453),
                              (amplifier_output, "ground", 1000000)])
            diodes.extend([(pin, feedback, 0.6, 10), (feedback, pin, 0.6, 10)])
        if follower_feedback_pf:
            output = "follower" + suffix
            nodes.append(output)
            resistors.append((output, "ground", 1000000))
            capacitors.append((pin, output, follower_feedback_pf * 1e-12))
            diodes.extend([(output, "rail", clamp_threshold_v, 10), ("negative_supply", output, clamp_threshold_v, 10)])
        if protection_threshold_v is not None:
            diodes.extend([(bus, "ground", protection_threshold_v, 1),
                           ("ground", bus, protection_threshold_v, 1)])
    if kind == "resistive_receiver" or differential_resistance_ohm is not None:
        resistors.append(("inputp", "inputn", differential_resistance_ohm or 1000000))
    known = {"ground": 0, "drivep": input_voltages[0], "driven": input_voltages[1],
             "rail_supply": positive_supply_v, "negative_supply": negative_supply_v}
    if output_backdrive_v is not None:
        resistors.append(("backend", "output", 100))
        known["backend"] = output_backdrive_v
    capacitors = [element for element in capacitors if element[2] > 0]
    return differential.legacy.RcCircuit(nodes, resistors, capacitors, diodes), injections, known


def off_dc(kind, **parameters):
    circuit, injections, known = off_equivalent(kind, **parameters)
    voltage, metrics = circuit.solve(known, injections=injections)
    branch = parameters.get("branch_ohm", 100)
    source = parameters.get("source_ohm", 100000)
    currents = {suffix: (voltage["bus" + suffix] - voltage["input" + suffix]) / branch for suffix in ("p", "n")}
    rail_current = sum(current for diode, current in zip(circuit.diodes, metrics["diode_currents_a"]) if diode[1] == "rail")
    pair_resistance = parameters.get("differential_resistance_ohm", 1000000 if kind == "resistive_receiver" else None)
    link_current = (voltage["inputp"] - voltage["inputn"]) / pair_resistance if pair_resistance else 0
    return {"kind": kind, "classification": "ASSUMED_EQUIVALENT_NOT_DEVICE_GUARANTEE",
            "parameters": parameters, "nodes_v": voltage, "rail_v": voltage["rail"],
            "rail_injection_ua": rail_current * 1e6,
            "aux_pin_current_na": {suffix: current * 1e9 for suffix, current in currents.items()},
            "aux_source_current_na": {suffix: (known["drive" + suffix] - voltage["bus" + suffix]) / source * 1e9
                                       for suffix in ("p", "n")},
            "positive_to_negative_current_ua": link_current * 1e6,
            "maximum_kcl_residual_a": metrics["residual_a"],
            "powered_off_classification": "POWERED_OFF_BEHAVIOR_UNRESOLVED", "hardware_authorized": False}


def candidate_off_parameters(identifier, protection="ESD122DMXR"):
    item = candidate(identifier)
    parameters = model_parameters(identifier, protection)
    values = {"input_pf": parameters["input_common_pf"], "cross_pf": parameters["input_differential_pf"] +
              parameters["protection_cross_pf"], "protection_pf": parameters["protection_pf"]}
    if identifier == "B_OPA810_BUFFERED":
        values.update(input_pf=2, follower_feedback_pf=0.5)
    if "input_differential_resistance_ohm" in parameters:
        values["differential_resistance_ohm"] = parameters["input_differential_resistance_ohm"]
    return item["off_kind"], values


def candidate_off_sweep(identifier, protection="ESD122DMXR"):
    kind, base = candidate_off_parameters(identifier, protection)
    rows = []
    for source in (50, 100000):
        for discharge in (1, 1000000):
            for voltages in ((0.3, 3), (-0.5, 3), (3.6, 3.6)):
                result = off_dc(kind, **base, source_ohm=source, rail_discharge_ohm=discharge,
                                input_voltages=voltages)
                result["candidate"] = identifier
                result["topology_basis"] = candidate(identifier)["off_topology_basis"]
                result["iv_curve_basis"] = "ASSUMED: diode knee/dynamic resistance and rail loads are not device limits"
                rows.append(result)
    rows.append(off_dc(kind, **base, output_backdrive_v=3.3))
    rows.append(off_dc(kind, **base, input_leakage_a=100e-9))
    rows.append(off_dc(kind, **base, positive_supply_v=0, negative_supply_v=-5, rail_discharge_ohm=1))
    rows.append(off_dc(kind, **base, positive_supply_v=5, negative_supply_v=0, rail_discharge_ohm=1,
                       input_voltages=(-0.5, 3)))
    return {"candidate": identifier, "rows": rows,
            "maximum_modeled_rail_injection_ua": max(row["rail_injection_ua"] for row in rows),
            "guaranteed_maximum_rail_injection_ua": None,
            "powered_off_classification": "POWERED_OFF_BEHAVIOR_UNRESOLVED", "hardware_authorized": False}


def off_transient(identifier, step_ns=5, source_ohm=100000, retain=True):
    if step_ns not in (1, 5):
        raise ValueError("Off-state convergence uses1 or5 ns integration")
    kind, parameters = candidate_off_parameters(identifier)
    circuit, injections, known = off_equivalent(kind, **parameters, source_ohm=source_ohm, input_voltages=(0, 0))
    previous, unused = circuit.solve(known, injections=injections)
    data = {name: [] for name in ("time_ns", "drivep_v", "driven_v", "busp_v", "busn_v", "rail_v",
                                  "rail_injection_a", "input_mutual_current_a")}
    rail_peak = current_peak = residual = mutual_peak = 0.0
    for timestamp in range(0, 20001, step_ns):
        ramp = max(0, min(1, (timestamp - 2000) / 10))
        negative = max(0, min(1, (timestamp - 12000) / 10, (16010 - timestamp) / 10))
        known.update(drivep=0.3 * ramp - 0.8 * negative, driven=3 * ramp)
        voltage, metrics = circuit.solve(known, previous, step_ns * 1e-9, injections)
        current = sum(value for diode, value in zip(circuit.diodes, metrics["diode_currents_a"]) if diode[1] == "rail")
        mutual = parameters["cross_pf"] * 1e-12 * ((voltage["inputp"] - voltage["inputn"]) -
                               (previous["inputp"] - previous["inputn"])) / (step_ns * 1e-9)
        mutual_peak = max(mutual_peak, abs(mutual))
        rail_peak = max(rail_peak, voltage["rail"])
        current_peak = max(current_peak, current)
        residual = max(residual, metrics["residual_a"])
        if retain:
            for name, value in zip(data, (timestamp, known["drivep"], known["driven"], voltage["busp"], voltage["busn"], voltage["rail"], current, mutual)):
                data[name].append(value)
        previous = voltage
    result = {"candidate": identifier, "step_ns": step_ns, "source_ohm": source_ohm,
              "initial_state": "cold zero rails and zero source, then finite10 ns source and negative excursion ramps",
              "maximum_rail_v": rail_peak, "maximum_rail_injection_ua": current_peak * 1e6,
              "maximum_input_mutual_current_ua": mutual_peak * 1e6,
              "maximum_kcl_residual_a": residual, "classification": "ASSUMED_EQUIVALENT_NOT_DEVICE_GUARANTEE",
              "powered_off_classification": "POWERED_OFF_BEHAVIOR_UNRESOLVED", "hardware_authorized": False}
    if retain:
        result["waveforms"] = data
    return result


def matching_sweep(identifier):
    base = {**differential.case_parameters("N1"), **model_parameters(identifier)}
    rows = []
    for frequency in (100000, 1000000, 10000000):
        for label, capacitance, resistance, protection in (("nominal", 0, 0, 0), ("input_0.1pf", 0.1, 0, 0),
                                                          ("resistors_0.1pct", 0, 0.001, 0), ("resistors_1pct", 0, 0.01, 0),
                                                          ("protection_0.01pf", 0, 0, 0.01), ("combined", 0.1, 0.001, 0.01)):
            parameters = {**base, "branch_resistor_tolerance": resistance}
            result = differential.direct_ac(parameters, frequency, capacitance, protection)
            rows.append({"case": label, "frequency_hz": frequency, **result,
                         "classification": "ASSUMED_MISMATCH_NOT_GUARANTEED_PART_TRACKING"})
    return rows


def difference_stage_ratio_error(tolerance=0.001):
    if not 0 <= tolerance < 1:
        raise ValueError("Invalid ratio tolerance")
    from itertools import product
    maximum = 0.0
    for signs in product((-1, 1), repeat=4):
        values = [10000 * (1 + sign * tolerance) for sign in signs]
        first, second = values[1] / values[0], values[3] / values[2]
        maximum = max(maximum, abs((1 + first) * second / (1 + second) - first))
    return {"resistor_tolerance": tolerance, "maximum_cm_gain_from_four_resistors": maximum,
            "frequency_scope": "low-frequency ideal amplifier; amplifierAC/PVT matching remains UNKNOWN"}


def jfet_matching_example(source_ohm=10000):
    gains = [transconductance * source_ohm / (1 + transconductance * source_ohm) for transconductance in (0.0045, 0.0075)]
    return {"source_ohm": source_ohm, "gain_range": gains, "cm_conversion_from_gain_spread": gains[1] - gains[0],
            "classification": "INFERRED_FROM_STATED_TEST_POINT_GM_NOT_GUARANTEED_FOLLOWER_GAIN",
            "condition": "MMBF4416 gm4.5..7.5mS at VDS15V,VGS0,1kHz,25C; chosen follower bias and MHzPVT UNKNOWN"}


def current_limit_tradeoff(input_pf=2.5):
    rows = []
    for knee in (0.3, 0.8):
        resistance = (3 - knee) / 100e-9
        gain = abs(1 / (1 + 2j * math.pi * 1000000 * resistance * input_pf * 1e-12))
        rows.append({"assumed_clamp_knee_v": knee, "series_ohm_for_100na": resistance,
                     "gain_at_1mhz": gain, "received_mv_for_90mv": gain * 90})
    return {"classification": "ASSUMED_CLAMP_KNEE_WITH_ANALYTICAL_RC", "rows": rows}


def off_range_conflict(source_v=3, maximum_pin_v=0.5, total_series_ohm=100100, allowed_current_na=100):
    required_current = max(0, source_v - maximum_pin_v) / total_series_ohm
    return {"source_v": source_v, "maximum_off_pin_v": maximum_pin_v,
            "total_series_ohm": total_series_ohm, "minimum_current_to_keep_pin_in_range_ua": required_current * 1e6,
            "pin_v_if_loading_limit_met": source_v - allowed_current_na * 1e-9 * total_series_ohm,
            "range_and_loading_can_coexist": required_current * 1e9 <= allowed_current_na,
            "classification": "INFERRED_KCL_CONSTRAINT_NOT_DIODE_CURRENT_PREDICTION"}


def simulate_candidate(identifier, protection="ESD122DMXR", step_ns=5, combined=False, retain=True):
    item = candidate(identifier)
    if item is None:
        raise ValueError("Unknown candidate")
    parameters = model_parameters(identifier, protection)
    if combined:
        parameters.update(input_delta_pf=0.1, protection_delta_pf=0.01 if protection == "ESD122DMXR" else 0,
                          branch_resistor_tolerance=0.001)
        parameters["receiver_cm_gain"] += difference_stage_ratio_error()["maximum_cm_gain_from_four_resistors"]
        if identifier == "C_MMBF4416_FOLLOWERS":
            parameters["receiver_cm_gain"] += jfet_matching_example()["cm_conversion_from_gain_spread"]
    result, unused = differential.simulate_record(step_ns=step_ns, extra=parameters, retain=retain,
                                                 conditioning=item["conditioning"])
    result["candidate"] = identifier
    result["candidate_interpretation"] = "CONDITIONAL_PROFILE_PROXY_NOT_FULL_PART_OR_GUARANTEED_ENVELOPE"
    result["capacitance_budget"] = candidate_budget(identifier, protection)
    result["guaranteed_residual_margin_mv"] = None
    result["guaranteed_cm_conversion_v_per_v"] = None
    result["powered_off_classification"] = "POWERED_OFF_BEHAVIOR_UNRESOLVED"
    result["release"] = candidate_gates(identifier, protection)
    return result


def tlv9031_conditioning_comparison():
    cases = []
    for case in ("E1", "E8", "E7"):
        result = differential.legacy.simulate_packet(case=case, retain=False)
        cases.append({key: result[key] for key in ("case", "parameters", "residual_margin_mv", "common_mode_conversion_v_per_v",
                                                  "minimum_input_v", "maximum_input_v", "maximum_rail_v",
                                                  "maximum_positive_rail_injection_ua", "request_recovered",
                                                  "maximum_added_crossing_error_ns")})
    return {"legacy_ac_coupling": cases, "larger_coupling_tradeoff": differential.legacy.alternative_coupling(),
            "post_receiver_placement": {"input_stage": "B_OPA810_BUFFERED", "receiver_budget": candidate_budget("B_OPA810_BUFFERED"),
                                         "comparator_capacitance_at_aux": "Not directly added after a buffer; reverse transfer remains UNKNOWN"},
            "direct_bias_error_v": -2.7, "threshold_strategy": "FIXED_THRESHOLD_NOT_ESTABLISHED",
            "hardware_authorized": False}


def profile_summary(result, off, completeness):
    summary = compact_scenario(result)
    summary["powered_proxy_rail_injection_ua"] = summary.pop("maximum_rail_injection_ua")
    summary.update(maximum_rail_injection_ua=off["maximum_modeled_rail_injection_ua"],
                   rail_injection_basis="Maximum across declared off-state DC and cold-transient witnesses, not a device guarantee",
                   guaranteed_maximum_rail_injection_ua=None, completeness=completeness,
                   total_input_capacitance_pf_per_leg=result["capacitance_budget"]["representative_pf_per_leg"],
                   guaranteed_input_capacitance_pf_per_leg=result["capacitance_budget"]["guaranteed_maximum_pf_per_leg"])
    return summary


REQUIRED_GATES = ("receive_only", "input_capacitance", "dc_loading", "common_mode_range",
                  "differential_range", "margin", "timing", "protection", "powered_off",
                  "no_backdrive", "matching", "reproducible_model")


def release_gate(gates):
    if set(gates) != set(REQUIRED_GATES) or any(value not in ("PASS", "FAIL", "UNKNOWN") for value in gates.values()):
        raise ValueError("Every electrical release gate needs an explicit disposition")
    blockers = [name for name in REQUIRED_GATES if gates[name] != "PASS"]
    return {"frontend_gate": "AUX_FRONTEND_PROTOTYPE_STILL_BLOCKED" if blockers else "AUX_FRONTEND_PROTOTYPE_BUILD_WARRANTED",
            "blockers": blockers, "w1_gate": "W1_CAPTURE_SYSTEM_NOT_READY", "hardware_authorized": False,
            "authorization_reason": "M5P11 is offline-only even if a future candidate closes the electrical gates"}


def verify_m5p10_replay(destination):
    differential.run_evidence(destination)
    output = pathlib.Path(destination)
    hashes = json.loads((output / "hashes.json").read_bytes())
    expected = catalog()["m5p10_regression"]
    results = {name: digest for name, digest in hashes.items() if name != "manifest.json"}
    aggregate = hashlib.sha256(json.dumps(results, sort_keys=True).encode()).hexdigest()
    if len(results) != expected["result_files"] or aggregate != expected["result_hash_aggregate"]:
        raise ValueError("Retained M5P10 numerical/capture/analysis output changed")
    manifest = json.loads((output / "manifest.json").read_bytes())
    manifest["source_sha256"]["tools/dp_aux_differential.py"] = expected["original_model_source_sha256"]
    normalized = (json.dumps(manifest, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()
    if hashlib.sha256(normalized).hexdigest() != expected["manifest_sha256"]:
        raise ValueError("M5P10 manifest changed beyond the explicitly extended source file")
    return {"result_files_identical": len(results), "manifest_identical_except_model_source_hash": True,
            "result_hash_aggregate": aggregate, "hardware_authorized": False}


def compact_scenario(result):
    return {key: value for key, value in result.items() if key not in ("waveforms", "capture_record", "decoded_events")}


def write_waveform(path, waveform):
    with path.open("x", encoding="ascii", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(waveform)
        writer.writerows(zip(*waveform.values()))


def run_evidence(destination, include_pipeline=True):
    output = pathlib.Path(destination).absolute()
    if output.exists() or any(path.is_symlink() for path in (output, *output.parents)):
        raise ValueError("Evidence directory must be new and nonsymlinked")
    source_records = catalog()["sources"]
    for record in source_records.values():
        if hashlib.sha256((differential.ROOT / record["path"]).read_bytes()).hexdigest() != record["sha256"]:
            raise ValueError("Source receipt hash mismatch")
    output.mkdir(parents=True, exist_ok=False)
    write = differential.legacy.write_json
    summaries, budgets, sensitivities, off_results, convergence, pipeline_results = [], [], {}, [], [], []
    for item in catalog()["candidates"]:
        identifier = item["id"]
        off_summary = candidate_off_sweep(identifier)
        off_results.append(off_summary)
        for source in (50, 100000):
            result = off_transient(identifier, source_ohm=source)
            write_waveform(output / (identifier + f"-off-{source}ohm.csv"), result.pop("waveforms"))
            off_results.append(result)
            off_summary["maximum_modeled_rail_injection_ua"] = max(off_summary["maximum_modeled_rail_injection_ua"], result["maximum_rail_injection_ua"])
        budgets.extend(candidate_budget(identifier, protection) for protection in catalog()["protection"])
        sensitivities[identifier] = matching_sweep(identifier)
        for combined in (False, True):
            result = simulate_candidate(identifier, combined=combined)
            profile = identifier + ("-combined" if combined else "-nominal")
            write_waveform(output / (profile + "-waveform.csv"), result["waveforms"])
            write(output / (profile + "-window.json"), {"schema_version": 1, "capture_id": profile,
                                                       "evidence_kind": "synthetic", "records": [result["capture_record"]]})
            write(output / (profile + "-decoded.json"), result["decoded_events"])
            summaries.append({"profile": profile, **profile_summary(result, off_summary, "NOT_EVALUATED")})
        if include_pipeline:
            for combined in (False, True):
                parameters = model_parameters(identifier)
                if combined:
                    parameters.update(input_delta_pf=0.1, protection_delta_pf=0.01, branch_resistor_tolerance=0.001)
                    parameters["receiver_cm_gain"] += difference_stage_ratio_error()["maximum_cm_gain_from_four_resistors"]
                    if identifier == "C_MMBF4416_FOLLOWERS":
                        parameters["receiver_cm_gain"] += jfet_matching_example()["cm_conversion_from_gain_spread"]
                fault = "direct" if item["conditioning"] == "direct" else None
                capture, analysis = differential.pipeline_capture(extra=parameters, fault=fault)
                profile = identifier + ("-combined" if combined else "-nominal")
                write(output / (profile + "-pipeline-window.json"), capture)
                write(output / (profile + "-pipeline-analysis.json"), analysis)
                pipeline_results.append({"profile": profile, "completeness": analysis["completeness"],
                                         "enable": analysis["gates"]["W1.2"]["result"],
                                         "component_envelope_qualified": False, "hardware_authorized": False})
                next(summary for summary in summaries if summary["profile"] == profile)["completeness"] = analysis["completeness"]
    for identifier in ("A_TLV9031_DIRECT", "B_OPA810_BUFFERED", "C_MMBF4416_FOLLOWERS"):
        fine = simulate_candidate(identifier, step_ns=1, combined=True, retain=False)
        coarse = simulate_candidate(identifier, step_ns=5, combined=True, retain=False)
        off_fine = off_transient(identifier, step_ns=1, source_ohm=50, retain=False)
        off_coarse = off_transient(identifier, step_ns=5, source_ohm=50, retain=False)
        convergence.append({"candidate": identifier, "steps_ns": [1, 5],
                            "packet_recovery_agrees": fine["packet_recovered"] == coarse["packet_recovered"],
                            "margin_difference_mv": abs(fine["residual_margin_mv"] - coarse["residual_margin_mv"]),
                            "sink_peak_difference_v": abs(fine["sink_peak_v"] - coarse["sink_peak_v"]),
                            "off_rail_difference_v": abs(off_fine["maximum_rail_v"] - off_coarse["maximum_rail_v"]),
                            "hardware_authorized": False})
    write(output / "candidate-results.json", summaries)
    write(output / "capacitance-budgets.json", budgets)
    write(output / "off-state-results.json", off_results)
    write(output / "matching.json", {"input_networks": sensitivities,
                                     "difference_stage": [difference_stage_ratio_error(value) for value in (0.0005, 0.001, 0.01)],
                                     "jfet": jfet_matching_example(), "series_limit": current_limit_tradeoff(),
                                     "opa810_off_range_conflict": off_range_conflict()})
    write(output / "convergence.json", convergence)
    write(output / "catalog.json", catalog())
    write(output / "gates.json", {item["id"]: candidate_gates(item["id"]) for item in catalog()["candidates"]})
    thresholds = []
    for result in summaries:
        thresholds.append({"profile": result["profile"], "guaranteed_threshold_range": differential.threshold_interval(None, None, None, None, None),
                           "conditional_window": differential.threshold_interval(max(0, result["minimum_signed_midcell_signal_v"]),
                                                  0.3 * result["common_mode_conversion_bound_v_per_v"], 0.002, 0.001, 0.001),
                           "single_fixed": "Cannot prove quiet idle from offset/noise without guaranteed bounds",
                           "hysteretic": "Local-only possible; real threshold band and propagation limits required",
                           "window": "Preserves idle/invalid; explicit channel-skew contract still required"})
    write(output / "thresholds.json", thresholds)
    write(output / "tlv9031-conditioning.json", tlv9031_conditioning_comparison())
    names = ["tools/dp_aux_receiver.py", "tools/dp_aux_differential.py", "hardware/aux-observer/receivers.json",
             "hardware/aux-observer/differential.json", "tools/dp_aux_closure.py", "hardware/aux-observer/closure.json",
             "tools/dp_aux_frontend_model.py", "hardware/aux-observer/model.json", "tools/dp_aux_decode.py",
             "tools/dp_mst_decode.py", "tools/dp_wire_analyze.py", "tools/dp_wire_synthetic.py"]
    write(output / "manifest.json", {"schema_version": 1, "evidence_kind": "synthetic", "hardware_authorized": False,
                                    "model_kind": "CONDITIONAL_COMPONENT_PROFILE_WITH_UNKNOWN_GUARANTEES",
                                    "component_guarantees_established": False, "step_ns": 5, "pipeline_step_ns": 20,
                                    "criteria_sha256": catalog()["criteria_sha256"], "pipeline_results": pipeline_results,
                                    "source_receipts": source_records,
                                    "source_sha256": {name: hashlib.sha256((differential.ROOT / name).read_bytes()).hexdigest() for name in names}})
    hashes = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(output.iterdir())}
    write(output / "hashes.json", hashes)
    return {"files_hashed": len(hashes), "pipeline_results": pipeline_results,
            "frontend_gate": "AUX_FRONTEND_PROTOTYPE_STILL_BLOCKED", "w1_gate": "W1_CAPTURE_SYSTEM_NOT_READY",
            "hardware_authorized": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--output", type=pathlib.Path)
    group.add_argument("--replay-m5p10", type=pathlib.Path)
    parser.add_argument("--skip-pipeline", action="store_true")
    arguments = parser.parse_args()
    try:
        if arguments.replay_m5p10:
            result = verify_m5p10_replay(arguments.replay_m5p10)
        elif arguments.output:
            result = run_evidence(arguments.output, not arguments.skip_pipeline)
        else:
            result = {item["id"]: {"budget": candidate_budget(item["id"]), "release": candidate_gates(item["id"])}
                      for item in catalog()["candidates"]}
        print(json.dumps(result, sort_keys=True, indent=2, allow_nan=False))
    except (OSError, ValueError) as error:
        parser.exit(2, str(error) + "\n")


if __name__ == "__main__":
    main()