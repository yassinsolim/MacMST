"""Validate self-contained offline capture bundles and human handoff facts."""

import datetime
import hashlib
import io
import os
import pathlib
import re
import stat

if __package__:
    from . import dcp_trace_import as trace
    from . import dcp_trace_schema as schema
else:
    import dcp_trace_import as trace
    import dcp_trace_schema as schema


MAX_METADATA_BYTES = 1024 * 1024
MAX_BUNDLE_BYTES = schema.MAX_INPUT_BYTES + 16 * MAX_METADATA_BYTES


def _require(condition, message):
    schema.require(condition, "INVALID_BUNDLE", message)


def safe_path(root, relative):
    schema.text(relative, "bundle path")
    path = pathlib.PurePosixPath(relative)
    _require(not path.is_absolute() and "\\" not in relative and
             all(part not in ("", ".", "..") for part in relative.split("/")), "unsafe bundle path")
    current = pathlib.Path(root)
    _require(current.is_dir() and not current.is_symlink(), "bundle root must be a nonsymlink directory")
    for part in path.parts:
        current = current / part
        _require(not current.is_symlink(), "bundle paths cannot contain symlinks")
    _require(current.resolve().is_relative_to(pathlib.Path(root).resolve()), "bundle path escapes root")
    return current


def read_bytes(path, limit=MAX_METADATA_BYTES):
    path = pathlib.Path(path)
    _require(path.is_file() and not path.is_symlink(), "expected a regular nonsymlink file")
    descriptor = os.open(path, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW)
    with os.fdopen(descriptor, "rb") as source:
        _require(stat.S_ISREG(os.fstat(source.fileno()).st_mode), "expected regular file")
        raw = source.read(limit + 1)
    _require(len(raw) <= limit, "file exceeds resource bound")
    return raw


def read_json(path):
    return schema.loads(read_bytes(path))


def _sha(value, name):
    _require(isinstance(value, str) and re.fullmatch(r"[a-f0-9]{40}", value) is not None, "invalid " + name)


def validate_topology(topology):
    schema.object_fields(topology, ("version", "nodes", "edges"), "topology")
    _require(type(topology["version"]) is int and topology["version"] == 1, "unknown topology version")
    nodes, edges = topology["nodes"], topology["edges"]
    _require(isinstance(nodes, list) and 1 <= len(nodes) <= 128 and isinstance(edges, list) and len(edges) <= 127,
             "topology must be a bounded graph")
    kinds = {}
    for node in nodes:
        schema.object_fields(node, ("id", "kind"), "topology node")
        schema.text(node["id"], "node ID")
        _require(node["id"] not in kinds, "duplicate topology node")
        schema.choice(node["kind"], ("mac", "physical_output", "hub", "dock", "sink"), "node kind")
        kinds[node["id"]] = node["kind"]
        for name in ("label", "connection_type", "sink_logical_identity", "mst_branch_identity"):
            if name in node and node[name] is not None:
                schema.text(node[name], name)
        for name, maximum in (("vendor_id", 65535), ("product_id", 65535), ("port_index", 65535)):
            if name in node and node[name] is not None:
                schema.integer(node[name], name, maximum)
    roots = [name for name, kind in kinds.items() if kind == "mac"]
    _require(len(roots) == 1, "topology needs exactly one Mac root")
    parents = {}
    children = {name: [] for name in kinds}
    allowed = {"mac": {"physical_output"}, "physical_output": {"hub", "dock", "sink"},
               "hub": {"hub", "dock", "sink"}, "dock": {"hub", "dock", "sink"}, "sink": set()}
    for edge in edges:
        schema.object_fields(edge, ("source", "target", "connection_type"), "topology edge")
        for field in ("source", "target", "connection_type"):
            schema.text(edge[field], field)
        source, target = edge["source"], edge["target"]
        _require(source in kinds and target in kinds and source != target, "unknown/self topology edge")
        _require(target not in parents and kinds[target] in allowed[kinds[source]], "invalid parent or topology direction")
        parents[target] = source
        children[source].append(target)
    visited = set()
    queue = list(roots)
    while queue:
        node = queue.pop()
        _require(node not in visited, "topology cycle")
        visited.add(node)
        queue.extend(children[node])
    _require(visited == set(kinds), "topology has unreachable nodes or a cycle")
    return topology


def _timestamp(value):
    schema.text(value, "capture timestamp")
    try:
        parsed = datetime.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise schema.TraceFormatError("invalid capture timestamp", "INVALID_BUNDLE") from error
    _require(parsed.tzinfo is not None, "capture timestamp requires a timezone")
    return parsed


def _hashed_files(root, hashes):
    schema.object_fields(hashes, ("algorithm", "files"), "hashes")
    _require(hashes["algorithm"] == "sha256", "unsupported hash algorithm")
    files = hashes["files"]
    _require(isinstance(files, dict) and 1 <= len(files) <= 64, "invalid hash file inventory")
    retained = {}
    total = 0
    for relative, expected in files.items():
        _require(relative != "hashes.json" and not relative.startswith("analysis/"), "self/output hashes are not input evidence")
        schema.digest(expected, "file hash")
        path = safe_path(root, relative)
        raw = read_bytes(path, schema.MAX_INPUT_BYTES if relative == "records.jsonl" else MAX_METADATA_BYTES)
        total += len(raw)
        _require(total <= MAX_BUNDLE_BYTES, "bundle exceeds byte limit")
        _require(hashlib.sha256(raw).hexdigest() == expected, "bundle file hash mismatch: " + relative)
        retained[relative] = raw
    return retained


def validate_bundle(root, review_name=None):
    root = pathlib.Path(root)
    hashes = read_json(safe_path(root, "hashes.json"))
    files = _hashed_files(root, hashes)
    _require({"manifest.json", "source-info.json", "records.jsonl"} <= files.keys(), "missing required input hashes")
    manifest = schema.loads(files["manifest.json"])
    required = ("bundle_version", "schema_version", "capture_id", "synthetic", "machine", "producer",
                "capture_start", "capture_end", "observer_configuration", "stimulus_description",
                "topology", "known_loss", "tool_commits")
    schema.object_fields(manifest, required, "manifest")
    for field in ("bundle_version", "schema_version"):
        _require(type(manifest[field]) is int and manifest[field] == 1, "unsupported bundle/schema version")
    schema.text(manifest["capture_id"], "manifest capture_id")
    _require(type(manifest["synthetic"]) is bool, "manifest must declare synthetic status")
    schema.object_fields(manifest["machine"], ("model", "soc", "os_version", "os_build"), "machine")
    for field in ("model", "soc", "os_version", "os_build"):
        schema.text(manifest["machine"][field], field)
    _require(_timestamp(manifest["capture_start"]) <= _timestamp(manifest["capture_end"]), "capture ends before start")
    schema.object_fields(manifest["observer_configuration"], (), "observer configuration")
    schema.text(manifest["stimulus_description"], "stimulus description", 4096)
    validate_topology(manifest["topology"])
    schema.object_fields(manifest["tool_commits"], (), "tool commits")
    _require(bool(manifest["tool_commits"]), "tool commits cannot be empty")
    for tool, commit in manifest["tool_commits"].items():
        schema.text(tool, "tool name")
        if commit != "UNKNOWN":
            _sha(commit, "tool commit")
    source = schema.loads(files["source-info.json"])
    schema.object_fields(source, ("kind", "producer", "description"), "source-info")
    schema.choice(source["kind"], ("synthetic", "observed"), "source kind")
    schema.text(source["description"], "source description", 4096)
    records = list(trace.read_record_stream(io.BytesIO(files["records.jsonl"])))
    summary = trace.summarize(records, include_correlations=True)
    _require(summary["capture_id"] == manifest["capture_id"], "manifest/capture identity mismatch")
    _require(summary["synthetic"] == manifest["synthetic"] == (source["kind"] == "synthetic"), "synthetic origin mismatch")
    _require(records[0]["producer"] == source["producer"] == manifest["producer"], "producer metadata mismatch")
    loss = manifest["known_loss"]
    expected_loss = {"reported_dropped_records": summary["reported_dropped_records"],
                     "sequence_gaps": summary["sequence_gaps"],
                     "incomplete_records": sum(not record["record_complete"] for record in records),
                     "loss_count_unknown": summary["loss_count_unknown"]}
    schema.object_fields(loss, expected_loss.keys(), "known loss")
    for field, expected in expected_loss.items():
        _require(type(loss[field]) is type(expected) and loss[field] == expected, "manifest loss inventory mismatch")
    review = None
    if review_name is not None:
        _require(review_name in files, "review must be a hash-inventoried bundle input")
        review = schema.loads(files[review_name])
    return {"manifest": manifest, "source_info": source, "hashes": hashes,
            "records": records, "summary": summary, "review": review,
            "integrity": "HASHES_VALID", "authenticity": "NOT_ESTABLISHED_BY_HASHES"}


def validate_human_result(path):
    path = pathlib.Path(path)
    result = read_json(path)
    required = ("handoff_version", "upstream_base_sha", "patch_commits", "build_command", "build_result",
                "artifact_hashes", "producer_version", "unit_tests", "execution_status", "files", "build_log")
    schema.object_fields(result, required, "human result")
    _require(type(result["handoff_version"]) is int and result["handoff_version"] == 1, "unsupported handoff version")
    _sha(result["upstream_base_sha"], "upstream base")
    _require(isinstance(result["patch_commits"], list) and len(result["patch_commits"]) <= 128, "invalid patch commit list")
    for commit in result["patch_commits"]:
        _sha(commit, "patch commit")
    _require(len(set(result["patch_commits"])) == len(result["patch_commits"]), "duplicate patch commit")
    schema.text(result["build_command"], "build command", 4096)
    schema.choice(result["build_result"], ("PASS", "FAIL", "NOT_RUN"), "build result")
    schema.text(result["producer_version"], "producer version")
    schema.object_fields(result["unit_tests"], ("status", "count"), "unit tests")
    schema.choice(result["unit_tests"]["status"], ("PASS", "FAIL", "NOT_RUN"), "unit test status")
    schema.integer(result["unit_tests"]["count"], "unit test count")
    schema.choice(result["execution_status"], ("NO_HARDWARE", "HARDWARE"), "execution status")
    schema.object_fields(result["artifact_hashes"], (), "artifact hashes")
    for artifact, digest in result["artifact_hashes"].items():
        schema.text(artifact, "artifact name")
        schema.digest(digest, "artifact hash")
    files = _hashed_files(path.parent, {"algorithm": "sha256", "files": result["files"]})
    _require(isinstance(result["build_log"], str) and result["build_log"] in files, "hashed build log required")
    if result["unit_tests"]["status"] != "NOT_RUN":
        _require(isinstance(result.get("unit_test_log"), str) and result["unit_test_log"] in files, "hashed unit test log required")
    return {"status": "EXTERNAL_PROVENANCE_FORMAT_VALID", "facts": result,
            "unverified": ["commit ancestry", "reviewer/producer authenticity", "artifact hashes without artifact files", "claimed execution status"],
            "platform_target_state": "M5_OBSERVER_CODE_NOT_READY_FOR_TARGET_TEST", "hardware_authorized": False}