#!/usr/bin/env python3
"""Offline differential-first AUX topology experiments, never a hardware driver."""

import argparse
import copy
import csv
import hashlib
import json
import math
import pathlib

import dp_aux_closure as legacy
import dp_aux_decode as aux
import dp_wire_analyze as wire
import dp_wire_synthetic as synthetic


ROOT = pathlib.Path(__file__).resolve().parents[1]
DESIGN = ROOT / "hardware/aux-observer/differential.json"


def design():
    value = json.loads(DESIGN.read_bytes())
    criteria = json.loads((ROOT / value["criteria_source"]).read_bytes())["criteria"]
    digest = hashlib.sha256(json.dumps(criteria, sort_keys=True).encode()).hexdigest()
    if digest != value["criteria_sha256"] or value["hardware_authorized"] is not False:
        raise ValueError("Frozen criteria or authorization mismatch")
    return value, criteria


def review_summary():
    value, unused = design()
    previous = json.loads((ROOT / value["criteria_source"]).read_bytes())["review"]
    original = {row["id"]: row for row in previous}
    rows = value["review_dispositions"]
    identifiers = [row["id"] for row in rows]
    if identifiers[:len(previous)] != list(original) or len(set(identifiers)) != len(identifiers):
        raise ValueError("Every original review row must survive in order, exactly once")
    if any(row["result"] not in ("PASS", "FAIL", "UNRESOLVED") or type(row["frontend_critical"]) is not bool for row in rows):
        raise ValueError("Invalid review disposition")
    deferred = {row["id"] for row in rows if not row["frontend_critical"]}
    if deferred != {"P8-07", "P8-09", "P8-12", "P8-13"}:
        raise ValueError("Only explicitly scoped live-DP and W1 backend rows may be deferred")
    merged = [{**row, "requirement": original[row["id"]]["requirement"] if row["id"] in original else row["requirement"],
               "m5p9_result": original[row["id"]]["result"] if row["id"] in original else None,
               "w1_critical": True} for row in rows]
    blockers = [row["id"] for row in rows if row["frontend_critical"] and row["result"] != "PASS"]
    return {"rows": merged, "counts": {result: sum(row["result"] == result for row in rows)
                                        for result in ("PASS", "FAIL", "UNRESOLVED")},
            "frontend_blockers": blockers, "frontend_gate": "AUX_FRONTEND_PROTOTYPE_STILL_BLOCKED" if blockers
            else "AUX_FRONTEND_PROTOTYPE_BUILD_WARRANTED", "w1_gate": "W1_CAPTURE_SYSTEM_NOT_READY",
            "schematic_released": False, "bom_released": False, "hardware_authorized": False}


def direct_network(parameters, input_mismatch_pf=0, protection_mismatch_pf=0, clamps=False, off_upper_clamp=False):
    original = legacy.scenario_parameters("E1")
    link, injections = legacy.network(original, attached=False)
    nodes = list(link.nodes) + ["inputp", "inputn"]
    resistors = list(link.resistors)
    capacitors = list(link.capacitors)
    diodes = []
    for suffix, sign in (("p", 1), ("n", -1)):
        input_cap = parameters["input_common_pf"] + sign * input_mismatch_pf / 2
        protection = parameters["protection_pf"] + sign * protection_mismatch_pf / 2
        if input_cap <= 0 or protection < 0:
            raise ValueError("Invalid capacitance corner")
        branch = parameters["branch_ohm"] * (1 + sign * parameters.get("branch_resistor_tolerance", 0))
        resistors.extend([("bus" + suffix, "input" + suffix, branch),
                          ("input" + suffix, "ground", parameters["input_resistance_ohm"])])
        if "input_bias_a" in parameters:
            injections["input" + suffix] = -parameters["input_bias_a"]
        capacitors.extend([("input" + suffix, "ground", (input_cap + protection) * 1e-12),
                           ("bus" + suffix, "ground", parameters["board_pf"] * 1e-12)])
        if clamps:
            diodes.append(("ground", "input" + suffix, 0.3, 10))
        if off_upper_clamp:
            diodes.append(("input" + suffix, "rail", 0.3, 10))
    capacitors.append(("inputp", "inputn", (parameters["input_differential_pf"] +
                                            parameters["protection_cross_pf"]) * 1e-12))
    if "input_differential_resistance_ohm" in parameters:
        resistors.append(("inputp", "inputn", parameters["input_differential_resistance_ohm"]))
    if off_upper_clamp:
        nodes.append("rail")
        resistors.append(("rail", "ground", 1000000))
        capacitors.append(("rail", "ground", 1.1e-6))
    return legacy.RcCircuit(nodes, resistors, [element for element in capacitors if element[2] != 0], diodes), injections


def direct_ac(parameters, frequency_hz, input_mismatch_pf=0, protection_mismatch_pf=0):
    circuit, unused = direct_network(parameters, input_mismatch_pf, protection_mismatch_pf)
    common = circuit.ac({"drivep": 1, "driven": 1}, frequency_hz)
    differential = circuit.ac({"drivep": 0.5, "driven": -0.5}, frequency_hz)
    return {"frequency_hz": frequency_hz,
            "external_common_mode_gain": abs(common["inputp"] - common["inputn"]),
            "differential_gain": abs(differential["inputp"] - differential["inputn"]),
            "component_guarantees_established": False}


def threshold_interval(signal_min_v, false_differential_v, offset_v, noise_v,
                       reference_error_v, required_margin_v=0.010):
    values = (signal_min_v, false_differential_v, offset_v, noise_v, reference_error_v, required_margin_v)
    if any(value is None for value in values):
        return {"classification": "FIXED_THRESHOLD_NOT_ESTABLISHED", "lower_v": None,
                "upper_v": None, "reason": "A design-critical bound is missing"}
    if any(type(value) not in (int, float) or not math.isfinite(value) or value < 0 for value in values):
        raise ValueError("Invalid threshold bound")
    disturbance = false_differential_v + offset_v + noise_v
    lower = disturbance + reference_error_v
    upper = signal_min_v - disturbance - reference_error_v - required_margin_v
    return {"classification": "CONDITIONAL_MODEL_INTERVAL" if lower < upper else "EMPTY_THRESHOLD_INTERVAL",
            "lower_v": lower, "upper_v": upper, "component_guarantees_established": False}


def attenuation_example(frequency_hz=1000000):
    impedance = 1 / (1 / 50000000 + 2j * math.pi * frequency_hz * 3e-12)
    gain = abs(impedance / (50000000 + impedance))
    return {"top_ohm": 50000000, "bottom_ohm": 50000000, "input_shunt_pf": 3,
            "dc_input_ohm": 100000000, "frequency_hz": frequency_hz, "gain": gain,
            "received_mv_for_90mv_input": gain * 90, "classification": "BANDWIDTH_FAILURE_EXAMPLE"}


def threshold_reference_example():
    from itertools import product
    nominal = [10000, 124, 124, 10000]
    thresholds = []
    for signs in product((-1, 1), repeat=5):
        resistors = [value * (1 + sign * 0.001) for value, sign in zip(nominal, signs[:4])]
        current = 3.3 * (1 + signs[4] * 0.005) / sum(resistors)
        thresholds.extend(current * resistance for resistance in resistors[1:3])
    return {"topology": "3.3V--10k--VTH+--124R--VMID--124R--VTH---10k--GND",
            "nominal_threshold_v": 3.3 * 124 / sum(nominal), "conditional_minimum_v": min(thresholds),
            "conditional_maximum_v": max(thresholds), "resistor_tolerance_fraction": 0.001,
            "reference_error_fraction": 0.005, "location": "receiver output only; never on AUX",
            "buffer_error_bound_v": None, "complete_worst_case_bound_v": None,
            "construction_released": False}


def differential_state(positive, negative):
    if type(positive) is not int or type(negative) is not int or positive not in (0, 1) or negative not in (0, 1):
        raise ValueError("Binary comparator outputs required")
    return {(1, 0): "POSITIVE", (0, 1): "NEGATIVE", (0, 0): "IDLE", (1, 1): "INVALID"}[(positive, negative)]


def slice_value(voltage, threshold_v, offset_v=0, reference_error_v=0):
    values = (voltage, threshold_v, offset_v, reference_error_v)
    if any(type(value) not in (int, float) or not math.isfinite(value) for value in values):
        raise ValueError("Finite slicer parameters required")
    positive = threshold_v + reference_error_v
    negative = -threshold_v - reference_error_v
    if positive <= negative:
        raise ValueError("Thresholds must enclose a nonempty dead band")
    return int(voltage - offset_v > positive) | (int(voltage - offset_v < negative) << 1)


def adapt_window_record(record, maximum_deadband_ns=40):
    if not isinstance(record, dict) or record.get("representation") != "differential_window_samples":
        raise ValueError("Expected a differential window record")
    samples = record.get("samples")
    if not isinstance(samples, list) or not samples or len(samples) > 2000000:
        raise ValueError("Invalid or oversized window samples")
    if any(type(sample) is not int or sample not in (0, 1, 2, 3) for sample in samples):
        raise ValueError("Window samples require two bits: bit0 positive, bit1 negative")
    period = aux.integer(record.get("sample_period_ns"), "sample period", 1, 100)
    timestamp = aux.integer(record.get("timestamp_ns"), "timestamp_ns")
    aux.integer(timestamp + len(samples) * period, "window end")
    metadata = {key: value for key, value in record.items() if key != "samples"}
    aux.decode_packet({**metadata, "raw_hex": ""}, "window-metadata-check", 0)
    aux.integer(maximum_deadband_ns, "maximum dead band", 0, 100)
    working = list(samples)
    annotations = []
    cursor = 0
    while cursor < len(samples):
        if samples[cursor] != 0:
            cursor += 1
            continue
        start = cursor
        while cursor < len(samples) and samples[cursor] == 0:
            cursor += 1
        end = cursor
        if (start and end < len(samples) and {samples[start - 1], samples[end]} == {1, 2}
                and (end - start) * period <= maximum_deadband_ns):
            crossing = (start + end) // 2
            working[start:crossing] = [samples[start - 1]] * (crossing - start)
            working[crossing:end] = [samples[end]] * (end - crossing)
            annotations.append({"kind": "bounded_opposite_polarity_deadband",
                                "sample_range": [start, end], "crossing_sample": crossing,
                                "method": "midpoint_interpolation_not_observed_binary_samples"})
    normalized = []
    cursor = 0
    origin = {key: copy.deepcopy(value) for key, value in record.items() if key != "samples"}
    while cursor < len(working):
        start = cursor
        category = "asserted" if working[cursor] in (1, 2) else "invalid" if working[cursor] == 3 else "idle"
        while cursor < len(working):
            current = "asserted" if working[cursor] in (1, 2) else "invalid" if working[cursor] == 3 else "idle"
            if current != category:
                break
            cursor += 1
        segment = {**origin, "timestamp_ns": timestamp + start * period,
                   "window_sample_range": [start, cursor]}
        if category == "asserted":
            normalized.append({**segment, "representation": "digital_samples",
                               "samples": [int(value == 1) for value in working[start:cursor]]})
        elif category == "invalid" or (start and cursor < len(working) and
                                       (cursor - start) * period <= maximum_deadband_ns):
            reason = "impossible_dual_assertion" if category == "invalid" else "unexplained_window_gap"
            normalized.append({**segment, "representation": "bytes", "kind": "unknown",
                               "direction": "unknown", "raw_hex": "", "truncated": True,
                               "waveform_errors": [reason]})
            annotations.append({"kind": reason, "sample_range": [start, cursor]})
        else:
            annotations.append({"kind": "retained_idle_or_unresolved_long_gap",
                                "sample_range": [start, cursor]})
        if len(normalized) > aux.MAX_RECORDS:
            raise ValueError("Too many window segments")
    return normalized, annotations


def adapt_window_capture(capture, maximum_deadband_ns=40):
    if (not isinstance(capture, dict) or type(capture.get("schema_version")) is not int
            or capture["schema_version"] != 1 or capture.get("evidence_kind") not in ("synthetic", "hardware")):
        raise ValueError("Explicit schema and evidence origin required")
    records = capture.get("records")
    if not isinstance(records, list) or len(records) > aux.MAX_RECORDS:
        raise ValueError("Invalid window records")
    result = copy.deepcopy(capture)
    result["raw_window_records"] = result["records"]
    result["records"] = []
    annotations = []
    previous_end = capture.get("interval", {}).get("start_ns", 0)
    aux.integer(previous_end, "interval start")
    result["loss_intervals"] = copy.deepcopy(capture.get("loss_intervals", []))
    for index, record in enumerate(records):
        if not isinstance(record, dict) or record.get("evidence_kind", capture["evidence_kind"]) != capture["evidence_kind"]:
            raise ValueError("Mixed window evidence origins")
        if capture["evidence_kind"] == "hardware" and str(record.get("direction_basis", "")).startswith("synthetic"):
            raise ValueError("Synthetic direction cannot become hardware evidence, including idle")
        normalized, spans = adapt_window_record(record, maximum_deadband_ns)
        if record["timestamp_ns"] < previous_end:
            raise ValueError("Window records overlap or run backwards")
        if record["timestamp_ns"] > previous_end:
            result["loss_intervals"].append({"start_ns": previous_end, "end_ns": record["timestamp_ns"],
                                             "reason": "unobserved_window_interval"})
        previous_end = record["timestamp_ns"] + len(record["samples"]) * record["sample_period_ns"]
        if record.get("loss_state", "unknown") != "none":
            result.setdefault("coverage", {})["complete"] = False
            result["coverage"]["loss_state"] = record.get("loss_state", "unknown")
            if record.get("loss_state") == "lost":
                result["loss_intervals"].append({"start_ns": record["timestamp_ns"], "end_ns": previous_end,
                                                 "reason": "window_record_loss"})
            else:
                normalized.insert(0, {"representation": "bytes", "timestamp_ns": record["timestamp_ns"],
                                      "kind": "unknown", "direction": "unknown", "raw_hex": "", "loss_state": "unknown",
                                      "waveform_errors": ["unknown_window_loss"], "truncated": True})
        result["records"].extend({**item, "window_source_record": index} for item in normalized)
        annotations.extend({**item, "window_source_record": index} for item in spans)
        if len(result["records"]) > aux.MAX_RECORDS:
            raise ValueError("Too many normalized window segments")
    interval_end = capture.get("interval", {}).get("end_ns", previous_end)
    aux.integer(interval_end, "interval end", previous_end)
    if interval_end > previous_end:
        result["loss_intervals"].append({"start_ns": previous_end, "end_ns": interval_end,
                                         "reason": "unobserved_window_interval"})
    result["window_adapter"] = {"version": "macmst-window-1", "maximum_deadband_ns": maximum_deadband_ns,
                                "annotations": annotations, "raw_states_preserved": True,
                                "direction_inferred": False, "hardware_authorized": False}
    aux.decode_capture(result)
    return result


def case_parameters(case):
    if case not in {f"N{index}" for index in range(13)}:
        raise ValueError("Unknown differential scenario")
    parameters = dict(design()[0]["parameters"])
    parameters.update(input_delta_pf=0, protection_delta_pf=0, offset_v=0.0003,
                      reference_error_v=0, noise_v=0, positive_delay_ns=60, negative_delay_ns=60)
    if case in ("N2", "N6", "N12"):
        parameters["input_delta_pf"] = parameters["input_mismatch_pf"]
    if case in ("N3", "N6", "N12"):
        parameters["protection_delta_pf"] = parameters["protection_mismatch_pf"]
    if case in ("N4", "N6"):
        parameters["offset_v"] = parameters["comparator_offset_v"]
    if case in ("N5", "N6"):
        parameters["reference_error_v"] = parameters["threshold_error_v"]
    if case == "N6":
        parameters.update(input_common_pf=8, protection_pf=0.5, receiver_cm_gain=0.002,
                          receiver_bandwidth_hz=15000000, noise_v=parameters["noise_allowance_v"])
    return parameters


def simulate_record(raw_hex="90002100", case="N1", kind="request", step_ns=5,
                    extra=None, origin_ns=0, duration_ns=None, state=None, retain=True,
                    conditioning="post_difference", observer_attached=None):
    parameters = case_parameters(case)
    parameters.update(extra or {})
    if conditioning not in ("post_difference", "direct") or kind not in ("request", "reply"):
        raise ValueError("Invalid receiver conditioning or packet kind")
    sample_period = parameters["sample_period_ns"]
    if type(step_ns) is not int or step_ns not in (1, 5, 20) or sample_period % step_ns:
        raise ValueError("Use a 1, 5 or 20 ns step dividing the sample period")
    aux.integer(origin_ns, "origin_ns")
    if origin_ns % sample_period:
        raise ValueError("Origin must retain the shared sample clock")
    attached = case != "N0" if observer_attached is None else observer_attached
    powered = case != "N7"
    if attached:
        circuit, injections = direct_network(parameters, parameters["input_delta_pf"],
                                             parameters["protection_delta_pf"], not powered, not powered)
    else:
        circuit, injections = legacy.network(legacy.scenario_parameters("E1"), attached=False)
    known = {"ground": 0, "drivep": 0, "driven": 0, "biasp": 0.3, "biasn": 3}
    if state is None:
        previous, unused = circuit.solve(known, injections=injections)
        initial = previous.get("inputp", 0) - previous.get("inputn", 0)
        initial += parameters["receiver_cm_gain"] * (previous.get("inputp", 0) + previous.get("inputn", 0)) / 2
        lowpass = initial
        highpass = 0.0
        desired = digital = 0
        pending = []
    else:
        if state["next_timestamp_ns"] != origin_ns or state["parameters"] != parameters:
            raise ValueError("Continuous state requires identical parameters and adjacent windows")
        previous = dict(state["voltage"])
        lowpass, highpass = state["lowpass"], state["highpass"]
        desired, digital = state["desired"], state["digital"]
        pending = list(state["pending"])
    bits = legacy.baseline.manchester(raw_hex, step_ns, parameters["half_cell_ns"])
    if case in ("N11", "N12"):
        bits = []
    packet_start = 4000
    packet_end = packet_start + len(bits) * step_ns
    duration = duration_ns if duration_ns is not None else packet_end + 30000
    if type(duration) is not int or duration < packet_end + 20 or duration % sample_period:
        raise ValueError("Window must contain the packet and end on the sample clock")
    data = {name: [] for name in ("time_ns", "source_differential_v", "source_common_mode_v", "bus_differential_v",
                                  "sink_differential_v", "input_positive_v", "input_negative_v", "receiver_output_v",
                                  "conditioned_v", "rail_v", "rail_injection_a", "window_state")}
    samples, expected_edges, margins, valid_signal = [], [], [], []
    sink_peak = maximum_residual = maximum_rail = maximum_injection = 0.0
    minimum_input, maximum_input = math.inf, -math.inf
    lowpass_tau_ns = 1e9 / (2 * math.pi * parameters["receiver_bandwidth_hz"])
    highpass_tau_ns = parameters["post_difference_highpass_tau_ns"]
    for relative in range(0, duration, step_ns):
        timestamp = origin_ns + relative
        index = (relative - packet_start) // step_ns
        active = 0 <= index < len(bits)
        stimulus = 0.0
        if active:
            cell_start = index - index % (parameters["half_cell_ns"] // step_ns)
            target = 0.18 if bits[index] else -0.18
            prior = (0.18 if bits[cell_start - 1] else -0.18) if cell_start else 0
            stimulus = prior + min(1, (index - cell_start) * step_ns / 10) * (target - prior)
            if index and bits[index] != bits[index - 1]:
                expected_edges.append(timestamp)
        elif packet_end <= relative < packet_end + 10 and bits:
            stimulus = (0.18 if bits[-1] else -0.18) * (1 - (relative - packet_end) / 10)
        common = 0 if case == "N11" else 0.3 * math.sin(2 * math.pi * timestamp * 1e-9 * 1000000)
        if case == "N7":
            common = 3.6 * max(0, min(1, (relative - 12000) / 10, (16010 - relative) / 10))
        near = stimulus if kind == "request" else 0
        far = stimulus if kind == "reply" else 0
        known.update(drivep=common + near / 2, driven=common - near / 2)
        currents = {**injections, "sinkp": far / 100, "sinkn": -far / 100}
        voltage, metrics = circuit.solve(known, previous, step_ns * 1e-9, currents)
        input_positive, input_negative = voltage.get("inputp", 0), voltage.get("inputn", 0)
        receiver = input_positive - input_negative + parameters["receiver_cm_gain"] * (input_positive + input_negative) / 2
        receiver = max(-4.0, min(4.0, receiver))
        next_lowpass = lowpass + step_ns / (lowpass_tau_ns + step_ns) * (receiver - lowpass)
        highpass = highpass_tau_ns / (highpass_tau_ns + step_ns) * (highpass + next_lowpass - lowpass)
        lowpass = next_lowpass
        conditioned = (highpass if conditioning == "post_difference" else lowpass)
        conditioned += parameters["noise_v"] * math.sin(2 * math.pi * timestamp * 1e-9 * 3100000)
        target = slice_value(conditioned, parameters["threshold_v"], parameters["offset_v"],
                             parameters["reference_error_v"]) if powered and attached else 0
        for bit, delay_key in ((1, "positive_delay_ns"), (2, "negative_delay_ns")):
            if (target & bit) != (desired & bit):
                edge_delay = parameters.get("comparator_rise_delay_ns" if target & bit else "comparator_fall_delay_ns",
                                            parameters[delay_key])
                pending.append((timestamp + edge_delay, bit, target & bit))
        pending.sort()
        desired = target
        while pending and pending[0][0] <= timestamp:
            unused, bit, value = pending.pop(0)
            digital = (digital & ~bit) | value
        rail = voltage.get("rail", 0)
        injection = sum(current for diode, current in zip(circuit.diodes, metrics["diode_currents_a"])
                        if diode[1] == "rail")
        maximum_rail = max(maximum_rail, rail)
        maximum_injection = max(maximum_injection, injection)
        maximum_residual = max(maximum_residual, metrics["residual_a"])
        sink = voltage["sinkp"] - voltage["sinkn"]
        sink_peak = max(sink_peak, abs(sink))
        minimum_input = min(minimum_input, input_positive, input_negative)
        maximum_input = max(maximum_input, input_positive, input_negative)
        phase = (relative - packet_start) % parameters["half_cell_ns"]
        if active and parameters["half_cell_ns"] // 2 <= phase < parameters["half_cell_ns"] // 2 + step_ns:
            sign = 1 if bits[index] else -1
            valid_signal.append(sign * conditioned)
            margins.append(sign * (conditioned - parameters["offset_v"]) - parameters["threshold_v"] - parameters["reference_error_v"])
        if relative % sample_period == 0:
            samples.append(digital)
        if retain:
            values = (timestamp, stimulus, common, voltage["busp"] - voltage["busn"], sink, input_positive,
                      input_negative, lowpass, conditioned, rail, injection, digital)
            for name, value in zip(data, values):
                data[name].append(value)
        previous = voltage
    record = {"representation": "differential_window_samples", "timestamp_ns": origin_ns,
              "sample_period_ns": sample_period, "samples": samples, "kind": kind,
              "direction": "source_to_sink" if kind == "request" else "sink_to_source",
              "direction_basis": "synthetic_circuit_stimulus", "loss_state": "none"}
    capture = {"schema_version": 1, "capture_id": "synthetic-differential-" + case,
               "evidence_kind": "synthetic", "records": [record]}
    normalized = adapt_window_capture(capture)
    decoded = aux.decode_capture(normalized)
    edges = [item["timestamp_ns"] + index * sample_period for item in normalized["records"]
             if item["representation"] == "digital_samples" for index in range(1, len(item["samples"]))
             if item["samples"][index] != item["samples"][index - 1]]
    timing = [observed - expected - parameters["comparator_delay_ns"]
              for observed, expected in zip(edges, expected_edges)] if len(edges) == len(expected_edges) else []
    response = direct_ac(parameters, 1000000, parameters["input_delta_pf"], parameters["protection_delta_pf"])
    common_mode_bound = response["external_common_mode_gain"] + abs(parameters["receiver_cm_gain"])
    effective_capacitance = parameters["input_common_pf"] + parameters["protection_pf"] + parameters["board_pf"]
    effective_capacitance += 2 * (parameters["input_differential_pf"] + parameters["protection_cross_pf"])
    summary = {"case": case, "model_kind": "CONDITIONAL_DIFFERENTIAL_RECEIVER_MODEL", "conditioning": conditioning,
               "hardware_authorized": False, "component_guarantees_established": False, "step_ns": step_ns,
               "parameters": parameters, "analog_state_continued": state is not None,
               "midcell_time_quantization_ns": (-parameters["half_cell_ns"] // 2) % step_ns,
               "source_differential_peak_v": 0.18 if bits else 0, "sink_peak_v": sink_peak,
               "external_common_mode_gain": response["external_common_mode_gain"] if attached else None,
               "common_mode_conversion_bound_v_per_v": common_mode_bound if attached else None,
               "effective_differential_capacitance_pf_per_leg": effective_capacitance if attached else 0,
               "capacitance_difference_pf": abs(parameters["input_delta_pf"] + parameters["protection_delta_pf"]) if attached else 0,
               "minimum_input_v": minimum_input if attached else None, "maximum_input_v": maximum_input if attached else None,
               "residual_margin_mv": min(margins) * 1000 if margins and attached and powered else None,
               "minimum_signed_midcell_signal_v": min(valid_signal) if valid_signal and attached and powered else None,
               "maximum_rail_v": maximum_rail, "maximum_rail_injection_ua": maximum_injection * 1e6,
               "maximum_kcl_residual_a": maximum_residual, "edge_count": len(edges), "expected_edge_count": len(expected_edges),
               "maximum_added_crossing_error_ns": max(map(abs, timing)) if timing else None,
               "edge_dispersion_ns": max(timing) - min(timing) if timing else None,
               "packet_recovered": any(event["raw_hex"] == raw_hex and not event["truncated"] and not event["malformed"]
                                       for event in decoded["events"]),
               "idle_asserted_samples": sum(value != 0 for index, value in enumerate(samples)
                                             if index * sample_period < packet_start or index * sample_period > packet_end + 200),
               "invalid_samples": samples.count(3), "decoded_events": decoded["events"], "capture_record": record}
    if retain:
        summary["waveforms"] = data
    next_state = {"voltage": previous, "lowpass": lowpass, "highpass": highpass, "desired": desired,
                  "digital": digital, "pending": pending, "next_timestamp_ns": origin_ns + duration,
                  "parameters": parameters}
    return summary, next_state


def simulate_case(case, step_ns=5, retain=True):
    raw = "8004000f" + "aa55" * 8 if case == "N8" else "0001" if case == "N9" else "90002100"
    kind = "reply" if case == "N9" else "request"
    duration = 10000 + len(legacy.baseline.manchester(raw, 20, 500)) * 20 if case == "N10" else None
    result, state = simulate_record(raw, case, kind, step_ns, duration_ns=duration, retain=retain)
    result["capture_records"] = [result["capture_record"]]
    if case == "N10":
        reply, unused = simulate_record("0001", case, "reply", step_ns, origin_ns=duration, state=state, retain=retain)
        result["capture_records"].append(reply["capture_record"])
        result["reply_recovered"] = reply["packet_recovered"]
        decoded = aux.decode_capture(adapt_window_capture({"schema_version": 1, "capture_id": "synthetic-turnaround",
                                                          "evidence_kind": "synthetic", "records": result["capture_records"]}))
        result["transaction_accepted"] = any(item["accepted"] for item in decoded["transactions"])
        result["continuous_turnaround_state"] = True
        result["decoded_events"] = decoded["events"]
        if retain:
            for name in result["waveforms"]:
                result["waveforms"][name].extend(reply["waveforms"][name])
    return result


def pipeline_capture(case="N1", step_ns=20, fault=None, extra=None):
    if fault not in (None, "invalid", "gap", "unknown_direction", "channel_skew", "direct"):
        raise ValueError("Unknown differential pipeline fault")
    trace = synthetic.Trace()
    trace.transaction(0x108, b"\x01")
    trace.transaction(0x21, b"\x01", True)
    trace.transaction(0x111, b"\x07")
    topology = b"\x01" + bytes(range(16)) + b"\x01\x31\x40\x14" + bytes([1]) * 16 + b"\x11"
    trace.exchange(b"\x01", topology)
    trace.exchange(bytes.fromhex("1110010100"), bytes.fromhex("1110010100"))
    trace.transaction(0x1c0, b"\x01\x01\x0a")
    trace.transaction(0x2c0, b"\x01", True)
    trace.transaction(0x2c0, b"\x03", True)
    records = []
    state = None
    parameters = dict(extra or {})
    if fault == "channel_skew":
        parameters["negative_delay_ns"] = 100
    for index, source in enumerate(trace.records):
        result, state = simulate_record(source["raw_hex"], case, source["kind"], step_ns,
                                        extra=parameters,
                                        origin_ns=source["timestamp_ns"], duration_ns=250000,
                                        state=state, retain=False,
                                        conditioning="direct" if fault == "direct" else "post_difference")
        record = result["capture_record"]
        if fault == "invalid" and index == 4:
            record["samples"][2100] = 3
        if fault == "unknown_direction":
            record.update(kind="unknown", direction="unknown", direction_basis=None)
        records.append(record)
    capture = {"schema_version": 1, "capture_id": "synthetic-differential-pipeline-" + case + "-" + str(fault),
               "capture_generation": "synthetic-differential-generation", "physical_link_id": "synthetic-circuit-link",
               "evidence_kind": "synthetic", "interval": {"start_ns": 0, "end_ns": trace.timestamp},
               "coverage": {"complete": case != "N7", "armed_before_attach": True, "filters_disabled": True,
                            "initial_payload_table_empty": True, "loss_state": "unknown" if case == "N7" else "none"},
               "acquisition": {"model_kind": "CONDITIONAL_DIFFERENTIAL_RECEIVER_MODEL", "case": case, "fault": fault,
                               "hardware_authorized": False, "component_guarantees_established": False,
                               "continuous_analog_state": True, "step_ns": step_ns,
                               "sample_rate_hz": 50000000, "clock_source": "shared_deterministic_counter",
                               "timestamp_resolution_ns": 20, "input_configuration": "two_channel_window"},
               "records": records}
    if extra is not None:
        capture["acquisition"]["candidate_parameters"] = copy.deepcopy(parameters)
    if fault == "gap":
        capture["loss_intervals"] = [{"start_ns": 1050000, "end_ns": 1051000, "reason": "synthetic_acquisition_gap"}]
    normalized = adapt_window_capture(capture)
    return capture, wire.analyze(normalized)["analysis"]


def evaluate_model(result, reference):
    unused, criteria = design()
    amplitude = abs(result["sink_peak_v"] / reference["sink_peak_v"] - 1) if result["source_differential_peak_v"] else None
    def upper(name, limit):
        return result[name] <= criteria[limit] if result[name] is not None else None
    checks = {"amplitude": amplitude <= criteria["maximum_amplitude_change_fraction"] if amplitude is not None else None,
              "common_mode": upper("common_mode_conversion_bound_v_per_v", "maximum_common_mode_conversion_v_per_v"),
              "margin": result["residual_margin_mv"] >= criteria["minimum_residual_differential_margin_mv"]
              if result["residual_margin_mv"] is not None else None,
              "capacitance": upper("effective_differential_capacitance_pf_per_leg", "maximum_added_capacitance_pf_per_leg"),
              "capacitance_balance": upper("capacitance_difference_pf", "maximum_capacitance_imbalance_pf"),
              "crossing": upper("maximum_added_crossing_error_ns", "maximum_added_crossing_error_ns"),
              "dispersion": upper("edge_dispersion_ns", "maximum_edge_dispersion_ns"),
              "packet": result["packet_recovered"] if result["case"] not in ("N0", "N7", "N11", "N12") else None,
              "component_guarantees": False}
    if result["case"] == "N7":
        checks["off_rail"] = upper("maximum_rail_v", "maximum_off_rail_v")
        checks["sustained_off_backfeed"] = None
    return {"checks": checks, "amplitude_error_fraction": amplitude, "build_release": False,
            "scope": "Assumed circuit envelope only; unchanged criteria also expose failed loading limits"}


def backend_rates(sample_rate_hz=50000000, duration_s=180):
    aux.integer(sample_rate_hz, "sample rate", 50000000, 1000000000)
    aux.integer(duration_s, "duration", 1, 3600)
    raw_bytes_s = sample_rate_hz * 2 // 8
    edge_events_s = 2 * 2500000
    return {"sample_rate_hz": sample_rate_hz, "channels": 2, "duration_s": duration_s,
            "packed_raw_bytes_per_second": raw_bytes_s, "packed_raw_total_bytes": raw_bytes_s * duration_s,
            "byte_per_sample_total_bytes": sample_rate_hz * duration_s,
            "maximum_protocol_window_events_per_second": edge_events_s,
            "eight_byte_event_bytes_per_second": edge_events_s * 8,
            "eight_byte_event_total_bytes": edge_events_s * 8 * duration_s,
            "arbitrary_sample_change_events_per_second": sample_rate_hz,
            "arbitrary_eight_byte_event_bytes_per_second": sample_rate_hz * 8,
            "hardware_authorized": False}


def run_evidence(destination, step_ns=5, include_pipeline=True):
    output = pathlib.Path(destination).absolute()
    if output.exists() or any(path.is_symlink() for path in (output, *output.parents)):
        raise ValueError("Evidence destination must be new and nonsymlinked")
    output.mkdir(parents=True, exist_ok=False)
    summaries = []
    for index in range(13):
        case = f"N{index}"
        result = simulate_case(case, step_ns)
        raw = "8004000f" + "aa55" * 8 if case == "N8" else "0001" if case == "N9" else "90002100"
        reference, unused = simulate_record(raw, case, "reply" if case == "N9" else "request", step_ns,
                                            observer_attached=False, retain=False)
        result["evaluation"] = evaluate_model(result, reference)
        with (output / (case + "-waveform.csv")).open("x", encoding="ascii", newline="") as stream:
            writer = csv.writer(stream)
            writer.writerow(result["waveforms"])
            writer.writerows(zip(*result["waveforms"].values()))
        legacy.write_json(output / (case + "-window.json"), {"schema_version": 1, "capture_id": "synthetic-" + case,
                                                           "evidence_kind": "synthetic", "records": result["capture_records"]})
        legacy.write_json(output / (case + "-decoded.json"), result["decoded_events"])
        summaries.append({key: value for key, value in result.items()
                          if key not in ("waveforms", "capture_record", "capture_records", "decoded_events")})
    legacy.write_json(output / "scenarios.json", summaries)
    parameters = design()[0]["parameters"]
    sweep = [direct_ac(parameters, frequency, delta, protection)
             for frequency in (100000, 1000000, 10000000) for delta, protection in ((0, 0), (0.25, 0), (0, 0.1), (0.25, 0.1))]
    legacy.write_json(output / "comparison.json", {"legacy": legacy.matching_decomposition(),
                                                 "legacy_perfect_resistors": legacy.precision_sweep()[-1],
                                                 "differential_ac_sweep": sweep,
                                                 "high_resistance_attenuator": attenuation_example(),
                                                 "bench_P4_capacitance_pf": parameters["input_common_pf"] +
                                                 2 * parameters["input_differential_pf"] + parameters["board_pf"],
                                                 "capacitance_and_off_state_qualified": False})
    worst = summaries[6]
    conditional = threshold_interval(worst["minimum_signed_midcell_signal_v"],
                                     0.3 * worst["common_mode_conversion_bound_v_per_v"], 0.002, 0.001, 0.001)
    legacy.write_json(output / "thresholds.json", {"conditional_model": conditional,
                                                 "local_reference_example": threshold_reference_example(),
                                                 "guaranteed_design": threshold_interval(None, None, 0.002, None, None)})
    legacy.write_json(output / "backend-rates.json", backend_rates())
    legacy.write_json(output / "review.json", review_summary())
    pipeline_results = []
    if include_pipeline:
        profiles = [(f"N{index}", None) for index in range(1, 7)] + [("N7", None)]
        profiles += [("N1", fault) for fault in ("invalid", "gap", "unknown_direction", "channel_skew", "direct")]
        for case, fault in profiles:
            capture, analysis = pipeline_capture(case, 20, fault)
            name = case + ("-" + fault if fault else "")
            legacy.write_json(output / ("pipeline-" + name + "-window.json"), capture)
            legacy.write_json(output / ("pipeline-" + name + "-analysis.json"), analysis)
            pipeline_results.append({"profile": name, "completeness": analysis["completeness"],
                                     "enable": analysis["gates"]["W1.2"]["result"],
                                     "payload_ids": analysis["gates"]["W1.7"]["observed_payload_ids"]})
    source_names = ["tools/dp_aux_differential.py", "hardware/aux-observer/differential.json",
                    "tools/dp_aux_closure.py", "hardware/aux-observer/closure.json", "tools/dp_aux_frontend_model.py",
                    "hardware/aux-observer/model.json", "tools/dp_aux_decode.py", "tools/dp_mst_decode.py",
                    "tools/dp_wire_analyze.py", "tools/dp_wire_synthetic.py"]
    manifest = {"schema_version": 1, "evidence_kind": "synthetic", "hardware_authorized": False,
                "component_guarantees_established": False, "spice_executed": False, "step_ns": step_ns,
                "pipeline_step_ns": 20,
                "model_kind": "CONDITIONAL_DIFFERENTIAL_RECEIVER_MODEL", "pipeline_results": pipeline_results,
                "source_sha256": {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in source_names},
                "criteria_sha256": design()[0]["criteria_sha256"]}
    legacy.write_json(output / "manifest.json", manifest)
    hashes = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(output.iterdir())}
    legacy.write_json(output / "hashes.json", hashes)
    return {"files_hashed": len(hashes), "pipeline_results": pipeline_results,
            "scenarios": [{key: value for key, value in result.items() if key in
                           ("case", "residual_margin_mv", "packet_recovered", "evaluation")} for result in summaries],
            "hardware_authorized": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=pathlib.Path)
    parser.add_argument("--step-ns", type=int, choices=(1, 5, 20), default=5)
    parser.add_argument("--skip-pipeline", action="store_true")
    parser.add_argument("--window-input", type=pathlib.Path)
    arguments = parser.parse_args()
    try:
        if arguments.window_input:
            if arguments.output:
                raise ValueError("Window decoding cannot also generate model evidence")
            result = wire.analyze(adapt_window_capture(aux.load_capture(arguments.window_input)))["analysis"]
        elif arguments.output:
            result = run_evidence(arguments.output, arguments.step_ns, not arguments.skip_pipeline)
        else:
            parameters = design()[0]["parameters"]
            result = {"legacy_frontend": legacy.matching_decomposition(), "hardware_authorized": False,
                      "differential_frontend": [direct_ac(parameters, frequency, 0.25, 0.1)
                                                 for frequency in (100000, 1000000, 10000000)],
                      "backend_rates": backend_rates()}
        print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))
    except (OSError, ValueError) as error:
        parser.exit(2, str(error) + "\n")


if __name__ == "__main__":
    main()