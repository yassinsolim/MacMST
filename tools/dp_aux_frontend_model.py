#!/usr/bin/env python3
"""Offline AUX loading calculations; assumptions are not DisplayPort limits."""

import argparse
import copy
import json
import math
import pathlib


DESIGN = pathlib.Path(__file__).resolve().parents[1] / "hardware/aux-observer/model.json"


def positive(value, name):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
        raise ValueError(f"Invalid {name}")
    return value


def series_sense(resistance_ohm, capacitance_pf, pin_voltage_v=3.6, clamp_voltage_v=0.3):
    resistance = positive(resistance_ohm, "series resistance")
    capacitance = positive(capacitance_pf, "input capacitance") * 1e-12
    return {"classification": "ASSUMED_FOR_SIMULATION",
            "resistance_ohm": resistance, "capacitance_pf": capacitance_pf,
            "pole_hz": 1 / (2 * math.pi * resistance * capacitance),
            "rise_10_90_ns": math.log(9) * resistance * capacitance * 1e9,
            "off_clamp_current_ua": max(0, pin_voltage_v - clamp_voltage_v) / resistance * 1e6}


def shunt_loading(source_ohm, termination_ohm, observer_ohm, capacitance_pf, frequency_hz):
    source = positive(source_ohm, "source impedance")
    termination = positive(termination_ohm, "termination")
    observer = positive(observer_ohm, "observer resistance")
    capacitance = positive(capacitance_pf, "shunt capacitance") * 1e-12
    frequency = positive(frequency_hz, "frequency")
    admittance = 1 / termination + 1 / observer + 2j * math.pi * frequency * capacitance
    transfer = 1 / (1 + source * admittance)
    baseline = termination / (termination + source)
    return {"classification": "ASSUMED_FOR_SIMULATION",
            "relative_amplitude": abs(transfer) / baseline,
            "phase_degrees": math.degrees(math.atan2(transfer.imag, transfer.real))}


def dc_bias_loading(observer_ohm, endpoint_bias_ohm=100000, bias_difference_v=2.7):
    observer = positive(observer_ohm, "DC observer resistance")
    endpoint = positive(endpoint_bias_ohm, "endpoint detection bias resistance")
    difference = positive(bias_difference_v, "bias difference")
    current = difference / (2 * endpoint + observer)
    return {"classification": "ASSUMED_FOR_SIMULATION", "observer_ohm": observer,
            "retained_bias_difference_v": current * observer,
            "observer_current_ua": current * 1e6,
            "relative_bias": observer / (2 * endpoint + observer)}


def load_design(path=DESIGN):
    value = json.loads(pathlib.Path(path).read_text(encoding="ascii"))
    if value.get("schema_version") != 1 or value.get("hardware_authorized") is not False:
        raise ValueError("Expected non-authorizing model schema")
    for name, parameter in value["parameters"].items():
        positive(parameter, name)
    return value


def ac_transfer(parameters, frequency_hz, attached=True, off=False):
    frequency = positive(frequency_hz, "frequency")
    laplace = 2j * math.pi * frequency
    source = parameters["source_leg_ohm"] + 1 / (laplace * parameters["source_coupling_nf"] * 1e-9)
    termination = parameters["termination_leg_ohm"]
    sink = termination + 1 / (laplace * parameters["sink_coupling_nf"] * 1e-9)
    input_impedance = 1 / (1 / parameters["bias_ohm"] + laplace * parameters["input_pf"] * 1e-12)
    if off:
        input_impedance = parameters["off_clamp_ohm"]
    coupled_input = 1 / (laplace * parameters["sense_pf"] * 1e-12) + parameters["input_series_ohm"] + input_impedance
    protected = 1 / (1 / coupled_input + laplace * parameters["protection_pf"] * 1e-12)
    sense = parameters["sense_series_ohm"] + protected
    admittance = 1 / sink + 1 / parameters["endpoint_bias_ohm"]
    if attached:
        admittance += 1 / sense + laplace * parameters["bus_stray_pf"] * 1e-12
    bus = 1 / (1 + source * admittance)
    return {"bus": bus, "sink": bus * termination / sink,
            "sense": bus * protected / sense * input_impedance / coupled_input if attached else 0j,
            "observer_admittance": 1 / sense + laplace * parameters["bus_stray_pf"] * 1e-12 if attached else 0j,
            "observer_gain": protected / sense * input_impedance / coupled_input if attached else 0j}


def pair_transfer(first, second, frequency_hz, attached=True, off=False, common_mode=False):
    laplace = 2j * math.pi * positive(frequency_hz, "frequency")
    source_first = first["source_leg_ohm"] + 1 / (laplace * first["source_coupling_nf"] * 1e-9)
    source_second = second["source_leg_ohm"] + 1 / (laplace * second["source_coupling_nf"] * 1e-9)
    termination = first["termination_leg_ohm"] + second["termination_leg_ohm"]
    sink = termination + 1 / (laplace * first["sink_coupling_nf"] * 1e-9) + 1 / (laplace * second["sink_coupling_nf"] * 1e-9)
    positive_branch = ac_transfer(first, frequency_hz, attached, off)
    negative_branch = ac_transfer(second, frequency_hz, attached, off)
    diagonal_first = 1 / source_first + 1 / sink + positive_branch["observer_admittance"] + 1 / first["endpoint_bias_ohm"]
    diagonal_second = 1 / source_second + 1 / sink + negative_branch["observer_admittance"] + 1 / second["endpoint_bias_ohm"]
    coupling = -1 / sink
    drive_first = (1 if common_mode else 0.5) / source_first
    drive_second = (1 if common_mode else -0.5) / source_second
    determinant = diagonal_first * diagonal_second - coupling * coupling
    bus_first = (drive_first * diagonal_second - coupling * drive_second) / determinant
    bus_second = (drive_second * diagonal_first - coupling * drive_first) / determinant
    return {"sink": (bus_first - bus_second) * termination / sink,
            "sense": bus_first * positive_branch["observer_gain"] - bus_second * negative_branch["observer_gain"]}


def loading_sweep(design):
    nominal = design["parameters"]
    cases = {}
    for name in ("S0", "S1", "S2", "S3", "S4"):
        positive_leg = dict(nominal)
        negative_leg = dict(nominal)
        if name == "S3":
            for leg in (positive_leg, negative_leg):
                leg["input_pf"] = design["worst_case"]["input_pf"]
                leg["bus_stray_pf"] = design["worst_case"]["bus_stray_pf"]
        if name == "S4":
            for leg, sign in ((positive_leg, 1), (negative_leg, -1)):
                leg["sense_pf"] += sign * design["worst_case"]["sense_tolerance_pf"]
                leg["bias_ohm"] *= 1 + sign * design["worst_case"]["resistor_fraction"]
                leg["sense_series_ohm"] *= 1 + sign * design["worst_case"]["resistor_fraction"]
                leg["input_series_ohm"] *= 1 + sign * design["worst_case"]["resistor_fraction"]
                leg["input_pf"] -= sign * design["worst_case"]["input_imbalance_pf"] / 2
        observations = []
        for frequency in design["frequencies_hz"]:
            baseline = pair_transfer(nominal, nominal, frequency, attached=False)
            differential = pair_transfer(positive_leg, negative_leg, frequency, attached=name != "S0", off=name == "S2")
            common = pair_transfer(positive_leg, negative_leg, frequency, attached=name != "S0", off=name == "S2", common_mode=True)
            observations.append({"frequency_hz": frequency,
                                 "sink_relative_amplitude": abs(differential["sink"] / baseline["sink"]),
                                 "sense_per_loaded_differential": abs(differential["sense"] / baseline["sink"]),
                                 "common_to_differential_gain": abs(common["sense"])})
        cases[name] = observations
    return cases


def manchester(raw_hex, sample_period_ns=10, half_period_ns=500):
    positive(sample_period_ns, "sample period")
    positive(half_period_ns, "half period")
    if type(sample_period_ns) is not int or type(half_period_ns) is not int or half_period_ns % sample_period_ns:
        raise ValueError("Integral sample count per half-cell required")
    raw = bytes.fromhex(raw_hex)
    if not raw or len(raw) > 20:
        raise ValueError("Bounded nonempty AUX packet required")
    cells = [0, 1] * 16 + [1] * 4 + [0] * 4
    for byte in raw:
        for shift in range(7, -1, -1):
            cells.extend((1, 0) if byte & (1 << shift) else (0, 1))
    cells.extend([1] * 4 + [0] * 4)
    return [cell for cell in cells for unused in range(half_period_ns // sample_period_ns)]


def conditioned_record(raw_hex="90002100", parameters=None, sample_period_ns=10,
                       half_period_ns=500, amplitude_v=0.09, threshold_v=0,
                       hysteresis_v=0.004, rise_delay_ns=40, fall_delay_ns=40,
                       jitter_ns=0, invert=False, missed_edge=None, glitch_at=None):
    parameters = parameters or load_design()["parameters"]
    ideal = manchester(raw_hex, sample_period_ns, half_period_ns)
    positive(amplitude_v, "differential amplitude")
    capacitance = parameters["sense_pf"] + parameters["input_pf"]
    gain = parameters["sense_pf"] / capacitance
    highpass_decay = math.exp(-sample_period_ns / (parameters["bias_ohm"] * capacitance * 1e-3))
    lowpass_tau_ns = (parameters["sense_series_ohm"] + parameters["input_series_ohm"]) * parameters["sense_pf"] * parameters["input_pf"] / capacitance * 1e-3
    lowpass_decay = math.exp(-sample_period_ns / lowpass_tau_ns)
    previous = highpass = filtered = 0.0
    level = 0
    transitions = []
    analog = []
    for index, bit in enumerate(ideal):
        voltage = amplitude_v if bit else -amplitude_v
        highpass = highpass_decay * highpass + gain * (voltage - previous)
        filtered = lowpass_decay * filtered + (1 - lowpass_decay) * highpass
        previous = voltage
        target = level
        if filtered > threshold_v + hysteresis_v / 2:
            target = 1
        elif filtered < threshold_v - hysteresis_v / 2:
            target = 0
        if target != level:
            edge = len(transitions)
            delay = rise_delay_ns if target else fall_delay_ns
            jitter = jitter_ns if edge % 2 else -jitter_ns
            at = max(0, index + round((delay + jitter) / sample_period_ns))
            transitions.append((at, target, edge))
            level = target
        analog.append(filtered)
    transitions.sort()
    extension = math.ceil((max(rise_delay_ns, fall_delay_ns) + abs(jitter_ns)) / sample_period_ns) + 2
    samples = []
    cursor = level = 0
    for index in range(len(ideal) + extension):
        while cursor < len(transitions) and transitions[cursor][0] <= index:
            unused, target, edge = transitions[cursor]
            if edge != missed_edge:
                level = target
            cursor += 1
        samples.append(level ^ bool(invert))
    if glitch_at is not None:
        start, width = glitch_at
        for index in range(start, min(start + width, len(samples))):
            samples[index] ^= 1
    record = {"representation": "digital_samples", "timestamp_ns": 0,
              "kind": "request", "direction": "source_to_sink",
              "direction_basis": "synthetic_frontend_model", "loss_state": "none",
              "evidence_kind": "synthetic", "sample_period_ns": sample_period_ns,
              "samples": [int(sample) for sample in samples]}
    metrics = {"classification": "ASSUMED_FOR_SIMULATION", "gain_high_frequency": gain,
               "highpass_tau_ns": parameters["bias_ohm"] * capacitance * 1e-3,
               "sense_peak_v": max(abs(voltage) for voltage in analog),
               "midcell_min_abs_v": min(abs(analog[index]) for index in range(half_period_ns // sample_period_ns // 2,
                                                                           len(analog), half_period_ns // sample_period_ns)),
               "edge_count": len(transitions), "sample_period_ns": sample_period_ns,
               "rise_delay_ns": rise_delay_ns, "fall_delay_ns": fall_delay_ns,
               "jitter_ns": jitter_ns, "threshold_v": threshold_v,
               "hardware_authorized": False}
    return record, metrics


def transient_bounds(parameters, step_v=3.6, rise_ns=10):
    positive(step_v, "step voltage")
    positive(rise_ns, "step rise time")
    capacitance = parameters["sense_pf"] * 1e-12
    effective = parameters["sense_pf"] * parameters["input_pf"] / (parameters["sense_pf"] + parameters["input_pf"])
    return {"classification": "ASSUMED_FOR_SIMULATION",
            "off_input_capacitance_bound_pf": parameters["sense_pf"] + parameters["protection_pf"] + parameters["bus_stray_pf"],
            "powered_effective_capacitance_pf": effective + parameters["protection_pf"] + parameters["bus_stray_pf"],
            "maximum_coupled_charge_pc": capacitance * step_v * 1e12,
            "resistor_limited_peak_ma": step_v / parameters["sense_series_ohm"] * 1e3,
            "capacitive_ramp_current_ma": capacitance * step_v / (rise_ns * 1e-9) * 1e3,
            "leakage_offset_if_protection_after_cap_mv": 10e-9 * parameters["bias_ohm"] * 1e3,
            "protection_leakage_drop_before_cap_uv": 10e-9 * parameters["sense_series_ohm"] * 1e6,
            "idle_bias_error_per_pin_mv_at_10na": 10e-9 * parameters["endpoint_bias_ohm"] * 1e3,
            "internal_clamp_bound_ma_at_15v_off": (15 - 0.3) / parameters["input_series_ohm"] * 1e3,
            "supply_backfeed_excluded": False}


def spice_deck(design, case):
    if case not in ("S0", "S1", "S2", "S3", "S4", "S5"):
        raise ValueError("Unknown SPICE case")
    parameters = dict(design["parameters"])
    if case == "S3":
        parameters.update(input_pf=design["worst_case"]["input_pf"], bus_stray_pf=design["worst_case"]["bus_stray_pf"])
    cells = manchester("90002100", sample_period_ns=500)
    points = [(0.0, 0.0)]
    previous = 0
    for index, bit in enumerate(cells):
        target = 0.09 if bit else -0.09
        timestamp = (index + 2) * 500e-9
        if target != previous:
            points.extend(((timestamp, previous), (timestamp + 10e-9, target)))
            previous = target
    stop = (len(cells) + 2) * 500e-9
    points.extend(((stop, previous), (stop + 10e-9, 0), (stop + 5e-6, 0)))
    lines = [f"M5P8 {case} ANALYSIS_ONLY_NOT_FOR_CONSTRUCTION",
             DESIGN.with_name("aux-sense.cir").read_text(encoding="ascii"),
             f".param RSOURCE={parameters['source_leg_ohm']} RTERM={parameters['termination_leg_ohm']}",
             f".param CSOURCE={parameters['source_coupling_nf']}n CSINK={parameters['sink_coupling_nf']}n",
             "VSTIMP DRVP CMBENCH DC 0 AC 0.5 PWL("]
    lines.extend(f"+ {timestamp:.12g} {voltage:.12g}" for timestamp, voltage in points)
    lines.append("+ )")
    lines.append("VSTIMN DRVN CMBENCH DC 0 AC 0.5 180 PWL(")
    lines.extend(f"+ {timestamp:.12g} {-voltage:.12g}" for timestamp, voltage in points)
    lines.extend(["+ )", "VCMBENCH CMBENCH 0 " + ("PULSE(0 0.3 12u 10n 10n 2u 16u)" if case == "S4" else "0"),
                  "RSOURCEP DRVP TXP {RSOURCE}", "RSOURCEN DRVN TXN {RSOURCE}",
                  "CSOURCEP TXP AUXP {CSOURCE}", "CSOURCEN TXN AUXN {CSOURCE}",
                  "CSINKP AUXP SINKP {CSINK}", "CSINKN AUXN SINKN {CSINK}",
                  "RTERM SINKP SINKN {2*RTERM}",
                  "VBIASP BIASP 0 0.3", "VBIASN BIASN 0 3.0",
                  f"RENDPOINTP AUXP BIASP {parameters['endpoint_bias_ohm']}",
                  f"RENDPOINTN AUXN BIASN {parameters['endpoint_bias_ohm']}",
                  f"VPOWER VDD 0 {0 if case == 'S2' else parameters['supply_v']}",
                  "VDIGITAL VIO DGND 3.3", "RGROUNDREFERENCE DGND 0 1G"])
    if case != "S0":
        lines.extend(["XOBSERVER AUXP AUXN VDD 0 RXD VIO DGND AUX_RX_ONLY",
                      f"+ RBRANCH={parameters['sense_series_ohm']} RLIMIT={parameters['input_series_ohm']}",
                      f"+ CSENSE={parameters['sense_pf']}p RBIAS={parameters['bias_ohm']}",
                      f"+ CIN={parameters['input_pf']}p CPROT={parameters['protection_pf']}p CSTRAY={parameters['bus_stray_pf']}p",
                      f"+ MISMATCH={design['worst_case']['resistor_fraction'] if case == 'S4' else 0}",
                      f"+ CAPDELTA={design['worst_case']['sense_tolerance_pf'] if case == 'S4' else 0}p",
                      f"+ INDELTA={-design['worst_case']['input_imbalance_pf'] / 2 if case == 'S4' else 0}p"])
    lines.extend([f".tran 2n {stop + 5e-6:.12g}", ".ac dec 40 100k 100Meg",
                  ".print tran V(AUXP,AUXN) V(SINKP,SINKN)", ".print ac V(SINKP,SINKN)", ".end"])
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--design", type=pathlib.Path, default=DESIGN)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--capture", action="store_true")
    mode.add_argument("--spice-case", choices=("S0", "S1", "S2", "S3", "S4", "S5"))
    parser.add_argument("--profile", choices=("nominal", "delay", "jitter", "capacitance_offset", "inverted", "glitch", "missed_edge"), default="nominal")
    parser.add_argument("--output", type=pathlib.Path)
    arguments = parser.parse_args()
    design = load_design(arguments.design)
    parameters = dict(design["parameters"])
    profile_options = {"nominal": {}, "delay": {"rise_delay_ns": 100, "fall_delay_ns": 100},
                       "jitter": {"rise_delay_ns": 50, "fall_delay_ns": 30, "jitter_ns": 10},
                       "capacitance_offset": {"threshold_v": 0.020}, "inverted": {"invert": True},
                       "glitch": {"glitch_at": (880, 4)}, "missed_edge": {"missed_edge": 45}}
    if arguments.profile == "capacitance_offset":
        parameters["input_pf"] = design["worst_case"]["input_pf"]
    record, metrics = conditioned_record(parameters=parameters, sample_period_ns=25, **profile_options[arguments.profile])
    result = {"schema_version": 1, "hardware_authorized": False,
              "model": "analytical_rc_and_behavioural_sense_not_spice_or_compliance",
              "cases": [series_sense(resistance, 4) for resistance in (1000, 10000, 100000, 1000000, 3300000)],
              "loading_example": shunt_loading(100, 100, 1000000, 5, 10000000),
              "idle_bias_examples": [dc_bias_loading(resistance) for resistance in (200000, 1000000, 200000000)],
              "sweeps": loading_sweep(design), "conditioned_signal": metrics,
              "transient_bounds": transient_bounds(design["parameters"])}
    if arguments.capture:
        result = {"schema_version": 1, "capture_id": "synthetic-frontend-" + arguments.profile,
                  "evidence_kind": "synthetic", "hardware_authorized": False,
              "acquisition": {"model": copy.deepcopy(design), "effective_parameters": parameters,
                      "profile": arguments.profile, "profile_options": profile_options[arguments.profile],
                      "metrics": metrics}, "records": [record]}
    output = spice_deck(design, arguments.spice_case) if arguments.spice_case else json.dumps(result, sort_keys=True, indent=2, allow_nan=False) + "\n"
    if arguments.output is None:
        print(output, end="")
    else:
        destination = arguments.output.absolute()
        if any(parent.is_symlink() for parent in (destination, *destination.parents)):
            parser.exit(2, "Output must not use symlinks\n")
        try:
            destination.parent.mkdir(parents=True, exist_ok=True)
            with destination.open("x", encoding="ascii") as stream:
                stream.write(output)
        except OSError as error:
            parser.exit(2, str(error) + "\n")


if __name__ == "__main__":
    main()