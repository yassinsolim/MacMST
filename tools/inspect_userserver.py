import argparse
import contextlib
import ctypes
import datetime
import hashlib
import json
import pathlib
import plistlib
import re
import sys


TEXT_FIELDS = frozenset({
    "IOClass", "IOProviderClass", "IOUserClass", "IOUserClientClass", "IOUserServerName",
    "CFBundleIdentifier", "CFBundleIdentifierKernel", "IOModuleIdentifier", "CFBundleVersion", "Location",
    "IOPersonalityPublisher", "IOMatchCategory", "EPICName", "EPICLocation", "EPICProviderClass",
})
SCALAR_FIELDS = frozenset({
    "Unit", "IODPDeviceUserInterfaceSupported", "IODPServiceUserInterfaceSupported",
    "IOAVDeviceUserInterfaceSupported", "IOUserServerTag", "IOUserServerOneProcess",
    "IOUserServerPreserveUserspaceReboot", "IOUserServerCDHashValid", "IOUserService",
    "Active", "HPD_State", "LaneCount", "LinkRate", "SinkCount", "Tunneled",
    "IOMatchedAtBoot", "EPICUnit",
})
MATCH_FIELDS = frozenset({"EPICName", "EPICLocation", "EPICUnit", "Location", "Unit"})
IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z0-9_.:$-]{0,255}\Z")


def select_properties(properties):
    if not isinstance(properties, dict) or len(properties) > 4096:
        raise ValueError("Missing or excessive registry property dictionary")
    if any(not isinstance(key, str) or not key.isascii() or not key.isprintable() or not 1 <= len(key) <= 512 for key in properties):
        raise ValueError("Registry property names cannot be safely represented")
    values = {}
    unrepresented = []
    for key, value in properties.items():
        accepted = False
        if key in TEXT_FIELDS:
            accepted = isinstance(value, str) and IDENTIFIER.fullmatch(value) is not None
        elif key in SCALAR_FIELDS:
            accepted = type(value) is bool or (type(value) is int and 0 <= value < 1 << 64)
        elif key == "IOUserClasses":
            accepted = isinstance(value, list) and len(value) <= 256 and all(isinstance(item, str) and IDENTIFIER.fullmatch(item) for item in value)
        elif key == "IOAssociatedServices":
            accepted = isinstance(value, list) and len(value) <= 256 and all(type(item) is int and 0 <= item < 1 << 64 for item in value)
        elif key == "IOPropertyMatch":
            accepted = isinstance(value, dict) and set(value) <= MATCH_FIELDS and all(
                (isinstance(item, str) and IDENTIFIER.fullmatch(item)) or (type(item) is int and 0 <= item < 1 << 64)
                for item in value.values())
        else:
            continue
        if accepted:
            values[key] = value
        else:
            unrepresented.append(key)
    return {"property_names": sorted(properties), "property_names_complete": True,
            "values": values, "relevant_values_unrepresented": sorted(unrepresented)}


def driver_personality(file):
    if file.stat().st_size > 4 * 1024 * 1024:
        raise ValueError("Driver personality file exceeds bound")
    raw = file.read_bytes()
    properties = plistlib.loads(raw)
    if properties.get("CFBundleIdentifier") != "com.apple.driver.DCPDPFamilyProxy":
        raise ValueError("Unexpected DCPDP personality bundle")
    personalities = properties.get("IOKitPersonalities", {})
    selected = {name: select_properties(value) for name, value in personalities.items()
                if isinstance(value, dict) and value.get("IOClass") == "DCPDPDeviceProxy"}
    if len(selected) != 1:
        raise ValueError("DCPDP matching personality missing or ambiguous")
    return {"path": str(file), "sha256": hashlib.sha256(raw).hexdigest(),
            "bundle_id": properties["CFBundleIdentifier"], "personalities": selected}


def select_exact(records, expected_id, expected_path, interface_flag):
    candidates = []
    for index, record in enumerate(records):
        values = (record.get("properties") or {}).get("values", {})
        if values.get("Location") == "External" and type(values.get("Unit")) is int and values["Unit"] == 0 and values.get(interface_flag) is True:
            candidates.append(index)
    if len(candidates) != 1:
        raise ValueError("Expected exactly one supported External Unit 0 provider")
    selected = records[candidates[0]]
    if selected.get("entry_id_raw") != expected_id or selected.get("path") != expected_path or "RTBuddy(DCPEXT0)/" not in expected_path:
        raise ValueError("Provider changed since the supplied public baseline")
    return candidates[0]


class RegistryReader:
    def __init__(self):
        self.calls = []
        self.iokit = ctypes.CDLL("/System/Library/Frameworks/IOKit.framework/IOKit")
        self.cf = ctypes.CDLL("/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation")
        pointer = ctypes.c_void_p
        port = ctypes.c_uint32
        result = ctypes.c_int32
        signatures = {
            "IOServiceMatching": (pointer, [ctypes.c_char_p]),
            "IOServiceGetMatchingServices": (result, [port, pointer, ctypes.POINTER(port)]),
            "IOIteratorNext": (port, [port]), "IOObjectRelease": (result, [port]),
            "IORegistryEntryGetRegistryEntryID": (result, [port, ctypes.POINTER(ctypes.c_uint64)]),
            "IORegistryEntryGetPath": (result, [port, ctypes.c_char_p, pointer]),
            "IORegistryEntryCreateCFProperties": (result, [port, ctypes.POINTER(pointer), pointer, port]),
            "IORegistryEntryGetParentIterator": (result, [port, ctypes.c_char_p, ctypes.POINTER(port)]),
            "IORegistryEntryGetChildIterator": (result, [port, ctypes.c_char_p, ctypes.POINTER(port)]),
            "IORegistryEntryInPlane": (ctypes.c_uint32, [port, ctypes.c_char_p]),
            "IORegistryGetRootEntry": (port, [port]),
            "IOObjectCopyClass": (pointer, [port]),
            "IOObjectCopyBundleIdentifierForClass": (pointer, [pointer]),
            "IOObjectCopySuperclassForClass": (pointer, [pointer]),
        }
        for name, (return_type, arguments) in signatures.items():
            function = getattr(self.iokit, name)
            function.restype, function.argtypes = return_type, arguments
        for name, return_type, arguments in (
            ("CFRelease", None, [pointer]),
            ("CFStringGetCString", ctypes.c_bool, [pointer, pointer, ctypes.c_long, ctypes.c_uint32]),
            ("CFGetTypeID", ctypes.c_ulong, [pointer]),
            ("CFDictionaryGetTypeID", ctypes.c_ulong, []),
            ("CFDictionaryGetCount", ctypes.c_long, [pointer]),
            ("CFDictionaryGetKeysAndValues", None, [pointer, pointer, pointer]),
            ("CFPropertyListCreateData", pointer, [pointer, pointer, ctypes.c_long, ctypes.c_ulong, ctypes.POINTER(pointer)]),
            ("CFDataGetLength", ctypes.c_long, [pointer]),
            ("CFDataGetBytePtr", pointer, [pointer]),
        ):
            function = getattr(self.cf, name)
            function.restype, function.argtypes = return_type, arguments

    def status(self, name, *arguments):
        result = getattr(self.iokit, name)(*arguments)
        self.calls.append({"api": name, "ioreturn_raw": result, "ioreturn_hex": f"0x{result & 0xffffffff:08x}"})
        return result

    def string(self, value, identifier=True):
        if not value:
            return None
        buffer = ctypes.create_string_buffer(4096)
        if not self.cf.CFStringGetCString(value, buffer, len(buffer), 0x08000100):
            raise ValueError("Public class identity exceeds string bound")
        text = buffer.value.decode("utf-8")
        if identifier and not IDENTIFIER.fullmatch(text):
            raise ValueError("Public class identity is not a technical identifier")
        if not identifier and (not text.isascii() or not text.isprintable() or not 1 <= len(text) <= 512):
            raise ValueError("Public property name is not safely representable")
        return text

    def dictionary_items(self, dictionary):
        if not dictionary or self.cf.CFGetTypeID(dictionary) != self.cf.CFDictionaryGetTypeID():
            raise ValueError("Expected public property dictionary")
        count = self.cf.CFDictionaryGetCount(dictionary)
        if not 0 <= count <= 4096:
            raise ValueError("Public property dictionary exceeds bound")
        keys = (ctypes.c_void_p * count)()
        values = (ctypes.c_void_p * count)()
        self.cf.CFDictionaryGetKeysAndValues(dictionary, keys, values)
        return [(self.string(key, identifier=False), value) for key, value in zip(keys, values)]

    def property_value(self, value):
        error = ctypes.c_void_p()
        data = self.cf.CFPropertyListCreateData(None, value, 200, 0, ctypes.byref(error))
        try:
            if not data:
                return None
            size = self.cf.CFDataGetLength(data)
            if not 0 < size <= 4 * 1024 * 1024:
                return None
            return plistlib.loads(ctypes.string_at(self.cf.CFDataGetBytePtr(data), size))
        finally:
            if error.value:
                self.cf.CFRelease(error)
            if data:
                self.cf.CFRelease(data)

    def property_dictionary(self, properties):
        result = {}
        for key, value in self.dictionary_items(properties):
            if key == "IORegistryPlanes":
                result[key] = {plane: None for plane, unused in self.dictionary_items(value)}
            elif key in TEXT_FIELDS | SCALAR_FIELDS | {"IOUserClasses", "IOAssociatedServices", "IOPropertyMatch"}:
                result[key] = self.property_value(value)
            else:
                result[key] = None
        return result

    def properties(self, handle):
        properties = ctypes.c_void_p()
        result = self.status("IORegistryEntryCreateCFProperties", handle, ctypes.byref(properties), None, 0)
        if result != 0 or not properties.value:
            if properties.value:
                self.cf.CFRelease(properties)
            return result, None
        try:
            return result, self.property_dictionary(properties)
        finally:
            self.cf.CFRelease(properties)

    @contextlib.contextmanager
    def entries(self, class_name=None, parent=None, children=False):
        iterator = ctypes.c_uint32()
        handles = []
        if class_name is not None:
            matching = self.iokit.IOServiceMatching(class_name.encode("ascii"))
            if not matching:
                raise ValueError("Public matching dictionary unavailable")
            result = self.status("IOServiceGetMatchingServices", 0, matching, ctypes.byref(iterator))
        else:
            name = "IORegistryEntryGetChildIterator" if children else "IORegistryEntryGetParentIterator"
            result = self.status(name, parent, b"IOService", ctypes.byref(iterator))
        try:
            if result == 0 and iterator.value:
                while True:
                    handle = self.iokit.IOIteratorNext(iterator)
                    if not handle:
                        break
                    handles.append(handle)
                    if len(handles) > 256:
                        raise ValueError("Public registry iterator exceeds 256 entries")
            yield result, handles
        finally:
            for handle in handles:
                self.status("IOObjectRelease", handle)
            if iterator.value:
                self.status("IOObjectRelease", iterator)

    def identity(self, handle):
        entry_id = ctypes.c_uint64()
        result = self.status("IORegistryEntryGetRegistryEntryID", handle, ctypes.byref(entry_id))
        buffer = ctypes.create_string_buffer(512)
        path_result = self.status("IORegistryEntryGetPath", handle, b"IOService", buffer)
        class_name = self.iokit.IOObjectCopyClass(handle)
        bundle = self.iokit.IOObjectCopyBundleIdentifierForClass(class_name) if class_name else None
        superclass = self.iokit.IOObjectCopySuperclassForClass(class_name) if class_name else None
        try:
            return {"entry_id_result_raw": result, "entry_id_raw": entry_id.value if result == 0 else None,
                    "path_result_raw": path_result, "path": buffer.value.decode("utf-8") if path_result == 0 else None,
                    "class": self.string(class_name), "class_bundle": self.string(bundle),
                    "superclass": self.string(superclass)}
        finally:
            for value in (superclass, bundle, class_name):
                if value:
                    self.cf.CFRelease(value)

    def record(self, handle):
        identity = self.identity(handle)
        result, properties = self.properties(handle)
        return {**identity, "properties_result_raw": result,
                "properties": select_properties(properties) if properties is not None else None}

    def ancestry(self, handle, seen=None, depth=0):
        seen = set() if seen is None else seen
        record = self.record(handle)
        if record["entry_id_raw"] in seen:
            raise ValueError("Cycle or invalid identity in public ancestry")
        seen.add(record["entry_id_raw"])
        if record["class"] == "RTBuddy":
            return [record]
        if depth >= 8:
            raise ValueError("Expected RTBuddy within bounded provider ancestry")
        with self.entries(parent=handle) as (result, parents):
            if result != 0 or len(parents) != 1:
                raise ValueError("Provider ancestry is unavailable or ambiguous")
            return [record, *self.ancestry(parents[0], seen, depth + 1)]

    def collect(self, baseline):
        candidates = baseline.get("external_dp_candidates", [])
        if len(candidates) != 1 or baseline["public_displayport_interface"]["active_external_display_count"] != 1:
            raise ValueError("Baseline lacks a unique active external context")
        target = candidates[0]
        with self.entries(class_name="DCPDPDeviceProxy") as (result, handles):
            if result != 0:
                raise ValueError("Cannot enumerate current DP providers")
            records = [self.record(handle) for handle in handles]
            index = select_exact(records, target["device_entry_id_raw"], target["device_path"], "IODPDeviceUserInterfaceSupported")
            provider = records[index]
            ancestors = self.ancestry(handles[index])
            with self.entries(parent=handles[index], children=True) as (child_result, children):
                child_records = [self.identity(child) for child in children]
            root = self.iokit.IORegistryGetRootEntry(0)
            if not root:
                raise ValueError("Registry root unavailable")
            try:
                plane_result, root_properties = self.properties(root)
                planes = root_properties.get("IORegistryPlanes") if isinstance(root_properties, dict) else None
                if plane_result != 0 or not isinstance(planes, dict):
                    raise ValueError("Public registry planes unavailable")
                if any(not isinstance(plane, str) or not IDENTIFIER.fullmatch(plane) for plane in planes):
                    raise ValueError("Invalid public registry plane name")
                memberships = {plane: bool(self.iokit.IORegistryEntryInPlane(handles[index], plane.encode("ascii"))) for plane in sorted(planes)}
            finally:
                self.status("IOObjectRelease", root)
        with self.entries(class_name="DCPDPServiceProxy") as (result, handles):
            if result != 0:
                raise ValueError("Cannot enumerate current DP service")
            records = [self.record(handle) for handle in handles]
            index = select_exact(records, target["service_entry_id_raw"], target["service_path"], "IODPServiceUserInterfaceSupported")
            service = records[index]
        with self.entries(class_name="IOPortTransportStateDisplayPort") as (result, handles):
            records = [self.record(handle) for handle in handles]
            active = [record for record in records if record.get("properties") and record["properties"]["values"].get("Active") is True]
            if result != 0 or len(active) != 1 or active[0]["path"] not in target["active_transport_paths"] or active[0]["properties"]["values"].get("HPD_State") != 2:
                raise ValueError("Active HPD/path changed since the public baseline")
        with self.entries(class_name="IOUserServer") as (server_result, handles):
            servers = [self.record(handle) for handle in handles]
            for server in servers:
                associated = (server.get("properties") or {}).get("values", {}).get("IOAssociatedServices")
                server["associated_with_selected_id"] = provider["entry_id_raw"] in associated if isinstance(associated, list) else None
        return {"provider": provider, "ancestry_to_rtbuddy": ancestors, "matching_dp_service": service,
                "active_dp_path": active[0], "provider_children_result_raw": child_result,
                "provider_children": child_records, "registry_plane_membership": memberships,
            "user_server_matching_result_raw": server_result, "user_servers": servers,
            "driver_personality": driver_personality(pathlib.Path("/System/Library/Extensions/DCPDPFamilyProxy.kext/Contents/Info.plist"))}


def main():
    parser = argparse.ArgumentParser(description="Public registry-only userServer discriminator; no client open or selector.")
    parser.add_argument("--baseline", required=True, type=pathlib.Path)
    args = parser.parse_args()
    if sys.platform != "darwin":
        parser.error("requires public macOS IOKit")
    repository = pathlib.Path(__file__).resolve().parents[1]
    root = repository / "artifacts/probes"
    baseline = args.baseline.resolve()
    if not baseline.is_relative_to(root.resolve()):
        parser.error("baseline must be under artifacts/probes")
    raw = (baseline / "macmst-probe.json").read_bytes()
    reader = RegistryReader()
    started = datetime.datetime.now(datetime.timezone.utc)
    output = root / ("userserver-" + started.strftime("%Y%m%dT%H%M%SZ"))
    output.mkdir(exist_ok=False)
    report = {"schema_version": 1, "started_utc": started.isoformat(), "snapshot_atomic": False,
              "baseline": str(baseline.relative_to(repository)), "baseline_report_sha256": hashlib.sha256(raw).hexdigest(),
              "tool_sha256": hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),
              "safety": "Public registry/class metadata only; no client open, selector, private memory or transport.",
              "privacy": "All property names; values restricted to technical identifiers, flags and registry IDs; no EDID/serial/private blobs retained."}
    exit_code = 0
    try:
        report["observation"] = reader.collect(json.loads(raw))
    except (ValueError, KeyError) as error:
        report["error"] = str(error)
        exit_code = 1
    report["calls"] = reader.calls
    report["completed_utc"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    with (output / "userserver.json").open("x") as stream:
        json.dump(report, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print("Public user-server evidence: " + output.name + ("; incomplete, see error/calls" if exit_code else "; no private calls"))
    return exit_code


if __name__ == "__main__":
    sys.exit(main())