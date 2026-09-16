import contextlib
import hashlib
import io
import json
import pathlib
import tempfile
import unittest

from tools import dcp_trace_analyze as analyze
from tools import dcp_trace_bundle as bundle
from tools import dcp_trace_schema as schema
from tools import dcp_trace_synthetic as synthetic


class BundleTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = pathlib.Path(self.directory.name) / "capture"
        synthetic.write_bundle(self.root, "two_sources")

    def rewrite(self, name, change):
        path = self.root / name
        value = json.loads(path.read_text())
        change(value)
        path.write_text(schema.dumps(value) + "\n", encoding="utf-8")
        hashes = json.loads((self.root / "hashes.json").read_text())
        hashes["files"][name] = hashlib.sha256(path.read_bytes()).hexdigest()
        (self.root / "hashes.json").write_text(schema.dumps(hashes), encoding="utf-8")

    def test_self_contained_synthetic_bundle_valid(self):
        result = bundle.validate_bundle(self.root)
        self.assertEqual(result["integrity"], "HASHES_VALID")
        self.assertEqual(result["authenticity"], "NOT_ESTABLISHED_BY_HASHES")
        self.assertTrue(result["manifest"]["synthetic"])

    def test_bundle_analysis_has_zero_real_passes(self):
        result = analyze.analyze(self.root)
        self.assertEqual(result["gates"]["A"]["status"], "SYNTHETIC_GATE_TEST_PASS")
        self.assertEqual(result["real_evidence_passes"], 0)
        self.assertEqual(result["platform_target_state"], "M5_OBSERVER_CODE_NOT_READY_FOR_TARGET_TEST")

    def test_modified_raw_file_fails_hash(self):
        with (self.root / "records.jsonl").open("a") as destination:
            destination.write("\n")
        with self.assertRaises(schema.TraceFormatError):
            bundle.validate_bundle(self.root)

    def test_manifest_origin_mismatch_rejected(self):
        self.rewrite("manifest.json", lambda value: value.update(synthetic=False))
        with self.assertRaises(schema.TraceFormatError):
            bundle.validate_bundle(self.root)

    def test_source_info_origin_mismatch_rejected(self):
        self.rewrite("source-info.json", lambda value: value.update(kind="observed"))
        with self.assertRaises(schema.TraceFormatError):
            bundle.validate_bundle(self.root)

    def test_capture_id_mismatch_rejected(self):
        self.rewrite("manifest.json", lambda value: value.update(capture_id="other"))
        with self.assertRaises(schema.TraceFormatError):
            bundle.validate_bundle(self.root)

    def test_false_loss_inventory_rejected(self):
        self.rewrite("manifest.json", lambda value: value["known_loss"].update(reported_dropped_records=1))
        with self.assertRaises(schema.TraceFormatError):
            bundle.validate_bundle(self.root)

    def test_loss_bundle_reports_known_loss_exactly(self):
        root = pathlib.Path(self.directory.name) / "loss"
        synthetic.write_bundle(root, "dropped")
        self.assertEqual(bundle.validate_bundle(root)["summary"]["reported_dropped_records"], 3)

    def test_missing_input_hash_rejected(self):
        hashes = json.loads((self.root / "hashes.json").read_text())
        del hashes["files"]["source-info.json"]
        (self.root / "hashes.json").write_text(schema.dumps(hashes), encoding="utf-8")
        with self.assertRaises(schema.TraceFormatError):
            bundle.validate_bundle(self.root)

    def test_path_traversal_and_absolute_paths_rejected(self):
        for path in ("../outside", "/etc/passwd", "sub/../file", "sub\\file", "./records.jsonl"):
            with self.subTest(path=path), self.assertRaises(schema.TraceFormatError):
                bundle.safe_path(self.root, path)

    def test_symlink_input_rejected(self):
        path = self.root / "records.jsonl"
        target = pathlib.Path(self.directory.name) / "outside.jsonl"
        path.rename(target)
        path.symlink_to(target)
        with self.assertRaises(schema.TraceFormatError):
            bundle.validate_bundle(self.root)

    def test_missing_review_and_unhashed_review_rejected(self):
        with self.assertRaises(schema.TraceFormatError):
            analyze.analyze(self.root, "review.json")
        (self.root / "review.json").write_text("{}")
        with self.assertRaises(schema.TraceFormatError):
            analyze.analyze(self.root, "review.json")

    def test_bundle_unknown_metadata_preserved(self):
        self.rewrite("manifest.json", lambda value: value.update(future={"new": [1, None]}))
        result = bundle.validate_bundle(self.root)
        self.assertEqual(result["manifest"]["future"], {"new": [1, None]})

    def test_cli_machine_readable_bundle_result(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.assertEqual(analyze.main([str(self.root), "--json"]), 0)
        self.assertEqual(json.loads(output.getvalue())["real_evidence_passes"], 0)

    def test_bundle_writer_refuses_existing_directory(self):
        original = (self.root / "records.jsonl").read_bytes()
        with self.assertRaises(FileExistsError):
            synthetic.write_bundle(self.root, "zero_length")
        self.assertEqual((self.root / "records.jsonl").read_bytes(), original)


class TopologyTests(unittest.TestCase):
    def test_neutral_hub_and_sink_graph(self):
        topology = synthetic.neutral_topology()
        self.assertEqual(bundle.validate_topology(topology), topology)
        self.assertNotIn("vendor_id", topology["nodes"][2])

    def test_dock_metadata_optional_and_preserved(self):
        topology = synthetic.neutral_topology()
        topology["nodes"][2].update(kind="dock", vendor_id=1234, product_id=5678, mst_branch_identity="UNKNOWN")
        self.assertEqual(bundle.validate_topology(topology)["nodes"][2]["vendor_id"], 1234)

    def test_duplicate_nodes_rejected(self):
        topology = synthetic.neutral_topology()
        topology["nodes"].append(topology["nodes"][0])
        with self.assertRaises(schema.TraceFormatError):
            bundle.validate_topology(topology)

    def test_disconnected_sink_rejected(self):
        topology = synthetic.neutral_topology()
        topology["edges"].pop()
        with self.assertRaises(schema.TraceFormatError):
            bundle.validate_topology(topology)

    def test_cycle_or_wrong_direction_rejected(self):
        topology = synthetic.neutral_topology()
        topology["edges"].append({"source": "sink-a", "target": "hub", "connection_type": "displayport"})
        with self.assertRaises(schema.TraceFormatError):
            bundle.validate_topology(topology)

    def test_sink_cannot_have_two_parents(self):
        topology = synthetic.neutral_topology()
        topology["edges"].append({"source": "output", "target": "sink-a", "connection_type": "displayport"})
        with self.assertRaises(schema.TraceFormatError):
            bundle.validate_topology(topology)

    def test_vendor_ids_are_not_booleans(self):
        topology = synthetic.neutral_topology()
        topology["nodes"][2]["vendor_id"] = True
        with self.assertRaises(schema.TraceFormatError):
            bundle.validate_topology(topology)


class HumanHandoffTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = pathlib.Path(self.directory.name)
        (self.root / "build.log").write_bytes(b"Synthetic build log; no platform execution.\n")
        digest = hashlib.sha256((self.root / "build.log").read_bytes()).hexdigest()
        self.result = {"handoff_version": 1, "upstream_base_sha": "a" * 40, "patch_commits": [],
                       "build_command": "synthetic recorded command; never executed", "build_result": "NOT_RUN",
                       "artifact_hashes": {}, "producer_version": "UNKNOWN", "unit_tests": {"status": "NOT_RUN", "count": 0},
                       "execution_status": "NO_HARDWARE", "files": {"build.log": digest}, "build_log": "build.log"}
        self.path = self.root / "result.json"

    def validate(self):
        self.path.write_text(schema.dumps(self.result), encoding="utf-8")
        return bundle.validate_human_result(self.path)

    def test_external_facts_do_not_authorize_execution(self):
        result = self.validate()
        self.assertEqual(result["status"], "EXTERNAL_PROVENANCE_FORMAT_VALID")
        self.assertFalse(result["hardware_authorized"])
        self.assertIn("commit ancestry", result["unverified"])

    def test_missing_build_log_hash_rejected(self):
        self.result["build_log"] = "absent.log"
        with self.assertRaises(schema.TraceFormatError):
            self.validate()

    def test_wrong_commit_format_rejected(self):
        self.result["patch_commits"] = ["main"]
        with self.assertRaises(schema.TraceFormatError):
            self.validate()

    def test_execution_status_must_be_explicit(self):
        self.result["execution_status"] = "probably safe"
        with self.assertRaises(schema.TraceFormatError):
            self.validate()

    def test_reported_test_success_needs_hashed_test_log(self):
        self.result["unit_tests"] = {"status": "PASS", "count": 1}
        with self.assertRaises(schema.TraceFormatError):
            self.validate()


if __name__ == "__main__":
    unittest.main()