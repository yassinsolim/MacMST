#!/usr/bin/env python3
"""M5P9 offline circuit closure analysis. No hardware or acquisition interface."""

import argparse
import csv
import hashlib
import json
import math
import pathlib

import dp_aux_decode as aux
import dp_aux_frontend_model as baseline
import dp_wire_analyze as wire
import dp_wire_synthetic as synthetic


ROOT = pathlib.Path(__file__).resolve().parents[1]
CRITERIA = ROOT / "hardware/aux-observer/closure.json"


def factor_matrix(matrix):
    factors = [list(row) for row in matrix]
    size = len(factors)
    order = list(range(size))
    for column in range(size):
        pivot = max(range(column, size), key=lambda row: abs(factors[row][column]))
        if abs(factors[pivot][column]) < 1e-20:
            raise ValueError("Singular circuit matrix")
        factors[column], factors[pivot] = factors[pivot], factors[column]
        order[column], order[pivot] = order[pivot], order[column]
        for row in range(column + 1, size):
            factors[row][column] /= factors[column][column]
            for following in range(column + 1, size):
                factors[row][following] -= factors[row][column] * factors[column][following]
    return factors, order


def solve_factored(factorization, vector):
    factors, order = factorization
    answer = [vector[index] for index in order]
    for row in range(len(answer)):
        answer[row] -= sum(factors[row][column] * answer[column] for column in range(row))
    for row in range(len(answer) - 1, -1, -1):
        answer[row] = (answer[row] - sum(factors[row][column] * answer[column]
                                       for column in range(row + 1, len(answer)))) / factors[row][row]
    return answer


class RcCircuit:
    """Backward-Euler nodal RC solver with explicit piecewise-linear diodes."""

    def __init__(self, nodes, resistors, capacitors, diodes=()):
        if len(nodes) != len(set(nodes)) or not 0 < len(nodes) <= 32:
            raise ValueError("Invalid circuit nodes")
        self.nodes = tuple(nodes)
        self.index = {name: index for index, name in enumerate(nodes)}
        self.resistors = tuple(resistors)
        self.capacitors = tuple(capacitors)
        self.diodes = tuple(diodes)
        self.factorizations = {}
        for first, second, value in (*self.resistors, *self.capacitors):
            baseline.positive(value, "circuit component")
            if first == second:
                raise ValueError("Shorted circuit component")
        for first, second, threshold, resistance in self.diodes:
            baseline.positive(threshold, "diode threshold")
            baseline.positive(resistance, "diode resistance")

    def solve(self, known, previous=None, dt_s=None, injections=None):
        if previous is not None:
            baseline.positive(dt_s, "time step")
        injections = injections or {}
        voltage = {**known, **{node: (previous or {}).get(node, 0.0) for node in self.nodes}}
        active = tuple(voltage[first] - voltage[second] > threshold for first, second, threshold, unused in self.diodes)
        for iteration in range(64):
            matrix = [[0.0] * len(self.nodes) for unused in self.nodes]
            vector = [injections.get(node, 0.0) for node in self.nodes]

            def stamp(first, second, conductance, history=0.0):
                for source, sink, sign in ((first, second, 1), (second, first, -1)):
                    if source not in self.index:
                        continue
                    row = self.index[source]
                    matrix[row][row] += conductance
                    vector[row] += sign * history
                    if sink in self.index:
                        matrix[row][self.index[sink]] -= conductance
                    else:
                        vector[row] += conductance * known[sink]

            for first, second, resistance in self.resistors:
                stamp(first, second, 1 / resistance)
            if previous is not None:
                for first, second, capacitance in self.capacitors:
                    conductance = capacitance / dt_s
                    stamp(first, second, conductance, conductance * (previous[first] - previous[second]))
            for enabled, (first, second, threshold, resistance) in zip(active, self.diodes):
                if enabled:
                    stamp(first, second, 1 / resistance, threshold / resistance)
            key = (dt_s if previous is not None else None, active, tuple(sorted(known)))
            if key not in self.factorizations:
                self.factorizations[key] = factor_matrix(matrix)
            solution = solve_factored(self.factorizations[key], vector)
            voltage.update(zip(self.nodes, solution))
            updated = tuple(voltage[first] - voltage[second] > threshold + 1e-12
                            for first, second, threshold, unused in self.diodes)
            if updated == active:
                residual = max(abs(sum(value * solution[column] for column, value in enumerate(row)) - vector[index])
                               for index, row in enumerate(matrix))
                if not all(math.isfinite(value) for value in solution) or residual > 1e-7:
                    raise ValueError("Circuit residual or finite-value check failed")
                return voltage, {"iterations": iteration + 1, "residual_a": residual,
                                 "diode_currents_a": [max(0, (voltage[first] - voltage[second] - threshold) / resistance)
                                                       for first, second, threshold, resistance in self.diodes]}
            active = updated
        raise ValueError("Piecewise-linear circuit did not converge")

    def ac(self, known, frequency_hz):
        laplace = 2j * math.pi * baseline.positive(frequency_hz, "frequency")
        matrix = [[0j] * len(self.nodes) for unused in self.nodes]
        vector = [0j] * len(self.nodes)
        elements = [(first, second, 1 / value) for first, second, value in self.resistors]
        elements.extend((first, second, laplace * value) for first, second, value in self.capacitors)
        for first, second, admittance in elements:
            for source, sink in ((first, second), (second, first)):
                if source not in self.index:
                    continue
                row = self.index[source]
                matrix[row][row] += admittance
                if sink in self.index:
                    matrix[row][self.index[sink]] -= admittance
                else:
                    vector[row] += admittance * known.get(sink, 0)
        return dict(zip(self.nodes, solve_factored(factor_matrix(matrix), vector)))


def capacitive_gain(sense_pf, input_pf):
    baseline.positive(sense_pf, "sense capacitance")
    baseline.positive(input_pf, "input capacitance")
    return sense_pf / (sense_pf + input_pf)


def leg_transfer(sense_pf, input_pf, bias_ohm, series_ohm, frequency_hz):
    laplace = 2j * math.pi * baseline.positive(frequency_hz, "frequency")
    sense = baseline.positive(sense_pf, "sense capacitance") * 1e-12
    input_cap = baseline.positive(input_pf, "input capacitance") * 1e-12
    resistance = baseline.positive(bias_ohm, "bias resistance")
    series = baseline.positive(series_ohm, "series resistance")
    return laplace * sense * resistance / (1 + laplace * (series * sense + resistance * (sense + input_cap)) +
                                           laplace * laplace * series * resistance * sense * input_cap)


def matching_decomposition():
    design = baseline.load_design()
    nominal = design["parameters"]
    rows = []
    for label in ("nominal", "resistors_only", "sense_caps_only", "input_caps_only", "combined"):
        first, second = dict(nominal), dict(nominal)
        for leg, sign in ((first, 1), (second, -1)):
            if label in ("resistors_only", "combined"):
                for name in ("bias_ohm", "sense_series_ohm", "input_series_ohm"):
                    leg[name] *= 1 + sign * 0.01
            if label in ("sense_caps_only", "combined"):
                leg["sense_pf"] += sign * 0.1
            if label in ("input_caps_only", "combined"):
                leg["input_pf"] -= sign * 0.125
        result = baseline.pair_transfer(first, second, 1000000, common_mode=True)
        plateau = capacitive_gain(first["sense_pf"], first["input_pf"]) - capacitive_gain(second["sense_pf"], second["input_pf"])
        rows.append({"case": label, "frequency_hz": 1000000,
                     "full_network_error_mv": abs(result["sense"]) * 300,
                     "capacitive_plateau_error_mv": abs(plateau) * 300})
    return rows


def precision_sweep():
    nominal = baseline.load_design()["parameters"]
    rows = []
    for tolerance in (0.01, 0.001, 0.0005, 0.0001, 0):
        first, second = dict(nominal), dict(nominal)
        for leg, sign in ((first, 1), (second, -1)):
            for name in ("bias_ohm", "sense_series_ohm", "input_series_ohm"):
                leg[name] *= 1 + sign * tolerance
            leg["sense_pf"] += sign * 0.1
            leg["input_pf"] -= sign * 0.125
        error = abs(baseline.pair_transfer(first, second, 1000000, common_mode=True)["sense"]) * 300
        rows.append({"per_leg_resistor_tolerance_fraction": tolerance, "combined_error_mv": error})
    return rows


def network(parameters, attached=True, powered=True, mismatch=False, upper_clamp=False):
    nodes = ["txp", "txn", "busp", "busn", "sinkp", "sinkn"]
    resistors = [("sinkp", "sinkn", parameters["sink_differential_ohm"]),
                 ("sinkp", "ground", 1e12), ("sinkn", "ground", 1e12)]
    capacitors = []
    diodes = []
    injections = {}
    for suffix, sign in (("p", 1), ("n", -1)):
        resistors.extend([("drive" + suffix, "tx" + suffix, parameters["source_leg_ohm"]),
                          ("bus" + suffix, "bias" + suffix, parameters["endpoint_bias_ohm"])])
        capacitors.extend([("tx" + suffix, "bus" + suffix, parameters["endpoint_coupling_nf"] * 1e-9),
                           ("bus" + suffix, "sink" + suffix, parameters["endpoint_coupling_nf"] * 1e-9)])
        if not attached:
            continue
        nodes.extend(["prot" + suffix, "coupled" + suffix, "input" + suffix])
        ratio = 1 + sign * parameters.get("resistor_tolerance", 0)
        sense = parameters["sense_pf"] + sign * parameters.get("sense_delta_pf", 0.1 if mismatch else 0)
        input_cap = parameters["input_shunt_pf"] + sign * parameters.get("input_delta_pf", -0.125 if mismatch else 0)
        protection_cap = parameters["protection_pf"] + sign * parameters.get("protection_delta_pf", 0)
        resistors.extend([("bus" + suffix, "prot" + suffix, parameters["branch_ohm"] * ratio),
                          ("coupled" + suffix, "input" + suffix, parameters["limiter_ohm"] * ratio),
                          ("input" + suffix, "midpoint", parameters["input_bias_ohm"] * ratio)])
        capacitors.extend([("bus" + suffix, "ground", parameters["bus_stray_pf"] * 1e-12),
                           ("prot" + suffix, "ground", protection_cap * 1e-12),
                           ("prot" + suffix, "coupled" + suffix, sense * 1e-12),
                           ("input" + suffix, "ground", input_cap * 1e-12)])
        diodes.extend([("prot" + suffix, "ground", parameters["tvs_threshold_v"], parameters["tvs_dynamic_ohm"]),
                       ("ground", "prot" + suffix, parameters["tvs_threshold_v"], parameters["tvs_dynamic_ohm"]),
                       ("ground", "input" + suffix, parameters["input_clamp_drop_v"], parameters["input_clamp_dynamic_ohm"])])
        if upper_clamp:
            diodes.append(("input" + suffix, "rail", parameters["input_clamp_drop_v"], parameters["input_clamp_dynamic_ohm"]))
        injections["input" + suffix] = -parameters["input_bias_a"] + sign * parameters.get("input_leakage_imbalance_a", 0)
        injections["prot" + suffix] = sign * parameters.get("protection_leakage_imbalance_a", 0)
    if attached:
        nodes.extend(["rail", "midpoint"])
        resistors.extend([("power", "rail", 1 if powered else parameters["off_supply_ohm"]),
                          ("rail", "midpoint", parameters["bias_divider_leg_ohm"]),
                          ("midpoint", "ground", parameters["bias_divider_leg_ohm"])])
        capacitors.extend([("inputp", "inputn", parameters["input_cross_pf"] * 1e-12),
                           ("rail", "ground", parameters["rail_capacitance_uf"] * 1e-6),
                           ("midpoint", "ground", parameters["bias_capacitance_nf"] * 1e-9)])
    return RcCircuit(nodes, resistors, capacitors, diodes), injections


def scenario_parameters(case, extra=None):
    if case not in {f"E{index}" for index in range(11)}:
        raise ValueError("Unknown electrical scenario")
    configuration = json.loads(CRITERIA.read_bytes())["numerical_assumptions"]
    parameters = dict(configuration)
    if case in ("E2", "E8"):
        parameters["resistor_tolerance"] = 0.01
    if case in ("E3", "E8"):
        parameters["offset_v"] = configuration["maximum_sweep_offset_v"]
    if case in ("E4", "E8"):
        parameters["protection_pf"] = configuration["maximum_sweep_protection_pf"]
    if case in ("E5", "E8"):
        parameters["input_shunt_pf"] = configuration["maximum_sweep_input_pf"]
    if case in ("E6", "E8"):
        parameters["input_leakage_imbalance_a"] = configuration["maximum_sweep_input_leakage_a"]
        parameters["protection_leakage_imbalance_a"] = configuration["maximum_sweep_protection_leakage_a"]
    parameters.update(extra or {})
    return parameters


def sensitivity_sweep():
    nominal = scenario_parameters("E1")
    sweep_values = {"resistor_tolerance": [0, 0.0001, 0.0005, 0.001, 0.01],
                    "offset_v": [-0.006, -0.002, 0, 0.002, 0.006],
                    "sense_delta_pf": [-0.1, -0.02, 0, 0.02, 0.1],
                    "input_delta_pf": [-0.25, -0.125, 0, 0.125, 0.25],
                    "protection_delta_pf": [-0.1, -0.02, 0, 0.02, 0.1],
                    "input_leakage_imbalance_a": [-5e-9, -1e-9, 0, 1e-9, 5e-9],
                    "protection_leakage_imbalance_a": [-10e-9, -5e-9, 0, 5e-9, 10e-9]}
    rows = []
    for parameter, values in sweep_values.items():
        for value in values:
            parameters = {**nominal, parameter: value}
            circuit, injections = network(parameters)
            common = circuit.ac({"drivep": 1, "driven": 1}, 1000000)
            dc, unused = circuit.solve({"ground": 0, "drivep": 0, "driven": 0, "biasp": 0.3, "biasn": 3,
                                         "power": parameters["supply_v"]}, injections=injections)
            conversion = abs(common["inputp"] - common["inputn"])
            input_offset = abs(dc["inputp"] - dc["inputn"])
            offset_term = abs(value) if parameter == "offset_v" else 0
            rows.append({"parameter": parameter, "value": value, "classification": "ASSUMED_SWEEP_NOT_PART_GUARANTEE",
                         "common_mode_error_mv_at_0_3v": conversion * 300,
                         "dc_input_error_mv": input_offset * 1000,
                         "combined_magnitude_mv": conversion * 300 + input_offset * 1000 + offset_term * 1000})
    ranking = sorted(({"parameter": parameter,
                       "maximum_contribution_mv": max(row["combined_magnitude_mv"] for row in rows if row["parameter"] == parameter)}
                      for parameter in sweep_values), key=lambda row: row["maximum_contribution_mv"], reverse=True)
    return {"rows": rows, "ranking": ranking, "monte_carlo_used": False}


def alternative_coupling():
    rows = []
    for sense in (2.2, 10, 22, 47, 100):
        error = abs(capacitive_gain(sense + 0.1, 2.375) - capacitive_gain(sense - 0.1, 2.625)) * 300
        rows.append({"sense_pf": sense, "plateau_error_mv": error,
                     "conducting_clamp_capacitance_bound_pf": sense + 0.23 + 0.5,
                     "matching_target_met_in_approximation": error <= 1.5,
                     "off_capacitance_target_met": sense + 0.73 <= 4})
    return rows


def error_budget():
    decomposition = {row["case"]: row for row in matching_decomposition()}
    contributions = [
        {"name": "resistor_ratio", "nominal_mv": 0, "bounded_or_assumed_mv": decomposition["resistors_only"]["full_network_error_mv"], "basis": "M5P8 +/-1% assumed corner"},
        {"name": "resistor_temperature_tracking", "nominal_mv": 0, "bounded_or_assumed_mv": None, "basis": "Network part and temperature range not selected; RES11A ratio drift not a bound on comparator C"},
        {"name": "comparator_offset", "nominal_mv": 0.3, "bounded_or_assumed_mv": 2, "basis": "TLV9031 stated 1.8V/5V and temperature conditions; 3.3V complete envelope still unqualified"},
        {"name": "input_bias_mismatch", "nominal_mv": 0.001, "bounded_or_assumed_mv": None, "basis": "1pA typical offset current times 1Mohm; no guaranteed maximum in inspected table"},
        {"name": "sense_cap_mismatch", "nominal_mv": 0, "bounded_or_assumed_mv": decomposition["sense_caps_only"]["full_network_error_mv"], "basis": "+/-0.1pF assumed, not selected capacitor matching"},
        {"name": "input_cap_mismatch", "nominal_mv": 0, "bounded_or_assumed_mv": decomposition["input_caps_only"]["full_network_error_mv"], "basis": "0.25pF assumed difference; no device maximum/matching guarantee"},
        {"name": "ESD_leakage_mismatch", "nominal_mv": 0, "bounded_or_assumed_mv": None, "basis": "Before sense cap DC contribution blocked; leakage transients and temperature envelope not closed"},
        {"name": "PCB_parasitic_mismatch", "nominal_mv": 0, "bounded_or_assumed_mv": None, "basis": "No selected connector/stackup extracted capacitance"},
        {"name": "supply_offset_variation", "nominal_mv": 0, "bounded_or_assumed_mv": 0.165 * 10**(-75/20) * 1000, "basis": "Assumed +/-5% of 3.3V with TLV9031 stated minimum75dB PSRR; not total midpoint/transient error"},
        {"name": "intrinsic_common_mode_rejection", "nominal_mv": 0.3 * 10**(-70/20) * 1000, "bounded_or_assumed_mv": 0.3 * 10**(-50/20) * 1000, "basis": "Conservative inspected CMRR condition; separate from external-network conversion"},
        {"name": "threshold_and_noise", "nominal_mv": 0, "bounded_or_assumed_mv": None, "basis": "No internal hysteresis; no independent threshold/noise margin design"},
        {"name": "edge_delay_asymmetry", "nominal_mv": None, "bounded_or_assumed_mv": None, "basis": "Time-domain contribution requires delay dispersion versus overdrive/temperature, not nominal fixed delay"}]
    return {"contributions": contributions,
            "nominal_known_terms_mv": sum(row["nominal_mv"] or 0 for row in contributions),
            "guaranteed_total_worst_case_mv": None,
            "worst_case_closed": False,
            "rss_used_as_acceptance": False,
            "reason": "Unbounded critical terms cannot be treated as zero or replaced with statistics"}


def simulate_packet(raw_hex="90002100", case="E1", step_ns=None, attached=None,
                    extra=None, retain=True):
    parameters = scenario_parameters(case, extra)
    step = parameters["step_ns"] if step_ns is None else step_ns
    if type(step) is not int or step <= 0 or parameters["half_cell_ns"] % step:
        raise ValueError("Time step must divide a half-cell")
    powered = case != "E7"
    enabled = case != "E0" if attached is None else attached
    circuit, injections = network(parameters, enabled, powered, case == "E8", parameters.get("upper_clamp", False))
    known = {"ground": 0.0, "drivep": 0.0, "driven": 0.0, "biasp": 0.3, "biasn": 3.0,
             "power": parameters["supply_v"] if powered else 0.0}
    previous, unused = circuit.solve(known, injections=injections)
    bits = baseline.manchester(raw_hex, step, parameters["half_cell_ns"])
    packet_start = 4000
    packet_end = packet_start + len(bits) * step
    reply_bits = baseline.manchester("0001", step, parameters["half_cell_ns"]) if case == "E10" else []
    reply_start = packet_end + 10000
    waveform_end = reply_start + len(reply_bits) * step if reply_bits else packet_end
    stop = waveform_end + 50000
    data = {name: [] for name in ("time_ns", "source_differential_v", "source_common_mode_v",
                                  "sink_differential_v", "bus_differential_v", "observer_differential_v",
                                  "rail_v", "rail_injection_a", "input_positive_v", "input_negative_v",
                                  "digital", "ideal_digital")}
    pending_edges = []
    comparator = digital = 0
    last_ideal = 0
    edges = []
    ideal_edges = []
    maximum_residual = 0.0
    maximum_diode_current = 0.0
    edge_number = 0

    def stimulus(values, index):
        peak = parameters["source_differential_peak_v"]
        elapsed = index * step
        duration = len(values) * step
        if elapsed < 0 or elapsed >= duration + 10:
            return 0.0
        if elapsed >= duration:
            return (peak if values[-1] else -peak) * (1 - (elapsed - duration) / 10)
        cell_start = index - index % (parameters["half_cell_ns"] // step)
        target = peak if values[index] else -peak
        prior = (peak if values[cell_start - 1] else -peak) if cell_start else 0
        fraction = min(1, (index - cell_start) * step / 10)
        return prior + fraction * (target - prior)

    for timestamp in range(0, stop + step, step):
        index = (timestamp - packet_start) // step
        reply_index = (timestamp - reply_start) // step
        in_request = 0 <= index < len(bits)
        in_reply = 0 <= reply_index < len(reply_bits)
        ideal = bits[index] if in_request else reply_bits[reply_index] if in_reply else last_ideal
        near_differential = stimulus(bits, index)
        far_differential = stimulus(reply_bits, reply_index) if reply_bits else 0
        differential = near_differential + far_differential
        common = parameters["common_mode_peak_v"] * math.sin(2 * math.pi * timestamp * 1e-9 * 1000000)
        if case == "E7":
            common = 3.6 * max(0, min(1, (timestamp - 12000) / 10, (16010 - timestamp) / 10))
        known.update(drivep=common + near_differential / 2, driven=common - near_differential / 2)
        currents = dict(injections)
        if far_differential:
            currents.update(sinkp=far_differential / parameters["sink_differential_ohm"],
                            sinkn=-far_differential / parameters["sink_differential_ohm"])
        voltage, metrics = circuit.solve(known, previous, step * 1e-9, currents)
        maximum_residual = max(maximum_residual, metrics["residual_a"])
        maximum_diode_current = max(maximum_diode_current, max(metrics["diode_currents_a"], default=0))
        observed = voltage.get("inputp", 0) - voltage.get("inputn", 0)
        rail = voltage.get("rail", 0)
        if in_request or in_reply:
            if ideal != last_ideal:
                ideal_edges.append(timestamp)
            last_ideal = ideal
        target = comparator
        threshold = parameters.get("offset_v", 0)
        if rail < 1.65:
            target = 0
        elif observed > threshold + parameters["comparator_hysteresis_v"] / 2:
            target = 1
        elif observed < threshold - parameters["comparator_hysteresis_v"] / 2:
            target = 0
        if target != comparator:
            delay = parameters.get("rise_delay_ns" if target else "fall_delay_ns", parameters["comparator_delay_ns"])
            jitter = parameters.get("jitter_ns", 0) * (1 if edge_number % 2 else -1)
            pending_edges.append((timestamp + delay + jitter, target))
            pending_edges.sort()
            edge_number += 1
            comparator = target
        while pending_edges and pending_edges[0][0] <= timestamp:
            unused, new_level = pending_edges.pop(0)
            if new_level != digital:
                edges.append(timestamp)
            digital = new_level
        rail_injection = ((voltage.get("midpoint", 0) - rail) / parameters["bias_divider_leg_ohm"] if enabled else 0)
        for first, second, threshold, resistance in circuit.diodes:
            if second == "rail":
                rail_injection += max(0, (voltage[first] - voltage[second] - threshold) / resistance)
        values = (timestamp, differential, common, voltage["sinkp"] - voltage["sinkn"],
                  voltage["busp"] - voltage["busn"], observed, rail, rail_injection,
                  voltage.get("inputp", 0), voltage.get("inputn", 0), digital, ideal)
        for name, value in zip(data, values):
            data[name].append(value)
        previous = voltage
    midcells = range((packet_start + parameters["half_cell_ns"] // 2) // step, packet_end // step,
                     parameters["half_cell_ns"] // step)
    margin = min((1 if data["ideal_digital"][index] else -1) *
                 (data["observer_differential_v"][index] - parameters.get("offset_v", 0)) -
                 parameters["comparator_hysteresis_v"] / 2 for index in midcells) if enabled and powered else None
    cutoff = max(abs(value) for value in data["observer_differential_v"]) * 0.01
    unsettled = [index for index in range(waveform_end // step, len(data["time_ns"]))
                 if abs(data["observer_differential_v"][index] -
                        data["observer_differential_v"][0]) > cutoff]
    settling = None if unsettled and unsettled[-1] == len(data["time_ns"]) - 1 else (data["time_ns"][unsettled[-1]] - waveform_end + step if unsettled else 0)
    matching_edges = [edge for edge in edges if packet_start <= edge <= packet_end + parameters["comparator_delay_ns"] + 500]
    request_ideal = [edge for edge in ideal_edges if edge < packet_end]
    timing = [edge - reference - parameters["comparator_delay_ns"] for edge, reference in zip(matching_edges, request_ideal)] if len(matching_edges) == len(request_ideal) else []
    sample_period = parameters["sample_period_ns"]
    if sample_period % step:
        raise ValueError("Sampling period must be an integral simulation-step multiple")
    record = {"representation": "digital_samples", "timestamp_ns": 0,
              "kind": "request", "direction": "source_to_sink", "direction_basis": "synthetic_circuit_stimulus",
              "loss_state": "none", "sample_period_ns": sample_period,
              "samples": data["digital"][::sample_period // step]}
    records = [record]
    if reply_bits:
        split = (reply_start - 2000) // sample_period
        records = [{**record, "samples": record["samples"][:split]},
                   {**record, "samples": record["samples"][split:], "timestamp_ns": split * sample_period,
                    "kind": "reply", "direction": "sink_to_source"}]
    decoded = aux.decode_capture({"schema_version": 1, "capture_id": "synthetic-closure-" + case,
                                  "evidence_kind": "synthetic", "records": records})
    recovered = any(event["request_raw"] == raw_hex and not event["malformed"] and not event["truncated"]
                    for event in decoded["events"])
    common_response = circuit.ac({"drivep": 1, "driven": 1}, 1000000)
    summary = {"case": case, "model_kind": "NUMERICAL_CIRCUIT_MODEL", "hardware_authorized": False,
               "zero_threshold_numerical_sensitivity": parameters.get("offset_v", 0) == 0 and parameters["comparator_hysteresis_v"] == 0,
               "component_limits_guaranteed": False, "parameters": parameters, "step_ns": step,
               "source_peak_v": max(abs(value) for value in data["source_differential_v"]),
               "sink_peak_v": max(abs(value) for value in data["sink_differential_v"]),
               "observer_peak_v": max(abs(value) for value in data["observer_differential_v"]) if enabled else None,
               "residual_margin_mv": margin * 1000 if margin is not None else None,
               "settling_to_one_percent_ns": settling,
               "maximum_rail_v": max(data["rail_v"]) if enabled else None,
               "minimum_input_v": min(min(data["input_positive_v"]), min(data["input_negative_v"])) if enabled else None,
               "maximum_input_v": max(max(data["input_positive_v"]), max(data["input_negative_v"])) if enabled else None,
               "maximum_positive_rail_injection_ua": max(0, max(data["rail_injection_a"])) * 1e6,
               "maximum_diode_current_ma": maximum_diode_current * 1000,
               "common_mode_conversion_v_per_v": abs(common_response.get("inputp", 0) - common_response.get("inputn", 0)) if enabled and powered else None,
               "maximum_kcl_residual_a": maximum_residual,
               "edge_count": len(matching_edges), "expected_edge_count": len(request_ideal),
               "maximum_added_crossing_error_ns": max(map(abs, timing)) if timing else None,
               "edge_dispersion_ns": max(timing) - min(timing) if timing else None,
               "request_recovered": recovered, "capture_record": record, "capture_records": records,
               "reply_recovered": any(event["reply_raw"] == "0001" and not event["malformed"] and not event["truncated"]
                                       for event in decoded["events"]) if reply_bits else None,
               "transaction_accepted": any(transaction["accepted"] for transaction in decoded["transactions"]),
               "decoded_events": decoded["events"]}
    if retain:
        summary["waveforms"] = data
    return summary


def pipeline_capture(profile="nominal", step_ns=25):
    choices = {"nominal": ("E1", {}),
               "accepted_envelope": ("E5", {"offset_v": 0.002}),
               "jittered": ("E1", {"offset_v": 0.002, "jitter_ns": 5}),
               "asymmetric": ("E1", {"offset_v": -0.002, "rise_delay_ns": 115, "fall_delay_ns": 100}),
               "powered_off": ("E7", {}), "glitched": ("E1", {"offset_v": 0.002})}
    if profile not in choices:
        raise ValueError("Unknown pipeline profile")
    case, extra = choices[profile]
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
    cache = {}
    records = []
    for index, source in enumerate(trace.records):
        raw = source["raw_hex"]
        if raw not in cache:
            result = simulate_packet(raw, case, step_ns, extra=extra, retain=False)
            cache[raw] = result["capture_record"]
        record = dict(cache[raw])
        record.update(timestamp_ns=source["timestamp_ns"], kind=source["kind"], direction=source["direction"])
        if profile == "glitched" and index == 4:
            record["samples"] = list(record["samples"])
            record["samples"][1200:1204] = [1 - value for value in record["samples"][1200:1204]]
        records.append(record)
    capture = {"schema_version": 1, "capture_id": "synthetic-closure-pipeline-" + profile,
               "capture_generation": "synthetic-closure-generation-" + profile,
               "physical_link_id": "synthetic-circuit-link", "evidence_kind": "synthetic",
               "interval": {"start_ns": 0, "end_ns": trace.timestamp + 500000},
               "coverage": {"complete": True, "armed_before_attach": True, "filters_disabled": True,
                            "loss_state": "none", "initial_payload_table_empty": True},
               "acquisition": {"model_kind": "NUMERICAL_CIRCUIT_MODEL", "hardware_authorized": False,
                               "continuous_analog_state": False, "window_initialization": "DC operating point per packet",
                               "purpose": "Electrical packet-window interoperability, not continuous capture completeness",
                               "profile": profile, "step_ns": step_ns, "case": case, "extra": extra},
               "records": records}
    return capture, wire.analyze(capture)["analysis"]


def evaluate_model(result, reference):
    criteria = json.loads(CRITERIA.read_bytes())["criteria"]
    amplitude_error = abs(result["sink_peak_v"] / reference["sink_peak_v"] - 1)
    checks = {"amplitude": amplitude_error <= criteria["maximum_amplitude_change_fraction"],
              "common_mode": (result["common_mode_conversion_v_per_v"] <= criteria["maximum_common_mode_conversion_v_per_v"]
                              if result["common_mode_conversion_v_per_v"] is not None else None),
              "margin": (result["residual_margin_mv"] >= criteria["minimum_residual_differential_margin_mv"]
                         if result["residual_margin_mv"] is not None else None),
              "crossing": (result["maximum_added_crossing_error_ns"] <= criteria["maximum_added_crossing_error_ns"]
                           if result["maximum_added_crossing_error_ns"] is not None else None),
              "dispersion": (result["edge_dispersion_ns"] <= criteria["maximum_edge_dispersion_ns"]
                             if result["edge_dispersion_ns"] is not None else None),
              "packet_recovery": result["request_recovered"],
              "guaranteed_component_envelope": False}
    if result["case"] == "E7":
        checks["off_rail"] = result["maximum_rail_v"] <= criteria["maximum_off_rail_v"]
    return {"amplitude_error_fraction": amplitude_error, "checks": checks,
            "hardware_authorized": False, "build_release": False,
            "scope": "Model checks are not component, PCB or power-off qualification"}


def write_json(path, value):
    with pathlib.Path(path).open("x", encoding="ascii") as stream:
        json.dump(value, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write("\n")


def run_evidence(destination, step_ns=5, include_pipeline=True):
    output = pathlib.Path(destination).absolute()
    if output.exists() or any(path.is_symlink() for path in (output, *output.parents)):
        raise ValueError("Evidence destination must be new and nonsymlinked")
    output.mkdir(parents=True, exist_ok=False)
    source_names = ["tools/dp_aux_closure.py", "hardware/aux-observer/closure.json",
                    "tools/dp_aux_frontend_model.py", "hardware/aux-observer/model.json",
                    "tools/dp_aux_decode.py", "tools/dp_mst_decode.py", "tools/dp_wire_analyze.py",
                    "tools/dp_wire_synthetic.py"]
    manifest = {"schema_version": 1, "evidence_kind": "synthetic", "model_kind": "NUMERICAL_CIRCUIT_MODEL",
                "hardware_authorized": False, "spice_executed": False, "step_ns": step_ns,
                "source_sha256": {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in source_names},
                "criteria_sha256": hashlib.sha256(json.dumps(json.loads(CRITERIA.read_bytes())["criteria"],
                                                              sort_keys=True).encode()).hexdigest()}
    summaries = []
    reference = simulate_packet(case="E0", step_ns=step_ns)
    for case in (f"E{index}" for index in range(11)):
        raw = "8004000f" + "aa55" * 8 if case == "E9" else "90002100"
        result = reference if case == "E0" else simulate_packet(raw, case, step_ns)
        matching_reference = reference
        if case in ("E7", "E9", "E10"):
            matching_reference = simulate_packet(raw, case, step_ns, attached=False)
        result["evaluation"] = evaluate_model(result, matching_reference)
        with (output / (case + "-waveform.csv")).open("x", encoding="ascii", newline="") as stream:
            writer = csv.writer(stream)
            writer.writerow(result["waveforms"])
            writer.writerows(zip(*result["waveforms"].values()))
        capture = {"schema_version": 1, "capture_id": "synthetic-closure-" + case,
                   "evidence_kind": "synthetic", "records": result["capture_records"],
                   "acquisition": {"model_kind": "NUMERICAL_CIRCUIT_MODEL", "parameters": result["parameters"],
                                   "step_ns": step_ns, "hardware_authorized": False}}
        write_json(output / (case + "-capture.json"), capture)
        write_json(output / (case + "-decoded.json"), result["decoded_events"])
        summaries.append({key: value for key, value in result.items()
                          if key not in {"waveforms", "capture_record", "capture_records", "decoded_events"}})
    write_json(output / "scenarios.json", summaries)
    write_json(output / "matching.json", {"decomposition": matching_decomposition(),
                                          "precision": precision_sweep(), "coupling_alternatives": alternative_coupling()})
    write_json(output / "error-budget.json", error_budget())
    write_json(output / "tolerances.json", sensitivity_sweep())
    pipeline_results = []
    if include_pipeline:
        for profile in ("nominal", "accepted_envelope", "jittered", "asymmetric", "powered_off", "glitched"):
            capture, analysis = pipeline_capture(profile, step_ns)
            write_json(output / ("pipeline-" + profile + ".json"), capture)
            write_json(output / ("pipeline-" + profile + "-analysis.json"), analysis)
            pipeline_results.append({"profile": profile, "completeness": analysis["completeness"],
                                     "enable": analysis["gates"]["W1.2"]["result"],
                                     "payload_ids": analysis["gates"]["W1.7"]["observed_payload_ids"]})
    manifest["pipeline_results"] = pipeline_results
    write_json(output / "manifest.json", manifest)
    hashes = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(output.iterdir())}
    write_json(output / "hashes.json", hashes)
    return {"files_hashed": len(hashes), "model_kind": "NUMERICAL_CIRCUIT_MODEL",
            "hardware_authorized": False, "pipeline_results": pipeline_results,
            "scenarios": [{"case": item["case"], "evaluation": item["evaluation"]} for item in summaries]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=pathlib.Path)
    parser.add_argument("--step-ns", type=int, choices=(1, 5, 25), default=5)
    parser.add_argument("--skip-pipeline", action="store_true")
    arguments = parser.parse_args()
    try:
        result = run_evidence(arguments.output, arguments.step_ns, not arguments.skip_pipeline) if arguments.output else {
            "model_kind": "NUMERICAL_CIRCUIT_MODEL", "hardware_authorized": False,
            "matching": matching_decomposition(), "resistor_precision": precision_sweep(),
            "coupling_alternatives": alternative_coupling(), "error_budget": error_budget(),
            "sensitivity": sensitivity_sweep()}
        print(json.dumps(result, sort_keys=True, indent=2, allow_nan=False))
    except (OSError, ValueError) as error:
        parser.exit(2, str(error) + "\n")


if __name__ == "__main__":
    main()