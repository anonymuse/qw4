"""Phase 1 PDD topology manifest validation for DS5-F001.

This module validates a narrow placement contract. It does not load model
weights, inspect tokenizer assets, or make throughput claims.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any


BYTES_PER_GB = 1_000_000_000
PLACEMENT_SCHEMA_VERSION = "ds5.pdd_placement.v1"
MEMORY_LEDGER_SCHEMA_VERSION = "ds5.pdd_memory_ledger.v1"
FEATURE_ID = "DS5-F001"
EVIDENCE_CLASS = "scaffold/planning"
EXPECTED_MODEL_NAME = "Qwen3-235B-A22B"
EXPECTED_MODEL_VARIANT = "Qwen3-235B-A22B-Instruct-2507"
EXPECTED_MODEL_LAYERS = 94
EXPECTED_MODEL_EXPERTS = 128
EXPECTED_MODEL_ACTIVE_EXPERTS = 8
EXPECTED_NODES = ("A", "B", "C")
EXPECTED_LAYER_RANGES = {
    "A": [],
    "B": [(0, 46)],
    "C": [(47, 93)],
}
EXPECTED_WORKER_MEMORY_GB = 48.0
EXPECTED_STATIC_CAP_GB = 33.6
EXPECTED_RUNTIME_HEADROOM_GB = 14.4
EXPECTED_STATIC_CAP_FRACTION = 0.70
EXPECTED_RUNTIME_HEADROOM_FRACTION = 0.30
FLOAT_TOLERANCE = 1e-6
MEMORY_EVIDENCE_SCHEMA_VERSION = "ds5.pdd_memory_evidence.v1"
BYTE_SOURCE_PLACEHOLDER_CAP_TEST = "placeholder_cap_test"
BYTE_SOURCE_MEASURED_RUNTIME = "measured_runtime"
BYTE_SOURCE_DERIVED_FROM_PINNED_TENSOR = "derived_from_pinned_tensor_metadata"
ALLOWED_BYTE_SOURCE_STATES = (
    BYTE_SOURCE_PLACEHOLDER_CAP_TEST,
    BYTE_SOURCE_MEASURED_RUNTIME,
    BYTE_SOURCE_DERIVED_FROM_PINNED_TENSOR,
)
MEMORY_BYTE_FIELDS = (
    "nodes[].static_memory.primary_moe_decode_bytes",
    "nodes[].static_memory.dense_decode_bytes",
    "nodes[].static_memory.router_gate_mirror_bytes",
    "nodes[].static_memory.other_static_bytes",
    "nodes[].static_memory.total_static_bytes",
)
CONTEXT_EVIDENCE_CLASS = "planning_only"
EXPECTED_FIRST_PERFORMANCE_CONTEXT_MIN_TOKENS = 8_192
EXPECTED_FIRST_PERFORMANCE_CONTEXT_MAX_TOKENS = 32_768
EXPECTED_STRETCH_CONTEXT_TOKENS = 65_536
EXPECTED_RESEARCH_ONLY_CONTEXT_MIN_TOKENS = 131_072
EXPECTED_RESEARCH_ONLY_CONTEXT_MAX_TOKENS = 262_144
TENSOR_POLICY_EVIDENCE_CLASS = "placeholder/planning"
EXPECTED_TENSOR_CLASS_POLICY_KEYS = (
    "router_gate",
    "attention",
    "hot_moe_experts",
    "cold_moe_experts",
    "kv_cache",
)
NODE_A_STEADY_STATE_CONSTRAINT = "forbidden_outside_correctness_mode"


class PlacementValidationError(ValueError):
    """Raised when a DS5-F001 placement manifest violates the Phase 1 contract."""


def load_manifest(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise PlacementValidationError("placement manifest root must be an object")
    return data


def validate_manifest(manifest: dict[str, Any], *, manifest_path: str | None = None) -> dict[str, Any]:
    """Validate a manifest and return the machine-readable memory ledger."""

    return build_memory_ledger(manifest, manifest_path=manifest_path)


def build_memory_ledger(manifest: dict[str, Any], *, manifest_path: str | None = None) -> dict[str, Any]:
    if not isinstance(manifest, dict):
        raise PlacementValidationError("placement manifest root must be an object")

    _require_equal(manifest.get("schema_version"), PLACEMENT_SCHEMA_VERSION, "schema_version")
    _require_equal(manifest.get("feature_id"), FEATURE_ID, "feature_id")

    model = _required_mapping(manifest, "model", "root")
    _validate_model(model)

    evidence_metadata = _required_mapping(manifest, "evidence_metadata", "root")
    memory_accounting = _validate_evidence_metadata(evidence_metadata)

    context_length_assumption = _validate_context_length_assumption(
        _required_mapping(manifest, "context_length_assumption", "root")
    )
    tensor_class_policy_placeholders = _validate_tensor_class_policy_placeholders(
        _required_mapping(manifest, "tensor_class_policy_placeholders", "root")
    )
    runtime_path_constraints = _validate_runtime_path_constraints(
        _required_mapping(manifest, "runtime_path_constraints", "root")
    )

    limits = _required_mapping(manifest, "limits", "root")
    _validate_limits(limits)

    artifact_policy = _required_mapping(manifest, "artifact_policy", "root")
    _require_equal(
        artifact_policy.get("memory_ledger_schema_version"),
        MEMORY_LEDGER_SCHEMA_VERSION,
        "artifact_policy.memory_ledger_schema_version",
    )
    default_ledger_path = _required_string(artifact_policy, "default_ledger_path", "artifact_policy")
    default_summary_path = _required_string(artifact_policy, "default_summary_path", "artifact_policy")

    nodes = _required_list(manifest, "nodes", "root")
    nodes_by_name = _index_nodes(nodes)
    ledger_nodes = [_validate_node(nodes_by_name[name], memory_accounting) for name in EXPECTED_NODES]
    _validate_layer_coverage(ledger_nodes)

    return {
        "schema_version": MEMORY_LEDGER_SCHEMA_VERSION,
        "feature_id": FEATURE_ID,
        "source_manifest": manifest_path,
        "model": {
            "name": EXPECTED_MODEL_NAME,
            "variant": EXPECTED_MODEL_VARIANT,
            "layers": EXPECTED_MODEL_LAYERS,
            "experts": EXPECTED_MODEL_EXPERTS,
            "active_experts": EXPECTED_MODEL_ACTIVE_EXPERTS,
        },
        "limits": {
            "byte_unit": "decimal_gb",
            "worker_memory_bytes": _gb_to_bytes(EXPECTED_WORKER_MEMORY_GB),
            "static_cap_fraction": EXPECTED_STATIC_CAP_FRACTION,
            "runtime_headroom_fraction": EXPECTED_RUNTIME_HEADROOM_FRACTION,
            "static_cap_bytes": _gb_to_bytes(EXPECTED_STATIC_CAP_GB),
            "runtime_headroom_bytes": _gb_to_bytes(EXPECTED_RUNTIME_HEADROOM_GB),
        },
        "artifact_policy": {
            "default_ledger_path": default_ledger_path,
            "default_summary_path": default_summary_path,
        },
        "evidence": {
            "class": EVIDENCE_CLASS,
            "measured_full_runtime": False,
            "source": "placement manifest constants and validator arithmetic",
            "memory_accounting": memory_accounting,
            "not_measured": [
                "Qwen model weights",
                "tokenizer assets",
                "speculative drafter",
                "primary-weight loader",
                "KV allocator",
                "Metal kernels",
                "startup, warmup, or decode runtime memory",
            ],
        },
        "context_length_assumption": context_length_assumption,
        "tensor_class_policy_placeholders": tensor_class_policy_placeholders,
        "runtime_path_constraints": runtime_path_constraints,
        "nodes": ledger_nodes,
        "validation": {
            "status": "pass",
            "checked_invariants": [
                "Qwen3-235B-A22B Instruct model identity constants",
                "exact A/B/C node set",
                "Node A owns 0 primary MoE decode bytes",
                "Node B owns inclusive decode layers 0-46",
                "Node C owns inclusive decode layers 47-93",
                "48GB workers keep 30% memory headroom",
                "48GB workers stay at or below a 33.6GB static cap",
                "memory byte evidence is machine-readable placeholder cap-test metadata",
                "context-length assumption is planning-only metadata",
                "tensor-class policy placeholders are present and not runtime implemented",
                "Node A is off the steady-state decode critical path outside correctness mode",
            ],
            "checked_claims": [
                _claim(
                    "Model constants match Qwen3-235B-A22B-Instruct-2507 with "
                    "94 layers, 128 experts, and 8 active experts"
                ),
                _claim("Node A primary MoE decode bytes are exactly 0"),
                _claim("Node B owns inclusive decode layers 0-46"),
                _claim("Node C owns inclusive decode layers 47-93"),
                _claim("Node B stays under the 33.6GB static cap and preserves 14.4GB runtime headroom"),
                _claim("Node C stays under the 33.6GB static cap and preserves 14.4GB runtime headroom"),
                _claim("Memory byte buckets are placeholder cap-test bytes, not measured or pinned-tensor-derived bytes"),
                _claim("Node A is forbidden from the steady-state decode critical path outside correctness mode"),
            ],
        },
        "limits_of_claim": list(manifest.get("limits_of_claim", [])),
    }


def write_memory_ledger(ledger: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(ledger, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_finding_summary(ledger: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(format_finding_summary(ledger), encoding="utf-8")


def format_ledger_summary(ledger: dict[str, Any]) -> str:
    memory_accounting = ledger["evidence"]["memory_accounting"]
    lines = [
        f"{FEATURE_ID} PDD topology manifest: PASS",
        f"Evidence: {ledger['evidence']['class']} (measured full runtime: no)",
        f"Memory bytes: {memory_accounting['byte_source_state']} "
        f"(measured runtime: {str(memory_accounting['measured_runtime']).lower()}, "
        f"pinned tensor derived: {str(memory_accounting['derived_from_pinned_tensor_metadata']).lower()})",
        f"Context assumption: {ledger['context_length_assumption']['evidence_class']}",
        f"Node A steady-state decode path: "
        f"{ledger['runtime_path_constraints']['node_a_steady_state_decode_critical_path']}",
        "",
        "Node  Layers    Primary MoE decode  Static total  Static cap  Static margin  Runtime headroom  Result",
    ]
    for node in ledger["nodes"]:
        layers = _format_layer_ranges(node["decode_layer_ranges"])
        result = "PASS" if node["passes_static_cap"] and node["passes_runtime_headroom"] else "FAIL"
        lines.append(
            f"{node['name']:<5} "
            f"{layers:<9} "
            f"{_fmt_gb(node['primary_moe_decode_bytes']):>18} "
            f"{_fmt_gb(node['total_static_bytes']):>13} "
            f"{_fmt_gb(node['static_cap_bytes']):>11} "
            f"{_fmt_gb(node['static_headroom_bytes']):>14} "
            f"{_fmt_gb(node['runtime_headroom_bytes']):>17} "
            f"{result}"
        )
    lines.extend(
        [
            "",
            "This is a topology and memory-budget scaffold only.",
            "It does not load Qwen weights, tokenizers, speculative drafters, or Metal kernels.",
        ]
    )
    return "\n".join(lines)


def format_finding_summary(ledger: dict[str, Any]) -> str:
    nodes = {node["name"]: node for node in ledger["nodes"]}
    memory_accounting = ledger["evidence"]["memory_accounting"]
    context_assumption = ledger["context_length_assumption"]
    runtime_constraints = ledger["runtime_path_constraints"]
    lines = [
        "# DS5-F001 PDD Topology Acceptance Summary",
        "",
        "Status: pass as scaffold/planning evidence. This is not measured full-runtime evidence.",
        "",
        "## Reproduction",
        "",
        "```bash",
        "make pdd-topology-validate",
        "```",
        "",
        "The command emits:",
        "",
        f"- `{ledger['artifact_policy']['default_ledger_path']}`",
        f"- `{ledger['artifact_policy']['default_summary_path']}`",
        "",
        "## Evidence Classification",
        "",
        "| Field | Value |",
        "|---|---|",
        f"| Evidence class | `{ledger['evidence']['class']}` |",
        f"| Measured full runtime | `{str(ledger['evidence']['measured_full_runtime']).lower()}` |",
        f"| Evidence source | {ledger['evidence']['source']} |",
        f"| Memory byte source state | `{memory_accounting['byte_source_state']}` |",
        f"| Placeholder cap-test bytes | `{str(memory_accounting['placeholder_cap_test']).lower()}` |",
        f"| Measured runtime bytes | `{str(memory_accounting['measured_runtime']).lower()}` |",
        f"| Derived from pinned tensor metadata | `{str(memory_accounting['derived_from_pinned_tensor_metadata']).lower()}` |",
        f"| Context assumption evidence | `{context_assumption['evidence_class']}` |",
        (
            "| Node A steady-state decode critical path | "
            f"`{runtime_constraints['node_a_steady_state_decode_critical_path']}` |"
        ),
        "",
        "This summary validates placement-manifest constants and memory-budget arithmetic only. It does not "
        "load Qwen weights, tokenizer assets, a speculative drafter, a primary-weight loader, a KV allocator, "
        "or Metal kernels.",
        "",
        "## Acceptance Checks",
        "",
        "| Claim | Ledger evidence | Result | Evidence class |",
        "|---|---|---:|---|",
        (
            "| Model constants match Qwen3-235B-A22B-Instruct-2507 "
            f"| `layers = {ledger['model']['layers']}`; "
            f"`experts = {ledger['model']['experts']}`; "
            f"`active_experts = {ledger['model']['active_experts']}` "
            "| PASS "
            f"| `{EVIDENCE_CLASS}` |"
        ),
        (
            "| Node A primary MoE decode bytes are exactly 0 "
            f"| `nodes.A.primary_moe_decode_bytes = {nodes['A']['primary_moe_decode_bytes']}` "
            "| PASS "
            f"| `{EVIDENCE_CLASS}` |"
        ),
        (
            "| Node B owns layers 0-46 "
            f"| `nodes.B.decode_layer_ranges = {_format_layer_ranges(nodes['B']['decode_layer_ranges'])}` "
            "| PASS "
            f"| `{EVIDENCE_CLASS}` |"
        ),
        (
            "| Node C owns layers 47-93 "
            f"| `nodes.C.decode_layer_ranges = {_format_layer_ranges(nodes['C']['decode_layer_ranges'])}` "
            "| PASS "
            f"| `{EVIDENCE_CLASS}` |"
        ),
        (
            "| Node B stays under 33.6GB static cap and preserves 14.4GB runtime headroom "
            f"| `{_fmt_gb(nodes['B']['total_static_bytes'])} <= {_fmt_gb(nodes['B']['static_cap_bytes'])}`; "
            f"`runtime_headroom = {_fmt_gb(nodes['B']['runtime_headroom_bytes'])}` "
            "| PASS "
            f"| `{EVIDENCE_CLASS}` |"
        ),
        (
            "| Node C stays under 33.6GB static cap and preserves 14.4GB runtime headroom "
            f"| `{_fmt_gb(nodes['C']['total_static_bytes'])} <= {_fmt_gb(nodes['C']['static_cap_bytes'])}`; "
            f"`runtime_headroom = {_fmt_gb(nodes['C']['runtime_headroom_bytes'])}` "
            "| PASS "
            f"| `{EVIDENCE_CLASS}` |"
        ),
        (
            "| Memory byte buckets are placeholder cap-test bytes "
            f"| `byte_source_state = {memory_accounting['byte_source_state']}`; "
            f"`measured_runtime = {str(memory_accounting['measured_runtime']).lower()}`; "
            f"`derived_from_pinned_tensor_metadata = "
            f"{str(memory_accounting['derived_from_pinned_tensor_metadata']).lower()}` "
            "| PASS "
            f"| `{EVIDENCE_CLASS}` |"
        ),
        (
            "| Node A stays off the steady-state decode critical path outside correctness mode "
            "| `node_a_steady_state_decode_critical_path = "
            f"{runtime_constraints['node_a_steady_state_decode_critical_path']}` "
            "| PASS "
            f"| `{EVIDENCE_CLASS}` |"
        ),
        "",
        "## Memory Ledger Summary",
        "",
        "| Node | Decode layers | Primary MoE decode bytes | Static total | Static cap | Static margin | Runtime headroom | Byte source state | Evidence class |",
        "|---|---|---:|---:|---:|---:|---:|---|---|",
    ]

    for node in ledger["nodes"]:
        lines.append(
            f"| {node['name']} "
            f"| {_format_layer_ranges(node['decode_layer_ranges'])} "
            f"| {node['primary_moe_decode_bytes']} "
            f"| {_fmt_gb(node['total_static_bytes'])} "
            f"| {_fmt_gb(node['static_cap_bytes'])} "
            f"| {_fmt_gb(node['static_headroom_bytes'])} "
            f"| {_fmt_gb(node['runtime_headroom_bytes'])} "
            f"| `{node['byte_source_state']}` "
            f"| `{node['evidence_class']}` |"
        )

    lines.extend(
        [
            "",
            "## Planning Assumptions",
            "",
            "| Field | Value |",
            "|---|---|",
            f"| Context evidence class | `{context_assumption['evidence_class']}` |",
            f"| Runtime validated | `{str(context_assumption['runtime_validated']).lower()}` |",
            (
                "| First performance context tokens | "
                f"`{context_assumption['first_performance_context_tokens']['min']}`-"
                f"`{context_assumption['first_performance_context_tokens']['max']}` |"
            ),
            f"| Stretch context tokens | `{context_assumption['stretch_context_tokens']}` |",
            (
                "| Research-only context tokens | "
                f"`{context_assumption['research_only_context_tokens']['min']}`-"
                f"`{context_assumption['research_only_context_tokens']['max']}` |"
            ),
            "",
            "## Tensor-Class Policy Placeholders",
            "",
            "| Tensor class | Runtime implemented | Policy placeholder |",
            "|---|---:|---|",
        ]
    )
    for key in EXPECTED_TENSOR_CLASS_POLICY_KEYS:
        policy = ledger["tensor_class_policy_placeholders"][key]
        lines.append(
            f"| `{key}` | `{str(policy['runtime_implemented']).lower()}` | {policy['policy']} |"
        )

    lines.extend(
        [
            "",
            "## Runtime Path Constraints",
            "",
            "| Constraint | Value |",
            "|---|---|",
            (
                "| Node A steady-state decode critical path | "
                f"`{runtime_constraints['node_a_steady_state_decode_critical_path']}` |"
            ),
            (
                "| Correctness-mode Node A routing allowed | "
                f"`{str(runtime_constraints['correctness_mode_node_a_routing_allowed']).lower()}` |"
            ),
            (
                "| Performance mode requires B/C local router mirrors | "
                f"`{str(runtime_constraints['performance_mode_requires_bc_local_router_mirrors']).lower()}` |"
            ),
            (
                "| Steady-state decode runtime implemented | "
                f"`{str(runtime_constraints['steady_state_decode_runtime_implemented']).lower()}` |"
            ),
            "",
            "## Limits Of Claim",
            "",
        ]
    )
    for limit in ledger["limits_of_claim"]:
        lines.append(f"- {limit}")
    lines.append("")
    return "\n".join(lines)


def _validate_model(model: dict[str, Any]) -> None:
    _require_equal(model.get("name"), EXPECTED_MODEL_NAME, "model.name")
    _require_equal(model.get("variant"), EXPECTED_MODEL_VARIANT, "model.variant")
    _require_equal(model.get("layers"), EXPECTED_MODEL_LAYERS, "model.layers")
    _require_equal(model.get("experts"), EXPECTED_MODEL_EXPERTS, "model.experts")
    _require_equal(
        model.get("active_experts"),
        EXPECTED_MODEL_ACTIVE_EXPERTS,
        "model.active_experts",
    )


def _validate_evidence_metadata(evidence_metadata: dict[str, Any]) -> dict[str, Any]:
    _require_equal(
        evidence_metadata.get("schema_version"),
        MEMORY_EVIDENCE_SCHEMA_VERSION,
        "evidence_metadata.schema_version",
    )
    memory_accounting = _required_mapping(evidence_metadata, "memory_accounting", "evidence_metadata")
    byte_source_state = _required_string(
        memory_accounting,
        "byte_source_state",
        "evidence_metadata.memory_accounting",
    )
    if byte_source_state not in ALLOWED_BYTE_SOURCE_STATES:
        raise PlacementValidationError(
            "evidence_metadata.memory_accounting.byte_source_state must be one of "
            f"{list(ALLOWED_BYTE_SOURCE_STATES)!r}"
        )
    allowed_states = _required_string_list(
        memory_accounting,
        "allowed_byte_source_states",
        "evidence_metadata.memory_accounting",
    )
    if tuple(allowed_states) != ALLOWED_BYTE_SOURCE_STATES:
        raise PlacementValidationError(
            "evidence_metadata.memory_accounting.allowed_byte_source_states must be "
            f"{list(ALLOWED_BYTE_SOURCE_STATES)!r}"
        )
    applies_to_fields = _required_string_list(
        memory_accounting,
        "applies_to_fields",
        "evidence_metadata.memory_accounting",
    )
    if tuple(applies_to_fields) != MEMORY_BYTE_FIELDS:
        raise PlacementValidationError(
            "evidence_metadata.memory_accounting.applies_to_fields must enumerate static memory byte fields"
        )
    placeholder_cap_test = _required_bool(
        memory_accounting,
        "placeholder_cap_test",
        "evidence_metadata.memory_accounting",
    )
    measured_runtime = _required_bool(
        memory_accounting,
        "measured_runtime",
        "evidence_metadata.memory_accounting",
    )
    derived_from_pinned_tensor_metadata = _required_bool(
        memory_accounting,
        "derived_from_pinned_tensor_metadata",
        "evidence_metadata.memory_accounting",
    )
    if byte_source_state == BYTE_SOURCE_PLACEHOLDER_CAP_TEST:
        if not placeholder_cap_test or measured_runtime or derived_from_pinned_tensor_metadata:
            raise PlacementValidationError(
                "placeholder cap-test bytes must set placeholder_cap_test=true and "
                "measured_runtime=false and derived_from_pinned_tensor_metadata=false"
            )
    elif byte_source_state == BYTE_SOURCE_MEASURED_RUNTIME:
        if placeholder_cap_test or not measured_runtime or derived_from_pinned_tensor_metadata:
            raise PlacementValidationError(
                "measured runtime bytes must set measured_runtime=true only"
            )
    elif byte_source_state == BYTE_SOURCE_DERIVED_FROM_PINNED_TENSOR:
        if placeholder_cap_test or measured_runtime or not derived_from_pinned_tensor_metadata:
            raise PlacementValidationError(
                "pinned tensor derived bytes must set derived_from_pinned_tensor_metadata=true only"
            )
    source_detail = _required_string(
        memory_accounting,
        "source_detail",
        "evidence_metadata.memory_accounting",
    )
    return {
        "schema_version": MEMORY_EVIDENCE_SCHEMA_VERSION,
        "byte_source_state": byte_source_state,
        "allowed_byte_source_states": list(ALLOWED_BYTE_SOURCE_STATES),
        "applies_to_fields": list(MEMORY_BYTE_FIELDS),
        "placeholder_cap_test": placeholder_cap_test,
        "measured_runtime": measured_runtime,
        "derived_from_pinned_tensor_metadata": derived_from_pinned_tensor_metadata,
        "source_detail": source_detail,
    }


def _validate_context_length_assumption(context: dict[str, Any]) -> dict[str, Any]:
    _require_equal(
        context.get("evidence_class"),
        CONTEXT_EVIDENCE_CLASS,
        "context_length_assumption.evidence_class",
    )
    runtime_validated = _required_bool(context, "runtime_validated", "context_length_assumption")
    if runtime_validated:
        raise PlacementValidationError("context_length_assumption.runtime_validated must be false")
    first_performance = _required_mapping(
        context,
        "first_performance_context_tokens",
        "context_length_assumption",
    )
    _require_equal(
        _required_nonnegative_int(
            first_performance,
            "min",
            "context_length_assumption.first_performance_context_tokens",
        ),
        EXPECTED_FIRST_PERFORMANCE_CONTEXT_MIN_TOKENS,
        "context_length_assumption.first_performance_context_tokens.min",
    )
    _require_equal(
        _required_nonnegative_int(
            first_performance,
            "max",
            "context_length_assumption.first_performance_context_tokens",
        ),
        EXPECTED_FIRST_PERFORMANCE_CONTEXT_MAX_TOKENS,
        "context_length_assumption.first_performance_context_tokens.max",
    )
    stretch_context_tokens = _required_nonnegative_int(
        context,
        "stretch_context_tokens",
        "context_length_assumption",
    )
    _require_equal(
        stretch_context_tokens,
        EXPECTED_STRETCH_CONTEXT_TOKENS,
        "context_length_assumption.stretch_context_tokens",
    )
    research_only = _required_mapping(
        context,
        "research_only_context_tokens",
        "context_length_assumption",
    )
    _require_equal(
        _required_nonnegative_int(
            research_only,
            "min",
            "context_length_assumption.research_only_context_tokens",
        ),
        EXPECTED_RESEARCH_ONLY_CONTEXT_MIN_TOKENS,
        "context_length_assumption.research_only_context_tokens.min",
    )
    _require_equal(
        _required_nonnegative_int(
            research_only,
            "max",
            "context_length_assumption.research_only_context_tokens",
        ),
        EXPECTED_RESEARCH_ONLY_CONTEXT_MAX_TOKENS,
        "context_length_assumption.research_only_context_tokens.max",
    )
    source = _required_string(context, "source", "context_length_assumption")
    return {
        "evidence_class": CONTEXT_EVIDENCE_CLASS,
        "runtime_validated": False,
        "first_performance_context_tokens": {
            "min": EXPECTED_FIRST_PERFORMANCE_CONTEXT_MIN_TOKENS,
            "max": EXPECTED_FIRST_PERFORMANCE_CONTEXT_MAX_TOKENS,
        },
        "stretch_context_tokens": EXPECTED_STRETCH_CONTEXT_TOKENS,
        "research_only_context_tokens": {
            "min": EXPECTED_RESEARCH_ONLY_CONTEXT_MIN_TOKENS,
            "max": EXPECTED_RESEARCH_ONLY_CONTEXT_MAX_TOKENS,
        },
        "source": source,
    }


def _validate_tensor_class_policy_placeholders(policies: dict[str, Any]) -> dict[str, Any]:
    keys = tuple(policies.keys())
    if keys != EXPECTED_TENSOR_CLASS_POLICY_KEYS:
        raise PlacementValidationError(
            "tensor_class_policy_placeholders must contain exactly "
            f"{list(EXPECTED_TENSOR_CLASS_POLICY_KEYS)!r}"
        )
    validated: dict[str, Any] = {}
    for key in EXPECTED_TENSOR_CLASS_POLICY_KEYS:
        policy = _required_mapping(policies, key, "tensor_class_policy_placeholders")
        _require_equal(
            policy.get("evidence_class"),
            TENSOR_POLICY_EVIDENCE_CLASS,
            f"tensor_class_policy_placeholders.{key}.evidence_class",
        )
        runtime_implemented = _required_bool(
            policy,
            "runtime_implemented",
            f"tensor_class_policy_placeholders.{key}",
        )
        if runtime_implemented:
            raise PlacementValidationError(
                f"tensor_class_policy_placeholders.{key}.runtime_implemented must be false"
            )
        validated[key] = {
            "evidence_class": TENSOR_POLICY_EVIDENCE_CLASS,
            "runtime_implemented": False,
            "policy": _required_string(
                policy,
                "policy",
                f"tensor_class_policy_placeholders.{key}",
            ),
            "notes": _required_string_list(
                policy,
                "notes",
                f"tensor_class_policy_placeholders.{key}",
            ),
        }
    return validated


def _validate_runtime_path_constraints(constraints: dict[str, Any]) -> dict[str, Any]:
    _require_equal(
        constraints.get("node_a_steady_state_decode_critical_path"),
        NODE_A_STEADY_STATE_CONSTRAINT,
        "runtime_path_constraints.node_a_steady_state_decode_critical_path",
    )
    correctness_mode_allowed = _required_bool(
        constraints,
        "correctness_mode_node_a_routing_allowed",
        "runtime_path_constraints",
    )
    if not correctness_mode_allowed:
        raise PlacementValidationError(
            "runtime_path_constraints.correctness_mode_node_a_routing_allowed must be true"
        )
    bc_local_router_mirrors = _required_bool(
        constraints,
        "performance_mode_requires_bc_local_router_mirrors",
        "runtime_path_constraints",
    )
    if not bc_local_router_mirrors:
        raise PlacementValidationError(
            "runtime_path_constraints.performance_mode_requires_bc_local_router_mirrors must be true"
        )
    steady_state_decode_runtime_implemented = _required_bool(
        constraints,
        "steady_state_decode_runtime_implemented",
        "runtime_path_constraints",
    )
    if steady_state_decode_runtime_implemented:
        raise PlacementValidationError(
            "runtime_path_constraints.steady_state_decode_runtime_implemented must be false"
        )
    node_a_allowed_roles = _required_string_list(
        constraints,
        "node_a_allowed_decode_roles",
        "runtime_path_constraints",
    )
    return {
        "node_a_steady_state_decode_critical_path": NODE_A_STEADY_STATE_CONSTRAINT,
        "correctness_mode_node_a_routing_allowed": True,
        "performance_mode_requires_bc_local_router_mirrors": True,
        "steady_state_decode_runtime_implemented": False,
        "node_a_allowed_decode_roles": node_a_allowed_roles,
    }


def _validate_limits(limits: dict[str, Any]) -> None:
    _require_equal(limits.get("byte_unit"), "decimal_gb", "limits.byte_unit")
    _require_close(limits.get("worker_memory_gb"), EXPECTED_WORKER_MEMORY_GB, "limits.worker_memory_gb")
    _require_close(limits.get("static_cap_fraction"), EXPECTED_STATIC_CAP_FRACTION, "limits.static_cap_fraction")
    _require_close(
        limits.get("runtime_headroom_fraction"),
        EXPECTED_RUNTIME_HEADROOM_FRACTION,
        "limits.runtime_headroom_fraction",
    )
    _require_close(limits.get("static_cap_gb"), EXPECTED_STATIC_CAP_GB, "limits.static_cap_gb")
    _require_close(
        limits.get("runtime_headroom_gb"),
        EXPECTED_RUNTIME_HEADROOM_GB,
        "limits.runtime_headroom_gb",
    )


def _index_nodes(nodes: list[Any]) -> dict[str, dict[str, Any]]:
    if len(nodes) != len(EXPECTED_NODES):
        raise PlacementValidationError("nodes must contain exactly A, B, and C")
    indexed: dict[str, dict[str, Any]] = {}
    for item in nodes:
        if not isinstance(item, dict):
            raise PlacementValidationError("nodes entries must be objects")
        name = str(item.get("name", "")).strip()
        if name in indexed:
            raise PlacementValidationError(f"duplicate node {name!r}")
        indexed[name] = item
    missing = [name for name in EXPECTED_NODES if name not in indexed]
    extra = [name for name in indexed if name not in EXPECTED_NODES]
    if missing or extra:
        raise PlacementValidationError(
            f"nodes must contain exactly A, B, and C; missing={missing}, extra={extra}"
        )
    return indexed


def _validate_node(node: dict[str, Any], memory_accounting: dict[str, Any]) -> dict[str, Any]:
    name = str(node["name"])
    memory_gb = _required_number(node, "memory_gb", f"node {name}")
    static_cap_gb = _required_number(node, "static_cap_gb", f"node {name}")
    runtime_headroom_gb = _required_number(node, "runtime_headroom_gb", f"node {name}")

    _require_close(memory_gb, EXPECTED_WORKER_MEMORY_GB, f"node {name}.memory_gb")
    _require_close(static_cap_gb, EXPECTED_STATIC_CAP_GB, f"node {name}.static_cap_gb")
    _require_close(runtime_headroom_gb, EXPECTED_RUNTIME_HEADROOM_GB, f"node {name}.runtime_headroom_gb")

    ranges = _parse_layer_ranges(node, name)
    expected_ranges = EXPECTED_LAYER_RANGES[name]
    if ranges != expected_ranges:
        expected = _format_layer_ranges_from_tuples(expected_ranges)
        actual = _format_layer_ranges_from_tuples(ranges)
        raise PlacementValidationError(
            f"node {name}: decode layer ranges must be exactly {expected}; got {actual}"
        )

    owns_primary = _required_bool(node, "owns_primary_moe_decode", f"node {name}")
    if name == "A" and owns_primary:
        raise PlacementValidationError("node A: owns_primary_moe_decode must be false")
    if name in {"B", "C"} and not owns_primary:
        raise PlacementValidationError(f"node {name}: owns_primary_moe_decode must be true")

    static_memory = _required_mapping(node, "static_memory", f"node {name}")
    primary_moe_decode_bytes = _required_nonnegative_int(
        static_memory, "primary_moe_decode_bytes", f"node {name}.static_memory"
    )
    dense_decode_bytes = _required_nonnegative_int(
        static_memory, "dense_decode_bytes", f"node {name}.static_memory"
    )
    router_gate_mirror_bytes = _required_nonnegative_int(
        static_memory, "router_gate_mirror_bytes", f"node {name}.static_memory"
    )
    other_static_bytes = _required_nonnegative_int(
        static_memory, "other_static_bytes", f"node {name}.static_memory"
    )
    total_static_bytes = _required_nonnegative_int(
        static_memory, "total_static_bytes", f"node {name}.static_memory"
    )

    if name == "A" and primary_moe_decode_bytes != 0:
        raise PlacementValidationError("node A: primary_moe_decode_bytes must be 0")
    if name in {"B", "C"} and primary_moe_decode_bytes <= 0:
        raise PlacementValidationError(f"node {name}: primary_moe_decode_bytes must be positive")

    component_total = (
        primary_moe_decode_bytes + dense_decode_bytes + router_gate_mirror_bytes + other_static_bytes
    )
    if total_static_bytes != component_total:
        raise PlacementValidationError(
            f"node {name}: total_static_bytes must equal component byte sum {component_total}"
        )

    memory_bytes = _gb_to_bytes(memory_gb)
    static_cap_bytes = _gb_to_bytes(static_cap_gb)
    runtime_headroom_bytes = _gb_to_bytes(runtime_headroom_gb)
    expected_headroom_bytes = math.ceil(memory_bytes * EXPECTED_RUNTIME_HEADROOM_FRACTION)
    passes_runtime_headroom = runtime_headroom_bytes >= expected_headroom_bytes
    if not passes_runtime_headroom:
        raise PlacementValidationError(
            f"node {name}: runtime headroom must be at least 30% of memory "
            f"({expected_headroom_bytes} bytes)"
        )
    expected_static_cap_bytes = _gb_to_bytes(EXPECTED_STATIC_CAP_GB)
    if static_cap_bytes != expected_static_cap_bytes:
        raise PlacementValidationError(
            f"node {name}: 48GB worker static cap must be {expected_static_cap_bytes} bytes"
        )
    if total_static_bytes > static_cap_bytes:
        raise PlacementValidationError(
            f"node {name}: total_static_bytes {total_static_bytes} exceeds static cap {static_cap_bytes}"
        )

    return {
        "name": name,
        "role": str(node.get("role", "")),
        "memory_bytes": memory_bytes,
        "static_cap_bytes": static_cap_bytes,
        "runtime_headroom_bytes": runtime_headroom_bytes,
        "runtime_headroom_required_bytes": expected_headroom_bytes,
        "decode_layer_ranges": [{"start": start, "end": end} for start, end in ranges],
        "owns_primary_moe_decode": owns_primary,
        "primary_moe_decode_bytes": primary_moe_decode_bytes,
        "dense_decode_bytes": dense_decode_bytes,
        "router_gate_mirror_bytes": router_gate_mirror_bytes,
        "other_static_bytes": other_static_bytes,
        "total_static_bytes": total_static_bytes,
        "static_headroom_bytes": static_cap_bytes - total_static_bytes,
        "passes_static_cap": total_static_bytes <= static_cap_bytes,
        "passes_runtime_headroom": passes_runtime_headroom,
        "byte_source_state": memory_accounting["byte_source_state"],
        "memory_accounting": {
            "byte_source_state": memory_accounting["byte_source_state"],
            "placeholder_cap_test": memory_accounting["placeholder_cap_test"],
            "measured_runtime": memory_accounting["measured_runtime"],
            "derived_from_pinned_tensor_metadata": memory_accounting[
                "derived_from_pinned_tensor_metadata"
            ],
        },
        "evidence_class": EVIDENCE_CLASS,
        "measured_full_runtime": False,
        "notes": list(node.get("notes", [])),
    }


def _parse_layer_ranges(node: dict[str, Any], node_name: str) -> list[tuple[int, int]]:
    raw_ranges = _required_list(node, "decode_layer_ranges", f"node {node_name}")
    ranges: list[tuple[int, int]] = []
    for item in raw_ranges:
        if not isinstance(item, dict):
            raise PlacementValidationError(f"node {node_name}: layer range entries must be objects")
        start = _required_nonnegative_int(item, "start", f"node {node_name}.decode_layer_ranges")
        end = _required_nonnegative_int(item, "end", f"node {node_name}.decode_layer_ranges")
        if start > end:
            raise PlacementValidationError(f"node {node_name}: layer range start must be <= end")
        if end >= EXPECTED_MODEL_LAYERS:
            raise PlacementValidationError(
                f"node {node_name}: layer range end must be < {EXPECTED_MODEL_LAYERS}"
            )
        ranges.append((start, end))
    return ranges


def _validate_layer_coverage(ledger_nodes: list[dict[str, Any]]) -> None:
    seen: dict[int, str] = {}
    for node in ledger_nodes:
        for item in node["decode_layer_ranges"]:
            for layer in range(item["start"], item["end"] + 1):
                if layer in seen:
                    raise PlacementValidationError(
                        f"decode layer {layer} is assigned to both {seen[layer]} and {node['name']}"
                    )
                seen[layer] = node["name"]
    expected_layers = set(range(EXPECTED_MODEL_LAYERS))
    missing = sorted(expected_layers - set(seen))
    extra = sorted(set(seen) - expected_layers)
    if missing or extra:
        raise PlacementValidationError(
            f"decode layers must cover 0-{EXPECTED_MODEL_LAYERS - 1}; missing={missing}, extra={extra}"
        )


def _required_mapping(data: dict[str, Any], key: str, parent: str) -> dict[str, Any]:
    value = data.get(key)
    if not isinstance(value, dict):
        raise PlacementValidationError(f"{parent}: missing object {key!r}")
    return value


def _required_list(data: dict[str, Any], key: str, parent: str) -> list[Any]:
    value = data.get(key)
    if not isinstance(value, list):
        raise PlacementValidationError(f"{parent}: missing list {key!r}")
    return value


def _required_number(data: dict[str, Any], key: str, parent: str) -> int | float:
    value = data.get(key)
    if not isinstance(value, (int, float)):
        raise PlacementValidationError(f"{parent}: missing number {key!r}")
    return value


def _required_string(data: dict[str, Any], key: str, parent: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value:
        raise PlacementValidationError(f"{parent}: missing string {key!r}")
    return value


def _required_string_list(data: dict[str, Any], key: str, parent: str) -> list[str]:
    values = _required_list(data, key, parent)
    strings: list[str] = []
    for value in values:
        if not isinstance(value, str) or not value:
            raise PlacementValidationError(f"{parent}: {key} must contain non-empty strings")
        strings.append(value)
    return strings


def _required_nonnegative_int(data: dict[str, Any], key: str, parent: str) -> int:
    value = data.get(key)
    if not isinstance(value, int) or value < 0:
        raise PlacementValidationError(f"{parent}: {key} must be a non-negative integer")
    return value


def _required_bool(data: dict[str, Any], key: str, parent: str) -> bool:
    value = data.get(key)
    if not isinstance(value, bool):
        raise PlacementValidationError(f"{parent}: {key} must be a boolean")
    return value


def _require_equal(actual: Any, expected: Any, field: str) -> None:
    if actual != expected:
        raise PlacementValidationError(f"{field} must be {expected!r}, got {actual!r}")


def _require_close(actual: Any, expected: float, field: str) -> None:
    if not isinstance(actual, (int, float)):
        raise PlacementValidationError(f"{field} must be numeric, got {actual!r}")
    if not math.isclose(float(actual), expected, rel_tol=0.0, abs_tol=FLOAT_TOLERANCE):
        raise PlacementValidationError(f"{field} must be {expected:g}, got {actual!r}")


def _gb_to_bytes(gb_value: int | float) -> int:
    return int(round(float(gb_value) * BYTES_PER_GB))


def _fmt_gb(byte_count: int | float) -> str:
    return f"{byte_count / BYTES_PER_GB:.2f}GB"


def _format_layer_ranges(ranges: list[dict[str, int]]) -> str:
    if not ranges:
        return "none"
    return ",".join(f"{item['start']}-{item['end']}" for item in ranges)


def _format_layer_ranges_from_tuples(ranges: list[tuple[int, int]]) -> str:
    if not ranges:
        return "none"
    return ",".join(f"{start}-{end}" for start, end in ranges)


def _claim(description: str) -> dict[str, Any]:
    return {
        "description": description,
        "evidence_class": EVIDENCE_CLASS,
        "measured_full_runtime": False,
    }
