import argparse
import datetime
import hashlib
import json
import math
import os
import pathlib
import re
import subprocess
import sys

import capture_baseline


REPOSITORY = pathlib.Path(__file__).resolve().parents[1]
PRE_OPERATION_COMMIT = "1fc8f0241acec829fa732503c13a9ab588e26fb0"
PRE_OPERATION_TAG = "f01208571d395ded9857a2c663f5276e12220c49"
ALLOWED_IO = frozenset({
    "IOServiceMatching", "IOServiceGetMatchingServices", "IOIteratorNext", "IOIteratorIsValid",
    "IOObjectRelease", "IOObjectCopyClass", "IORegistryEntryCreateCFProperties",
    "IORegistryEntryGetRegistryEntryID", "IORegistryEntryGetPath", "IOServiceOpen", "IOServiceClose",
})
ALLOWED_CF = frozenset({
    "CFRelease", "CFEqual", "CFGetTypeID", "CFBooleanGetTypeID", "CFBooleanGetValue",
    "CFDictionaryGetValue", "CFNumberGetTypeID", "CFNumberIsFloatType", "CFNumberGetValue",
    "CFStringGetTypeID", "CFConstantStringClassReference", "kCFAllocatorDefault",
})
DISPLAY_FIELDS = ("mode_width", "mode_height", "pixel_width", "pixel_height", "refresh_hz", "in_mirror_set")
LINK_FIELDS = ("Active", "HPD_State", "LaneCount", "LinkRate", "LinkRateDescription", "Tunneled", "SinkCount")


def sha256(file):
    return hashlib.sha256(file.read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def load_json(file):
    return json.loads(file.read_text())


def save(file, value):
    with file.open("x") as stream:
        json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())


def semantic_state(report):
    require(report.get("display_enumeration_ok") is True and report.get("errors") == [], "Public probe is incomplete")
    displays = []
    for display in report["displays"]:
        require(type(display["active"]) is bool and type(display["built_in"]) is bool, "Invalid display flags")
        if display["active"] and not display["built_in"]:
            selected = {field: display[field] for field in DISPLAY_FIELDS}
            require(all(type(selected[field]) in (int, float) and math.isfinite(selected[field]) and selected[field] > 0
                        for field in DISPLAY_FIELDS if field != "in_mirror_set"), "Invalid external display mode")
            require(type(selected["in_mirror_set"]) is bool, "Invalid mirror state")
            displays.append(selected)
    endpoints = {}
    for class_name, flag in (("DCPDPDeviceProxy", "IODPDeviceUserInterfaceSupported"),
                             ("DCPDPServiceProxy", "IODPServiceUserInterfaceSupported")):
        query = report["registry"][class_name]
        require(query["query_status_code_raw"] == 0, "Public endpoint enumeration failed")
        entries = []
        for entry in query["entries"]:
            require(entry["property_status_code_raw"] == 0, "Public endpoint properties failed")
            values = entry["properties"]
            if values.get("Location") == "External":
                entries.append({"class": entry["class"], "path": entry["path"], "location": values["Location"],
                                "unit": values.get("Unit"), "supported": values.get(flag)})
        endpoints[class_name] = sorted(entries, key=lambda entry: entry["path"])
    query = report["registry"]["IOPortTransportStateDisplayPort"]
    require(query["query_status_code_raw"] == 0, "Public transport enumeration failed")
    links = []
    for entry in query["entries"]:
        require(entry["property_status_code_raw"] == 0, "Public transport properties failed")
        links.append({"path": entry["path"], **{field: entry["properties"].get(field) for field in LINK_FIELDS}})
    return {"host": report["host"], "external_display_count": len(displays),
            "external_modes": sorted(displays, key=lambda item: json.dumps(item, sort_keys=True)),
            "processor_paths": sorted({candidate["processor_path"] for candidate in report["external_dp_candidates"]}),
            "endpoints": endpoints, "dp_paths": sorted(links, key=lambda entry: entry["path"]),
            "public_path_result": report["public_displayport_interface"]["result"], "public_errors": report["errors"]}


def preflight(report):
    state = semantic_state(report)
    require(state["host"]["soc"] == "Apple M5", "Unexpected processor")
    require(state["external_display_count"] == 1, "Expected one active external logical display")
    require(report["public_displayport_interface"]["active_external_display_count"] == 1, "Public display count disagrees")
    candidates = report["external_dp_candidates"]
    require(len(candidates) == 1, "External target is absent or ambiguous")
    candidate = candidates[0]
    require(candidate["location"] == "External" and type(candidate["unit_raw"]) is int and candidate["unit_raw"] == 0,
            "External Unit 0 required")
    require(candidate["device_interface_supported_raw"] is True and candidate["matching_service_count"] == 1,
            "Supported device and unique matching service required")
    processor = candidate["processor_path"]
    require(processor.endswith("/RTBuddy(DCPEXT0)") and "/dcpext0@" in processor, "DCPEXT0 correlation missing")
    for class_name, path_field, id_field in (("DCPDPDeviceProxy", "device_path", "device_entry_id_raw"),
                                           ("DCPDPServiceProxy", "service_path", "service_entry_id_raw")):
        entries = state["endpoints"][class_name]
        require(len(entries) == 1, "External endpoint ambiguity")
        entry = entries[0]
        require(entry["class"] == class_name and entry["path"] == candidate[path_field] and
                entry["path"].startswith(processor + "/") and type(entry["unit"]) is int and entry["unit"] == 0 and
                entry["supported"] is True, "External endpoint invariant failed")
        require(type(candidate[id_field]) is int and candidate[id_field] > 0, "Invalid transient endpoint identity")
        matching = [item for item in report["registry"][class_name]["entries"] if item["path"] == entry["path"]]
        require(len(matching) == 1 and matching[0]["entry_id_raw"] == candidate[id_field], "Candidate identity disagreement")
    active = [entry for entry in report["registry"]["IOPortTransportStateDisplayPort"]["entries"] if entry["properties"].get("Active") is True]
    require(len(active) == 1 and len(candidate["active_transport_paths"]) == 1, "Active DP transport absent or ambiguous")
    transport = active[0]
    values = transport["properties"]
    require(transport["path"] == candidate["active_transport_paths"][0] and "/Port-USB-C@" in transport["path"], "Active USB-C path disagreement")
    require(all(type(values.get(key)) is int and values[key] == expected for key, expected in
                (("HPD_State", 2), ("LaneCount", 2), ("LinkRate", 4), ("SinkCount", 1))), "HPD/lane/rate/sink topology changed")
    require(values.get("Tunneled") is False and values.get("LinkRateDescription") == "8.1 Gbps (HBR3)", "Unexpected DP link transport")
    require(type(transport["entry_id_raw"]) is int and transport["entry_id_raw"] > 0, "Invalid transport identity")
    return state, {"device_id_raw": candidate["device_entry_id_raw"], "service_id_raw": candidate["service_entry_id_raw"],
                   "transport_id_raw": transport["entry_id_raw"]}


def comparison(before, after):
    if after is None:
        return "AFTER_STATE_UNAVAILABLE"
    return "NO_PUBLIC_DISPLAY_STATE_CHANGE" if before == after else "PUBLIC_DISPLAY_STATE_CHANGED"


def record_preflight_stop(output, report, before, reason):
    report.update({"outcome": "EXPERIMENT_NOT_RUN", "runtime_gate": "DPDV_OPEN_CHECK_PREFLIGHT_FAILED",
                   "preflight_error": reason, "private_open_attempts": 0, "selector_calls": 0,
                   "helper_spawn_attempts": 0, "dry_run_agreement": False,
                   "state_comparison": "AFTER_STATE_UNAVAILABLE"})
    for name in ("macmst-probe.json", "manifest.json"):
        file = before / name
        if file.is_file():
            report["before_" + ("report" if name == "macmst-probe.json" else "manifest") + "_sha256"] = sha256(file)
    try:
        report["before_state"] = semantic_state(load_json(before / "macmst-probe.json"))
    except (OSError, ValueError, KeyError):
        report["before_state"] = None
    save(output / "result.json", report)


def valid_dry_run(result, identities):
    frame = result.get("frame") or {}
    return (result.get("runner_outcome") == "success" and result.get("spawn_attempts") == 1 and
            result.get("reaped") is True and result.get("termination_sent") is False and
            result.get("failure_trigger") is None and result.get("exit_code") == 0 and result.get("signal_raw") is None and
            result.get("selector_calls") == 0 and result.get("stdout_bytes") == 64 and result.get("stderr_bytes_omitted") == 0 and
            frame.get("phase") == "DRY_RUN_READY" and frame.get("flags") == 0 and
            frame.get("open_return_raw") is None and frame.get("close_return_raw") is None and
            all(frame.get(key) == value for key, value in identities.items()))


def classify(result, state_comparison):
    if result.get("runner_outcome") in ("timeout", "reap_timeout") or result.get("failure_trigger") == "timeout":
        return "DPDV_OPEN_RUNTIME_HANG"
    if result.get("runner_outcome") == "abnormal_exit" or result.get("signal_raw") is not None:
        return "DPDV_OPEN_CRASH_OR_SYSTEM_INSTABILITY"
    if state_comparison == "PUBLIC_DISPLAY_STATE_CHANGED":
        return "DPDV_OPEN_AFFECTED_DISPLAY_STATE"
    frame = result.get("frame") or {}
    if frame.get("phase") == "CLOSE_FAILED":
        return "DPDV_CLOSE_FAILED"
    if result.get("runner_outcome") in ("invalid_input", "spawn_failure", "attempt_marker_refused") or frame.get("phase") == "PRECHECK_FAILED":
        return "EXPERIMENT_NOT_RUN"
    if (state_comparison == "NO_PUBLIC_DISPLAY_STATE_CHANGE" and result.get("reaped") is True and
        result.get("exit_code") == 0 and result.get("spawn_attempts") == 1 and not result.get("termination_sent")):
        if result.get("runner_outcome") == "operation_failure" and frame.get("phase") == "OPEN_FAILED" and frame.get("connection_returned") is False:
            return "DPDV_OPEN_DENIED_CLEANLY"
        if result.get("runner_outcome") == "success" and frame.get("phase") == "CLOSE_SUCCEEDED":
            return "DPDV_OPEN_CLOSE_SUCCEEDED_NO_PUBLIC_STATE_CHANGE"
    return None


def audit_binaries(probe, parent, helper):
    output = {}
    for file in (probe, parent, helper):
        imports_result = subprocess.run(["/usr/bin/nm", "-u", str(file)], capture_output=True, text=True, check=True)
        imports = {line.split()[-1].lstrip("_") for line in imports_result.stdout.splitlines() if line.split()}
        require(not any(symbol.startswith("IOConnect") or symbol.startswith("IODP") for symbol in imports), "Forbidden selector/private API import")
        if file == helper:
            require({"IOServiceOpen", "IOServiceClose"} <= imports, "Real helper open/close imports missing")
            require({symbol for symbol in imports if symbol.startswith("IO")} <= ALLOWED_IO, "Unexpected IOKit helper import")
            require({symbol for symbol in imports if symbol.startswith(("CF", "kCF"))} <= ALLOWED_CF, "Unexpected CoreFoundation helper import")
            require(not any(symbol.startswith("CG") or symbol in {"dlopen", "dlsym", "sleep", "usleep", "nanosleep"} for symbol in imports), "Dynamic transport/dwell import in real helper")
            disassembly = subprocess.check_output(["/usr/bin/otool", "-tvV", str(file)], text=True)
            for symbol in ("IOServiceOpen", "IOServiceClose"):
                require(len(re.findall(r"\bbl\s+[^\n]*_" + symbol + r"\b", disassembly)) == 1,
                        "Expected exactly one compiled " + symbol + " callsite")
        else:
            require(not ({"IOServiceOpen", "IOServiceClose"} & imports), "Private operation escaped the helper")
            if file == parent:
                require(not any(symbol.startswith(("IO", "CF", "CG")) or symbol in {"dlopen", "dlsym"} for symbol in imports), "Parent imports display transport")
        output[file.name] = {"sha256": sha256(file), "imports": sorted(imports)}
    source = (REPOSITORY / "src/isolation/dpdv_open_helper.cpp").read_text()
    require(len(re.findall(r"\bIOServiceOpen\s*\(", source)) == 1, "Expected exactly one open callsite")
    require(len(re.findall(r"\bIOServiceClose\s*\(", source)) == 1, "Expected exactly one close callsite")
    require(not re.search(r"\b(?:IOConnect\w*|IODP\w*|IOI2C\w*)\s*\(", source), "Forbidden connection/private function in helper")
    main_body = source.split("int main(int argc, char** argv) {")[1]
    require(not re.search(r"\b(?:for|while|do)\b", main_body), "Loop in real operation control flow")
    require("if (open_result == KERN_SUCCESS && connection != IO_OBJECT_NULL)" in main_body, "Close success/nonnull guard missing")
    require("if (no_open)" in main_body and main_body.index("IOServiceClose(") < main_body.index("frame.open_return ="), "Immediate close/no-open boundary missing")
    return output


def source_hashes():
    files = [REPOSITORY / "CMakeLists.txt", pathlib.Path(__file__), REPOSITORY / "tools/capture_baseline.py"]
    files.extend(file for file in (REPOSITORY / "src").rglob("*") if file.is_file())
    return {str(file.relative_to(REPOSITORY)): sha256(file) for file in sorted(files)}


def git_value(*arguments):
    return subprocess.check_output(["git", "-C", str(REPOSITORY), *arguments], text=True).strip()


def main():
    parser = argparse.ArgumentParser(description="One-shot M2F parent orchestration; zero selectors; no retry.")
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--no-open", action="store_true")
    modes.add_argument("--execute-once", action="store_true")
    parser.add_argument("--preflight", required=True, type=pathlib.Path)
    parser.add_argument("--dry-run-receipt", type=pathlib.Path)
    parser.add_argument("--build", type=pathlib.Path, default=REPOSITORY / "build")
    args = parser.parse_args()
    require(git_value("branch", "--show-current") == "experiment/dpdv-open-check", "Wrong experiment branch")
    require(git_value("rev-parse", "refs/tags/pre-dpdv-open-v0.2") == PRE_OPERATION_TAG, "Forensic tag changed")
    require(git_value("rev-parse", "pre-dpdv-open-v0.2^{commit}") == PRE_OPERATION_COMMIT, "Forensic baseline changed")
    require(args.preflight.resolve().is_relative_to((REPOSITORY / "artifacts/probes").resolve()), "Preflight must be a retained public capture")
    reference, unused = preflight(load_json(args.preflight / "macmst-probe.json"))
    build = args.build.resolve()
    probe, parent, helper = (build / name for name in ("macmst", "macmst_dpdv_open_check", "macmst_dpdv_open_helper"))
    require(build.is_relative_to(REPOSITORY), "Build must be in this workspace")
    audit = audit_binaries(probe, parent, helper)
    sources = source_hashes()
    commit = git_value("rev-parse", "HEAD")
    marker = REPOSITORY / "artifacts/probes/M2F-ATTEMPTED"
    require(not marker.exists(), "One-shot M2F marker exists: no further private experimentation")
    dry = None
    if args.execute_once:
        require(not git_value("status", "--porcelain"), "Real execution requires a clean committed worktree")
        require(args.dry_run_receipt is not None, "A successful recorded dry run is required")
        dry = load_json(args.dry_run_receipt)
        require(dry.get("mode") == "no-open" and dry.get("implementation_commit") == commit, "Dry-run commit mismatch")
        require(dry.get("sources") == sources and dry.get("audit") == audit, "Dry-run source/binary mismatch")
        require(dry.get("dry_run_agreement") is True, "Dry-run target agreement missing")
    timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    output = REPOSITORY / "artifacts/probes" / ("m2f-" + timestamp)
    output.mkdir(exist_ok=False)
    report = {"schema_version": 1, "mode": "execute-once" if args.execute_once else "no-open",
              "implementation_commit": commit, "sources": sources, "audit": audit,
              "residual_risk": "Unresolved userServer delegation; parent watchdog is not kernel cancellation; no selector calls.",
              "global_gate": "NOT_READY_FOR_DPCD_TEST", "preflight": str(args.preflight.resolve().relative_to(REPOSITORY))}
    before = output / "before"
    try:
        require(capture_baseline.capture(before, probe) == 0, "BEFORE public capture failed: no experiment")
        state, identities = preflight(load_json(before / "macmst-probe.json"))
        require(state == reference, "Material public state change from initial preflight: no experiment")
    except (OSError, ValueError, KeyError) as error:
        record_preflight_stop(output, report, before, str(error))
        print("M2F STOP receipt: " + str(output.relative_to(REPOSITORY)) + "; EXPERIMENT_NOT_RUN")
        return 1
    report.update({"before_state": state, "selected_ids": identities, "before_report_sha256": sha256(before / "macmst-probe.json"),
                   "before_manifest_sha256": sha256(before / "manifest.json")})
    if dry is not None:
        require(dry.get("before_state") == state and dry.get("selected_ids") == identities, "Dry-run/preflight target disagreement")
        require(valid_dry_run(dry.get("helper", {}), identities), "Dry-run response invalid")
        require(not git_value("status", "--porcelain") and source_hashes() == sources, "Code changed during preflight")
        require(audit_binaries(probe, parent, helper) == audit, "Binary changed during preflight")
    save(output / "prepared.json", report)
    command = [str(parent), "--open-once" if args.execute_once else "--no-open", str(helper),
               *(str(identities[key]) for key in ("device_id_raw", "service_id_raw", "transport_id_raw"))]
    if args.execute_once:
        command.append(str(marker))
    execution = subprocess.run(command, capture_output=True, text=True)
    try:
        require(execution.returncode == 0, "Parent exited abnormally")
        require(len(execution.stdout) <= 8192, "Parent response too large")
        helper_result = json.loads(execution.stdout)
    except (ValueError, json.JSONDecodeError):
        helper_result = {"runner_outcome": "abnormal_exit", "parent_returncode": execution.returncode,
                         "parent_stdout_bytes_omitted": len(execution.stdout), "parent_stderr_bytes_omitted": len(execution.stderr)}
    report["helper"] = helper_result
    report["parent_stderr_bytes_omitted"] = len(execution.stderr)
    if args.no_open:
        report["dry_run_agreement"] = valid_dry_run(helper_result, identities)
        report["outcome"] = "EXPERIMENT_NOT_RUN"
    else:
        after = output / "after"
        after_state = None
        try:
            if capture_baseline.capture(after, probe) == 0:
                after_state = semantic_state(load_json(after / "macmst-probe.json"))
                report["after_report_sha256"] = sha256(after / "macmst-probe.json")
                report["after_manifest_sha256"] = sha256(after / "manifest.json")
        except (OSError, ValueError, KeyError):
            report["after_error"] = "Public AFTER state unavailable; no further private activity"
        report["after_state"] = after_state
        report["state_comparison"] = comparison(state, after_state)
        report["outcome"] = classify(helper_result, report["state_comparison"])
        if report["outcome"] is None:
            report["classification_error"] = "Incomplete or unexpected runtime evidence; STOP without asserting an unobserved crash or success"
        report["runtime_gate"] = "DPDV_OPEN_CLOSE_RUNTIME_VALIDATED" if report["outcome"] == "DPDV_OPEN_CLOSE_SUCCEEDED_NO_PUBLIC_STATE_CHANGE" else report["outcome"] or "DPDV_OPEN_CHECK_INCONCLUSIVE"
        report["reboot_before_further_work"] = helper_result.get("reaped") is False and helper_result.get("spawn_attempts", 0) > 0
        report["helper_timeout_status"] = "HELPER_UNREAPED_AFTER_TIMEOUT" if report["reboot_before_further_work"] and report["outcome"] == "DPDV_OPEN_RUNTIME_HANG" else None
    save(output / "result.json", report)
    print("M2F receipt: " + str(output.relative_to(REPOSITORY)) + "; " + (report["outcome"] or "INCONCLUSIVE: STOP"))
    return 0 if args.execute_once or report.get("dry_run_agreement") else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as error:
        print("M2F STOP: " + str(error), file=sys.stderr)
        sys.exit(1)