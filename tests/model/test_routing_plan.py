#!/usr/bin/env python3
from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from model.routing_plan import (  # noqa: E402
    EVIDENCE_CLASS,
    ROUTING_ARTIFACT_SCHEMA_VERSION,
    RoutingPlanValidationError,
    format_finding_summary,
    load_manifest,
    validate_manifest,
    write_finding_summary,
    write_routing_artifact,
)


FIXTURE = REPO_ROOT / "configs" / "qwen3_fused_routing_phase0.json"


class RoutingPlanTests(unittest.TestCase):
    def load_fixture(self) -> dict:
        return copy.deepcopy(load_manifest(FIXTURE))

    def first_record(self, manifest: dict) -> dict:
        return manifest["blocks"][0]["routing_records"][0]

    def test_valid_manifest_emits_machine_readable_artifact(self) -> None:
        manifest = self.load_fixture()
        artifact = validate_manifest(manifest, manifest_path=str(FIXTURE))

        self.assertEqual(artifact["schema_version"], ROUTING_ARTIFACT_SCHEMA_VERSION)
        self.assertEqual(artifact["evidence"]["class"], EVIDENCE_CLASS)
        self.assertFalse(artifact["evidence"]["model_weights_loaded"])
        self.assertFalse(artifact["evidence"]["runtime_packet_implemented"])
        self.assertFalse(artifact["evidence"]["copy_counts_measured"])
        self.assertEqual(artifact["routing_payload_contract"]["record_shape"], [
            "layer_id",
            "active_expert_ids",
            "weight_coefficients",
            "target_nodes",
        ])
        self.assertEqual(artifact["payload_summary"]["block_count"], 1)
        self.assertEqual(artifact["payload_summary"]["record_count"], 4)
        self.assertEqual(artifact["payload_summary"]["min_layer_id"], 0)
        self.assertEqual(artifact["payload_summary"]["max_layer_id"], 93)

        with tempfile.TemporaryDirectory() as tmp_raw:
            artifact_path = Path(tmp_raw) / "routing.json"
            summary_path = Path(tmp_raw) / "finding.md"
            write_routing_artifact(artifact, artifact_path)
            write_finding_summary(artifact, summary_path)
            written = json.loads(artifact_path.read_text(encoding="utf-8"))
            self.assertEqual(written["schema_version"], ROUTING_ARTIFACT_SCHEMA_VERSION)
            summary = summary_path.read_text(encoding="utf-8")
            self.assertIn("Status: pass as Phase 0 scaffold/planning evidence", summary)
            self.assertIn("Runtime packet implemented | `false`", summary)
            self.assertIn("Copy counts measured | `false`", summary)

        inline_summary = format_finding_summary(artifact)
        self.assertIn("Qwen top-8 record constraints", inline_summary)

    def test_record_must_use_exact_field_shape_and_order(self) -> None:
        manifest = self.load_fixture()
        record = self.first_record(manifest)
        record["extra"] = "not allowed"

        with self.assertRaisesRegex(RoutingPlanValidationError, "routing record fields must be exactly"):
            validate_manifest(manifest)

    def test_active_expert_ids_must_have_exactly_top_8(self) -> None:
        manifest = self.load_fixture()
        self.first_record(manifest)["active_expert_ids"] = [0, 1, 2, 3, 4, 5, 6]

        with self.assertRaisesRegex(RoutingPlanValidationError, "active_expert_ids must contain exactly 8"):
            validate_manifest(manifest)

    def test_weight_coefficients_must_align_to_top_8(self) -> None:
        manifest = self.load_fixture()
        self.first_record(manifest)["weight_coefficients"] = [0.2] * 9

        with self.assertRaisesRegex(RoutingPlanValidationError, "weight_coefficients must contain exactly 8"):
            validate_manifest(manifest)

    def test_duplicate_experts_are_invalid(self) -> None:
        manifest = self.load_fixture()
        self.first_record(manifest)["active_expert_ids"] = [0, 0, 2, 3, 4, 5, 6, 7]

        with self.assertRaisesRegex(RoutingPlanValidationError, "active_expert_ids must be unique"):
            validate_manifest(manifest)

    def test_out_of_range_expert_is_invalid(self) -> None:
        manifest = self.load_fixture()
        self.first_record(manifest)["active_expert_ids"][-1] = 128

        with self.assertRaisesRegex(RoutingPlanValidationError, "expert IDs must be in 0-127"):
            validate_manifest(manifest)

    def test_layer_id_must_be_qwen_range(self) -> None:
        manifest = self.load_fixture()
        self.first_record(manifest)["layer_id"] = 94

        with self.assertRaisesRegex(RoutingPlanValidationError, "layer_id must be in 0-93"):
            validate_manifest(manifest)

    def test_target_nodes_must_be_b_c_or_both(self) -> None:
        manifest = self.load_fixture()
        self.first_record(manifest)["target_nodes"] = ["A"]

        with self.assertRaisesRegex(RoutingPlanValidationError, "target_nodes must only contain B and/or C"):
            validate_manifest(manifest)

    def test_target_nodes_must_use_canonical_order(self) -> None:
        manifest = self.load_fixture()
        self.first_record(manifest)["target_nodes"] = ["C", "B"]

        with self.assertRaisesRegex(RoutingPlanValidationError, "canonical B, C order"):
            validate_manifest(manifest)

    def test_block_sequences_reject_replay_ordering(self) -> None:
        manifest = self.load_fixture()
        replay = copy.deepcopy(manifest["blocks"][0])
        replay["block_id"] = "phase0-routing-block-0001-replay"
        replay["sequence"] = 0
        manifest["blocks"].append(replay)

        with self.assertRaisesRegex(RoutingPlanValidationError, "block sequence values must be strictly increasing"):
            validate_manifest(manifest)

    def test_records_must_be_layer_ordered_within_block(self) -> None:
        manifest = self.load_fixture()
        records = manifest["blocks"][0]["routing_records"]
        records[1], records[2] = records[2], records[1]

        with self.assertRaisesRegex(RoutingPlanValidationError, "routing records must be strictly increasing by layer_id"):
            validate_manifest(manifest)

    def test_topology_must_remain_a_with_b_c_workers(self) -> None:
        manifest = self.load_fixture()
        manifest["topology"]["compute_workers"] = ["B", "D"]

        with self.assertRaisesRegex(RoutingPlanValidationError, "compute_workers must contain exactly B and C"):
            validate_manifest(manifest)

    def test_layer_owner_topology_must_not_drift(self) -> None:
        manifest = self.load_fixture()
        manifest["topology"]["layer_owners"][0]["end_layer"] = 45

        with self.assertRaisesRegex(RoutingPlanValidationError, "layer_owners must be exactly B:0-46 and C:47-93"):
            validate_manifest(manifest)

    def test_zero_copy_must_not_claim_runtime_or_measured_counts(self) -> None:
        manifest = self.load_fixture()
        manifest["zero_copy_assumptions"]["runtime_implemented"] = True

        with self.assertRaisesRegex(RoutingPlanValidationError, "zero_copy_assumptions.runtime_implemented must be False"):
            validate_manifest(manifest)

        manifest = self.load_fixture()
        manifest["zero_copy_assumptions"]["measured_copy_counts_available"] = True

        with self.assertRaisesRegex(
            RoutingPlanValidationError,
            "zero_copy_assumptions.measured_copy_counts_available must be False",
        ):
            validate_manifest(manifest)


if __name__ == "__main__":
    raise SystemExit(unittest.main())
