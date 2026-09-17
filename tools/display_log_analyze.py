#!/usr/bin/env python3
"""M5P4 narrow public display log normalization; no private display interfaces."""

import argparse
import collections
import datetime
import hashlib
import json
import os
import pathlib
import re
import selectors
import subprocess
import sys
import time


REPOSITORY = pathlib.Path(__file__).resolve().parents[1]
M5P3_HEAD = "369b5e5f202640f906904d2dc91413bd1b0930f3"
TERMS = ("DCPDPDeviceProxy", "DCPDPServiceProxy", "DCPAVVideoInterfaceProxy",
         "AppleDCPDPTXRemotePortProxy", "AppleDCPDP2HDMI")
PREDICATE = 'process == "kernel" AND (\n' + " OR\n".join(
    '\teventMessage CONTAINS[c] "' + term + '"' for term in TERMS) + "\n)"
WINDOW_START = "2026-09-16T11:11:59Z"
WINDOW_END = "2026-09-16T11:27:49Z"
MAX_RECORDS = 1000
MAX_INPUT_BYTES = 2 * 1024 * 1024
MAX_LINE_BYTES = 64 * 1024
TIMESTAMP = re.compile(r"(\d{4}-\d\d-\d\d)[T ](\d\d:\d\d:\d\d)(?:\.(\d{1,9}))?(Z|[+-]\d\d:?\d\d)\Z")
PRIVATE = re.compile(r"<private>|<redacted>|\[REDACTED[^\]]*\]", re.I)
IRRELEVANT_PRIVATE = re.compile(r"/(?:Users|home)/|(?:https?|ssh|ftp)://|\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b|\b(?:\d{1,3}\.){3}\d{1,3}\b")
PERSONAL_IDENTIFIER = re.compile(r"\b(serial(?:[_ -]?number)?|uuid|guid|udid|mac[_ -]?address)\s*[:=]\s*(?:\"[^\"]*\"|[^\s,;]+)", re.I)
NEGATED_OR_HYPOTHETICAL = re.compile(r"\b(?:not|never|would|might|could|hypothetical|example|attempt(?:ing)?|request(?:ed)?|query|dry-run)\b", re.I)
IDENTIFIER = r"(?:0x[0-9a-fA-F]+|[0-9]+)"
EVENT_RULES = (
    ("LINK_DETECTED", r"\b(?:physical\s+)?link\s+(?:was\s+)?detected\b|\bdetected\s+(?:a\s+)?(?:DP|DisplayPort)\s+link\b"),
    ("HPD_CHANGE", r"\bHPD\s*(?:changed\s+(?:to\s+)?|[:=]\s*|is\s+)(?:high|low|asserted|deasserted|0|1|2)\b"),
    ("TRANSPORT_ACTIVE", r"\btransport\s+(?:is\s+|became\s+|state\s*[:=]\s*|active\s*[:=]\s*)?(?:active|true)\b"),
    ("SERVICE_ANNOUNCED", r"\b(?:announced|published)\s+(?:EPIC\s+)?service\b|\bservice\b.{0,80}\b(?:announced|published)\b"),
    ("DEVICE_CREATED", r"\bcreated\s+(?:DP\s+|AV\s+)?device\b|\bdevice\s+(?:id\s*[:=]\s*\w+\s+)?(?:was\s+)?created\b"),
    ("DEVICE_MATCHED", r"\bmatched\s+(?:DP\s+|AV\s+)?device\b|\bdevice\b.{0,40}\bmatched\b"),
    ("DISPLAY_CREATED", r"\bcreated\s+(?:logical\s+)?display\b|\b(?:logical\s+)?display\s+(?:id\s*[:=]\s*\w+\s+)?(?:was\s+)?created\b"),
    ("DISPLAY_ATTACHED", r"\b(?:logical\s+)?display\b.{0,40}\battached\b|\battached\s+(?:logical\s+)?display\b"),
    ("SINK_DISCOVERED", r"\bdiscovered\s+(?:(?:a|another|second)\s+)?(?:downstream\s+)?sink\b|\bsink\s+(?:id\s*[:=]\s*\w+\s+)?(?:was\s+)?discovered\b"),
    ("MODE_SELECTED", r"\bselected\s+(?:display\s+|video\s+)?mode\b|\bmode\b.{0,40}\bselected\b"),
    ("MIRROR_SELECTED", r"\b(?:selected|forced|chose|enforced|fell\s+back\s+to)\s+(?:the\s+)?(?:mirror(?:ing)?|clone)(?:\s+mode)?\b|\b(?:mirror|clone)\s+(?:mode\s+|policy\s+)?(?:selected|forced|enabled)\b"),
    ("STREAM_CREATED", r"\bcreated\s+(?:source\s+)?stream\s+(?:id\s*[:=]\s*)?(?:0x[0-9a-f]+|[0-9]+)\b|\bstream\s+(?:id\s*[:=]\s*)?(?:0x[0-9a-f]+|[0-9]+)\s+(?:was\s+)?created\b"),
    ("STREAM_REJECTED", r"\brejected\s+(?:source\s+)?stream\b|\bstream\s+(?:id\s*[:=]\s*)?(?:0x[0-9a-f]+|[0-9]+)\s+(?:was\s+)?rejected\b"),
    ("MST_DETECTED", r"\bMST\s+(?:branch\s+|topology\s+)?detected\b|\bdetected\s+(?:an?\s+)?MST\b"),
    ("MST_DISABLED", r"\b(?:MST|multi-stream)\s+(?:is\s+|was\s+)?disabled\b|\bdisabled\s+(?:MST|multi-stream)\b"),
)
MST_DECISION = re.compile(
    r"\b(?:MST|multi-stream)\s+(?:topology\s+|mode\s+)?(?:is\s+|was\s+)?(?:unsupported|disabled|rejected|forbidden)\b|"
    r"\b(?:rejected|disabled|forbids)\s+(?:the\s+)?(?:MST|multi-stream)\b|"
    r"\b(?:enforced|enforcing)\s+(?:a\s+)?(?:maximum\s+)?stream\s+(?:count\s+)?limit\b|"
    r"\b(?:MST\s+)?topology\s+rejected\s+because\s+(?:the\s+link\s+is\s+)?non-tunneled\b|"
    r"\bbranch\s+mode\s+forced\s+to\s+(?:SST|clone)\b", re.I)
SOURCE_BINDING = re.compile(
    rf"\bsource(?:[ _](?:stream|context))?(?:[ _]id)?\s*[:=# ]\s*({IDENTIFIER})\s*"
    rf"(?:->|bound\s+to|assigned\s+to)\s*(?:physical\s+)?DPTX\s*[:=# ]?\s*({IDENTIFIER})\b", re.I)
SOURCE_CREATED = re.compile(rf"\bcreated\s+source\s+(?:stream\s+|context\s+)?(?:id\s*[:=]\s*)?({IDENTIFIER})\b", re.I)
SECOND_ENTITY = re.compile(
    r"\b(?:discovered|detected|ignored|discarded|enumerated)\s+(?:a\s+|the\s+)?(?:second|another)\s+downstream\s+(?:sink|device|port)\b|"
    r"\bsecond\s+downstream\s+(?:sink|device|port)\s+(?:was\s+)?(?:discovered|detected|ignored|discarded|enumerated)\b", re.I)
METHOD = re.compile(r"\b(" + "|".join(TERMS) + r")(?:<(0x[0-9a-fA-F]+)>)?::([A-Za-z0-9_]+)")


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def json_bytes(value):
    return (json.dumps(value, sort_keys=True, ensure_ascii=True, allow_nan=False, separators=(",", ":")) + "\n").encode("ascii")


def timestamp_ns(value):
    if not isinstance(value, str) or (match := TIMESTAMP.fullmatch(value)) is None:
        raise ValueError("Log timestamp requires an explicit timezone and bounded precision")
    day, clock, fraction, offset = match.groups()
    offset = "+00:00" if offset == "Z" else offset
    moment = datetime.datetime.fromisoformat(day + "T" + clock + offset)
    delta = moment.astimezone(datetime.timezone.utc) - datetime.datetime(1970, 1, 1, tzinfo=datetime.timezone.utc)
    return (delta.days * 86400 + delta.seconds) * 1000000000 + int((fraction or "").ljust(9, "0"))


def process_name(record):
    explicit = record.get("process")
    image = record.get("processImagePath")
    name = pathlib.PurePosixPath(image).name if isinstance(image, str) else None
    if isinstance(explicit, str) and name is not None and explicit != name:
        raise ValueError("Inconsistent log process identity")
    return explicit if isinstance(explicit, str) else name


def in_scope(record, subsystems=(), categories=()):
    if not isinstance(record, dict) or process_name(record) != "kernel":
        return False
    message = record.get("eventMessage")
    if not isinstance(message, str) or not any(term.casefold() in message.casefold() for term in TERMS):
        return False
    if subsystems and record.get("subsystem") not in subsystems:
        return False
    if categories and record.get("category") not in categories:
        return False
    stamp = timestamp_ns(record.get("timestamp"))
    return timestamp_ns(WINDOW_START) <= stamp <= timestamp_ns(WINDOW_END)


def privacy_record(record):
    message = record["eventMessage"]
    if len(message.encode("utf-8")) > MAX_LINE_BYTES or IRRELEVANT_PRIVATE.search(message):
        return None, ["RECORD_DROPPED_FOR_IRRELEVANT_PRIVATE_CONTENT"]
    if any(ord(character) < 32 and character not in "\t\n\r" for character in message):
        return None, ["RECORD_DROPPED_FOR_CONTROL_CHARACTERS"]
    reasons = []
    message, count = PERSONAL_IDENTIFIER.subn(lambda match: match[1] + "=[REDACTED_IDENTIFIER]", message)
    if count:
        reasons.append("PERSONAL_IDENTIFIER_REDACTED")
    if PRIVATE.search(message):
        reasons.append("REDACTED_VALUES_REMAIN_UNKNOWN")
    retained = {"timestamp": record["timestamp"], "process": "kernel", "eventMessage": message}
    for key in ("senderImagePath", "subsystem", "category", "messageType", "eventType", "signpostName", "signpostType"):
        value = record.get(key)
        if isinstance(value, str) and len(value) <= 512 and value.isprintable() and not IRRELEVANT_PRIVATE.search(value):
            if key == "senderImagePath" and not value.startswith(("/System/", "/usr/lib/", "/kernel")):
                reasons.append("NON_SYSTEM_SENDER_PATH_OMITTED")
                continue
            retained[key] = value
    for key in ("activityIdentifier", "parentActivityIdentifier", "signpostIdentifier", "threadID", "processID", "traceID", "machTimestamp"):
        value = record.get(key)
        if type(value) is int and 0 <= value < 1 << 64 or isinstance(value, str) and re.fullmatch(IDENTIFIER, value):
            retained[key] = value
    return retained, reasons


def classify_message(message):
    if PRIVATE.search(message) or NEGATED_OR_HYPOTHETICAL.search(message):
        return {"events": ["UNKNOWN_EVENT"], "explicit_source_labels": [], "source_bindings": [],
                "second_downstream_statement": False, "mirror_decision": False, "mst_policy_decision": False,
                "qualification": "REDACTED_OR_NON_ASSERTIVE_MESSAGE; no hidden value inferred"}
    events = [name for name, pattern in EVENT_RULES if re.search(pattern, message, re.I)]
    mirror = "MIRROR_SELECTED" in events
    mst = MST_DECISION.search(message) is not None
    if mirror or mst or re.search(r"\bpolicy\s+(?:decision|selected|rejected|enforced)\b", message, re.I):
        events.append("POLICY_DECISION")
    bindings = [{"source_label": match[1], "dptx_label": match[2], "basis": "EXPLICIT_LOG_TEXT_NOT_INDEPENDENT_HARDWARE_SEMANTICS"}
                for match in SOURCE_BINDING.finditer(message)]
    sources = sorted({match[1] for match in SOURCE_CREATED.finditer(message)} | {item["source_label"] for item in bindings})
    return {"events": events or ["UNKNOWN_EVENT"], "explicit_source_labels": sources, "source_bindings": bindings,
            "second_downstream_statement": SECOND_ENTITY.search(message) is not None,
            "mirror_decision": mirror, "mst_policy_decision": mst,
            "qualification": "EXPLICIT_MESSAGE_PATTERN; manual contextual review required"}


def explicit_identifiers(message):
    patterns = {
        "registry_entry_id": rf"\b(?:IORegistryEntryID|registry[ _]entry[ _]id)\s*[:=]\s*({IDENTIFIER})\b",
        "epic_name": r"\bEPICName\s*[:=]\s*[\"]?([a-z0-9_-]+-epic)\b",
        "epic_unit": rf"\bEPICUnit\s*[:=]\s*({IDENTIFIER})\b",
        "unit": rf"\bUnit\s*[:= ]\s*({IDENTIFIER})\b",
        "port": rf"\bport(?:[ _]id)?\s*[:= ]\s*({IDENTIFIER})\b",
        "display_id": rf"\bdisplay[ _]id\s*[:= ]\s*({IDENTIFIER})\b",
        "framebuffer_id": rf"\bframebuffer[ _]id\s*[:= ]\s*({IDENTIFIER})\b",
    }
    identifiers = {name: sorted(set(re.findall(pattern, message, re.I))) for name, pattern in patterns.items()}
    identifiers["dcp_ancestry_label"] = sorted(set(re.findall(r"\bDCPEXT[01]\b", message)))
    return {name: values for name, values in identifiers.items() if values}


def normalize_record(record, generation, index, original_sha256=None):
    retained, redactions = privacy_record(record)
    if retained is None:
        return None, None, redactions
    message = retained["eventMessage"]
    normalized = {"schema_version": 1, "capture_generation": generation, "input_index": index,
                  "timestamp_raw": retained["timestamp"], "timestamp_ns": timestamp_ns(retained["timestamp"]),
                  "timestamp_units": "nanoseconds_since_unix_epoch", "timestamp_kind": "LOG_EVENT_TIMESTAMP",
                  "process": "kernel", "sender_image": retained.get("senderImagePath"),
                  "subsystem": retained.get("subsystem"), "category": retained.get("category"),
                  "level": retained.get("messageType"), "message": message,
                  "activity_id": retained.get("activityIdentifier"), "parent_activity_id": retained.get("parentActivityIdentifier"),
                  "signpost_id": retained.get("signpostIdentifier"), "thread_id": retained.get("threadID"),
                  "process_id": retained.get("processID"), "raw_filtered_sha256": digest(json_bytes(retained)),
                  "source_record_canonical_sha256": original_sha256, "privacy_notes": redactions,
                  "identifiers": explicit_identifiers(message), "classification": classify_message(message)}
    return retained, normalized, redactions


def analyze_records(records, generation="m5p4-historical-01", subsystems=(), categories=()):
    if len(records) > MAX_RECORDS:
        raise ValueError("Historical log record budget exceeded")
    filtered = []
    normalized = []
    excluded = 0
    dropped = 0
    for index, record in enumerate(records):
        if not in_scope(record, subsystems, categories):
            excluded += 1
            continue
        raw, value, reasons = normalize_record(record, generation, index, digest(json_bytes(record)))
        if raw is None:
            dropped += 1
            continue
        filtered.append(raw)
        normalized.append(value)
    if sum(len(json_bytes(record)) for record in filtered) > MAX_INPUT_BYTES:
        raise ValueError("Filtered log byte budget exceeded")
    ordered = sorted(normalized, key=lambda record: (record["timestamp_ns"], record["input_index"]))
    order = [{"before_input_index": previous["input_index"], "after_input_index": following["input_index"],
              "relation": "EARLIER_LOG_TIMESTAMP" if previous["timestamp_ns"] < following["timestamp_ns"] else "EQUAL_TIMESTAMP_NO_ORDER_PROVED",
              "confidence": "VERIFIED_LOG" if previous["timestamp_ns"] < following["timestamp_ns"] else "UNKNOWN",
              "causal_order_proved": False} for previous, following in zip(ordered, ordered[1:])]
    classifications = [record["classification"] for record in normalized]
    summary = {"record_count": len(normalized), "excluded_by_scope": excluded, "dropped_for_privacy": dropped,
               "redacted_record_count": sum(bool(record["privacy_notes"]) for record in normalized),
               "event_counts": dict(sorted(collections.Counter(event for record in classifications for event in record["events"]).items())),
               "timestamp_order": order, "timestamp_order_limit": "Timestamp ordering is not identity, cross-thread causation or user-transition timing",
               "second_downstream": "SECOND_DOWNSTREAM_ENTITY_LOGGED" if any(record["second_downstream_statement"] for record in classifications)
                                    else "NO_SECOND_DOWNSTREAM_ENTITY_IN_SCOPED_LOGS" if normalized and not dropped and not any(record["privacy_notes"] for record in normalized)
                                    else "SECOND_DOWNSTREAM_LOG_EVIDENCE_UNRESOLVED",
               "source_identity": "PUBLIC_LOG_SOURCE_IDENTITIES_FOUND" if any(record["explicit_source_labels"] for record in classifications)
                                  else "PUBLIC_LOG_SOURCE_IDENTITIES_NOT_ESTABLISHED",
               "mirror_policy": "PUBLIC_LOG_MIRROR_POLICY_FOUND" if any(record["mirror_decision"] for record in classifications) else "PUBLIC_LOG_MIRROR_POLICY_UNRESOLVED",
               "mst_policy": "PUBLIC_LOG_MST_POLICY_GATE_FOUND" if any(record["mst_policy_decision"] for record in classifications) else "PUBLIC_LOG_MST_POLICY_GATE_UNRESOLVED",
               "same_dptx_multi_source_established": False,
               "review_required": "Pattern results require full retained-message review; logs are not independently justified source ownership"}
    return {"filtered_records": filtered, "normalized_records": normalized, "summary": summary}


def parse_ndjson(raw):
    if not isinstance(raw, bytes) or len(raw) > MAX_INPUT_BYTES:
        raise ValueError("Historical output exceeds its input bound")
    if raw.strip() in (b"", b"[]"):
        return []
    def unique_object(pairs):
        value = {}
        for key, item in pairs:
            if key in value:
                raise ValueError("Duplicate log JSON key")
            value[key] = item
        return value
    result = []
    for line in raw.splitlines():
        if not line.strip():
            continue
        if len(line) > MAX_LINE_BYTES or len(result) >= MAX_RECORDS:
            raise ValueError("Historical line or record bound exceeded")
        value = json.loads(line, object_pairs_hook=unique_object,
                           parse_constant=lambda value: (_ for _ in ()).throw(ValueError("Non-finite JSON value")))
        if not isinstance(value, dict):
            raise ValueError("Historical NDJSON record must be an object")
        result.append(value)
    return result


def correlate(records, snapshot):
    nodes = snapshot["graph"]["objects"]
    by_id = {node["registry_entry_id"].lower(): node for node in nodes}
    correlations = []
    for record in records:
        identifiers = record["identifiers"]
        exact = []
        for value in identifiers.get("registry_entry_id", []):
            identity = hex(int(value, 0) if value.lower().startswith("0x") else int(value))
            if identity in by_id:
                exact.append(identity)
        candidates = []
        units = {int(value, 0) if value.lower().startswith("0x") else int(value)
                 for value in identifiers.get("epic_unit", []) + identifiers.get("unit", [])}
        groups = identifiers.get("dcp_ancestry_label", [])
        if units and groups:
            for node in nodes:
                class_match = re.search(r"\b" + re.escape(node["class"]) + r"\b", record["message"]) is not None
                unit_match = any(node["properties"].get(key) in units for key in ("EPICUnit", "Unit"))
                group_match = any("RTBuddy(" + group + ")" in (node["registry_path"] or "") for group in groups)
                if class_match and unit_match and group_match:
                    candidates.append(node["registry_entry_id"])
        correlations.append({"input_index": record["input_index"], "snapshot_generation": snapshot["capture_generation"],
                             "explicit_registry_id_value_matches": exact,
                             "class_ancestry_unit_candidates": candidates,
                             "confidence": "STRONG_LOG" if exact else "INFERRED_LOG" if candidates else "UNKNOWN",
                             "identity_limit": "Typed registry-ID value match requires boot/lifetime review; class/unit/path is only a candidate; raw pointers and timestamps never identify objects",
                             "source_identity_proved": False})
    return correlations


def method_observations(records, snapshot):
    by_id = {node["registry_entry_id"]: node for node in snapshot["graph"]["objects"]}
    groups = collections.defaultdict(list)
    tokens = collections.defaultdict(list)
    observations = []
    for record in records:
        message = record["message"]
        method = METHOD.search(message)
        if method is None:
            continue
        class_name, token, method_name = method.groups()
        groups[(class_name, method_name)].append(record["input_index"])
        if token:
            tokens[(class_name, token)].append(record["input_index"])
        fields = {}
        kind = None
        if method_name == "handleSinkCountChanged":
            match = re.search(r"\boldCount=(\d+) newCount=(\d+) add=(\d+) remove=(\d+)\b", message)
            if match:
                fields = dict(zip(("oldCount", "newCount", "add", "remove"), map(int, match.groups())))
                kind = "REPORTED_AGGREGATE_SINK_COUNT_CHANGE"
        elif "_current.displayAllocation:" in message:
            match = re.search(r"\bextraPipes=(\d+), mainUFP=(\d+), peerUFP=(\d+)\b", message)
            if match:
                fields = dict(zip(("extraPipes", "mainUFP", "peerUFP"), map(int, match.groups())))
                kind = "REPORTED_ALLOCATION_VALUES_NOT_POLICY"
        elif method_name in ("connectTo", "validateConnection"):
            match = re.search(r"\b(die\d+::dispext\d+::core\d+) -> (die\d+::atc\d+::dpphy)\b", message)
            if match:
                fields = {"upstream_route_label": match[1], "downstream_route_label": match[2]}
                kind = "REPORTED_ROUTE_LABELS_NOT_PHYSICAL_OWNER_PROOF"
        elif method_name in ("prepareLinkGated", "startLinkGated"):
            match = re.search(r"\btype=(Video|Audio) source=([A-Za-z]+)\b", message)
            if match:
                fields = {"link_type": match[1], "link_role": match[2]}
                kind = "REPORTED_LINK_ROLE_NOT_SOURCE_ID"
        elif method_name == "handleAddInterfaces":
            match = re.search(r"\b(videoInterface|audioInterface)=(0x[0-9a-fA-F]+)\b", message)
            if match:
                fields = {"interface_kind": match[1], "interface_token": match[2]}
                kind = "REPORTED_INTERFACE_TOKEN_NOT_SOURCE_ID"
        elif method_name == "copyEDID":
            match = re.search(r"\b_virtualEDIDMode=(\d+)\b", message)
            if match:
                fields = {"virtual_edid_mode_raw": int(match[1])}
                kind = "REPORTED_EDID_MODE_NOT_VIRTUAL_DEVICE_INSTANCE"
        if kind:
            observations.append({"input_index": record["input_index"], "timestamp_raw": record["timestamp_raw"],
                                 "class_label": class_name, "method_label": method_name, "observation": kind,
                                 "fields": fields, "confidence": "VERIFIED_LOG", "message": message,
                                 "raw_filtered_sha256": record["raw_filtered_sha256"], "source_identity_proved": False})
    token_candidates = []
    for (class_name, token), indices in sorted(tokens.items()):
        node = by_id.get(token)
        class_match = node is not None and node["class"] == class_name
        token_candidates.append({"class_label": class_name, "opaque_log_object_token": token, "record_indices": indices,
                                 "same_spelling_same_class_registry_id": token if class_match else None,
                                 "confidence": "INFERRED_LOG" if class_match else "UNKNOWN",
                                 "namespace_equivalence_verified": False,
                                 "limit": "Repeated explicit log token relates log records; matching registry hex/class is a candidate, not a verified identifier namespace"})
    return {"method_groups": [{"class_label": key[0], "method_label": key[1], "record_indices": indices}
                              for key, indices in sorted(groups.items())],
            "observations": observations, "opaque_token_correspondence_candidates": token_candidates,
            "message_redacted_count": sum(bool(PRIVATE.search(record["message"])) for record in records),
            "metadata_omission_count": sum("NON_SYSTEM_SENDER_PATH_OMITTED" in record["privacy_notes"] for record in records),
            "second_entity_distinct_identity_proved": False, "same_dptx_multi_source_established": False,
            "scope": "Exact field extraction from retained messages only; does not override immutable acquisition classifications"}


def review_historical():
    root = REPOSITORY / "artifacts/runtime/m5p4/historical"
    expected_files = {"raw-filtered.ndjson", "normalized.json", "analysis.json", "correlations.json", "manifest.json", "hashes.json"}
    if root.is_symlink() or {path.name for path in root.iterdir()} != expected_files:
        raise ValueError("Historical evidence file set differs")
    raw_files = {}
    for name in expected_files:
        path = root / name
        if path.is_symlink() or not path.is_file() or path.stat().st_size > 8 * MAX_INPUT_BYTES:
            raise ValueError("Invalid historical evidence file")
        raw_files[name] = path.read_bytes()
    hashes = json.loads(raw_files["hashes.json"])
    if set(hashes) != expected_files - {"hashes.json"} or any(digest(raw_files[name]) != value for name, value in hashes.items()):
        raise ValueError("Historical evidence hash mismatch")
    manifest = json.loads(raw_files["manifest.json"])
    if manifest["predicate"] != PREDICATE or manifest["command"]["argv"] != historical_command() or not manifest["query_complete"]:
        raise ValueError("Historical scope or completeness differs")
    baseline = m5p3_inputs()
    if baseline != manifest["baseline"]:
        raise ValueError("M5P3 input provenance changed")
    filtered = parse_ndjson(raw_files["raw-filtered.ndjson"])
    normalized = json.loads(raw_files["normalized.json"])
    if len(filtered) != len(normalized):
        raise ValueError("Historical raw/normalized count differs")
    for raw, record in zip(filtered, normalized):
        if raw["eventMessage"] != record["message"] or digest(json_bytes(raw)) != record["raw_filtered_sha256"] or not in_scope(raw):
            raise ValueError("Historical raw/normalized record binding differs")
    snapshot = json.loads((REPOSITORY / "artifacts/runtime/m5p3/connected/snapshot.json").read_bytes())
    result = method_observations(normalized, snapshot)
    result.update(schema_version=1, capture_generation=manifest["capture_generation"],
                  input_hashes={name: digest(raw) for name, raw in raw_files.items()},
                  review_tool_sha256=digest(pathlib.Path(__file__).read_bytes()),
                  acquisition_tool_provenance=manifest["tool_provenance"],
                  baseline=baseline)
    print(json.dumps(result, sort_keys=True, indent=2))
    return result


def historical_command():
    return ["/usr/bin/log", "show", "--style", "ndjson", "--timezone", "UTC", "--no-pager", "--no-backtrace",
            "--info", "--debug", "--signpost", "--start", "2026-09-16 11:11:59+0000",
            "--end", "2026-09-16 11:27:49+0000", "--predicate", PREDICATE]


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="microseconds")


def execute_historical(argv):
    if argv != historical_command():
        raise ValueError("Only the fixed historical public query is permitted")
    metadata = {"argv": argv, "started_utc": now(), "status": "STARTED"}
    output = bytearray()
    errors = bytearray()
    observed_hash = hashlib.sha256()
    stderr_hash = hashlib.sha256()
    output_bytes = 0
    stderr_bytes = 0
    deadline = time.monotonic() + 60
    with subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False) as process:
        with selectors.DefaultSelector() as selector:
            selector.register(process.stdout, selectors.EVENT_READ, "stdout")
            selector.register(process.stderr, selectors.EVENT_READ, "stderr")
            try:
                while selector.get_map():
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        metadata["status"] = "QUERY_TIMEOUT"
                        break
                    ready = selector.select(remaining)
                    if not ready:
                        metadata["status"] = "QUERY_TIMEOUT"
                        break
                    for selected, _ in ready:
                        chunk = os.read(selected.fileobj.fileno(), 65536)
                        if not chunk:
                            selector.unregister(selected.fileobj)
                            continue
                        if selected.data == "stdout":
                            output_bytes += len(chunk)
                            observed_hash.update(chunk)
                            if output_bytes > MAX_INPUT_BYTES:
                                metadata["status"] = "OUTPUT_LIMIT_EXCEEDED"
                                break
                            output.extend(chunk)
                        else:
                            stderr_bytes += len(chunk)
                            stderr_hash.update(chunk)
                            if stderr_bytes > MAX_LINE_BYTES:
                                metadata["status"] = "DIAGNOSTIC_LIMIT_EXCEEDED"
                                break
                            errors.extend(chunk)
                    if metadata["status"] != "STARTED":
                        break
                if metadata["status"] == "STARTED":
                    process.wait(timeout=max(0.01, deadline - time.monotonic()))
                    metadata["status"] = "OK" if process.returncode == 0 else "PUBLIC_QUERY_FAILED"
            except subprocess.TimeoutExpired:
                metadata["status"] = "QUERY_TIMEOUT"
            finally:
                if process.poll() is None:
                    process.terminate()
                    try:
                        process.wait(timeout=2)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait()
    diagnostic = errors.decode("utf-8", errors="replace")
    metadata.update(completed_utc=now(), exit_code=process.returncode,
                    stdout_bytes_observed=output_bytes, stdout_sha256_observed=observed_hash.hexdigest(),
                    stderr_bytes_omitted=stderr_bytes, stderr_sha256_observed=stderr_hash.hexdigest(),
                    output_complete=metadata["status"] == "OK",
                    diagnostic_flags={"permission_or_sandbox": bool(re.search(r"permission|not permitted|privilege|sandbox|access denied", diagnostic, re.I)),
                                      "retention_or_archive_notice": bool(re.search(r"expired|no log archive|not retained", diagnostic, re.I))},
                    diagnostic_text_retained=False)
    return metadata, bytes(output)


def m5p3_inputs():
    root = REPOSITORY / "artifacts/runtime/m5p3"
    report_path = REPOSITORY / "docs/research/m5-passive-runtime-topology.md"
    text = report_path.read_text()
    section = text.split("### Proposed Future Predicate\n", 1)[1]
    documented = re.search(r"```text\n(.*?)\n```", section, re.S)
    if documented is None or documented[1] != PREDICATE:
        raise ValueError("Historical predicate differs from the documented M5P3 scope")
    analysis_path = root / "analysis/manifest.json"
    if digest(analysis_path.read_bytes()) != "e467caf3cca3ee0f652065c048d82dd6a94c330f0b7d4ffd7aedb9b5bc79cfd1":
        raise ValueError("M5P3 analysis provenance changed")
    analysis = json.loads(analysis_path.read_bytes())
    if len(analysis["inputs"]) != 14:
        raise ValueError("M5P3 input inventory differs")
    for name, expected in analysis["inputs"].items():
        path = root / name
        if path.is_symlink() or not path.resolve().is_relative_to(root.resolve()) or digest(path.read_bytes()) != expected:
            raise ValueError("M5P3 immutable input differs")
    if digest((root / "analysis/differential.json").read_bytes()) != analysis["differential_sha256"]:
        raise ValueError("M5P3 differential changed")
    manifests = {state: json.loads((root / state / "manifest.json").read_bytes()) for state in ("disconnected", "connected")}
    if timestamp_ns(WINDOW_START) > timestamp_ns(manifests["disconnected"]["started_utc"]):
        raise ValueError("Window excludes the disconnected boundary")
    if timestamp_ns(WINDOW_END) < timestamp_ns(manifests["connected"]["completed_utc"]):
        raise ValueError("Window excludes the connected boundary")
    return {"m5p3_commit": M5P3_HEAD, "document_sha256": digest(report_path.read_bytes()),
            "capture_input_hashes": analysis["inputs"], "differential_sha256": analysis["differential_sha256"],
            "analysis_manifest_sha256": digest(analysis_path.read_bytes()),
            "capture_windows": {state: {key: value[key] for key in ("started_utc", "completed_utc", "capture_generation", "environment")}
                                for state, value in manifests.items()},
            "physical_transition_timestamp": None, "physical_transition_kind": "USER_TRANSITION_TIMESTAMP_NOT_RECORDED",
            "window_rationale": "Previously documented 950-second bracket; exact plug time unknown between validated disconnected and connected snapshots, so a short pre-connected-only margin could miss it"}


def tool_provenance():
    def git(*arguments):
        return subprocess.check_output(["/usr/bin/git", *arguments], cwd=REPOSITORY, stdin=subprocess.DEVNULL,
                                       stderr=subprocess.DEVNULL, timeout=10)
    commit = git("rev-parse", "HEAD").decode("ascii").strip()
    branch = git("symbolic-ref", "--short", "HEAD").decode("ascii").strip()
    source = REPOSITORY / "tools/display_log_analyze.py"
    if branch != "research/m5-public-log-correlation" or not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError("Historical acquisition requires the M5P4 research branch")
    if source.read_bytes() != git("show", "HEAD:tools/display_log_analyze.py") or git("status", "--porcelain=v1").strip():
        raise ValueError("Commit the tested log tool and use a clean worktree before acquisition")
    return {"macmst_commit": commit, "branch": branch, "tool_sha256": digest(source.read_bytes()), "worktree_clean": True}


def historical_capture():
    destination = REPOSITORY / "artifacts/runtime/m5p4/historical"
    if destination.exists() or any(path.is_symlink() for path in (destination, *destination.parents)):
        raise ValueError("Historical output must be a new nonsymlink directory")
    baseline = m5p3_inputs()
    provenance = tool_provenance()
    command, raw = execute_historical(historical_command())
    records = []
    parse_status = "NOT_PARSED"
    try:
        if command["status"] == "OK":
            records = parse_ndjson(raw)
            parse_status = "VALID"
        result = analyze_records(records)
    except (ValueError, TypeError, KeyError, UnicodeError, RecursionError) as error:
        parse_status = type(error).__name__
        result = analyze_records([])
    snapshot = json.loads((REPOSITORY / "artifacts/runtime/m5p3/connected/snapshot.json").read_bytes())
    correlations = correlate(result["normalized_records"], snapshot)
    complete = command["status"] == "OK" and parse_status == "VALID"
    retained_matches = sum(in_scope(record) for record in records) if parse_status == "VALID" else 0
    availability = "M5P3_HISTORICAL_LOGS_RETAINED" if retained_matches else "M5P3_HISTORICAL_LOGS_NOT_RETAINED" if complete else "HISTORICAL_ACCESS_OR_PARSE_UNRESOLVED"
    manifest = {"schema_version": 1, "milestone": "M5P4", "phase": "HISTORICAL_ONLY", "capture_generation": "m5p4-historical-01",
                "tool_provenance": provenance, "baseline": baseline, "command": command,
                "predicate": PREDICATE, "selected_processes": ["kernel"], "selected_subsystems": [], "selected_categories": [],
                "message_terms": list(TERMS), "window_start": WINDOW_START, "window_end": WINDOW_END,
                "parse_status": parse_status, "query_complete": complete, "scoped_records_returned": retained_matches,
                "historical_availability": availability, "retention_expiration_established": False,
                "availability_limit": "Retained means matching historical records returned; no-return does not distinguish non-emission, suppression, redaction, expiry or query failure",
                "privacy": "Retained raw-filtered JSON is an allowlisted projection, with original message text except documented identifier redactions; unrelated home/network records dropped; original stdout hashed and discarded",
                "limits": {"records": MAX_RECORDS, "stdout_bytes": MAX_INPUT_BYTES, "line_bytes": MAX_LINE_BYTES, "query_seconds": 60},
                "physical_state": "OWNER_REPORTED_CONNECTED_AND_MIRRORED; no new capture or transition",
                "live_cycle_performed": False, "user_transition_timestamp": None,
                "evidence_gate": "PENDING_SCOPED_HISTORICAL_REVIEW" if retained_matches and complete else "CONTROLLED_LIVE_LOG_CYCLE_REQUIRED"}
    files = {"raw-filtered.ndjson": b"".join(json_bytes(record) for record in result["filtered_records"]),
             "normalized.json": json_bytes(result["normalized_records"]), "analysis.json": json_bytes(result["summary"]),
             "correlations.json": json_bytes(correlations)}
    manifest["artifacts"] = {name: digest(value) for name, value in files.items()}
    files["manifest.json"] = json_bytes(manifest)
    files["hashes.json"] = json_bytes({name: digest(value) for name, value in files.items()})
    destination.mkdir(parents=True, exist_ok=False)
    for name, value in files.items():
        with (destination / name).open("xb") as stream:
            stream.write(value)
    printed_summary = {key: value for key, value in result["summary"].items() if key != "timestamp_order"}
    print(json.dumps({"capture": str(destination.relative_to(REPOSITORY)), "command_status": command["status"],
                      "parse_status": parse_status, "query_complete": complete, "scoped_records_returned": retained_matches,
                      "availability": availability, "summary": printed_summary}, sort_keys=True))
    return 0 if complete else 2


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="operation", required=True)
    subparsers.add_parser("plan")
    subparsers.add_parser("historical")
    subparsers.add_parser("review", help="extract fields from the immutable historical capture; no public query")
    analyzer = subparsers.add_parser("analyze")
    analyzer.add_argument("input", type=pathlib.Path)
    arguments = parser.parse_args(argv)
    try:
        if arguments.operation == "plan":
            print(json.dumps({"argv": historical_command(), "window_start": WINDOW_START, "window_end": WINDOW_END}, indent=2))
        elif arguments.operation == "historical":
            return historical_capture()
        elif arguments.operation == "review":
            review_historical()
        else:
            path = arguments.input
            if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_INPUT_BYTES:
                raise ValueError("Offline log input must be a bounded regular nonsymlink file")
            print(json.dumps(analyze_records(parse_ndjson(path.read_bytes())), indent=2, sort_keys=True))
    except (OSError, ValueError, TypeError, KeyError, subprocess.SubprocessError) as error:
        print(json.dumps({"status": "FAILED", "error_type": type(error).__name__,
                          "limit": "No privilege escalation, live stream or private fallback"}), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())