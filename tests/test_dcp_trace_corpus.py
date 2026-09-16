import contextlib
import hashlib
import io
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

from tools import dcp_trace_analyze as analyze
from tools import dcp_trace_evidence as evidence
from tools import dcp_trace_import as trace
from tools import dcp_trace_replay as replay
from tools import dcp_trace_schema as schema
from tools import dcp_trace_synthetic as synthetic


ROOT = pathlib.Path(__file__).resolve().parents[1]
CORPUS = ROOT / "tests" / "fixtures" / "dcp_trace"


class GoldenCorpusTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads((CORPUS / "manifest.json").read_text())

    def test_manifest_inventory_hashes_and_byte_lengths(self):
        self.assertTrue(self.manifest["synthetic"])
        self.assertEqual(set(self.manifest["files"]), {path.relative_to(CORPUS).as_posix() for path in CORPUS.glob("*/*.jsonl")})
        self.assertEqual({path.split("/")[0] for path in self.manifest["files"]}, {"valid", "warning", "invalid", "evidence"})
        for relative, metadata in self.manifest["files"].items():
            with self.subTest(relative=relative):
                raw = (CORPUS / relative).read_bytes()
                self.assertEqual(hashlib.sha256(raw).hexdigest(), metadata["sha256"])
                self.assertEqual(len(raw), metadata["bytes"])
                self.assertLess(len(raw), 16384)

    def test_fixture_values_match_reviewable_generator(self):
        self.assertEqual(set(synthetic.corpus_cases()), set(self.manifest["files"]))
        for relative, expected in synthetic.corpus_cases().items():
            with self.subTest(relative=relative):
                self.assertEqual((CORPUS / relative).read_text(), synthetic.corpus_content(expected["scenario"]))
                for field, value in expected.items():
                    self.assertEqual(self.manifest["files"][relative][field], value)

    def test_golden_validation_correlation_and_all_gates(self):
        real_passes = 0
        seen_gates = set()
        for relative, expected in self.manifest["files"].items():
            with self.subTest(relative=relative):
                if expected["validation"] == "INVALID":
                    with self.assertRaises(schema.TraceFormatError) as raised:
                        analyze.analyze(CORPUS / relative)
                    self.assertEqual(raised.exception.code, expected["error_code"])
                    continue
                result = analyze.analyze(CORPUS / relative)
                self.assertEqual(result["summary"]["validation_status"], expected["validation"])
                self.assertEqual(result["summary"]["matched_pairs"], expected["matched_pairs"])
                passed = [gate for gate, value in result["gates"].items() if value["status"] == "SYNTHETIC_GATE_TEST_PASS"]
                self.assertEqual(passed, expected["synthetic_gate_passes"])
                seen_gates.update(passed)
                real_passes += result["real_evidence_passes"]
                self.assertEqual(result["project_gate_state"], "NOT_ESTABLISHED")
        self.assertEqual(seen_gates, set("ABCDE"))
        self.assertEqual(real_passes, 0)

    def test_every_valid_record_explicitly_marks_synthetic_origin(self):
        for relative, expected in self.manifest["files"].items():
            if expected["validation"] == "INVALID":
                self.assertIn("synthetic", (CORPUS / relative).read_text())
                continue
            for record in trace.read_records(CORPUS / relative):
                self.assertTrue(record["producer"]["synthetic"])
                self.assertTrue(record["extensions"]["synthetic"])

    def test_replay_is_idempotent_for_evidence_results(self):
        path = CORPUS / "evidence" / "two_sources.jsonl"
        selected, summary = replay.replay(path)
        result = evidence.evaluate(selected)
        self.assertEqual(result["gates"], analyze.analyze(path)["gates"])
        self.assertEqual(summary["record_count"], 2)
        self.assertEqual(result["real_evidence_passes"], 0)

    def test_duplicate_replay_never_adds_evidence(self):
        path = CORPUS / "evidence" / "two_sources.jsonl"
        selected, _ = replay.replay(path)
        with self.assertRaises(schema.TraceFormatError):
            evidence.evaluate(selected + selected)

    def test_filtered_output_does_not_manufacture_missing_contexts(self):
        selected, _ = replay.replay(CORPUS / "evidence" / "endpoints_one_source.jsonl", {"endpoint": 43})
        result = evidence.evaluate(selected)
        self.assertEqual(result["synthetic_gate_passes"], 0)
        self.assertFalse(result["summary"]["record_coverage_complete"])

    def test_all_cli_help_commands_are_host_only(self):
        for name in ("import", "synthetic", "replay", "analyze"):
            completed = subprocess.run([sys.executable, "-X", "dev", "-W", "error", str(ROOT / "tools" / ("dcp_trace_" + name + ".py")), "--help"],
                                       capture_output=True, text=True, check=False, cwd=ROOT.parent)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn("usage:", completed.stdout)

    def test_cli_invalid_capture_returns_structured_error(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            result = analyze.main([str(CORPUS / "invalid" / "malformed.jsonl"), "--json"])
        self.assertEqual(result, 2)
        self.assertEqual(json.loads(output.getvalue())["issues"][0]["code"], "PAYLOAD_LENGTH_MISMATCH")

    def test_corpus_regeneration_is_deterministic_and_exclusive(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = pathlib.Path(temporary) / "new-corpus"
            synthetic.write_corpus(root)
            self.assertEqual((root / "manifest.json").read_bytes(), (CORPUS / "manifest.json").read_bytes())
            with self.assertRaises(FileExistsError):
                synthetic.write_corpus(root)


if __name__ == "__main__":
    unittest.main()