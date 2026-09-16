"""Evaluate explicit offline evidence assertions; never infer source identities."""

import collections
import hashlib
import itertools

if __package__:
    from . import dcp_trace_import as trace
    from . import dcp_trace_schema as schema
else:
    import dcp_trace_import as trace
    import dcp_trace_schema as schema


GATES = {
    "A": ("source_context", ("source_identity",)),
    "B": ("timing_generator", ("timing_identity",)),
    "C": ("source_payload_binding", ("source_identity", "payload_identity")),
    "D": ("source_api_space", ()),
    "E": ("wire_vc", ("vc_identity", "timing_identity")),
}
IDENTITIES = ("physical_dptx", "source_identity", "timing_identity", "payload_identity", "vc_identity")
MAX_EVIDENCE_CLAIMS = 2048
MAX_PAIR_COMPARISONS = 100000


def records_digest(records):
    digest = hashlib.sha256()
    for record in records:
        digest.update((schema.dumps(record) + "\n").encode("utf-8"))
    return digest.hexdigest()


def _record_key(record):
    return record["capture_id"], record["capture_generation"], record["sequence"]


def _references(annotation, record, lookup):
    references = annotation.get("provenance", {}).get("references", [])
    keys = []
    problems = []
    for reference in references:
        key = reference["capture_id"], reference["capture_generation"], reference["sequence"]
        target = lookup.get(key)
        if target is None:
            problems.append("raw reference does not exist")
            continue
        if (target["capture_id"] != record["capture_id"] or
                target["capture_generation"] != record["capture_generation"] or
                target["boot_generation"] != record["boot_generation"]):
            problems.append("raw reference crosses a capture/boot generation")
        expected = hashlib.sha256(bytes.fromhex(target["raw_payload"])).hexdigest()
        if expected != reference["payload_sha256"]:
            problems.append("raw reference hash mismatch")
        if not target["record_complete"] or target["loss_state"]["status"] != "none":
            problems.append("raw reference is incomplete")
        keys.append(key)
    if _record_key(record) not in keys:
        problems.append("assertion is not bound to its own raw record")
    return keys, problems


def normalize_evidence(records, summary=None):
    summary = trace.summarize(records, include_correlations=True) if summary is None else summary
    lookup = {_record_key(record): record for record in records}
    tainted = set()
    previous = {}
    for record in records:
        generation = record["capture_generation"]
        if (record["sequence"] != previous.get(generation, -1) + 1 or
                not record["record_complete"] or record["loss_state"]["status"] != "none"):
            tainted.add(generation)
        previous[generation] = record["sequence"]
    correlations = {(item["capture_generation"], item["sequence"]): item["status"]
                    for item in summary["correlations"]}
    counts = collections.Counter(record.get("annotations", {}).get("claim_id") for record in records
                                 if "annotations" in record)
    normalized = []
    for record in records:
        if "annotations" not in record:
            continue
        annotation = record["annotations"]
        provenance = annotation.get("provenance", {})
        problems = []
        if annotation.get("confidence", "UNKNOWN") not in ("VERIFIED", "STRONG"):
            problems.append("confidence is below STRONG")
        if not annotation.get("claim_id") or counts[annotation.get("claim_id")] != 1:
            problems.append("missing or duplicate claim identity")
        if record["capture_generation"] in tainted:
            problems.append("generation contains loss, a gap or incomplete data")
        if record["kind"] == "loss":
            problems.append("loss marker is not positive ownership evidence")
        if record["kind"] in ("request", "reply") and correlations.get((record["capture_generation"], record["sequence"])) != "CORRELATION_EXPLICIT":
            problems.append("exchange lacks complete explicit correlation")
        for field in ("capture_id", "capture_generation", "boot_generation", "lifetime_generation"):
            if annotation.get(field) != record[field]:
                problems.append("missing explicit " + field + " binding")
        origin = "synthetic" if record["producer"]["synthetic"] else "observed"
        if provenance.get("origin") != origin:
            problems.append("provenance origin does not match producer")
        if provenance.get("mapping_basis") not in ("explicit_contract", "independent_measurement"):
            problems.append("mapping basis is absent or heuristic")
        if provenance.get("independently_validated") is not True or not provenance.get("method"):
            problems.append("independent mapping validation not supplied")
        if annotation.get("independent") is not True:
            problems.append("independence is not explicit")
        if not annotation.get("evidence") or annotation.get("evidence") == "UNKNOWN":
            problems.append("evidence rationale missing")
        if annotation.get("physical_dptx", "UNKNOWN") == "UNKNOWN":
            problems.append("physical DPTX owner unknown")
        start, end = annotation.get("start_ns"), annotation.get("end_ns")
        if type(start) is not int or type(end) is not int or not start <= record["timestamp_ns"] < end:
            problems.append("observation is outside a justified lifetime interval")
        references, reference_problems = _references(annotation, record, lookup)
        problems.extend(reference_problems)
        normalized.append({
            **{name: annotation.get(name, "UNKNOWN") for name in IDENTITIES},
            "claim_id": annotation.get("claim_id", "UNKNOWN"), "assertion": annotation.get("assertion", "UNKNOWN"),
            "capture_id": record["capture_id"], "capture_generation": record["capture_generation"],
            "boot_generation": record["boot_generation"], "lifetime_generation": record["lifetime_generation"],
            "sequence": record["sequence"], "confidence": annotation.get("confidence", "UNKNOWN"),
            "simultaneous": annotation.get("simultaneous", False), "independent": annotation.get("independent", False),
            "coexistence_id": annotation.get("coexistence_id", "UNKNOWN"), "start_ns": start, "end_ns": end,
            "source_space": annotation.get("source_space", []), "provenance": provenance,
            "evidence": annotation.get("evidence", "UNKNOWN"), "raw_references": references,
            "synthetic": record["producer"]["synthetic"], "uncertainty": sorted(set(problems)),
        })
    return normalized


def _pair_qualifies(first, second, fields, gate):
    same_owner = ("capture_id", "capture_generation", "boot_generation", "physical_dptx", "coexistence_id")
    if any(first[name] != second[name] for name in same_owner):
        return False
    if first["coexistence_id"] == "UNKNOWN" or not first["simultaneous"] or not second["simultaneous"]:
        return False
    if first["claim_id"] == second["claim_id"] or set(first["raw_references"]) & set(second["raw_references"]):
        return False
    if max(first["start_ns"], second["start_ns"]) >= min(first["end_ns"], second["end_ns"]):
        return False
    if any(first[name] == "UNKNOWN" or second[name] == "UNKNOWN" or first[name] == second[name] for name in fields):
        return False
    if gate == "E":
        return all(item["provenance"].get("mapping_basis") == "independent_measurement" and
                   item["provenance"].get("observation_plane") == "dp_main_link" for item in (first, second))
    return True


def validate_review(review, records):
    schema.object_fields(review, ("review_version", "capture_id", "records_sha256", "reviewer", "basis", "approved_claim_ids"), "review")
    schema.require(type(review["review_version"]) is int and review["review_version"] == 1,
                   "INVALID_REVIEW", "unsupported review version")
    schema.text(review["reviewer"], "reviewer")
    schema.text(review["basis"], "review basis", 4096)
    schema.digest(review["records_sha256"], "review records_sha256")
    schema.require(review["records_sha256"] == records_digest(records) and
                   review["capture_id"] == records[0]["capture_id"], "INVALID_REVIEW", "review does not bind this exact capture")
    identifiers = review["approved_claim_ids"]
    schema.require(isinstance(identifiers, list) and 0 < len(identifiers) <= schema.MAX_RECORDS,
                   "INVALID_REVIEW", "review must explicitly name approved claims")
    for value in identifiers:
        schema.text(value, "approved claim ID")
    available = {record.get("annotations", {}).get("claim_id") for record in records}
    schema.require(len(set(identifiers)) == len(identifiers) and set(identifiers) <= available,
                   "INVALID_REVIEW", "review contains unknown or duplicated claims")
    schema.require(not any(record["producer"]["synthetic"] for record in records),
                   "INVALID_REVIEW", "synthetic data cannot receive a real provenance review")
    schema.require(all(record["producer"]["commit"] != "UNKNOWN" for record in records),
                   "INVALID_REVIEW", "real review needs exact producer revisions")
    return set(identifiers)


def evaluate(records, review=None):
    records = list(records)
    summary = trace.summarize(records, include_correlations=True)
    schema.require(sum("annotations" in record for record in records) <= MAX_EVIDENCE_CLAIMS,
                   "EVIDENCE_RESOURCE_LIMIT", "too many evidence claims for bounded evaluation")
    normalized = normalize_evidence(records, summary)
    approved = validate_review(review, records) if review is not None else set()
    gates = {}
    for gate, (assertion, fields) in GATES.items():
        eligible = [item for item in normalized if item["assertion"] == assertion and not item["uncertainty"]]
        candidates = []
        if gate == "D":
            candidates = [[item] for item in eligible if len(item["source_space"]) > 1 and "UNKNOWN" not in item["source_space"] and
                          item["provenance"].get("mapping_basis") == "explicit_contract"]
        else:
            for index, (first, second) in enumerate(itertools.combinations(eligible, 2)):
                schema.require(index < MAX_PAIR_COMPARISONS, "EVIDENCE_RESOURCE_LIMIT", "pair comparison budget exceeded; no gate decision emitted")
                if _pair_qualifies(first, second, fields, gate):
                    candidates.append([first, second])
                    break
        if not candidates:
            gates[gate] = {"status": "NOT_ESTABLISHED", "claim_ids": [],
                           "reason": "required independent same-owner facts are not established"}
            continue
        candidate = candidates[0]
        identifiers = [item["claim_id"] for item in candidate]
        if summary["synthetic"]:
            status = "SYNTHETIC_GATE_TEST_PASS"
        elif all(identifier in approved for identifier in identifiers):
            status = "REAL_EVIDENCE_GATE_PASS"
        else:
            status = "REAL_PROVENANCE_REVIEW_REQUIRED"
        gates[gate] = {"status": status, "claim_ids": identifiers,
                       "reason": "explicit annotated evidence, not inferred from transport identifiers"}
    real_passes = sum(item["status"] == "REAL_EVIDENCE_GATE_PASS" for item in gates.values())
    return {"summary": summary, "evidence": normalized, "gates": gates,
            "synthetic_gate_passes": sum(item["status"] == "SYNTHETIC_GATE_TEST_PASS" for item in gates.values()),
            "real_evidence_passes": real_passes,
            "project_gate_state": "REAL_EVIDENCE_GATE_PASS" if real_passes else "NOT_ESTABLISHED",
            "review_limit": "hash binding checks integrity, not truth or reviewer authenticity; human provenance review remains external",
            "hardware_authorized": False}