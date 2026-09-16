import copy
import unittest
from unittest import mock

from tools import dcp_trace_evidence as evidence
from tools import dcp_trace_schema as schema
from tools import dcp_trace_synthetic as synthetic


class OwnershipEvidenceTests(unittest.TestCase):
    def evaluate(self, scenario):
        result = evidence.evaluate(synthetic.scenario_records(scenario))
        self.assertEqual(result["real_evidence_passes"], 0)
        self.assertEqual(result["project_gate_state"], "NOT_ESTABLISHED")
        self.assertFalse(result["hardware_authorized"])
        return result

    def assert_no_gates(self, result):
        self.assertTrue(all(gate["status"] == "NOT_ESTABLISHED" for gate in result["gates"].values()))

    def test_two_independent_sources_test_gate_a_only(self):
        result = self.evaluate("two_sources")
        self.assertEqual(result["gates"]["A"]["status"], "SYNTHETIC_GATE_TEST_PASS")
        self.assertEqual(result["synthetic_gate_passes"], 1)

    def test_independent_timing_generators_test_gate_b(self):
        self.assertEqual(self.evaluate("two_timings")["gates"]["B"]["status"], "SYNTHETIC_GATE_TEST_PASS")

    def test_simultaneous_source_payload_bindings_test_gate_c(self):
        self.assertEqual(self.evaluate("two_bindings")["gates"]["C"]["status"], "SYNTHETIC_GATE_TEST_PASS")

    def test_explicit_api_space_tests_d_without_simultaneity(self):
        result = self.evaluate("api_space")
        self.assertEqual(result["gates"]["D"]["status"], "SYNTHETIC_GATE_TEST_PASS")
        self.assertEqual(result["gates"]["A"]["status"], "NOT_ESTABLISHED")

    def test_independent_main_link_vcs_test_gate_e(self):
        self.assertEqual(self.evaluate("wire_vcs")["gates"]["E"]["status"], "SYNTHETIC_GATE_TEST_PASS")

    def test_two_endpoints_can_still_be_one_source(self):
        self.assert_no_gates(self.evaluate("endpoints_one_source"))

    def test_source_recreated_after_disconnect_is_not_two_sources(self):
        self.assert_no_gates(self.evaluate("recreated_source"))

    def test_two_sequential_timings_are_not_simultaneous(self):
        self.assert_no_gates(self.evaluate("sequential_timings"))

    def test_duplicate_packet_invalidates_input(self):
        with self.assertRaises(schema.TraceFormatError) as raised:
            self.evaluate("duplicate_packet")
        self.assertEqual(raised.exception.code, "DUPLICATE_SEQUENCE")

    def test_request_id_reused_after_generation_reset(self):
        result = self.evaluate("id_generation_reset")
        self.assert_no_gates(result)
        self.assertEqual(result["summary"]["matched_pairs"], 0)

    def test_changed_payload_on_same_source_is_not_two_bindings(self):
        self.assert_no_gates(self.evaluate("payload_changed"))

    def test_loss_between_observations_prevents_coexistence_proof(self):
        result = self.evaluate("loss_between_sources")
        self.assert_no_gates(result)
        self.assertTrue(all(item["uncertainty"] for item in result["evidence"]))

    def test_incomplete_reply_is_not_complete_exchange_evidence(self):
        result = self.evaluate("incomplete_reply")
        self.assert_no_gates(result)
        self.assertEqual(result["summary"]["matched_pairs"], 0)

    def test_inferred_source_annotations_never_promoted(self):
        self.assert_no_gates(self.evaluate("inferred_sources"))

    def test_two_physical_dptx_owners_do_not_combine(self):
        self.assert_no_gates(self.evaluate("unrelated_dptx"))

    def test_ext0_and_ext1_are_separate(self):
        self.assert_no_gates(self.evaluate("ext0_ext1"))

    def test_duplicated_synthetic_event_is_not_another_context(self):
        self.assert_no_gates(self.evaluate("duplicate_event"))

    def test_endpoint_equal_source_heuristic_is_explicitly_rejected(self):
        self.assert_no_gates(self.evaluate("endpoint_is_source"))

    def test_service_port_and_payload_identifiers_alone_are_not_evidence(self):
        for field in ("service", "port", "payload_identity"):
            records = synthetic.scenario_records("multiple_endpoints")
            for index, record in enumerate(records):
                record.setdefault("extensions", {})[field] = "different-" + str(index)
            self.assert_no_gates(evidence.evaluate(records))

    def test_same_owner_label_cannot_bridge_generations(self):
        records = synthetic.scenario_records("two_sources")
        second = records[1]
        second["capture_generation"] = second["annotations"]["capture_generation"] = "generation-1"
        second["sequence"] = second["annotations"]["provenance"]["references"][0]["sequence"] = 0
        second["annotations"]["provenance"]["references"][0]["capture_generation"] = "generation-1"
        self.assert_no_gates(evidence.evaluate(records))

    def test_missing_simultaneous_assertion_cannot_be_inferred(self):
        records = synthetic.scenario_records("two_sources")
        del records[1]["annotations"]["simultaneous"]
        self.assert_no_gates(evidence.evaluate(records))

    def test_raw_hash_mismatch_blocks_evidence(self):
        records = synthetic.scenario_records("two_sources")
        records[1]["raw_payload"] = "00" * records[1]["payload_length"]
        self.assert_no_gates(evidence.evaluate(records))

    def test_decoded_fields_cannot_override_raw_or_annotations(self):
        records = synthetic.scenario_records("endpoints_one_source")
        records[1]["decoded_fields"] = {"source_identity": "different", "source_count": 2, "raw_payload": "invented"}
        self.assert_no_gates(evidence.evaluate(records))

    def test_aux_control_is_not_main_link_vc_evidence(self):
        records = synthetic.scenario_records("wire_vcs")
        for record in records:
            record["annotations"]["provenance"]["observation_plane"] = "dp_aux"
        self.assert_no_gates(evidence.evaluate(records))

    def test_shared_raw_reference_cannot_prove_two_contexts(self):
        records = synthetic.scenario_records("two_sources")
        records[1]["annotations"]["provenance"]["references"].append(copy.deepcopy(records[0]["annotations"]["provenance"]["references"][0]))
        self.assert_no_gates(evidence.evaluate(records))

    def test_observed_label_alone_never_produces_real_pass(self):
        records = synthetic.scenario_records("two_sources")
        for record in records:
            record["producer"]["synthetic"] = False
            record["extensions"] = {}
            record["annotations"]["provenance"]["origin"] = "observed"
        result = evidence.evaluate(records)
        self.assertEqual(result["gates"]["A"]["status"], "REAL_PROVENANCE_REVIEW_REQUIRED")
        self.assertEqual(result["real_evidence_passes"], 0)

    def test_synthetic_cannot_receive_real_review(self):
        records = synthetic.scenario_records("two_sources")
        review = {"review_version": 1, "capture_id": records[0]["capture_id"],
                  "records_sha256": evidence.records_digest(records), "reviewer": "synthetic-test-reviewer",
                  "basis": "Not a real review", "approved_claim_ids": [record["annotations"]["claim_id"] for record in records]}
        with self.assertRaises(schema.TraceFormatError):
            evidence.evaluate(records, review)

    def test_incomplete_provenance_not_runtime_truth(self):
        records = synthetic.scenario_records("two_sources")
        del records[1]["annotations"]["provenance"]
        self.assert_no_gates(evidence.evaluate(records))

    def test_synthetic_origin_cannot_be_changed_by_one_flag(self):
        records = synthetic.scenario_records("two_sources")
        for record in records:
            record["producer"]["synthetic"] = False
        with self.assertRaises(schema.TraceFormatError) as raised:
            evidence.evaluate(records)
        self.assertEqual(raised.exception.code, "SYNTHETIC_ORIGIN_MISMATCH")

    def test_evidence_budgets_fail_explicitly(self):
        records = synthetic.scenario_records("two_sources")
        with mock.patch.object(evidence, "MAX_EVIDENCE_CLAIMS", 1):
            with self.assertRaises(schema.TraceFormatError) as raised:
                evidence.evaluate(records)
            self.assertEqual(raised.exception.code, "EVIDENCE_RESOURCE_LIMIT")
        with mock.patch.object(evidence, "MAX_PAIR_COMPARISONS", 0):
            with self.assertRaises(schema.TraceFormatError):
                evidence.evaluate(records)

    def test_unknown_api_space_member_does_not_qualify(self):
        records = synthetic.scenario_records("api_space")
        records[0]["annotations"]["source_space"][1] = "UNKNOWN"
        self.assert_no_gates(evidence.evaluate(records))


if __name__ == "__main__":
    unittest.main()