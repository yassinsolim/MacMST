#!/usr/bin/env python3
"""M5P3 public-command topology snapshots and conservative offline graph diffs."""

import argparse
import collections
import datetime
import hashlib
import json
import pathlib
import plistlib
import re
import subprocess
import sys

from capture_baseline import PROFILER_FIELDS, REGISTRY_FIELDS


SCHEMA_VERSION = 1
MAX_INPUT_BYTES = 32 * 1024 * 1024
MAX_NODES = 20000
MAX_DEPTH = 128
REGISTRY_CLASSES = (
    "AppleDCPExpert", "AppleDCP", "DCPDPControllerProxy", "DCPDPDeviceProxy",
    "DCPDPServiceProxy", "DCPDPDevice", "DCPDPVirtualDevice", "IODPVirtualDevice",
    "DCPAVControllerProxy", "DCPAVDeviceProxy", "DCPAVServiceProxy",
    "DCPAVVideoInterfaceProxy", "AppleDCPDPTXProxy", "AppleDCPDPTXRemotePortProxy",
    "AppleDCPDPTXRemotePortUFP", "AppleDCPDPTXController", "AppleDCPDPTXNub",
    "AppleDisplayCrossbar", "AppleT8142DisplayCrossbar", "IODPTXPort", "IODPSwitch",
    "IODPSwitchAllocationState", "IOAVService", "IOFramebuffer",
    "IOMobileFramebuffer", "IOMobileFramebufferShim", "AppleCLCD", "AppleCLCD2",
    "IODisplay", "IODisplayConnect", "IOPortTransportStateDisplayPort",
    "AFKEndpointInterface", "IOUSBHostDevice",
)
TOPOLOGY_NODE = re.compile(
    r"DCP|DPTX|IODP|IOAV(?!B)|IOFramebuffer|IOMobileFramebuffer|AppleCLCD|"
    r"IODisplay|DisplayCrossbar|DisplayPipe|display-pipe|IOPortTransportStateDisplayPort", re.I)
SENSITIVE = re.compile(r"serial|uuid|udid|mac.?address|user.?name|computer.?name|token|password|secret|edid", re.I)
PROPERTY_KEYS = (REGISTRY_FIELDS | frozenset({
    "EPICName", "EPICUnit", "EPICLocation", "EPICProviderClass", "IOAVUnit",
    "IOAVLocation", "IONameMatched", "IOUserClass", "IOUserClientClass",
    "IOUserServerName", "CFBundleIdentifier", "IOPropertyMatch",
    "IOAssociatedServices", "PortAddress", "PortType", "PortIndex", "PortRole",
    "ConnectionAttributes", "ConnectionState", "ConnectionCount", "PeerAddress",
    "PeerPort", "Peer", "Connected", "DisplayCount", "DisplayID", "ModeID",
    "TimingID", "LinkSource", "IOAVLinkSource", "IOFBOnline", "IOFBDependentIndex",
    "IOFBDependentID", "IOFBCurrentPixelClock", "IOFBCurrentPixelCount",
    "supports-aux-only", "port-address", "port-type", "connection-state",
    "connection-attributes", "peer-port", "peer-address", "link-source",
    "DPTXPortAddress", "IODPTXPortAddress", "IOAVDisplayHints", "IOAVDisplayAllocation",
    "AllocationState", "ConnectionStates", "Connections", "PortNumber", "PortAttributes",
    "PeerPortAddress", "DisplayHints", "DisplayAllocation", "DPTXIndex", "PipeIndex",
})) - {"IORegistryEntryName", "IORegistryEntryID", "IOObjectClass", "USB Product Name", "USB Vendor Name"}
RELEVANT_KEY = re.compile(r"epic|dptx|display|framebuffer|pipe|source|stream|port|connection|peer|link|unit|location|timing|mode|sink|tunnel|hpd", re.I)
TECHNICAL_TEXT = re.compile(r"[A-Za-z0-9 _.,:;()\[\]/@+=$-]{1,192}\Z")
TREE_LINE = re.compile(r"\+-o (.+?)\s+<class ([A-Za-z_][A-Za-z0-9_.$:-]*), id (0x[0-9a-fA-F]+)(?:,|>)")
SAFE_NAME = re.compile(r"(?:Apple|DCP|IO|AFK|RTBuddy|dcp|disp|display|arm-io|atc|usb-drd|usb-xhci|XHC|port|nub)[A-Za-z0-9 _.,:()@+$-]{0,160}\Z")
REPOSITORY = pathlib.Path(__file__).resolve().parents[1]
TARGET_USB_PAIRS = frozenset({(0x05e3, 0x0625), (0x05e3, 0x0610), (0x1a40, 0x0801), (0x05e3, 0x0618)})
TARGET_DISPLAY_PAIR = (0x0469, 0x24a5)
DISPLAY_FIELDS = frozenset(key for key in PROFILER_FIELDS if key.startswith(("spdisplays_", "_spdisplays_", "sppci_"))) | {
    "_spdisplays_displayID", "spdisplays_displayID", "spdisplays_rotation", "spdisplays_depth"}
USB_FIELDS = frozenset({"vendor_id", "product_id", "speed", "bcd_device", "bus_power", "bus_power_used"})
THUNDERBOLT_FIELDS = frozenset({"current_speed", "link_status_key", "port_name", "receptacle", "link_width_key", "supported_link_widths_key"})


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="microseconds")


def command_plan():
    commands = [
        ("os_version", ("/usr/bin/sw_vers", "-productVersion")),
        ("os_build", ("/usr/bin/sw_vers", "-buildVersion")),
        ("machine_model", ("/usr/sbin/sysctl", "-n", "hw.model")),
        ("soc", ("/usr/sbin/sysctl", "-n", "machdep.cpu.brand_string")),
        ("boot_before", ("/usr/sbin/sysctl", "-n", "kern.boottime")),
        ("tree_before", ("/usr/sbin/ioreg", "-p", "IOService", "-w0")),
    ]
    commands.extend(("registry_" + name, ("/usr/sbin/ioreg", "-a", "-r", "-p", "IOService", "-c", name, "-d", "1"))
                    for name in REGISTRY_CLASSES)
    commands.extend([
        ("profiler", ("/usr/sbin/system_profiler", "-json", "SPDisplaysDataType", "SPUSBDataType", "SPThunderboltDataType", "-detailLevel", "mini")),
        ("tree_after", ("/usr/sbin/ioreg", "-p", "IOService", "-w0")),
        ("boot_after", ("/usr/sbin/sysctl", "-n", "kern.boottime")),
    ])
    return commands


def capture_policy():
    return {"schema_version": SCHEMA_VERSION, "commands": command_plan(),
            "registry_value_keys": sorted(PROPERTY_KEYS), "registry_name_pattern": RELEVANT_KEY.pattern,
            "topology_pattern": TOPOLOGY_NODE.pattern, "usb_descriptor_candidates": sorted(TARGET_USB_PAIRS),
            "display_descriptor_candidate": TARGET_DISPLAY_PAIR,
            "raw_retention": "FILTERED_TECHNICAL_VALUES_ONLY; complete command output hashed then discarded",
            "identity_rule": "Registry IDs are capture-local RUNTIME_OBJECT_ID, not STABLE_SEMANTIC_ID",
            "source_rule": "No source identities inferred from public object, sink, endpoint or framebuffer counts"}


def execute_public(argv):
    if tuple(argv) not in {command for _, command in command_plan()}:
        raise ValueError("Command is not in the fixed public-read allowlist")
    record = {"argv": list(argv), "started_utc": now()}
    try:
        result = subprocess.run(argv, stdin=subprocess.DEVNULL, capture_output=True, check=False,
                                shell=False, timeout=90 if argv[0].endswith("system_profiler") else 30)
        record.update(completed_utc=now(), exit_code=result.returncode,
                      status="OK" if result.returncode == 0 else "COMMAND_FAILED",
                      stdout_bytes=len(result.stdout), stdout_sha256=digest(result.stdout),
                      stderr_bytes_omitted=len(result.stderr))
        if len(result.stdout) > MAX_INPUT_BYTES:
            record["status"] = "OUTPUT_EXCEEDS_RETENTION_BOUND"
        return record, result.stdout if record["status"] == "OK" else b""
    except (OSError, subprocess.TimeoutExpired) as error:
        record.update(completed_utc=now(), status="COMMAND_FAILED", error_type=type(error).__name__)
        return record, b""


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def json_bytes(value):
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True, allow_nan=False) + "\n").encode("ascii")


def entry_id(value):
    if isinstance(value, str) and re.fullmatch(r"0x[0-9a-fA-F]{1,16}", value):
        value = int(value, 16)
    if type(value) is not int or not 0 < value < 1 << 64:
        raise ValueError("Invalid runtime registry entry ID")
    return hex(value)


def technical_value(value, depth=0):
    if depth > 3:
        raise ValueError("Nested property exceeds the retention bound")
    if type(value) is bool or type(value) is int and -(1 << 63) <= value < 1 << 64:
        return value
    if isinstance(value, str) and TECHNICAL_TEXT.fullmatch(value) and not re.search(r"/Users/|\b[^\s/@]+@[^\s/@]+\.[A-Za-z]{2,}\b", value):
        return value
    if isinstance(value, bytes) and len(value) <= 256:
        return {"type": "plist_data", "raw_hex": value.hex(), "length_bytes": len(value)}
    if isinstance(value, list) and len(value) <= 128:
        return [technical_value(item, depth + 1) for item in value]
    if isinstance(value, dict) and len(value) <= 32:
        return {key: technical_value(item, depth + 1) for key, item in value.items()
                if key in PROPERTY_KEYS and not SENSITIVE.search(key)}
    raise ValueError("Property value not approved for retention")


def select_properties(properties):
    if not isinstance(properties, dict) or len(properties) > 4096:
        raise ValueError("Invalid registry property dictionary")
    values = {}
    omitted = []
    names = []
    for key, value in properties.items():
        if not isinstance(key, str) or not re.fullmatch(r"[A-Za-z0-9_. -]{1,128}", key) or SENSITIVE.search(key):
            continue
        if key in PROPERTY_KEYS or RELEVANT_KEY.search(key):
            names.append(key)
        if key not in PROPERTY_KEYS:
            continue
        try:
            values[key] = technical_value(value)
        except ValueError:
            omitted.append(key)
    return {"values": values, "relevant_property_names": sorted(names),
            "unrepresented_allowed_values": sorted(omitted)}


def parse_registry_tree(raw):
    if not isinstance(raw, bytes) or not 0 < len(raw) <= MAX_INPUT_BYTES:
        raise ValueError("Missing or excessive IOService tree output")
    records = []
    ancestors = []
    for line in raw.decode("utf-8", errors="strict").splitlines():
        match = TREE_LINE.search(line)
        if match is None:
            continue
        depth = line.index("+-o")
        while ancestors and ancestors[-1][0] >= depth:
            ancestors.pop()
        if len(ancestors) > MAX_DEPTH or len(records) >= MAX_NODES:
            raise ValueError("Excessive IOService hierarchy")
        name, class_name, identity = match.groups()
        node = {"entry_id": entry_id(identity), "name": name, "class": class_name,
                "provider_id": ancestors[-1][1]["entry_id"] if ancestors else None,
                "ancestry": [item[1]["entry_id"] for item in ancestors]}
        records.append(node)
        ancestors.append((depth, node))
    if not records or not any(node["class"] == "IORegistryRoot" for node in records):
        raise ValueError("IOService tree has no recognizable root")
    return records


def parse_registry_properties(raw):
    if not isinstance(raw, bytes) or len(raw) > MAX_INPUT_BYTES:
        raise ValueError("Excessive registry property output")
    if not raw.strip():
        return []
    parsed = plistlib.loads(raw)
    if not isinstance(parsed, list) or len(parsed) > MAX_NODES:
        raise ValueError("Registry archive is not a bounded root list")
    records = []
    pending = [(item, 0) for item in parsed]
    while pending:
        item, depth = pending.pop()
        if not isinstance(item, dict) or depth > MAX_DEPTH or len(records) >= MAX_NODES:
            raise ValueError("Invalid registry property hierarchy")
        identity = entry_id(item.get("IORegistryEntryID"))
        records.append({"entry_id": identity, "properties": select_properties(item)})
        children = item.get("IORegistryEntryChildren", [])
        if not isinstance(children, list):
            raise ValueError("Invalid registry child list")
        pending.extend((child, depth + 1) for child in children)
    return records


def safe_name(node):
    if node["class"] == "IORegistryRoot":
        return "IOServiceRoot", True
    if node.get("name_redacted"):
        return node["name"], True
    if SAFE_NAME.fullmatch(node["name"]) and not SENSITIVE.search(node["name"]):
        return node["name"], False
    return node["class"], True


def normalize_registry(tree, properties, generation, extra_ids=()):
    if not isinstance(generation, str) or not re.fullmatch(r"[a-z0-9-]{1,64}", generation):
        raise ValueError("Invalid capture generation")
    grouped = collections.defaultdict(list)
    for node in tree:
        grouped[node["entry_id"]].append(node)
    selected = {node["entry_id"] for node in tree if node.get("selected") or TOPOLOGY_NODE.search(node["class"]) or TOPOLOGY_NODE.search(node["name"])}
    selected.update(extra_ids)
    for node in tree:
        if node["class"] == "AFKEndpointInterface" and any(identity in selected for identity in node["ancestry"]):
            selected.add(node["entry_id"])
    retained = set(selected)
    for node in tree:
        if node["entry_id"] in selected:
            retained.update(node["ancestry"])
    property_groups = collections.defaultdict(list)
    for query, records in properties.items():
        for record in records:
            if record["entry_id"] in selected:
                property_groups[record["entry_id"]].append((query, record["properties"]))
    objects = []
    issues = []
    for identity in sorted(retained, key=lambda value: int(value, 16)):
        occurrences = grouped.get(identity, [])
        if not occurrences:
            issues.append({"code": "MISSING_TREE_OBJECT", "entry_id": identity})
            continue
        class_names = {node["class"] for node in occurrences}
        if len(class_names) != 1:
            issues.append({"code": "AMBIGUOUS_CLASS", "entry_id": identity})
        node = occurrences[0]
        parents = sorted({value["provider_id"] for value in occurrences if value["provider_id"] is not None})
        paths = set()
        redacted_path = False
        for occurrence in occurrences:
            parts = []
            for ancestor in occurrence["ancestry"]:
                candidates = grouped.get(ancestor, [])
                if len(candidates) != 1:
                    redacted_path = True
                    continue
                if candidates[0]["class"] == "IORegistryRoot":
                    continue
                name, redacted = safe_name(candidates[0])
                parts.append(name)
                redacted_path |= redacted
            name, redacted = safe_name(occurrence)
            if occurrence["class"] != "IORegistryRoot":
                parts.append(name)
                redacted_path |= redacted
            paths.add("IOService:/" + "/".join(parts))
        values = {}
        conflicts = set()
        names = set()
        unrepresented = set()
        queries = set()
        for query, record in property_groups[identity]:
            queries.add(query)
            names.update(record["relevant_property_names"])
            unrepresented.update(record["unrepresented_allowed_values"])
            for key, value in record["values"].items():
                if key in values and json_bytes(values[key]) != json_bytes(value):
                    conflicts.add(key)
                else:
                    values[key] = value
        for key in conflicts:
            values.pop(key, None)
        if len(parents) > 1:
            issues.append({"code": "AMBIGUOUS_PROVIDER", "entry_id": identity, "candidates": parents})
        if conflicts:
            issues.append({"code": "PROPERTY_CHANGED_DURING_CAPTURE", "entry_id": identity, "keys": sorted(conflicts)})
        name, name_redacted = safe_name(node)
        objects.append({"class": node["class"], "class_candidates": sorted(class_names),
                        "name": name, "name_redacted": name_redacted,
                        "scope": "relevant" if identity in selected else "ancestor_context",
                        "registry_entry_id": identity, "registry_path": next(iter(paths)) if len(paths) == 1 else None,
                        "path_candidates": sorted(paths), "path_redacted": redacted_path,
                        "path_provenance": "RECONSTRUCTED_IOREG_IOSERVICE_TREE",
                        "runtime_identity": {"kind": "RUNTIME_OBJECT_ID", "registry_entry_id": identity,
                                             "capture_generation": generation},
                        "stable_semantic_id": None, "stable_semantic_id_status": "NOT_ESTABLISHED",
                        "capture_generation": generation,
                        "provider": parents[0] if len(parents) == 1 else None,
                        "provider_candidates": parents,
                        "provider_resolution": "AMBIGUOUS" if len(parents) > 1 else "TREE_PARENT" if parents else "ROOT",
                        "children": sorted({child["entry_id"] for child in tree if child["provider_id"] == identity and child["entry_id"] in retained}),
                        "matched_queries": sorted(queries), "properties": values,
                        "relevant_property_names": sorted(names), "unrepresented_allowed_values": sorted(unrepresented),
                        "conflicting_property_keys": sorted(conflicts), "source_identity_established": False})
    edges = [{"provider": node["provider"], "child": node["registry_entry_id"],
              "relation": "IOService_parent", "confidence": "VERIFIED_RUNTIME"}
             for node in objects if node["provider"] is not None and node["provider_resolution"] == "TREE_PARENT"]
    return {"objects": objects, "edges": edges, "issues": issues}


def topology_signature(graph):
    return digest(json_bytes([{key: node[key] for key in ("class", "registry_entry_id", "registry_path", "provider_candidates", "children")}
                              for node in graph["objects"]]))


def graph_summary(graph):
    relevant = [node for node in graph["objects"] if node["scope"] == "relevant"]
    counts = dict(sorted(collections.Counter(node["class"] for node in relevant).items()))
    epic = [{"registry_entry_id": node["registry_entry_id"], "class": node["class"],
             "registry_path": node["registry_path"], "provider": node["provider"],
             "properties": {key: value for key, value in node["properties"].items()
                            if key in ("EPICName", "EPICUnit", "EPICLocation", "Unit", "Location")}}
            for node in relevant if any(key in node["properties"] for key in ("EPICName", "EPICUnit"))]
    return {"relevant_object_count": len(relevant), "context_object_count": len(graph["objects"]) - len(relevant),
            "class_counts": counts, "epic_objects": epic,
            "source_count": None, "source_count_status": "NOT_ESTABLISHED_BY_PUBLIC_OBJECT_COUNTS",
            "baseline_lifetime": "PRESENT_WHILE_DISCONNECTED_NOT_PROOF_OF_PERMANENCE"}


def diff_snapshots(before, after):
    if before.get("schema_version") != SCHEMA_VERSION or after.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("Unsupported snapshot schema")
    if before.get("capture_generation") == after.get("capture_generation"):
        raise ValueError("A differential requires distinct capture generations")
    if not before.get("capture_policy_sha256") or before.get("capture_policy_sha256") != after.get("capture_policy_sha256"):
        raise ValueError("Capture policies differ")
    if before.get("tool_provenance", {}).get("source_sha256") != after.get("tool_provenance", {}).get("source_sha256"):
        raise ValueError("Capture normalization code differs")
    boot_before = before.get("environment", {}).get("boot_session")
    boot_after = after.get("environment", {}).get("boot_session")
    same_boot = boot_before is not None and boot_before == boot_after
    left = {node["registry_entry_id"]: node for node in before["graph"]["objects"]}
    right = {node["registry_entry_id"]: node for node in after["graph"]["objects"]}
    if len(left) != len(before["graph"]["objects"]) or len(right) != len(after["graph"]["objects"]):
        raise ValueError("Duplicate normalized runtime identity")
    events = []
    unmatched_left = set(left)
    unmatched_right = set(right)
    if same_boot:
        for identity in sorted(set(left) & set(right)):
            old, new = left[identity], right[identity]
            if old["class"] != new["class"]:
                continue
            kinds = ["PERSISTENT"]
            if json_bytes(old["properties"]) != json_bytes(new["properties"]):
                kinds.append("PROPERTY_CHANGED")
            if old["provider_candidates"] != new["provider_candidates"]:
                kinds.append("PROVIDER_CHANGED")
            if set(new["children"]) - set(old["children"]):
                kinds.append("CHILD_ADDED")
            events.append({"before": identity, "after": identity, "class": old["class"], "kinds": kinds,
                           "identity_basis": "REGISTRY_ID_WITHIN_SAME_BOOT_ONLY", "stable_semantic_id": None,
                           "property_changes": {key: {"before": old["properties"].get(key), "after": new["properties"].get(key),
                                                      "before_present": key in old["properties"], "after_present": key in new["properties"]}
                                                for key in sorted(set(old["properties"]) | set(new["properties"]))
                                                if (key in old["properties"]) != (key in new["properties"]) or json_bytes(old["properties"].get(key)) != json_bytes(new["properties"].get(key))}})
            unmatched_left.remove(identity)
            unmatched_right.remove(identity)
    def correspondence(nodes, identities):
        groups = collections.defaultdict(list)
        for identity in identities:
            node = nodes[identity]
            if node["registry_path"] and not node["path_redacted"] and node["provider_resolution"] != "AMBIGUOUS":
                groups[(node["class"], node["registry_path"])].append(identity)
        return groups
    left_paths = correspondence(left, unmatched_left)
    right_paths = correspondence(right, unmatched_right)
    for key in sorted(set(left_paths) & set(right_paths)):
        if len(left_paths[key]) == len(right_paths[key]) == 1:
            old, new = left_paths[key][0], right_paths[key][0]
            events.append({"before": old, "after": new, "class": key[0], "kinds": ["IDENTITY_RECREATED"],
                           "identity_basis": "UNIQUE_CLASS_PATH_CORRESPONDENCE_CANDIDATE", "confidence": "INFERRED_RUNTIME",
                           "stable_semantic_id": None, "same_object_proved": False})
            unmatched_left.remove(old)
            unmatched_right.remove(new)
    for identity in sorted(unmatched_left):
        events.append({"before": identity, "after": None, "class": left[identity]["class"], "kinds": ["REMOVED_ON_CONNECT"]})
    for identity in sorted(unmatched_right):
        events.append({"before": None, "after": identity, "class": right[identity]["class"], "kinds": ["CREATED_ON_CONNECT"]})
    before_counts = graph_summary(before["graph"])["class_counts"]
    after_counts = graph_summary(after["graph"])["class_counts"]
    return {"schema_version": SCHEMA_VERSION, "before_generation": before["capture_generation"],
            "after_generation": after["capture_generation"], "same_boot": same_boot,
            "events": events, "cardinality": [{"class": name, "disconnected": before_counts.get(name, 0),
                                                "connected": after_counts.get(name, 0),
                                                "delta": after_counts.get(name, 0) - before_counts.get(name, 0),
                                                "interpretation": "REGISTRY_OBJECTS_NOT_SOURCE_STREAMS"}
                                               for name in sorted(set(before_counts) | set(after_counts))],
            "provider_ambiguities": before["graph"]["issues"] + after["graph"]["issues"],
            "same_dptx_sources": "PASSIVE_SAME_DPTX_SOURCE_EVIDENCE_NOT_ESTABLISHED",
            "source_identity_inferred_from_counts": False,
            "causation_limit": "Observed between snapshots; connect labels describe the milestone, not proof of causation"}


def hexadecimal_identifier(value):
    if type(value) is int and 0 <= value <= 0xffff:
        return value
    if isinstance(value, str):
        match = re.fullmatch(r"(?:0x)?([0-9a-fA-F]{1,4})(?: \([^\n]*\))?", value)
        if match:
            return int(match[1], 16)
    return None


def profiler_fields(item, allowed):
    result = {}
    for key in allowed:
        if key not in item or SENSITIVE.search(key):
            continue
        try:
            result[key] = technical_value(item[key])
        except ValueError:
            continue
    return result


def parse_profiler(raw):
    if not isinstance(raw, bytes) or not 0 < len(raw) <= MAX_INPUT_BYTES:
        raise ValueError("Missing or excessive profiler output")
    parsed = json.loads(raw, parse_constant=lambda value: (_ for _ in ()).throw(ValueError("Non-finite profiler number")))
    if not isinstance(parsed, dict) or not all(isinstance(parsed.get(key), list) for key in ("SPDisplaysDataType", "SPUSBDataType")):
        raise ValueError("Missing display or USB profiler section")
    displays = []
    for adapter in parsed["SPDisplaysDataType"]:
        if not isinstance(adapter, dict) or not isinstance(adapter.get("spdisplays_ndrvs", []), list):
            raise ValueError("Invalid profiler display adapter")
        for item in adapter.get("spdisplays_ndrvs", []):
            if not isinstance(item, dict) or len(displays) >= 128:
                raise ValueError("Invalid or excessive profiler displays")
            fields = profiler_fields(item, DISPLAY_FIELDS - {"spdisplays_ndrvs"})
            connection = fields.get("spdisplays_connection_type")
            display_type = fields.get("spdisplays_display_type", "")
            builtin = connection == "spdisplays_internal" or fields.get("spdisplays_builtin") == "spdisplays_yes" or str(display_type).startswith("spdisplays_built-in")
            builtin_known = builtin or connection is not None or fields.get("spdisplays_builtin") == "spdisplays_no"
            vendor = hexadecimal_identifier(fields.get("_spdisplays_display-vendor-id"))
            product = hexadecimal_identifier(fields.get("_spdisplays_display-product-id"))
            label = item.get("_name")
            approved_label = label if label in ("Color LCD", "VG248", "ASUS VG248", "Liquid Retina XDR Display") else "display-name-omitted"
            displays.append({"capture_local_index": len(displays), "label": approved_label,
                             "raw_fields": fields, "builtin": builtin if builtin_known else None,
                             "vendor_id": vendor, "product_id": product,
                             "expected_monitor_descriptor_match": (vendor, product) == TARGET_DISPLAY_PAIR,
                             "identity_kind": "RUNTIME_DISPLAY_RECORD_NOT_SOURCE_ID"})
    hubs = []
    pending = [(item, None, 0) for item in parsed["SPUSBDataType"]]
    visited = 0
    while pending:
        item, parent_candidate, depth = pending.pop()
        visited += 1
        if not isinstance(item, dict) or depth > MAX_DEPTH or visited > MAX_NODES:
            raise ValueError("Invalid or excessive USB profiler hierarchy")
        vendor, product = hexadecimal_identifier(item.get("vendor_id")), hexadecimal_identifier(item.get("product_id"))
        if (vendor, product) in TARGET_USB_PAIRS:
            identity = len(hubs)
            hubs.append({"capture_local_index": identity, "parent_candidate_index": parent_candidate,
                         "vendor_id": vendor, "product_id": product, "raw_fields": profiler_fields(item, USB_FIELDS),
                         "identity_basis": "NON_UNIQUE_HISTORICAL_HUB_DESCRIPTOR_MATCH"})
            parent_candidate = identity
        children = item.get("_items", [])
        if not isinstance(children, list):
            raise ValueError("Invalid USB child list")
        pending.extend((child, parent_candidate, depth + 1) for child in children)
    thunderbolt = []
    roots = parsed.get("SPThunderboltDataType", [])
    if not isinstance(roots, list) or len(roots) > 64:
        raise ValueError("Invalid Thunderbolt context")
    for item in roots:
        if not isinstance(item, dict):
            raise ValueError("Invalid Thunderbolt port context")
        context = profiler_fields(item, THUNDERBOLT_FIELDS)
        ports = {key: profiler_fields(value, THUNDERBOLT_FIELDS) for key, value in item.items()
                 if re.fullmatch(r"receptacle_\d+", key) and isinstance(value, dict)}
        thunderbolt.append({"port_context": context, "receptacles": ports})
    return {"displays": displays, "usb_hub_candidates": hubs, "thunderbolt_port_context": thunderbolt,
            "privacy": "Display labels restricted; USB descriptor candidates only; root/device names, serials, EDID, UUIDs and unrelated devices omitted",
            "usb_descriptor_limit": "Matching descriptor pairs are non-unique and do not prove the physical hub or DP branch identity"}


def target_usb_ids(properties):
    return {record["entry_id"] for record in properties.get("IOUSBHostDevice", [])
            if (record["properties"]["values"].get("idVendor"), record["properties"]["values"].get("idProduct")) in TARGET_USB_PAIRS}


def filter_tree(tree, graph):
    retained = {node["registry_entry_id"]: node for node in graph["objects"]}
    return [{"entry_id": node["entry_id"], "class": node["class"],
             "name": safe_name(node)[0], "name_redacted": safe_name(node)[1],
             "provider_id": node["provider_id"], "ancestry": node["ancestry"],
             "selected": retained[node["entry_id"]]["scope"] == "relevant"}
            for node in tree if node["entry_id"] in retained]


def build_snapshot(tree_before, tree_after, properties, profiler, environment, state, generation, provenance):
    if state not in ("disconnected", "connected"):
        raise ValueError("Unknown connection state")
    usb_ids = target_usb_ids(properties)
    extra = usb_ids | {record["entry_id"] for query, records in properties.items()
                       if query not in ("AFKEndpointInterface", "IOUSBHostDevice") for record in records}
    extra.update(record["entry_id"] for record in properties.get("AFKEndpointInterface", [])
                 if str(record["properties"]["values"].get("EPICName", "")).startswith(("dcp", "DCP")))
    before = normalize_registry(tree_before, {}, generation, extra)
    graph = normalize_registry(tree_after, properties, generation, extra)
    selected = {node["registry_entry_id"] for node in graph["objects"] if node["scope"] == "relevant"}
    retained_properties = {query: [record for record in records if record["entry_id"] in selected | extra]
                           for query, records in properties.items()}
    unpaired = sorted({record["entry_id"] for records in retained_properties.values() for record in records} - selected)
    summary = graph_summary(graph)
    summary.update(display_record_count=len(profiler["displays"]),
                   builtin_display_count=sum(item["builtin"] is True for item in profiler["displays"]),
                   external_display_count=sum(item["builtin"] is False for item in profiler["displays"]),
                   unknown_display_location_count=sum(item["builtin"] is None for item in profiler["displays"]),
                   expected_monitor_record_count=sum(item["expected_monitor_descriptor_match"] for item in profiler["displays"]),
                   usb_hub_candidate_count=len(profiler["usb_hub_candidates"]),
                   usb_registry_candidate_count=len(usb_ids),
                   query_match_counts={query: len({record["entry_id"] for record in records}) for query, records in retained_properties.items()})
    stable = topology_signature(before) == topology_signature(graph)
    boot_stable = environment["boot_before"] == environment["boot_after"]
    blocking = [issue for issue in graph["issues"] + before["issues"] if issue["code"] != "PROPERTY_CHANGED_DURING_CAPTURE"]
    valid = stable and boot_stable and not blocking and not unpaired
    disconnected_absence = state == "disconnected" and valid and summary["builtin_display_count"] >= 1 and not any(
        summary[key] for key in ("external_display_count", "unknown_display_location_count", "expected_monitor_record_count",
                                 "usb_hub_candidate_count", "usb_registry_candidate_count"))
    value = {"schema_version": SCHEMA_VERSION, "milestone": "M5P3", "state": state, "capture_generation": generation,
             "capture_policy_sha256": digest(json_bytes(capture_policy())), "tool_provenance": provenance,
             "environment": {**environment, "boot_session": environment["boot_before"]},
             "graph": graph, "profiler": profiler, "summary": summary,
             "validation": {"status": "VALID" if valid else "INVALID", "relevant_hierarchy_stable": stable,
                            "boot_stable": boot_stable, "unpaired_property_objects": unpaired, "blocking_issues": blocking,
                            "disconnected_absence_confirmed": disconnected_absence,
                            "atomicity": "Sequential public queries bracketed by hierarchy and boot metadata; not an atomic runtime snapshot"},
             "physical_state_basis": "OWNER_DECLARED_UNPLUGGED" if state == "disconnected" else "OWNER_CONFIRMED_CONNECTED_AND_MIRRORED",
             "connected_results": "PENDING_USER_CONNECTION" if state == "disconnected" else "PENDING_OFFLINE_DIFFERENTIAL",
             "source_semantics": "NOT_ESTABLISHED_BY_PUBLIC_IDENTITIES",
             "hardware_commands_authorized": False}
    return value, {"before": filter_tree(tree_before, before), "after": filter_tree(tree_after, graph)}, retained_properties


def boot_value(raw):
    match = re.fullmatch(rb"\{ sec = ([0-9]+), usec = ([0-9]+) \}[^\r\n]*\n?", raw)
    if not match:
        raise ValueError("Unrecognized public boot-time metadata")
    return {"seconds_since_unix_epoch": int(match[1]), "microseconds": int(match[2])}


def git_metadata(arguments):
    allowed = {("rev-parse", "HEAD"), ("symbolic-ref", "--short", "HEAD"),
               ("status", "--porcelain=v1"), ("show", "HEAD:tools/runtime_display_snapshot.py"),
               ("show", "HEAD:tools/capture_baseline.py")}
    if tuple(arguments) not in allowed:
        raise ValueError("Unapproved Git metadata request")
    return subprocess.check_output(["/usr/bin/git", *arguments], cwd=REPOSITORY, stdin=subprocess.DEVNULL,
                                   stderr=subprocess.DEVNULL, timeout=10)


def tool_provenance():
    commit = git_metadata(("rev-parse", "HEAD")).decode("ascii").strip()
    branch = git_metadata(("symbolic-ref", "--short", "HEAD")).decode("ascii").strip()
    if not re.fullmatch(r"[0-9a-f]{40}", commit) or branch != "research/m5-passive-runtime-topology":
        raise ValueError("Capture requires the M5P3 branch and an exact commit")
    sources = {}
    for name in ("tools/runtime_display_snapshot.py", "tools/capture_baseline.py"):
        raw = (REPOSITORY / name).read_bytes()
        if raw != git_metadata(("show", "HEAD:" + name)):
            raise ValueError("Commit capture/normalization code before collecting runtime evidence")
        sources[name] = digest(raw)
    return {"macmst_commit": commit, "branch": branch, "source_sha256": sources,
            "worktree_clean": not bool(git_metadata(("status", "--porcelain=v1")).strip()),
            "host_evidence_baseline": "5aed45b9458be08ba05b24804d9439644ccb7c2c"}


def safe_output(path):
    root = REPOSITORY / "artifacts/runtime/m5p3"
    destination = path.absolute()
    if destination.exists() or not destination.resolve().is_relative_to(root.resolve()) or destination.resolve() == root.resolve():
        raise ValueError("Capture output must be a new directory under artifacts/runtime/m5p3")
    for component in (destination, *destination.parents):
        if component.is_symlink():
            raise ValueError("Symlink capture output is not allowed")
    return destination


def write_capture(destination, snapshot, tree, properties, commands, started):
    files = {"snapshot.json": snapshot, "registry-tree.json": tree, "registry-properties.json": properties,
             "system-profiler.json": snapshot["profiler"], "topology-summary.json": snapshot["summary"]}
    encoded = {name: json_bytes(value) for name, value in files.items()}
    manifest = {"schema_version": SCHEMA_VERSION, "milestone": "M5P3", "state": snapshot["state"],
                "capture_generation": snapshot["capture_generation"], "started_utc": started, "completed_utc": now(),
                "environment": snapshot["environment"], "tool_provenance": snapshot["tool_provenance"],
                "capture_policy": capture_policy(), "capture_policy_sha256": snapshot["capture_policy_sha256"],
                "commands": commands, "validation": snapshot["validation"],
                "topology_description": "Hub unplugged from Mac; no requested display/lid/sleep/mode change" if snapshot["state"] == "disconnected"
                                        else "Owner-confirmed usual two-monitor hub connection and existing mirrored behavior; no configuration changes",
                "privacy": "Only filtered technical registry/profiler values retained. Original stdout hashes are provenance, not retained unredacted dumps. No serials, EDID, user names or unrelated USB devices retained.",
                "artifacts": {name: digest(raw) for name, raw in encoded.items()}}
    encoded["manifest.json"] = json_bytes(manifest)
    encoded["hashes.json"] = json_bytes({name: digest(raw) for name, raw in encoded.items()})
    destination.mkdir(parents=True, exist_ok=False)
    for name, raw in encoded.items():
        with (destination / name).open("xb") as stream:
            stream.write(raw)


def validate_capture(directory):
    expected = {"snapshot.json", "registry-tree.json", "registry-properties.json", "system-profiler.json",
                "topology-summary.json", "manifest.json", "hashes.json"}
    if directory.is_symlink() or not directory.is_dir() or {path.name for path in directory.iterdir()} != expected:
        raise ValueError("Capture file set is incomplete or unexpected")
    raw_files = {}
    for name in expected:
        path = directory / name
        if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_INPUT_BYTES:
            raise ValueError("Invalid capture input file")
        raw_files[name] = path.read_bytes()
    values = {name: json.loads(raw) for name, raw in raw_files.items()}
    hashes = values["hashes.json"]
    if set(hashes) != expected - {"hashes.json"} or any(digest(raw_files[name]) != value for name, value in hashes.items()):
        raise ValueError("Capture input hash mismatch")
    manifest = values["manifest.json"]
    if set(manifest["artifacts"]) != expected - {"hashes.json", "manifest.json"} or any(digest(raw_files[name]) != value for name, value in manifest["artifacts"].items()):
        raise ValueError("Capture manifest hash mismatch")
    snapshot = values["snapshot.json"]
    if manifest["capture_policy_sha256"] != digest(json_bytes(manifest["capture_policy"])) or manifest["capture_policy_sha256"] != digest(json_bytes(capture_policy())):
        raise ValueError("Capture normalization policy differs")
    rebuilt, _, _ = build_snapshot(values["registry-tree.json"]["before"], values["registry-tree.json"]["after"],
                                    values["registry-properties.json"], values["system-profiler.json"], snapshot["environment"],
                                    snapshot["state"], snapshot["capture_generation"], snapshot["tool_provenance"])
    if json_bytes(rebuilt) != json_bytes(snapshot) or snapshot["summary"] != values["topology-summary.json"]:
        raise ValueError("Normalized capture does not reproduce from retained inputs")
    if any(manifest[key] != snapshot[key] for key in ("state", "capture_generation", "environment", "tool_provenance", "validation")):
        raise ValueError("Capture manifest/snapshot identity mismatch")
    if [(record.get("label"), tuple(record.get("argv", []))) for record in manifest["commands"]] != command_plan():
        raise ValueError("Capture command policy or sequence differs")
    if any(record["status"] != "OK" for record in manifest["commands"]) or snapshot["validation"]["status"] != "VALID":
        raise ValueError("Capture has command or topology failures")
    return snapshot


def capture(state, generation, output, confirmation=None):
    destination = safe_output(output)
    if state == "connected" and confirmation != "connected and mirrored":
        raise ValueError("Connected capture requires the owner's explicit connected and mirrored confirmation")
    if state == "disconnected" and confirmation is not None:
        raise ValueError("No connected confirmation belongs to a disconnected capture")
    provenance = tool_provenance()
    if state == "connected":
        before = validate_capture(REPOSITORY / "artifacts/runtime/m5p3/disconnected")
        if not before["validation"]["disconnected_absence_confirmed"] or before["tool_provenance"]["source_sha256"] != provenance["source_sha256"]:
            raise ValueError("Validated disconnected baseline and identical capture code are required")
    started = now()
    parsed = {}
    commands = []
    for label, argv in command_plan():
        record, raw = execute_public(argv)
        record["label"] = label
        commands.append(record)
        if record["status"] != "OK":
            raise ValueError("Public query failed; no privilege escalation or fallback permitted: " + label)
        if label.startswith("tree_"):
            parsed[label] = parse_registry_tree(raw)
        elif label.startswith("registry_"):
            parsed[label] = parse_registry_properties(raw)
        elif label == "profiler":
            parsed[label] = parse_profiler(raw)
        elif label.startswith("boot_"):
            parsed[label] = boot_value(raw)
        else:
            parsed[label] = raw.decode("ascii").strip()
        if label == "os_build" and (parsed["os_version"], parsed["os_build"]) != ("26.6.2", "25G83"):
            raise ValueError("OS changed from the approved 26.6.2/25G83 baseline")
        if label == "soc" and (parsed["machine_model"], parsed["soc"]) != ("Mac17,2", "Apple M5"):
            raise ValueError("Machine differs from the approved base M5 target")
    properties = {name: parsed["registry_" + name] for name in REGISTRY_CLASSES}
    environment = {key: parsed[key] for key in ("os_version", "os_build", "machine_model", "soc", "boot_before", "boot_after")}
    snapshot, tree, retained = build_snapshot(parsed["tree_before"], parsed["tree_after"], properties, parsed["profiler"],
                                               environment, state, generation, provenance)
    write_capture(destination, snapshot, tree, retained, commands, started)
    validated = validate_capture(destination)
    if state == "disconnected" and not validated["validation"]["disconnected_absence_confirmed"]:
        raise ValueError("Expected disconnected external-display/hub absence was not established")
    print(json.dumps({"state": state, "capture": str(destination.relative_to(REPOSITORY)), "validation": validated["validation"],
                      "class_counts": validated["summary"]["class_counts"], "display_record_count": validated["summary"]["display_record_count"],
                      "external_display_count": validated["summary"]["external_display_count"],
                      "usb_hub_candidate_count": validated["summary"]["usb_hub_candidate_count"],
                      "next_phase": "PENDING_USER_CONNECTION" if state == "disconnected" else "PENDING_OFFLINE_DIFFERENTIAL"}, sort_keys=True))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="operation", required=True)
    subparsers.add_parser("plan", help="print the fixed public-read command plan without executing it")
    collector = subparsers.add_parser("capture")
    collector.add_argument("--state", required=True, choices=("disconnected", "connected"))
    collector.add_argument("--generation", required=True)
    collector.add_argument("--output", required=True, type=pathlib.Path)
    collector.add_argument("--confirmation", choices=("connected and mirrored",))
    validator = subparsers.add_parser("validate")
    validator.add_argument("directory", type=pathlib.Path)
    differ = subparsers.add_parser("diff")
    differ.add_argument("disconnected", type=pathlib.Path)
    differ.add_argument("connected", type=pathlib.Path)
    arguments = parser.parse_args(argv)
    try:
        if arguments.operation == "plan":
            print(json.dumps(capture_policy(), indent=2, sort_keys=True))
        elif arguments.operation == "capture":
            capture(arguments.state, arguments.generation, arguments.output, arguments.confirmation)
        elif arguments.operation == "validate":
            value = validate_capture(arguments.directory)
            print(json.dumps({"state": value["state"], "validation": value["validation"], "summary": value["summary"]}, sort_keys=True))
        else:
            before, after = validate_capture(arguments.disconnected), validate_capture(arguments.connected)
            if before["state"] != "disconnected" or after["state"] != "connected":
                raise ValueError("Differential requires disconnected then connected captures")
            print(json.dumps(diff_snapshots(before, after), indent=2, sort_keys=True))
    except (OSError, ValueError, KeyError, TypeError, plistlib.InvalidFileException, subprocess.SubprocessError) as error:
        print(json.dumps({"status": "FAILED", "error_type": type(error).__name__, "scope": "public snapshot validation; no escalation or private fallback"}), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())