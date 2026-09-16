"""Frozen offline observer schema v1 and non-repairing validation results."""

import dataclasses
import json
import math
import re


SCHEMA_VERSION = 1
MAX_PAYLOAD_BYTES = 1024 * 1024
MAX_RECORD_BYTES = 2 * MAX_PAYLOAD_BYTES + 65536
MAX_INPUT_BYTES = 256 * 1024 * 1024
MAX_RECORDS = 100000
MAX_INTEGER = (1 << 64) - 1
CONFIDENCE = ("VERIFIED", "STRONG", "INFERRED", "HYPOTHESIS", "UNKNOWN")
ANNOTATION_FIELDS = ("physical_dptx", "source_identity", "timing_identity",
                     "payload_identity", "confidence", "evidence")
REQUIRED_FIELDS = {
    "schema_version", "capture_id", "capture_generation", "boot_generation",
    "lifetime_generation", "sequence", "timestamp_ns", "timestamp_units", "clock",
    "kind", "direction", "asc", "endpoint", "channel", "service", "opcode",
    "request_id", "payload_length", "declared_payload_length", "raw_payload",
    "record_complete", "truncated", "loss_state", "producer",
}
OPTIONAL_FIELDS = {"record_index", "correlation", "annotations", "decoded_fields", "extensions"}


@dataclasses.dataclass(frozen=True)
class Issue:
    code: str
    message: str
    field: str = ""
    severity: str = "error"

    def as_dict(self):
        return dataclasses.asdict(self)


@dataclasses.dataclass
class ValidationResult:
    record: object
    issues: list = dataclasses.field(default_factory=list)

    @property
    def status(self):
        if any(issue.severity == "error" for issue in self.issues):
            return "INVALID"
        return "VALID_WITH_WARNINGS" if self.issues else "VALID"

    def require_valid(self):
        if self.status == "INVALID":
            raise TraceFormatError(self.issues)
        return self.record


class TraceFormatError(ValueError):
    def __init__(self, issues, code="INVALID_RECORD"):
        self.issues = issues if isinstance(issues, list) else [Issue(code, str(issues))]
        self.code = self.issues[0].code
        super().__init__("; ".join(f"{issue.code}: {issue.message}" for issue in self.issues))


def require(condition, code, message, field=""):
    if not condition:
        raise TraceFormatError([Issue(code, message, field)])


def integer(value, name, maximum=MAX_INTEGER, code="INVALID_INTEGER"):
    require(type(value) is int and 0 <= value <= maximum, code,
            "expected a bounded nonnegative integer", name)


def text(value, name, maximum=256):
    require(isinstance(value, str) and 0 < len(value) <= maximum,
            "INVALID_TEXT", "expected a bounded nonempty string", name)


def identifier(value, name):
    if isinstance(value, str):
        text(value, name)
    elif value is not None:
        integer(value, name)


def choice(value, values, name, code="INVALID_ENUM"):
    require(isinstance(value, str) and value in values, code, "invalid enumerated value", name)


def object_fields(value, required, name):
    require(isinstance(value, dict), "INVALID_OBJECT", "expected a JSON object", name)
    require(set(required) <= value.keys(), "MISSING_FIELD", "required field missing", name)


def digest(value, name):
    require(isinstance(value, str) and re.fullmatch(r"[a-f0-9]{64}", value) is not None,
            "INVALID_HASH", "expected lowercase SHA-256", name)


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "DUPLICATE_JSON_KEY", "duplicate JSON object key")
        result[key] = value
    return result


def _finite_float(value):
    number = float(value)
    require(math.isfinite(number), "MALFORMED_JSON", "non-finite JSON number")
    return number


def _reject_constant(value):
    raise TraceFormatError("non-finite JSON number", "MALFORMED_JSON")


def loads(raw):
    try:
        return json.loads(raw, object_pairs_hook=_unique_object,
                          parse_float=_finite_float, parse_constant=_reject_constant)
    except TraceFormatError:
        raise
    except (ValueError, UnicodeError, RecursionError, TypeError) as error:
        raise TraceFormatError("malformed JSON or UTF-8", "MALFORMED_JSON") from error


def dumps(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=True, allow_nan=False, separators=(",", ":"))

def _json_value(value):
    pending = [(value, 0)]
    visited = 0
    while pending:
        item, depth = pending.pop()
        visited += 1
        require(depth <= 64 and visited <= 100000, "RESOURCE_LIMIT", "JSON structure exceeds depth/node bound")
        if isinstance(item, dict):
            require(all(isinstance(key, str) for key in item), "MALFORMED_JSON", "JSON object keys must be strings")
            pending.extend((child, depth + 1) for child in item.values())
        elif isinstance(item, list):
            pending.extend((child, depth + 1) for child in item)
        elif type(item) is float:
            require(math.isfinite(item), "MALFORMED_JSON", "non-finite extension value")
        else:
            require(item is None or type(item) in (str, int, bool), "MALFORMED_JSON", "non-JSON extension value")


def _annotations(record):
    annotation = record["annotations"]
    try:
        object_fields(annotation, (), "annotations")
        for name in ANNOTATION_FIELDS[:-1]:
            if name in annotation:
                text(annotation[name], name)
        choice(annotation.get("confidence", "UNKNOWN"), CONFIDENCE, "confidence")
        evidence = annotation.get("evidence", "UNKNOWN")
        if evidence != "UNKNOWN":
            require(isinstance(evidence, list) and 0 < len(evidence) <= 64,
                    "MALFORMED_ANNOTATION", "evidence must be UNKNOWN or a bounded nonempty list")
            for entry in evidence:
                text(entry, "evidence", 1024)
        if any(annotation.get(name, "UNKNOWN") != "UNKNOWN" for name in ANNOTATION_FIELDS[:4]):
            require(evidence != "UNKNOWN" and annotation.get("confidence", "UNKNOWN") != "UNKNOWN",
                    "MALFORMED_ANNOTATION", "claimed identities require confidence and evidence")
        for name in ("claim_id", "assertion", "coexistence_id", "vc_identity"):
            if name in annotation:
                text(annotation[name], name)
        for name in ("capture_id", "capture_generation", "boot_generation", "lifetime_generation"):
            if name in annotation:
                require(annotation[name] == record[name], "CAPTURE_GENERATION_MISMATCH",
                        "annotation must bind to its record generation", name)
        for name in ("simultaneous", "independent"):
            if name in annotation:
                require(type(annotation[name]) is bool, "MALFORMED_ANNOTATION", "expected boolean", name)
        for name in ("start_ns", "end_ns"):
            if name in annotation:
                integer(annotation[name], name)
        if "start_ns" in annotation and "end_ns" in annotation:
            require(annotation["start_ns"] < annotation["end_ns"], "MALFORMED_ANNOTATION",
                    "evidence interval must have positive duration")
        if "source_space" in annotation:
            values = annotation["source_space"]
            require(isinstance(values, list) and len(values) <= 64,
                    "MALFORMED_ANNOTATION", "source_space must be a bounded list")
            for value in values:
                text(value, "source_space identity")
            require(len(values) == len(set(values)), "MALFORMED_ANNOTATION", "duplicate source-space identity")
        if "provenance" in annotation:
            provenance = annotation["provenance"]
            object_fields(provenance, ("origin", "mapping_basis", "method", "independently_validated", "references"), "provenance")
            choice(provenance["origin"], ("synthetic", "observed", "UNKNOWN"), "provenance origin")
            choice(provenance["mapping_basis"], ("explicit_contract", "independent_measurement", "heuristic", "UNKNOWN"), "mapping_basis")
            text(provenance["method"], "provenance method", 1024)
            if "observation_plane" in provenance:
                choice(provenance["observation_plane"], ("host_dcp_transport", "dp_main_link", "dp_aux", "UNKNOWN"), "observation_plane")
            require(type(provenance["independently_validated"]) is bool,
                    "MALFORMED_ANNOTATION", "provenance validation flag must be boolean")
            references = provenance["references"]
            require(isinstance(references, list) and 0 < len(references) <= 64,
                    "MALFORMED_ANNOTATION", "provenance needs bounded raw references")
            for reference in references:
                object_fields(reference, ("capture_id", "capture_generation", "sequence", "payload_sha256"), "reference")
                text(reference["capture_id"], "reference capture_id")
                text(reference["capture_generation"], "reference capture_generation")
                integer(reference["sequence"], "reference sequence")
                digest(reference["payload_sha256"], "reference payload_sha256")
    except TraceFormatError as error:
        if error.code == "CAPTURE_GENERATION_MISMATCH":
            raise
        raise TraceFormatError("malformed ownership annotation", "MALFORMED_ANNOTATION") from error


def _validate(record):
    object_fields(record, REQUIRED_FIELDS, "record")
    require(type(record["schema_version"]) is int and record["schema_version"] == SCHEMA_VERSION,
            "UNSUPPORTED_SCHEMA", "only frozen observer schema v1 is supported", "schema_version")
    for name in ("capture_id", "capture_generation", "boot_generation", "lifetime_generation", "asc"):
        text(record[name], name)
    integer(record["sequence"], "sequence")
    integer(record["timestamp_ns"], "timestamp_ns")
    choice(record["timestamp_units"], ("ns",), "timestamp_units")
    choice(record["clock"], ("monotonic",), "clock")
    if "record_index" in record:
        integer(record["record_index"], "record_index")
        require(record["record_index"] == record["sequence"], "SEQUENCE_MISMATCH", "record_index alias disagrees with sequence")
    choice(record["kind"], ("request", "reply", "event", "loss"), "kind")
    choice(record["direction"], ("host_to_dcp", "dcp_to_host", "none"), "direction", "INVALID_DIRECTION")
    require((record["direction"] == "none") == (record["kind"] == "loss"),
            "INVALID_DIRECTION", "direction none is reserved for loss records")
    for name, maximum in (("endpoint", 255), ("channel", (1 << 32) - 1)):
        if record[name] is not None:
            integer(record[name], name, maximum, "INVALID_ENDPOINT" if name == "endpoint" else "INVALID_CHANNEL")
    if record["service"] is not None:
        text(record["service"], "service")
    for name in ("opcode", "request_id"):
        identifier(record[name], name)
    integer(record["payload_length"], "payload_length", MAX_PAYLOAD_BYTES, "IMPOSSIBLE_LENGTH")
    integer(record["declared_payload_length"], "declared_payload_length", code="IMPOSSIBLE_LENGTH")
    payload = record["raw_payload"]
    require(isinstance(payload, str) and len(payload) == 2 * record["payload_length"],
            "PAYLOAD_LENGTH_MISMATCH", "retained byte length disagrees with hex payload")
    require(re.fullmatch(r"[0-9a-fA-F]*", payload) is not None,
            "INVALID_PAYLOAD", "raw_payload must be hexadecimal without separators")
    require(record["declared_payload_length"] >= record["payload_length"],
            "IMPOSSIBLE_LENGTH", "declared length is smaller than retained length")
    require(type(record["record_complete"]) is bool and type(record["truncated"]) is bool,
            "INVALID_COMPLETENESS", "completeness and truncation flags must be boolean")
    require(record["truncated"] == (record["declared_payload_length"] > record["payload_length"]),
            "PAYLOAD_LENGTH_MISMATCH", "truncation flag disagrees with declared/retained lengths")
    loss = record["loss_state"]
    object_fields(loss, ("status", "dropped_records", "detail"), "loss_state")
    choice(loss["status"], ("none", "dropped", "wrapped", "truncated", "unknown"), "loss status")
    if loss["dropped_records"] is not None:
        integer(loss["dropped_records"], "dropped_records")
    if loss["detail"] is not None:
        text(loss["detail"], "loss detail", 1024)
    require(loss["status"] != "none" or loss["dropped_records"] == 0,
            "INVALID_LOSS", "loss-free state needs a zero drop count")
    require(loss["status"] != "dropped" or bool(loss["dropped_records"]),
            "INVALID_LOSS", "dropped status needs a positive count")
    require(record["kind"] != "loss" or loss["status"] != "none",
            "INVALID_LOSS", "loss record cannot report no loss")
    require(not record["truncated"] or (not record["record_complete"] and loss["status"] in ("truncated", "unknown")),
            "INVALID_COMPLETENESS", "partial payload must be explicitly incomplete")
    require(loss["status"] != "truncated" or record["truncated"], "INVALID_LOSS", "truncated status needs a partial payload")
    require(record["record_complete"] or loss["status"] != "none",
            "INVALID_COMPLETENESS", "incomplete record cannot claim loss-free state")
    producer = record["producer"]
    object_fields(producer, ("name", "version", "commit", "synthetic"), "producer")
    for name in ("name", "version"):
        text(producer[name], "producer " + name)
    require(isinstance(producer["commit"], str) and (producer["commit"] == "UNKNOWN" or
            re.fullmatch(r"[a-f0-9]{40}", producer["commit"]) is not None), "INVALID_PRODUCER", "invalid producer commit")
    require(type(producer["synthetic"]) is bool, "INVALID_PRODUCER", "producer must declare synthetic status")
    if "correlation" in record:
        correlation = record["correlation"]
        object_fields(correlation, ("scope", "evidence"), "correlation")
        text(correlation["scope"], "correlation scope")
        text(correlation["evidence"], "correlation evidence", 1024)
        require(record["kind"] in ("request", "reply") and record["request_id"] is not None and
                record["endpoint"] is not None and record["channel"] is not None,
                "INVALID_CORRELATION", "explicit correlation needs exchange kind, endpoint, channel and ID")
    for name in ("extensions", "decoded_fields"):
        if name in record:
            object_fields(record[name], (), name)
    require("synthetic" not in record.get("extensions", {}) or producer["synthetic"],
            "SYNTHETIC_ORIGIN_MISMATCH", "synthetic-tagged extensions cannot be relabeled as observed")
    if "annotations" in record:
        _annotations(record)


def inspect_record(record):
    result = ValidationResult(record)
    try:
        _json_value(record)
        _validate(record)
        require(len(dumps(record).encode("utf-8")) <= MAX_RECORD_BYTES,
                "RESOURCE_LIMIT", "serialized record exceeds byte bound")
    except TraceFormatError as error:
        result.issues.extend(error.issues)
        return result
    except (ValueError, RecursionError) as error:
        result.issues.append(Issue("MALFORMED_JSON", "record cannot be represented as bounded JSON"))
        return result
    for name in sorted(record.keys() - REQUIRED_FIELDS - OPTIONAL_FIELDS):
        result.issues.append(Issue("UNKNOWN_EXTENSION_FIELD", "unknown field preserved", name[:256], "warning"))
    nested = {"producer": {"name", "version", "commit", "synthetic"},
              "loss_state": {"status", "dropped_records", "detail"},
              "correlation": {"scope", "evidence"},
              "annotations": set(ANNOTATION_FIELDS) | {"claim_id", "assertion", "coexistence_id", "vc_identity",
                  "capture_id", "capture_generation", "boot_generation", "lifetime_generation", "start_ns", "end_ns",
                  "simultaneous", "independent", "source_space", "provenance"}}
    for parent, known in nested.items():
        for name in sorted(record.get(parent, {}).keys() - known):
            result.issues.append(Issue("UNKNOWN_EXTENSION_FIELD", "unknown nested field preserved", (parent + "." + name)[:256], "warning"))
    if not record["record_complete"] or record["truncated"]:
        result.issues.append(Issue("TRUNCATED_RECORD", "record is explicitly incomplete", "record_complete", "warning"))
    if record["loss_state"]["status"] != "none":
        result.issues.append(Issue("CAPTURE_LOSS", "loss, wrap or unknown coverage reported", "loss_state", "warning"))
    annotation = record.get("annotations", {})
    if annotation.get("confidence", "UNKNOWN") in ("INFERRED", "HYPOTHESIS"):
        result.issues.append(Issue("UNQUALIFIED_ANNOTATION", "annotation is not strong or verified", "annotations", "warning"))
    return result


def validate_record(record):
    return inspect_record(record).require_valid()


def parse_record(raw):
    try:
        return inspect_record(loads(raw))
    except TraceFormatError as error:
        return ValidationResult(None, error.issues)


class StreamValidator:
    def __init__(self):
        self.capture = None
        self.producer = None
        self.current = None
        self.positions = {}

    def feed(self, record):
        result = inspect_record(record)
        if result.status == "INVALID":
            return result
        try:
            if self.capture is not None:
                require(record["capture_id"] == self.capture and record["producer"] == self.producer,
                        "CAPTURE_GENERATION_MISMATCH", "capture identity/producer changed within one file")
            generation = record["capture_generation"]
            if generation in self.positions:
                require(generation == self.current, "CAPTURE_GENERATION_MISMATCH", "closed generation reappeared")
                previous_sequence, previous_time, boot = self.positions[generation]
                require(boot == record["boot_generation"], "CAPTURE_GENERATION_MISMATCH", "boot changed without a new capture generation")
                require(record["sequence"] != previous_sequence, "DUPLICATE_SEQUENCE", "duplicate sequence")
                require(record["sequence"] > previous_sequence, "SEQUENCE_REGRESSION", "sequence regressed")
                require(record["timestamp_ns"] >= previous_time, "TIMESTAMP_REGRESSION", "monotonic timestamp regressed")
            else:
                previous_sequence = -1
            gap = record["sequence"] - previous_sequence - 1
            if gap:
                result.issues.append(Issue("SEQUENCE_GAP", str(gap) + " missing sequence positions", "sequence", "warning"))
            self.capture, self.producer = record["capture_id"], record["producer"]
            self.current = generation
            self.positions[generation] = (record["sequence"], record["timestamp_ns"], record["boot_generation"])
        except TraceFormatError as error:
            result.issues.extend(error.issues)
        return result