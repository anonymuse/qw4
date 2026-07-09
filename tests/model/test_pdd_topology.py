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
    MEMORY_LEDGER_SCHEMA_VERSION,
    PlacementValidationError,
    load_manifest,
    validate_manifest,
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
        self.assertEqual(nodes["A"]["primary_moe_decode_bytes"], 0)
        self.assertEqual(nodes["A"]["decode_layer_ranges"], [])
        self.assertEqual(nodes["B"]["decode_layer_ranges"], [{"start": 0, "end": 46}])
        self.assertEqual(nodes["C"]["decode_layer_ranges"], [{"start": 47, "end": 93}])
        self.assertTrue(nodes["B"]["passes_static_cap"])
        self.assertTrue(nodes["C"]["passes_static_cap"])

        with tempfile.TemporaryDirectory() as tmp_raw:
            ledger_path = Path(tmp_raw) / "memory-ledger.json"
            write_memory_ledger(ledger, ledger_path)
            written = json.loads(ledger_path.read_text(encoding="utf-8"))
            self.assertEqual(written["schema_version"], MEMORY_LEDGER_SCHEMA_VERSION)

    def test_node_a_must_not_own_primary_moe_decode_bytes(self) -> None:
        manifest = self.load_fixture()
        node_a = manifest["nodes"][0]
        node_a["static_memory"]["primary_moe_decode_bytes"] = 1
        node_a["static_memory"]["total_static_bytes"] += 1

        with self.assertRaisesRegex(PlacementValidationError, "node A: primary_moe_decode_bytes must be 0"):
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


if __name__ == "__main__":
    raise SystemExit(unittest.main())
