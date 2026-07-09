"""Deterministic Qwen3 planning memory estimator.

This module intentionally works from local planning metadata only. It does not
download, mmap, or parse model weight files.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import math
from pathlib import Path
from typing import Any


BYTES_PER_GB = 1_000_000_000
BYTES_PER_GIB = 1024**3


class ConfigError(ValueError):
    """Raised when the planning config is incomplete or inconsistent."""


@dataclass(frozen=True)
class QuantClass:
    name: str
    bits_per_parameter: float
    block_size: int | None = None
    metadata_bytes_per_block: float = 0.0
    description: str = ""

    @classmethod
    def from_config(cls, name: str, data: dict[str, Any]) -> "QuantClass":
        bits = _required_number(data, "bits_per_parameter", f"quant class {name}")
        block_size = data.get("block_size")
        if block_size is not None:
            if not isinstance(block_size, int) or block_size <= 0:
                raise ConfigError(f"quant class {name}: block_size must be a positive integer or null")
        metadata_bytes = float(data.get("metadata_bytes_per_block", 0.0))
        if metadata_bytes < 0:
            raise ConfigError(f"quant class {name}: metadata_bytes_per_block must be non-negative")
        return cls(
            name=name,
            bits_per_parameter=float(bits),
            block_size=block_size,
            metadata_bytes_per_block=metadata_bytes,
            description=str(data.get("description", "")),
        )

    def estimate_bytes(self, parameters: int) -> dict[str, int | float]:
        if parameters < 0:
            raise ConfigError(f"cannot estimate negative parameter count for quant class {self.name}")
        payload_bytes = math.ceil(parameters * self.bits_per_parameter / 8.0)
        if self.block_size:
            blocks = math.ceil(parameters / self.block_size)
            metadata_bytes = math.ceil(blocks * self.metadata_bytes_per_block)
        else:
            blocks = 0
            metadata_bytes = 0
        return {
            "payload_bytes": payload_bytes,
            "metadata_bytes": metadata_bytes,
            "block_count": blocks,
            "total_bytes": payload_bytes + metadata_bytes,
            "effective_bits_per_parameter": (
                ((payload_bytes + metadata_bytes) * 8.0 / parameters) if parameters else 0.0
            ),
        }


@dataclass(frozen=True)
class NodeConfig:
    name: str
    role: str
    memory_bytes: int
    static_cap_bytes: int
    runtime_reserve_bytes: int
    static_fraction: float
    kv_fraction: float

    @classmethod
    def from_config(cls, data: dict[str, Any]) -> "NodeConfig":
        name = str(data.get("name", "")).strip()
        if not name:
            raise ConfigError("node is missing name")
        return cls(
            name=name,
            role=str(data.get("role", "")),
            memory_bytes=_gb_to_bytes(_required_number(data, "memory_gb", f"node {name}")),
            static_cap_bytes=_gb_to_bytes(_required_number(data, "static_cap_gb", f"node {name}")),
            runtime_reserve_bytes=_gb_to_bytes(
                _required_number(data, "runtime_reserve_gb", f"node {name}")
            ),
            static_fraction=float(data.get("static_fraction", 0.0)),
            kv_fraction=float(data.get("kv_fraction", 0.0)),
        )


@dataclass(frozen=True)
class DerivedParameters:
    total: int
    activated: int
    dense_shared: int
    moe_experts: int
    router_gate: int
    dense_shared_minus_router_gate: int
    active_expert_ratio: float

    def to_json(self) -> dict[str, Any]:
        return {
            "total": self.total,
            "activated": self.activated,
            "dense_shared": self.dense_shared,
            "moe_experts": self.moe_experts,
            "router_gate": self.router_gate,
            "dense_shared_minus_router_gate": self.dense_shared_minus_router_gate,
            "active_expert_ratio": self.active_expert_ratio,
            "derivation": (
                "activated = dense_shared + moe_experts * (active_experts / experts); "
                "total = dense_shared + moe_experts"
            ),
        }


def load_config(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def estimate_from_config(config: dict[str, Any], *, config_path: str | None = None) -> dict[str, Any]:
    model = _required_mapping(config, "model", "root")
    nodes = [NodeConfig.from_config(item) for item in _required_list(config, "nodes", "root")]
    if not nodes:
        raise ConfigError("at least one node is required")

    quant_config = _required_mapping(_required_mapping(config, "quantization", "root"), "classes", "quantization")
    quant_classes = {
        name: QuantClass.from_config(name, item)
        for name, item in quant_config.items()
        if isinstance(item, dict)
    }
    if not quant_classes:
        raise ConfigError("quantization.classes must contain at least one class")

    derived = _derive_parameters(model)
    static_groups = _required_list(config, "static_weight_groups", "root")
    overheads = config.get("overheads", {})
    if not isinstance(overheads, dict):
        raise ConfigError("overheads must be an object when present")
    static_margin_fraction = float(overheads.get("static_safety_margin_fraction", 0.0))
    if static_margin_fraction < 0:
        raise ConfigError("overheads.static_safety_margin_fraction must be non-negative")
    per_group_alignment_bytes = _parse_bytes(overheads.get("per_group_alignment_bytes", 0))

    static_result = _estimate_static(
        static_groups=static_groups,
        nodes=nodes,
        quant_classes=quant_classes,
        derived=derived,
        static_margin_fraction=static_margin_fraction,
        per_group_alignment_bytes=per_group_alignment_bytes,
    )
    kv_result = _estimate_kv(config=config, model=model, nodes=nodes)

    generated_assumptions = _generated_unresolved_assumptions()
    configured_assumptions = config.get("unresolved_assumptions", [])
    if configured_assumptions and not isinstance(configured_assumptions, list):
        raise ConfigError("unresolved_assumptions must be a list when present")

    return {
        "schema_version": config.get("schema_version"),
        "config_path": config_path,
        "model": model,
        "quant_classes": {
            name: {
                "bits_per_parameter": qc.bits_per_parameter,
                "block_size": qc.block_size,
                "metadata_bytes_per_block": qc.metadata_bytes_per_block,
                "description": qc.description,
            }
            for name, qc in quant_classes.items()
        },
        "derived_parameters": derived.to_json(),
        "static": static_result,
        "kv_cache": kv_result,
        "unresolved_assumptions": _dedupe_strings(
            [str(item) for item in configured_assumptions] + generated_assumptions
        ),
    }


def format_human_summary(result: dict[str, Any]) -> str:
    model = result["model"]
    static_nodes = result["static"]["nodes"]
    kv_contexts = result["kv_cache"]["contexts"]
    derived = result["derived_parameters"]

    lines: list[str] = []
    lines.append(f"Qwen3 planning memory estimate: {model.get('name', 'unknown model')}")
    if model.get("variant"):
        lines.append(f"Variant: {model['variant']}")
    if result.get("config_path"):
        lines.append(f"Config: {result['config_path']}")
    lines.append("")
    lines.append("Derived planning parameters")
    lines.append(f"  total parameters:             {_fmt_params(derived['total'])}")
    lines.append(f"  activated parameters:         {_fmt_params(derived['activated'])}")
    lines.append(f"  dense/shared estimate:        {_fmt_params(derived['dense_shared'])}")
    lines.append(f"  MoE expert estimate:          {_fmt_params(derived['moe_experts'])}")
    lines.append(f"  router/gate mirror estimate:  {_fmt_params(derived['router_gate'])}")
    lines.append("")
    lines.append("Static placement estimate")
    lines.append("  Node  Role                                   Estimate      Cap       Result")
    for node in static_nodes:
        result_label = "PASS" if node["passes_static_cap"] else "FAIL"
        lines.append(
            "  "
            f"{node['name']:<5} "
            f"{node.get('role', '')[:36]:<36} "
            f"{_fmt_gb(node['total_static_bytes']):>10} "
            f"{_fmt_gb(node['static_cap_bytes']):>9} "
            f"{result_label}"
        )
    lines.append(
        f"  Aggregate static estimate: {_fmt_gb(result['static']['aggregate_total_static_bytes'])}"
    )
    margin = result["static"].get("static_safety_margin_fraction", 0.0)
    lines.append(f"  Static safety margin: {margin:.1%}")
    lines.append("")
    lines.append("KV cache estimate, batch=1, KV-only")
    lines.append("  Context    Aggregate    Worst node    Reserve result")
    for item in kv_contexts:
        worst = item["worst_node"]
        reserve_result = "PASS" if worst["passes_runtime_reserve"] else "FAIL"
        lines.append(
            "  "
            f"{item['tokens']:>7,d} "
            f"{_fmt_gb(item['aggregate_bytes']):>12} "
            f"{worst['name']}={_fmt_gb(worst['kv_bytes']):<10} "
            f"{reserve_result}"
        )
    lines.append("")
    lines.append("Important limits")
    lines.append("  PASS/FAIL above is against the static cap only for weights, and runtime reserve only for KV.")
    lines.append("  It is not a final placement, throughput, quality, or long-context claim.")
    lines.append("")
    lines.append("Unresolved assumptions requiring real metadata")
    for item in result["unresolved_assumptions"]:
        lines.append(f"  - {item}")
    return "\n".join(lines)


def _estimate_static(
    *,
    static_groups: list[Any],
    nodes: list[NodeConfig],
    quant_classes: dict[str, QuantClass],
    derived: DerivedParameters,
    static_margin_fraction: float,
    per_group_alignment_bytes: int,
) -> dict[str, Any]:
    node_names = [node.name for node in nodes]
    node_working = {
        node.name: {
            "name": node.name,
            "role": node.role,
            "memory_bytes": node.memory_bytes,
            "static_cap_bytes": node.static_cap_bytes,
            "runtime_reserve_bytes": node.runtime_reserve_bytes,
            "subtotal_static_bytes": 0,
            "static_safety_margin_bytes": 0,
            "total_static_bytes": 0,
            "groups": [],
        }
        for node in nodes
    }
    group_summaries: list[dict[str, Any]] = []

    for group in static_groups:
        if not isinstance(group, dict):
            raise ConfigError("static_weight_groups items must be objects")
        name = str(group.get("name", "")).strip()
        if not name:
            raise ConfigError("static weight group is missing name")
        quant_name = str(group.get("quant_class", "")).strip()
        if quant_name not in quant_classes:
            raise ConfigError(f"static group {name}: unknown quant_class {quant_name!r}")
        parameters = _parameters_for_group(group, derived)
        quant_estimate = quant_classes[quant_name].estimate_bytes(parameters)
        alignment_bytes = per_group_alignment_bytes
        group_total_bytes = int(quant_estimate["total_bytes"]) + alignment_bytes
        placement = group.get("placement", {"type": "fractional_by_node_static_fraction"})
        allocations = _allocate_group_bytes(
            group_name=name,
            group_total_bytes=group_total_bytes,
            placement=placement,
            nodes=nodes,
            node_names=node_names,
        )

        group_summary = {
            "name": name,
            "parameters": parameters,
            "parameters_billions": parameters / 1_000_000_000,
            "quant_class": quant_name,
            "payload_bytes": quant_estimate["payload_bytes"],
            "metadata_bytes": quant_estimate["metadata_bytes"],
            "alignment_bytes": alignment_bytes,
            "total_group_bytes": group_total_bytes,
            "effective_bits_per_parameter": quant_estimate["effective_bits_per_parameter"],
            "placement": placement,
            "allocations": allocations,
            "notes": group.get("notes", ""),
        }
        group_summaries.append(group_summary)

        for node_name, bytes_for_node in allocations.items():
            if bytes_for_node == 0:
                continue
            node_working[node_name]["subtotal_static_bytes"] += bytes_for_node
            node_working[node_name]["groups"].append(
                {
                    "name": name,
                    "bytes": bytes_for_node,
                    "quant_class": quant_name,
                }
            )

    aggregate_total = 0
    node_results: list[dict[str, Any]] = []
    for node in nodes:
        item = node_working[node.name]
        subtotal = int(item["subtotal_static_bytes"])
        margin_bytes = math.ceil(subtotal * static_margin_fraction)
        total = subtotal + margin_bytes
        item["static_safety_margin_bytes"] = margin_bytes
        item["total_static_bytes"] = total
        item["passes_static_cap"] = total <= item["static_cap_bytes"]
        aggregate_total += total
        node_results.append(item)

    return {
        "nodes": node_results,
        "groups": group_summaries,
        "aggregate_total_static_bytes": aggregate_total,
        "static_safety_margin_fraction": static_margin_fraction,
        "per_group_alignment_bytes": per_group_alignment_bytes,
    }


def _estimate_kv(config: dict[str, Any], model: dict[str, Any], nodes: list[NodeConfig]) -> dict[str, Any]:
    kv_config = _required_mapping(config, "kv_cache", "root")
    bytes_per_element = int(_required_number(kv_config, "bytes_per_element", "kv_cache"))
    if bytes_per_element <= 0:
        raise ConfigError("kv_cache.bytes_per_element must be positive")
    batch_size = int(kv_config.get("batch_size", 1))
    if batch_size <= 0:
        raise ConfigError("kv_cache.batch_size must be positive")
    context_lengths = [int(item) for item in _required_list(kv_config, "context_lengths", "kv_cache")]
    if not context_lengths:
        raise ConfigError("kv_cache.context_lengths must not be empty")
    for tokens in context_lengths:
        if tokens <= 0:
            raise ConfigError("kv_cache.context_lengths must contain positive integers")

    layers = int(_required_number(model, "layers", "model"))
    kv_heads = int(_required_number(model, "kv_heads", "model"))
    head_dim = int(_required_number(model, "head_dim", "model"))
    elements_per_token = layers * kv_heads * head_dim * 2
    bytes_per_token = elements_per_token * bytes_per_element * batch_size

    contexts = []
    for tokens in context_lengths:
        aggregate_bytes = bytes_per_token * tokens
        per_node = []
        for node in nodes:
            kv_bytes = math.ceil(aggregate_bytes * node.kv_fraction)
            per_node.append(
                {
                    "name": node.name,
                    "role": node.role,
                    "kv_fraction": node.kv_fraction,
                    "kv_bytes": kv_bytes,
                    "runtime_reserve_bytes": node.runtime_reserve_bytes,
                    "passes_runtime_reserve": kv_bytes <= node.runtime_reserve_bytes,
                }
            )
        worst_node = max(per_node, key=lambda item: item["kv_bytes"] - item["runtime_reserve_bytes"])
        contexts.append(
            {
                "tokens": tokens,
                "aggregate_bytes": aggregate_bytes,
                "bytes_per_token": bytes_per_token,
                "per_node": per_node,
                "worst_node": worst_node,
            }
        )
    return {
        "dtype": kv_config.get("dtype", f"{bytes_per_element}-byte"),
        "bytes_per_element": bytes_per_element,
        "batch_size": batch_size,
        "elements_per_token": elements_per_token,
        "bytes_per_token": bytes_per_token,
        "formula": "layers * kv_heads * head_dim * 2(K,V) * bytes_per_element * batch_size * tokens",
        "contexts": contexts,
    }


def _allocate_group_bytes(
    *,
    group_name: str,
    group_total_bytes: int,
    placement: Any,
    nodes: list[NodeConfig],
    node_names: list[str],
) -> dict[str, int]:
    if not isinstance(placement, dict):
        raise ConfigError(f"static group {group_name}: placement must be an object")
    placement_type = str(placement.get("type", "fractional_by_node_static_fraction"))
    allocations = {name: 0 for name in node_names}

    if placement_type == "replicated":
        placement_nodes = placement.get("nodes", node_names)
        if not isinstance(placement_nodes, list) or not placement_nodes:
            raise ConfigError(f"static group {group_name}: replicated placement requires non-empty nodes")
        for node_name in placement_nodes:
            if node_name not in allocations:
                raise ConfigError(f"static group {group_name}: unknown placement node {node_name!r}")
            allocations[node_name] = group_total_bytes
        return allocations

    if placement_type == "fractional_by_node_static_fraction":
        fractions = {node.name: node.static_fraction for node in nodes}
        return _allocate_fractional(group_name, group_total_bytes, allocations, fractions)

    if placement_type == "fractional":
        raw_fractions = placement.get("fractions")
        if not isinstance(raw_fractions, dict):
            raise ConfigError(f"static group {group_name}: fractional placement requires fractions object")
        fractions = {str(name): float(value) for name, value in raw_fractions.items()}
        for name in fractions:
            if name not in allocations:
                raise ConfigError(f"static group {group_name}: unknown placement node {name!r}")
        return _allocate_fractional(group_name, group_total_bytes, allocations, fractions)

    raise ConfigError(f"static group {group_name}: unsupported placement type {placement_type!r}")


def _allocate_fractional(
    group_name: str,
    group_total_bytes: int,
    allocations: dict[str, int],
    fractions: dict[str, float],
) -> dict[str, int]:
    total_fraction = sum(fractions.values())
    if not math.isclose(total_fraction, 1.0, rel_tol=0.0, abs_tol=1e-6):
        raise ConfigError(
            f"static group {group_name}: fractional placement must sum to 1.0, got {total_fraction}"
        )
    running = 0
    nonzero_names = [name for name, fraction in fractions.items() if fraction > 0]
    if not nonzero_names:
        raise ConfigError(f"static group {group_name}: at least one positive placement fraction is required")
    for name in nonzero_names[:-1]:
        if name not in allocations:
            raise ConfigError(f"static group {group_name}: unknown placement node {name!r}")
        bytes_for_node = math.floor(group_total_bytes * fractions[name])
        allocations[name] = bytes_for_node
        running += bytes_for_node
    last_name = nonzero_names[-1]
    if last_name not in allocations:
        raise ConfigError(f"static group {group_name}: unknown placement node {last_name!r}")
    allocations[last_name] = group_total_bytes - running
    return allocations


def _derive_parameters(model: dict[str, Any]) -> DerivedParameters:
    total = int(_required_number(model, "total_parameters", "model"))
    activated = int(_required_number(model, "activated_parameters", "model"))
    experts = int(_required_number(model, "experts", "model"))
    active_experts = int(_required_number(model, "active_experts", "model"))
    layers = int(_required_number(model, "layers", "model"))
    hidden_size = int(_required_number(model, "hidden_size", "model"))
    if total <= 0 or activated <= 0:
        raise ConfigError("model total_parameters and activated_parameters must be positive")
    if not (0 < active_experts < experts):
        raise ConfigError("model active_experts must be greater than 0 and less than experts")

    active_ratio = active_experts / experts
    moe_experts = round((total - activated) / (1.0 - active_ratio))
    dense_shared = total - moe_experts
    router_gate = layers * hidden_size * experts
    dense_minus_router = dense_shared - router_gate
    if moe_experts < 0 or dense_shared < 0 or dense_minus_router < 0:
        raise ConfigError(
            "derived parameter buckets are negative; check total, activated, experts, and active_experts"
        )
    return DerivedParameters(
        total=total,
        activated=activated,
        dense_shared=dense_shared,
        moe_experts=moe_experts,
        router_gate=router_gate,
        dense_shared_minus_router_gate=dense_minus_router,
        active_expert_ratio=active_ratio,
    )


def _parameters_for_group(group: dict[str, Any], derived: DerivedParameters) -> int:
    if "parameters" in group:
        parameters = int(group["parameters"])
        if parameters < 0:
            raise ConfigError(f"static group {group.get('name', '<unknown>')}: parameters must be non-negative")
        return parameters

    source = str(group.get("param_source", "")).strip()
    if not source:
        raise ConfigError(f"static group {group.get('name', '<unknown>')}: missing param_source or parameters")
    source_map = {
        "total": derived.total,
        "activated": derived.activated,
        "derived_dense": derived.dense_shared,
        "derived_expert": derived.moe_experts,
        "router_gate": derived.router_gate,
        "derived_dense_minus_router_gate": derived.dense_shared_minus_router_gate,
    }
    if source not in source_map:
        raise ConfigError(f"static group {group.get('name', '<unknown>')}: unknown param_source {source!r}")
    return source_map[source]


def _generated_unresolved_assumptions() -> list[str]:
    return [
        "Pinned Qwen3 model config values: layer count, hidden size, attention heads, KV heads, head dimension, expert count, active experts, vocab size, and tying rules.",
        "Safetensors index metadata: complete tensor names, shapes, dtypes, shard membership, and per-file offsets without loading tensor payloads.",
        "Exact dense/shared versus expert parameter split, including embeddings, lm_head, shared experts if present, router bias, and normalization tensors.",
        "Real per-tensor quantization classes, block sizes, scale/zero metadata, padding, and tensor alignment from the selected quantizer.",
        "Which tensors must be replicated on A/B/C for correctness routing, local router mirrors, scheduler state, and promotion caches.",
        "Measured Metal heap, staging buffer, transport ring, allocator fragmentation, telemetry, and OS pressure inside the 14.4GB runtime reserve.",
        "KV ownership policy for prefill and decode; this estimator only applies configured layer/KV fractions and does not model traffic or cache paging.",
        "Quality impact of the low-bit expert planning class; IQ2-like expert quantization is not treated as proven.",
    ]


def _dedupe_strings(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        normalized = item.strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        result.append(normalized)
    return result


def _required_mapping(data: dict[str, Any], key: str, parent: str) -> dict[str, Any]:
    value = data.get(key)
    if not isinstance(value, dict):
        raise ConfigError(f"{parent}: missing object {key!r}")
    return value


def _required_list(data: dict[str, Any], key: str, parent: str) -> list[Any]:
    value = data.get(key)
    if not isinstance(value, list):
        raise ConfigError(f"{parent}: missing list {key!r}")
    return value


def _required_number(data: dict[str, Any], key: str, parent: str) -> int | float:
    value = data.get(key)
    if not isinstance(value, (int, float)):
        raise ConfigError(f"{parent}: missing number {key!r}")
    return value


def _gb_to_bytes(gb_value: int | float) -> int:
    return int(round(float(gb_value) * BYTES_PER_GB))


def _parse_bytes(value: Any) -> int:
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(round(value))
    raise ConfigError(f"byte value must be numeric, got {value!r}")


def _fmt_gb(byte_count: int | float) -> str:
    return f"{byte_count / BYTES_PER_GB:.2f} GB"


def _fmt_params(param_count: int | float) -> str:
    return f"{param_count / 1_000_000_000:.3f}B"
