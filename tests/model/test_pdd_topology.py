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

from model.pdd_topology import (  # noqa: E402
    EVIDENCE_CLASS,
    MEMORY_LEDGER_SCHEMA_VERSION,
    PlacementValidationError,
    format_finding_summary,
    load_manifest,
    validate_manifest,
    write_finding_summary,
    write_memory_ledger,
)


FIXTURE = REPO_ROOT / "configs" / "qwen3_pdd_topology_phase1.json"


class PddTopologyTests(unittest.TestCase):
    def load_fixture(self) -> dict:
        return copy.deepcopy(load_manifest(FIXTURE))

    def test_valid_manifest_emits_machine_readable_ledger(self) -> None:
        manifest = self.load_fixture()
        ledger = validate_manifest(manifest, manifest_path=str(FIXTURE))

        self.assertEqual(ledger["schema_version"], MEMORY_LEDGER_SCHEMA_VERSION)
        nodes = {node["name"]: node for node in ledger["nodes"]}
        self.assertEqual(ledger["evidence"]["class"], EVIDENCE_CLASS)
        self.assertFalse(ledger["evidence"]["measured_full_runtime"])
        memory_accounting = ledger["evidence"]["memory_accounting"]
        self.assertEqual(memory_accounting["byte_source_state"], "placeholder_cap_test")
        self.assertTrue(memory_accounting["placeholder_cap_test"])
        self.assertFalse(memory_accounting["measured_runtime"])
        self.assertFalse(memory_accounting["derived_from_pinned_tensor_metadata"])
        self.assertEqual(ledger["context_length_assumption"]["evidence_class"], "planning_only")
        self.assertFalse(ledger["context_length_assumption"]["runtime_validated"])
        self.assertEqual(
            sorted(ledger["tensor_class_policy_placeholders"]),
            ["attention", "cold_moe_experts", "hot_moe_experts", "kv_cache", "router_gate"],
        )
        self.assertEqual(
            ledger["runtime_path_constraints"]["node_a_steady_state_decode_critical_path"],
            "forbidden_outside_correctness_mode",
        )
        self.assertFalse(ledger["runtime_path_constraints"]["steady_state_decode_runtime_implemented"])
        self.assertEqual(nodes["A"]["primary_moe_decode_bytes"], 0)
        self.assertFalse(nodes["A"]["measured_full_runtime"])
        self.assertEqual(nodes["A"]["byte_source_state"], "placeholder_cap_test")
        self.assertEqual(nodes["A"]["decode_layer_ranges"], [])
        self.assertEqual(nodes["B"]["decode_layer_ranges"], [{"start": 0, "end": 46}])
        self.assertEqual(nodes["C"]["decode_layer_ranges"], [{"start": 47, "end": 93}])
        self.assertTrue(nodes["B"]["passes_static_cap"])
        self.assertTrue(nodes["C"]["passes_static_cap"])
        self.assertTrue(nodes["B"]["passes_runtime_headroom"])
        self.assertTrue(nodes["C"]["passes_runtime_headroom"])

        with tempfile.TemporaryDirectory() as tmp_raw:
            ledger_path = Path(tmp_raw) / "memory-ledger.json"
            summary_path = Path(tmp_raw) / "finding.md"
            write_memory_ledger(ledger, ledger_path)
            write_finding_summary(ledger, summary_path)
            written = json.loads(ledger_path.read_text(encoding="utf-8"))
            self.assertEqual(written["schema_version"], MEMORY_LEDGER_SCHEMA_VERSION)
            summary = summary_path.read_text(encoding="utf-8")
            self.assertIn("Status: pass as scaffold/planning evidence", summary)
            self.assertIn("Node A primary MoE decode bytes are exactly 0", summary)
            self.assertIn("Measured full runtime | `false`", summary)
            self.assertIn("Memory byte source state | `placeholder_cap_test`", summary)
            self.assertIn("Node A steady-state decode critical path", summary)

        inline_summary = format_finding_summary(ledger)
        self.assertIn("Node B stays under 33.6GB static cap", inline_summary)

    def test_model_name_must_match_qwen3_target(self) -> None:
        manifest = self.load_fixture()
        manifest["model"]["name"] = "Qwen3-30B-A3B"

        with self.assertRaisesRegex(PlacementValidationError, "model.name must be 'Qwen3-235B-A22B'"):
            validate_manifest(manifest)

    def test_model_variant_must_match_instruct_target(self) -> None:
        manifest = self.load_fixture()
        manifest["model"]["variant"] = "Qwen3-235B-A22B-Thinking-2507"

        with self.assertRaisesRegex(
            PlacementValidationError,
            "model.variant must be 'Qwen3-235B-A22B-Instruct-2507'",
        ):
            validate_manifest(manifest)

    def test_model_layer_count_must_match_qwen3_target(self) -> None:
        manifest = self.load_fixture()
        manifest["model"]["layers"] = 95

        with self.assertRaisesRegex(PlacementValidationError, "model.layers must be 94"):
            validate_manifest(manifest)

    def test_model_expert_count_must_match_qwen3_target(self) -> None:
        manifest = self.load_fixture()
        manifest["model"]["experts"] = 127

        with self.assertRaisesRegex(PlacementValidationError, "model.experts must be 128"):
            validate_manifest(manifest)

    def test_model_active_expert_count_must_match_qwen3_target(self) -> None:
        manifest = self.load_fixture()
        manifest["model"]["active_experts"] = 7

        with self.assertRaisesRegex(PlacementValidationError, "model.active_experts must be 8"):
            validate_manifest(manifest)

    def test_placeholder_byte_evidence_flags_must_not_claim_measurement(self) -> None:
        manifest = self.load_fixture()
        manifest["evidence_metadata"]["memory_accounting"]["measured_runtime"] = True

        with self.assertRaisesRegex(PlacementValidationError, "placeholder cap-test bytes"):
            validate_manifest(manifest)

    def test_context_length_assumption_must_remain_planning_only(self) -> None:
        manifest = self.load_fixture()
        manifest["context_length_assumption"]["runtime_validated"] = True

        with self.assertRaisesRegex(PlacementValidationError, "runtime_validated must be false"):
            validate_manifest(manifest)

    def test_node_a_decode_constraint_must_forbid_steady_state_critical_path(self) -> None:
        manifest = self.load_fixture()
        manifest["runtime_path_constraints"]["node_a_steady_state_decode_critical_path"] = "allowed"

        with self.assertRaisesRegex(
            PlacementValidationError,
            "runtime_path_constraints.node_a_steady_state_decode_critical_path",
        ):
            validate_manifest(manifest)

    def test_node_a_must_not_own_primary_moe_decode_bytes(self) -> None:
        manifest = self.load_fixture()
        node_a = manifest["nodes"][0]
        node_a["static_memory"]["primary_moe_decode_bytes"] = 1
        node_a["static_memory"]["total_static_bytes"] += 1

        with self.assertRaisesRegex(PlacementValidationError, "node A: primary_moe_decode_bytes must be 0"):
            validate_manifest(manifest)

    def test_node_a_must_not_claim_primary_moe_decode_ownership(self) -> None:
        manifest = self.load_fixture()
        manifest["nodes"][0]["owns_primary_moe_decode"] = True

        with self.assertRaisesRegex(PlacementValidationError, "node A: owns_primary_moe_decode must be false"):
            validate_manifest(manifest)

    def test_node_b_layer_range_must_be_lower_half(self) -> None:
        manifest = self.load_fixture()
        manifest["nodes"][1]["decode_layer_ranges"][0]["end"] = 45

        with self.assertRaisesRegex(PlacementValidationError, "node B: decode layer ranges must be exactly 0-46"):
            validate_manifest(manifest)

    def test_node_c_layer_range_must_be_upper_half(self) -> None:
        manifest = self.load_fixture()
        manifest["nodes"][2]["decode_layer_ranges"][0]["start"] = 46

        with self.assertRaisesRegex(PlacementValidationError, "node C: decode layer ranges must be exactly 47-93"):
            validate_manifest(manifest)

    def test_worker_layer_ranges_must_not_be_swapped(self) -> None:
        manifest = self.load_fixture()
        manifest["nodes"][1]["decode_layer_ranges"] = [{"start": 47, "end": 93}]
        manifest["nodes"][2]["decode_layer_ranges"] = [{"start": 0, "end": 46}]

        with self.assertRaisesRegex(PlacementValidationError, "node B: decode layer ranges must be exactly 0-46"):
            validate_manifest(manifest)

    def test_worker_layer_ranges_must_not_overlap(self) -> None:
        manifest = self.load_fixture()
        manifest["nodes"][1]["decode_layer_ranges"] = [
            {"start": 0, "end": 46},
            {"start": 46, "end": 47},
        ]

        with self.assertRaisesRegex(PlacementValidationError, "node B: decode layer ranges must be exactly 0-46"):
            validate_manifest(manifest)

    def test_static_total_must_match_component_sum(self) -> None:
        manifest = self.load_fixture()
        manifest["nodes"][1]["static_memory"]["total_static_bytes"] += 1

        with self.assertRaisesRegex(PlacementValidationError, "node B: total_static_bytes must equal component byte sum"):
            validate_manifest(manifest)

    def test_worker_static_total_must_fit_cap(self) -> None:
        manifest = self.load_fixture()
        node_b = manifest["nodes"][1]
        node_b["static_memory"]["primary_moe_decode_bytes"] = 31100000001
        node_b["static_memory"]["total_static_bytes"] = 33600000001

        with self.assertRaisesRegex(PlacementValidationError, "node B: total_static_bytes .* exceeds static cap"):
            validate_manifest(manifest)

    def test_worker_headroom_must_be_thirty_percent(self) -> None:
        manifest = self.load_fixture()
        manifest["nodes"][1]["runtime_headroom_gb"] = 12.0

        with self.assertRaisesRegex(PlacementValidationError, "node B.runtime_headroom_gb must be 14.4"):
            validate_manifest(manifest)

    def test_manifest_must_not_miss_node(self) -> None:
        manifest = self.load_fixture()
        manifest["nodes"] = manifest["nodes"][:2]

        with self.assertRaisesRegex(PlacementValidationError, "nodes must contain exactly A, B, and C"):
            validate_manifest(manifest)

    def test_manifest_must_not_include_extra_node(self) -> None:
        manifest = self.load_fixture()
        node_d = copy.deepcopy(manifest["nodes"][0])
        node_d["name"] = "D"
        manifest["nodes"].append(node_d)

        with self.assertRaisesRegex(PlacementValidationError, "nodes must contain exactly A, B, and C"):
            validate_manifest(manifest)

    def test_manifest_must_not_duplicate_node(self) -> None:
        manifest = self.load_fixture()
        manifest["nodes"][2] = copy.deepcopy(manifest["nodes"][1])

        with self.assertRaisesRegex(PlacementValidationError, "duplicate node 'B'"):
            validate_manifest(manifest)


if __name__ == "__main__":
    raise SystemExit(unittest.main())
