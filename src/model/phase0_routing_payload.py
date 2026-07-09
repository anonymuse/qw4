"""Phase 0 routing-payload validation for DS5-F000.

This module validates a narrow routing-payload contract. It does not load model
weights, implement a runtime packet decoder, or make transport performance claims.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any


ROUTING_MANIFEST_SCHEMA_VERSION = "ds5.phase0_routing_payload_manifest.v1"
ROUTING_ARTIFACT_SCHEMA_VERSION = "ds5.phase0_routing_payload_artifact.v1"
FEATURE_ID = "DS5-F000"
EVIDENCE_CLASS = "scaffold/planning"
EXPECTED_MODEL_LAYERS = 94
EXPECTED_EXPERTS = 128
EXPECTED_ACTIVE_EXPERTS = 8
EXPECTED_COORDINATOR = "A"
EXPECTED_COMPUTE_WORKERS = ("B", "C")
EXPECTED_LAYER_OWNERS = {
    "B": (0, 46),
    "C": (47, 93),
}
EXPECTED_RECORD_SHAPE = (
    "layer_id",
    "active_expert_ids",
    "weight_coefficients",
    "target_nodes",
)
FLOAT_TOLERANCE = 1e-9


class RoutingPlanValidationError(ValueError):
    """Raised when a Phase 0 routing-payload scaffold violates the planning contract."""


def load_manifest(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise RoutingPlanValidationError("routing manifest root must be an object")
    return data


def validate_manifest(manifest: dict[str, Any], *, manifest_path: str | None = None) -> dict[str, Any]:
    """Validate a manifest and return the machine-readable routing artifact."""

    return build_routing_artifact(manifest, manifest_path=manifest_path)


def build_routing_artifact(manifest: dict[str, Any], *, manifest_path: str | None = None) -> dict[str, Any]:
    if not isinstance(manifest, dict):
        raise RoutingPlanValidationError("routing manifest root must be an object")

    _require_equal(manifest.get("schema_version"), ROUTING_MANIFEST_SCHEMA_VERSION, "schema_version")
    _require_equal(manifest.get("feature_id"), FEATURE_ID, "feature_id")

    model = _required_mapping(manifest, "model", "root")
    _validate_model(model)

    topology = _required_mapping(manifest, "topology", "root")
    topology_artifact = _validate_topology(topology)

    packet_contract = _required_mapping(manifest, "packet_contract", "root")
    _validate_packet_contract(packet_contract)

    zero_copy_assumptions = _required_mapping(manifest, "zero_copy_assumptions", "root")
    _validate_zero_copy_assumptions(zero_copy_assumptions)

    artifact_policy = _required_mapping(manifest, "artifact_policy", "root")
    _require_equal(
        artifact_policy.get("routing_artifact_schema_version"),
        ROUTING_ARTIFACT_SCHEMA_VERSION,
        "artifact_policy.routing_artifact_schema_version",
    )
    default_artifact_path = _required_string(artifact_policy, "default_artifact_path", "artifact_policy")
    default_summary_path = _required_string(artifact_policy, "default_summary_path", "artifact_policy")

    blocks = _required_list(manifest, "blocks", "root")
    routing_payloads, payload_summary = _validate_blocks(blocks)

    return {
        "schema_version": ROUTING_ARTIFACT_SCHEMA_VERSION,
        "feature_id": FEATURE_ID,
        "source_manifest": manifest_path,
        "model": {
            "name": model.get("name"),
            "variant": model.get("variant"),
            "layers": EXPECTED_MODEL_LAYERS,
            "experts": EXPECTED_EXPERTS,
            "active_experts": EXPECTED_ACTIVE_EXPERTS,
        },
        "topology": topology_artifact,
        "routing_payload_contract": {
            "record_shape": list(EXPECTED_RECORD_SHAPE),
            "layer_id_range": [0, EXPECTED_MODEL_LAYERS - 1],
            "active_expert_ids_length": EXPECTED_ACTIVE_EXPERTS,
            "weight_coefficients_length": EXPECTED_ACTIVE_EXPERTS,
            "valid_target_nodes": list(EXPECTED_COMPUTE_WORKERS),
            "target_node_sets_allowed": [["B"], ["C"], ["B", "C"]],
            "encoding_status": packet_contract["encoding_status"],
            "checksum_required": packet_contract["checksum_required"],
            "replay_protection_required": packet_contract["replay_protection_required"],
            "runtime_packet_implemented": packet_contract["runtime_packet_implemented"],
        },
        "routing_payloads": routing_payloads,
        "payload_summary": payload_summary,
        "zero_copy_assumptions": {
            "evidence_class": EVIDENCE_CLASS,
            "runtime_implemented": False,
            "measured_copy_counts_available": False,
            "hot_path_heap_to_heap_copy_budget": 0,
            "buffer_ownership": list(zero_copy_assumptions["buffer_ownership"]),
            "requires_future_validation": list(zero_copy_assumptions["requires_future_validation"]),
        },
        "evidence": {
            "class": EVIDENCE_CLASS,
            "model_weights_loaded": False,
            "tokenizer_loaded": False,
            "runtime_packet_implemented": False,
            "metal_kernels_implemented": False,
            "kv_allocator_implemented": False,
            "primary_weight_loader_implemented": False,
            "copy_counts_measured": False,
            "benchmark_claim": False,
            "source": "routing manifest constants and validator checks",
        },
        "validation": {
            "status": "pass",
            "checked_invariants": [
                "exact DS5-F000 routing record field names",
                "exact Qwen top-8 active expert count per routed layer",
                "active_expert_ids and weight_coefficients are index-aligned by length",
                "layer_id is within 0-93",
                "expert IDs are unique and within 0-127",
                "target_nodes only contains B, C, or both",
                "block sequences are strictly increasing to reject replay ordering in this scaffold",
                "routing records are strictly increasing by layer within each block",
                "topology remains A coordinator with B/C compute workers and 0-46 / 47-93 layer ownership",
                "zero-copy status is recorded as an unmeasured planning assumption",
                "DS5-F002 remains blocked until DS5-F001A and DS5-F000 complete",
            ],
        },
        "artifact_policy": {
            "default_artifact_path": default_artifact_path,
            "default_summary_path": default_summary_path,
        },
        "limits_of_claim": list(manifest.get("limits_of_claim", [])),
    }


def write_routing_artifact(artifact: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")


def write_finding_summary(artifact: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(format_finding_summary(artifact), encoding="utf-8")


def format_artifact_summary(artifact: dict[str, Any]) -> str:
    summary = artifact["payload_summary"]
    lines = [
        f"{FEATURE_ID} Phase 0 routing-payload scaffold: PASS",
        f"Evidence: {artifact['evidence']['class']} (runtime packet implemented: no)",
        "",
        "Payload summary:",
        f"  blocks: {summary['block_count']}",
        f"  routing records: {summary['record_count']}",
        f"  layer range: {summary['min_layer_id']}-{summary['max_layer_id']}",
        f"  target node sets: {', '.join(summary['target_node_sets'])}",
        "",
        "This is a routing payload and zero-copy assumption scaffold only.",
        "It does not load Qwen weights, implement production routing, or report copy-count telemetry.",
        "It does not unblock DS5-F002.",
    ]
    return "\n".join(lines)


def format_finding_summary(artifact: dict[str, Any]) -> str:
    summary = artifact["payload_summary"]
    contract = artifact["routing_payload_contract"]
    evidence = artifact["evidence"]
    lines = [
        "# DS5-F000 Routing Payload Scaffold",
        "",
        "Status: pass as Phase 0 scaffold/planning evidence. This is not fused routing runtime evidence.",
        "",
        "## Reproduction",
        "",
        "```bash",
        "make phase0-routing-payload-validate",
        "```",
        "",
        "The command emits:",
        "",
        f"- `{artifact['artifact_policy']['default_artifact_path']}`",
        f"- `{artifact['artifact_policy']['default_summary_path']}`",
        "",
        "## Evidence Classification",
        "",
        "| Field | Value |",
        "|---|---|",
        f"| Evidence class | `{evidence['class']}` |",
        f"| Model weights loaded | `{str(evidence['model_weights_loaded']).lower()}` |",
        f"| Runtime packet implemented | `{str(evidence['runtime_packet_implemented']).lower()}` |",
        f"| Copy counts measured | `{str(evidence['copy_counts_measured']).lower()}` |",
        f"| Benchmark claim | `{str(evidence['benchmark_claim']).lower()}` |",
        "",
        "This summary validates synthetic routing payload shape, Qwen top-8 record constraints, DS5 B/C "
        "target-node bounds, and zero-copy assumptions as machine-readable planning data only. It does not "
        "load Qwen weights, tokenizer assets, Metal kernels, a KV allocator, or a primary-weight loader. "
        "It does not unblock DS5-F002, which remains blocked until DS5-F001A and DS5-F000 complete.",
        "",
        "## Payload Contract",
        "",
        "| Field | Value |",
        "|---|---|",
        f"| Record shape | `{', '.join(contract['record_shape'])}` |",
        f"| Layer range | `{contract['layer_id_range'][0]}-{contract['layer_id_range'][1]}` |",
        f"| Active experts per record | `{contract['active_expert_ids_length']}` |",
        f"| Valid target nodes | `{', '.join(contract['valid_target_nodes'])}` |",
        f"| Encoding status | `{contract['encoding_status']}` |",
        "",
        "## Payload Summary",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| Blocks | {summary['block_count']} |",
        f"| Routing records | {summary['record_count']} |",
        f"| Min layer | {summary['min_layer_id']} |",
        f"| Max layer | {summary['max_layer_id']} |",
        f"| Unique expert IDs referenced | {summary['unique_expert_id_count']} |",
        "",
        "## Target Node Sets",
        "",
        "| Target nodes | Record count |",
        "|---|---:|",
    ]
    for item in summary["target_node_set_counts"]:
        lines.append(f"| `{item['target_nodes']}` | {item['record_count']} |")

    lines.extend(
        [
            "",
            "## Zero-Copy Assumption Status",
            "",
            "| Assumption | Value |",
            "|---|---|",
            f"| Runtime implemented | `{str(artifact['zero_copy_assumptions']['runtime_implemented']).lower()}` |",
            (
                "| Measured copy counts available "
                f"| `{str(artifact['zero_copy_assumptions']['measured_copy_counts_available']).lower()}` |"
            ),
            (
                "| Hot-path heap-to-heap copy budget "
                f"| `{artifact['zero_copy_assumptions']['hot_path_heap_to_heap_copy_budget']}` |"
            ),
            "",
            "## Limits Of Claim",
            "",
        ]
    )
    for limit in artifact["limits_of_claim"]:
        lines.append(f"- {limit}")
    lines.append("")
    return "\n".join(lines)


def _validate_model(model: dict[str, Any]) -> None:
    _require_equal(model.get("name"), "Qwen3-235B-A22B", "model.name")
    _require_equal(model.get("variant"), "Qwen3-235B-A22B-Instruct-2507", "model.variant")
    _require_equal(model.get("layers"), EXPECTED_MODEL_LAYERS, "model.layers")
    _require_equal(model.get("experts"), EXPECTED_EXPERTS, "model.experts")
    _require_equal(model.get("active_experts"), EXPECTED_ACTIVE_EXPERTS, "model.active_experts")


def _validate_topology(topology: dict[str, Any]) -> dict[str, Any]:
    _require_equal(topology.get("coordinator"), EXPECTED_COORDINATOR, "topology.coordinator")
    workers = _required_list(topology, "compute_workers", "topology")
    if sorted(workers) != list(EXPECTED_COMPUTE_WORKERS):
        raise RoutingPlanValidationError("topology.compute_workers must contain exactly B and C")

    owners = _required_list(topology, "layer_owners", "topology")
    if len(owners) != len(EXPECTED_LAYER_OWNERS):
        raise RoutingPlanValidationError("topology.layer_owners must contain exactly B and C")

    indexed: dict[str, tuple[int, int]] = {}
    for owner in owners:
        if not isinstance(owner, dict):
            raise RoutingPlanValidationError("topology.layer_owners entries must be objects")
        node = _required_string(owner, "node", "topology.layer_owners")
        if node in indexed:
            raise RoutingPlanValidationError(f"duplicate layer owner {node!r}")
        start = _required_int(owner, "start_layer", f"topology.layer_owners.{node}")
        end = _required_int(owner, "end_layer", f"topology.layer_owners.{node}")
        indexed[node] = (start, end)

    if indexed != EXPECTED_LAYER_OWNERS:
        raise RoutingPlanValidationError("topology.layer_owners must be exactly B:0-46 and C:47-93")

    return {
        "coordinator": EXPECTED_COORDINATOR,
        "compute_workers": list(EXPECTED_COMPUTE_WORKERS),
        "layer_owners": [
            {"node": "B", "start_layer": 0, "end_layer": 46},
            {"node": "C", "start_layer": 47, "end_layer": 93},
        ],
    }


def _validate_packet_contract(packet_contract: dict[str, Any]) -> None:
    shape = _required_list(packet_contract, "record_shape", "packet_contract")
    if tuple(shape) != EXPECTED_RECORD_SHAPE:
        raise RoutingPlanValidationError(
            "packet_contract.record_shape must be exactly layer_id, active_expert_ids, "
            "weight_coefficients, target_nodes"
        )
    _require_equal(packet_contract.get("encoding_status"), "json_contract_only", "packet_contract.encoding_status")
    _require_equal(packet_contract.get("checksum_required"), True, "packet_contract.checksum_required")
    _require_equal(
        packet_contract.get("replay_protection_required"),
        True,
        "packet_contract.replay_protection_required",
    )
    _require_equal(
        packet_contract.get("runtime_packet_implemented"),
        False,
        "packet_contract.runtime_packet_implemented",
    )


def _validate_zero_copy_assumptions(assumptions: dict[str, Any]) -> None:
    _require_equal(assumptions.get("evidence_class"), EVIDENCE_CLASS, "zero_copy_assumptions.evidence_class")
    _require_equal(assumptions.get("runtime_implemented"), False, "zero_copy_assumptions.runtime_implemented")
    _require_equal(
        assumptions.get("measured_copy_counts_available"),
        False,
        "zero_copy_assumptions.measured_copy_counts_available",
    )
    _require_equal(
        assumptions.get("hot_path_heap_to_heap_copy_budget"),
        0,
        "zero_copy_assumptions.hot_path_heap_to_heap_copy_budget",
    )
    if not _required_list(assumptions, "buffer_ownership", "zero_copy_assumptions"):
        raise RoutingPlanValidationError("zero_copy_assumptions.buffer_ownership must not be empty")
    if not _required_list(assumptions, "requires_future_validation", "zero_copy_assumptions"):
        raise RoutingPlanValidationError("zero_copy_assumptions.requires_future_validation must not be empty")


def _validate_blocks(blocks: list[Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if not blocks:
        raise RoutingPlanValidationError("blocks must not be empty")

    payloads: list[dict[str, Any]] = []
    prior_sequence: int | None = None
    all_layers: list[int] = []
    all_experts: set[int] = set()
    target_counts: dict[str, int] = {}

    for index, block in enumerate(blocks):
        if not isinstance(block, dict):
            raise RoutingPlanValidationError("blocks entries must be objects")
        block_id = _required_string(block, "block_id", f"blocks[{index}]")
        sequence = _required_int(block, "sequence", f"blocks[{index}]")
        if prior_sequence is not None and sequence <= prior_sequence:
            raise RoutingPlanValidationError("block sequence values must be strictly increasing")
        prior_sequence = sequence

        records = _required_list(block, "routing_records", f"blocks[{index}]")
        if not records:
            raise RoutingPlanValidationError(f"block {block_id}: routing_records must not be empty")

        validated_records = []
        prior_layer: int | None = None
        for record_index, record in enumerate(records):
            validated = _validate_record(record, f"block {block_id} record {record_index}")
            if prior_layer is not None and validated["layer_id"] <= prior_layer:
                raise RoutingPlanValidationError(f"block {block_id}: routing records must be strictly increasing by layer_id")
            prior_layer = validated["layer_id"]
            validated_records.append(validated)
            all_layers.append(validated["layer_id"])
            all_experts.update(validated["active_expert_ids"])
            target_key = ",".join(validated["target_nodes"])
            target_counts[target_key] = target_counts.get(target_key, 0) + 1

        payloads.append(
            {
                "block_id": block_id,
                "sequence": sequence,
                "routing_records": validated_records,
            }
        )

    sorted_target_counts = [
        {"target_nodes": key, "record_count": target_counts[key]}
        for key in sorted(target_counts)
    ]
    summary = {
        "block_count": len(payloads),
        "record_count": sum(len(payload["routing_records"]) for payload in payloads),
        "min_layer_id": min(all_layers),
        "max_layer_id": max(all_layers),
        "unique_expert_id_count": len(all_experts),
        "target_node_sets": [item["target_nodes"] for item in sorted_target_counts],
        "target_node_set_counts": sorted_target_counts,
    }
    return payloads, summary


def _validate_record(record: Any, label: str) -> dict[str, Any]:
    if not isinstance(record, dict):
        raise RoutingPlanValidationError(f"{label}: routing record must be an object")
    keys = tuple(record.keys())
    if keys != EXPECTED_RECORD_SHAPE:
        raise RoutingPlanValidationError(
            f"{label}: routing record fields must be exactly {', '.join(EXPECTED_RECORD_SHAPE)}"
        )

    layer_id = _required_int(record, "layer_id", label)
    if layer_id < 0 or layer_id >= EXPECTED_MODEL_LAYERS:
        raise RoutingPlanValidationError(f"{label}: layer_id must be in 0-93")

    active_expert_ids = _required_list(record, "active_expert_ids", label)
    if len(active_expert_ids) != EXPECTED_ACTIVE_EXPERTS:
        raise RoutingPlanValidationError(f"{label}: active_expert_ids must contain exactly 8 entries")
    expert_ids = [_validate_expert_id(value, label) for value in active_expert_ids]
    if len(set(expert_ids)) != len(expert_ids):
        raise RoutingPlanValidationError(f"{label}: active_expert_ids must be unique")

    weight_coefficients = _required_list(record, "weight_coefficients", label)
    if len(weight_coefficients) != EXPECTED_ACTIVE_EXPERTS:
        raise RoutingPlanValidationError(f"{label}: weight_coefficients must contain exactly 8 entries")
    weights = [_validate_weight(value, label) for value in weight_coefficients]

    target_nodes = _required_list(record, "target_nodes", label)
    validated_targets = _validate_target_nodes(target_nodes, label)

    return {
        "layer_id": layer_id,
        "active_expert_ids": expert_ids,
        "weight_coefficients": weights,
        "target_nodes": validated_targets,
    }


def _validate_expert_id(value: Any, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise RoutingPlanValidationError(f"{label}: expert IDs must be integers")
    if value < 0 or value >= EXPECTED_EXPERTS:
        raise RoutingPlanValidationError(f"{label}: expert IDs must be in 0-127")
    return value


def _validate_weight(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise RoutingPlanValidationError(f"{label}: weight coefficients must be numeric")
    weight = float(value)
    if not math.isfinite(weight):
        raise RoutingPlanValidationError(f"{label}: weight coefficients must be finite")
    if weight < -FLOAT_TOLERANCE or weight > 1.0 + FLOAT_TOLERANCE:
        raise RoutingPlanValidationError(f"{label}: weight coefficients must be in [0, 1]")
    return weight


def _validate_target_nodes(nodes: list[Any], label: str) -> list[str]:
    if not nodes:
        raise RoutingPlanValidationError(f"{label}: target_nodes must contain B, C, or both")
    if len(nodes) > len(EXPECTED_COMPUTE_WORKERS):
        raise RoutingPlanValidationError(f"{label}: target_nodes may only contain B, C, or both")
    validated: list[str] = []
    for node in nodes:
        if not isinstance(node, str):
            raise RoutingPlanValidationError(f"{label}: target_nodes entries must be strings")
        if node not in EXPECTED_COMPUTE_WORKERS:
            raise RoutingPlanValidationError(f"{label}: target_nodes must only contain B and/or C")
        if node in validated:
            raise RoutingPlanValidationError(f"{label}: target_nodes must not contain duplicates")
        validated.append(node)
    if validated == ["C", "B"]:
        raise RoutingPlanValidationError(f"{label}: target_nodes must use canonical B, C order")
    return validated


def _required_mapping(data: dict[str, Any], key: str, context: str) -> dict[str, Any]:
    value = data.get(key)
    if not isinstance(value, dict):
        raise RoutingPlanValidationError(f"{context}.{key} must be an object")
    return value


def _required_list(data: dict[str, Any], key: str, context: str) -> list[Any]:
    value = data.get(key)
    if not isinstance(value, list):
        raise RoutingPlanValidationError(f"{context}.{key} must be a list")
    return value


def _required_string(data: dict[str, Any], key: str, context: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value:
        raise RoutingPlanValidationError(f"{context}.{key} must be a non-empty string")
    return value


def _required_int(data: dict[str, Any], key: str, context: str) -> int:
    value = data.get(key)
    if isinstance(value, bool) or not isinstance(value, int):
        raise RoutingPlanValidationError(f"{context}.{key} must be an integer")
    return value


def _require_equal(actual: Any, expected: Any, field: str) -> None:
    if actual != expected:
        raise RoutingPlanValidationError(f"{field} must be {expected!r}; got {actual!r}")
