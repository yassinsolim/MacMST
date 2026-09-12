import argparse
import datetime
import hashlib
import json
import pathlib
import re
import subprocess
import sys


REGISTRY_CLASSES = (
    "AppleDCPExpert",
    "DCPAVServiceProxy",
    "DCPAVControllerProxy",
    "DCPAVDeviceProxy",
    "DCPDPControllerProxy",
    "DCPDPDeviceProxy",
    "DCPDPServiceProxy",
    "AppleDCPDPTXRemotePortProxy",
    "AppleDCPDPTXRemotePortUFP",
    "IOMobileFramebufferShim",
    "IOFramebuffer",
    "IOI2CInterface",
    "IOPortTransportStateDisplayPort",
    "IOUSBHostDevice",
    "IOAVService",
)
REGISTRY_FIELDS = frozenset({
    "IORegistryEntryName", "IOObjectClass", "IORegistryEntryID", "IOClass",
    "IOProviderClass", "Location", "Unit", "role", "BootComplete",
    "DCPPowerState", "IOAVServiceUserInterfaceSupported", "Active", "HPD_State",
    "IODPDeviceUserInterfaceSupported", "IODPServiceUserInterfaceSupported",
    "IODPControllerUserInterfaceSupported", "IOAVDeviceUserInterfaceSupported",
    "HPD_StateDescription", "Index", "LaneCount", "LinkRate",
    "LinkRateDescription", "MaxLaneCount", "ParentBuiltInPortNumber",
    "ParentBuiltInPortType", "ParentBuiltInPortTypeDescription",
    "ParentPortBuiltIn", "ParentPortNumber", "ParentPortType",
    "ParentPortTypeDescription", "Role", "RoleDescription", "SinkCount",
    "TransportDescription", "TransportType", "TransportTypeDescription",
    "Tunneled", "idVendor", "idProduct", "bcdUSB", "bDeviceClass",
    "bDeviceSubClass", "bDeviceProtocol", "USB Product Name", "USB Vendor Name",
    "locationID", "USBSpeed", "PortNum", "DisplayVendorID", "DisplayProductID",
    "IOI2CTransactionTypes", "IOI2CBusType", "IOI2CBusID",
})
PROFILER_FIELDS = frozenset({
    "chip_type", "machine_model", "machine_name", "number_processors",
    "physical_memory", "spdisplays_ndrvs", "_spdisplays_display-vendor-id",
    "_spdisplays_display-product-id", "spdisplays_vendor", "sppci_model",
    "sppci_bus", "spdisplays_resolution", "spdisplays_ui_looks_like",
    "spdisplays_pixelresolution", "_spdisplays_resolution", "spdisplays_main",
    "spdisplays_mirror", "spdisplays_online", "spdisplays_builtin",
    "spdisplays_connection_type", "spdisplays_display_type", "spdisplays_pixels",
    "spdisplays_refresh_rate", "_items", "manufacturer", "vendor_id",
    "product_id", "speed", "device_name_key", "device_type", "port_name",
    "receptacle", "route_string", "current_speed", "link_status_key",
    "port_micro_firmware_version", "device_revision_key", "vendor_name_key",
    "switch_type_key", "supported_link_widths_key", "link_width_key",
})
SENSITIVE_KEY = re.compile(r"serial|uuid|udid|address|token|password|secret|computer_name", re.I)
DISPLAY_NODE = re.compile(r"DCP|DCPEXT|DPTX|AppleCLCD|IOMobileFramebuffer|IOAVService|IOPortTransportStateDisplayPort", re.I)


def utc_now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


def select_registry_properties(properties):
    return {
        key: value for key, value in properties.items()
        if key in REGISTRY_FIELDS and not SENSITIVE_KEY.search(key)
        and isinstance(value, (str, int, float, bool))
    }


def sanitize_profiler(value, section=""):
    if isinstance(value, list):
        return [sanitize_profiler(item, section) for item in value]
    if not isinstance(value, dict):
        return value
    result = {}
    for key, item in value.items():
        if SENSITIVE_KEY.search(key):
            continue
        if key in ("SPHardwareDataType", "SPDisplaysDataType", "SPThunderboltDataType", "SPUSBDataType"):
            result[key] = sanitize_profiler(item, key)
        elif key in PROFILER_FIELDS or (key == "_name" and section == "SPDisplaysDataType"):
            result[key] = sanitize_profiler(item, section)
    return result


def select_registry_tree(text):
    records = []
    ancestors = []
    for line in text.splitlines():
        match = re.search(r"\+-o (.+?)\s+<class ([^,>]+), id (0x[0-9a-f]+)", line)
        if not match:
            continue
        depth = line.index("+-o")
        name, class_name, entry_id = match.groups()
        while ancestors and ancestors[-1][0] >= depth:
            ancestors.pop()
        if DISPLAY_NODE.search(name) or DISPLAY_NODE.search(class_name):
            path = [entry[1] for entry in ancestors if entry[2] != "IORegistryRoot"]
            records.append({"name": name, "class": class_name, "entry_id_hex": entry_id,
                            "ancestors": path})
        ancestors.append((depth, name, class_name))
    return records


def extract_display_symbol_names(text):
    return sorted(set(re.findall(r"\b_(?:IOAVService|IODP)[A-Za-z0-9_]+\b", text)))


def inspect_sdk_surface(sdk_path):
    import plistlib

    framework = sdk_path / "System/Library/Frameworks/IOKit.framework/Versions/A"
    stub = framework / "IOKit.tbd"
    header = framework / "Headers/i2c/IOI2CInterface.h"
    evidence = {
        "sdk_path": str(sdk_path),
        "iokit_stub_sha256": hashlib.sha256(stub.read_bytes()).hexdigest(),
        "ioi2c_header_sha256": hashlib.sha256(header.read_bytes()).hexdigest(),
        "symbol_name_matches": extract_display_symbol_names(stub.read_text()),
        "interpretation": "Textual symbol-name matches, not ABI declarations or proof of hardware capability.",
        "driver_metadata": [],
    }
    for bundle in ("DCPDPFamilyProxy", "DCPAVFamilyProxy", "IOAVFamily", "AppleDCPDPTXProxy"):
        path = pathlib.Path("/System/Library/Extensions") / (bundle + ".kext") / "Contents/Info.plist"
        metadata = plistlib.loads(path.read_bytes())
        personalities = []
        for personality in metadata.get("IOKitPersonalities", {}).values():
            personalities.append({key: value for key, value in personality.items()
                                  if key in ("IOClass", "IOProviderClass", "IOUserClientClass")
                                  and isinstance(value, str)})
        evidence["driver_metadata"].append({
            "path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "bundle_id": metadata.get("CFBundleIdentifier"), "version": metadata.get("CFBundleVersion"),
            "personalities": personalities,
        })
    return evidence


def execute(argv):
    record = {"argv": [argument.replace(str(pathlib.Path.home()), "~") for argument in argv],
              "started_utc": utc_now()}
    try:
        result = subprocess.run(argv, capture_output=True, timeout=90, check=False)
        record.update(exit_code=result.returncode, completed_utc=utc_now(),
                      status="ok" if result.returncode == 0 else "error",
                      stderr_bytes_omitted=len(result.stderr))
        return record, result.stdout if result.returncode == 0 else b""
    except (OSError, subprocess.TimeoutExpired) as error:
        record.update(status="error", error_type=type(error).__name__, completed_utc=utc_now())
        return record, b""


def capture(output, probe=None):
    import plistlib

    output.mkdir(parents=True, exist_ok=False)
    records = []

    def save(name, data):
        with (output / name).open("x", encoding="utf-8") as stream:
            json.dump(data, stream, indent=2, sort_keys=True)
            stream.write("\n")

    argv = ["/usr/sbin/system_profiler", "-json", "SPHardwareDataType", "SPDisplaysDataType",
            "SPThunderboltDataType", "SPUSBDataType", "-detailLevel", "mini"]
    record, raw = execute(argv)
    if raw:
        try:
            save("system-profiler.json", sanitize_profiler(json.loads(raw)))
        except (ValueError, TypeError):
            record["status"] = "parse_error"
    records.append(record)

    for class_name in REGISTRY_CLASSES:
        record, raw = execute(["/usr/sbin/ioreg", "-a", "-r", "-c", class_name, "-d", "1"])
        try:
            nodes = plistlib.loads(raw) if raw else []
            save("ioreg-" + class_name + ".json", [select_registry_properties(node) for node in nodes])
        except (ValueError, TypeError, plistlib.InvalidFileException):
            record["status"] = "parse_error"
        records.append(record)

    record, raw = execute(["/usr/sbin/ioreg", "-p", "IOService", "-w0"])
    save("display-service-tree.json", select_registry_tree(raw.decode("utf-8", errors="replace")))
    records.append(record)

    environment = []
    for argv in (["/usr/bin/sw_vers"], ["/usr/bin/uname", "-m"],
                 ["/usr/sbin/sysctl", "-n", "machdep.cpu.brand_string"],
                 ["/usr/bin/xcode-select", "-p"], ["/usr/bin/xcodebuild", "-version"],
                 ["/usr/bin/xcrun", "--show-sdk-path"], ["/usr/bin/xcrun", "--show-sdk-version"],
                 ["/usr/bin/xcrun", "clang", "--version"], ["/usr/bin/xcrun", "swift", "--version"],
                 ["swift", "package", "--version"], ["cmake", "--version"], ["ninja", "--version"],
                 ["python3", "--version"], ["git", "--version"], ["rg", "--version"]):
        record, raw = execute(argv)
        environment.append({**record, "stdout": raw.decode("utf-8", errors="replace").replace(str(pathlib.Path.home()), "~")})
        records.append(record)
    save("environment.json", environment)
    sdk_record = next((item for item in environment if item["argv"] == ["/usr/bin/xcrun", "--show-sdk-path"]), None)
    if sdk_record is not None and sdk_record["status"] == "ok":
        try:
            save("sdk-surface.json", inspect_sdk_surface(pathlib.Path(sdk_record["stdout"].strip())))
        except (OSError, ValueError, plistlib.InvalidFileException) as error:
            records.append({"operation": "SDK and driver metadata inspection", "status": "error",
                            "error_type": type(error).__name__})
    if probe is not None:
        record, raw = execute([str(probe.resolve()), "probe", "--json"])
        if raw:
            try:
                save("macmst-probe.json", json.loads(raw))
            except (ValueError, TypeError):
                record["status"] = "parse_error"
        records.append(record)
    manifest = {
        "schema_version": 1, "completed_utc": utc_now(), "commands": records,
        "privacy": "Allowlisted technical properties; serials/UUIDs/EDID/private blobs and stderr omitted. Not complete raw dumps.",
        "topology": "Not independently confirmed; do not infer dock identity from missing observations.",
        "artifacts": {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(output.glob("*.json"))},
    }
    if probe is not None:
        manifest["probe_binary_sha256"] = hashlib.sha256(probe.read_bytes()).hexdigest()
    repository = pathlib.Path(__file__).resolve().parents[1]
    sources = [repository / "CMakeLists.txt", pathlib.Path(__file__).resolve()]
    sources.extend(path for path in (repository / "src").rglob("*") if path.is_file())
    manifest["source_sha256"] = {str(path.relative_to(repository)): hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in sorted(sources) if path.exists()}
    save("manifest.json", manifest)
    failures = sum(record["status"] != "ok" for record in records)
    print(f"Baseline: {output.name}; {len(records)} read-only commands; {failures} failures. See manifest.json.")
    return 1 if failures else 0


def main():
    parser = argparse.ArgumentParser(description="Capture an allowlisted, read-only MacMST baseline.")
    parser.add_argument("--output", type=pathlib.Path)
    parser.add_argument("--probe", type=pathlib.Path, help="Also capture JSON from the built macmst executable.")
    options = parser.parse_args()
    root = pathlib.Path(__file__).resolve().parents[1] / "artifacts" / "probes"
    output = options.output or root / datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    if not output.resolve().is_relative_to(root.resolve()) or output.resolve() == root.resolve():
        parser.error("output must be a new child directory under artifacts/probes")
    if options.probe is not None and not options.probe.is_file():
        parser.error("probe executable does not exist; build it first")
    return capture(output, options.probe)


if __name__ == "__main__":
    sys.exit(main())