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
EXPECTED_MODEL_LAYERS = 94
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
    _require_equal(model.get("layers"), EXPECTED_MODEL_LAYERS, "model.layers")

    limits = _required_mapping(manifest, "limits", "root")
    _validate_limits(limits)

    artifact_policy = _required_mapping(manifest, "artifact_policy", "root")
    _require_equal(
        artifact_policy.get("memory_ledger_schema_version"),
        MEMORY_LEDGER_SCHEMA_VERSION,
        "artifact_policy.memory_ledger_schema_version",
    )

    nodes = _required_list(manifest, "nodes", "root")
    nodes_by_name = _index_nodes(nodes)
    ledger_nodes = [_validate_node(nodes_by_name[name]) for name in EXPECTED_NODES]
    _validate_layer_coverage(ledger_nodes)

    return {
        "schema_version": MEMORY_LEDGER_SCHEMA_VERSION,
        "feature_id": FEATURE_ID,
        "source_manifest": manifest_path,
        "model": {
            "name": model.get("name"),
            "variant": model.get("variant"),
            "layers": model.get("layers"),
            "experts": model.get("experts"),
            "active_experts": model.get("active_experts"),
        },
        "limits": {
            "byte_unit": "decimal_gb",
            "worker_memory_bytes": _gb_to_bytes(EXPECTED_WORKER_MEMORY_GB),
            "static_cap_fraction": EXPECTED_STATIC_CAP_FRACTION,
            "runtime_headroom_fraction": EXPECTED_RUNTIME_HEADROOM_FRACTION,
            "static_cap_bytes": _gb_to_bytes(EXPECTED_STATIC_CAP_GB),
            "runtime_headroom_bytes": _gb_to_bytes(EXPECTED_RUNTIME_HEADROOM_GB),
        },
        "nodes": ledger_nodes,
        "validation": {
            "status": "pass",
            "checked_invariants": [
                "exact A/B/C node set",
                "Node A owns 0 primary MoE decode bytes",
                "Node B owns inclusive decode layers 0-46",
                "Node C owns inclusive decode layers 47-93",
                "48GB workers keep 30% memory headroom",
                "48GB workers stay at or below a 33.6GB static cap",
            ],
        },
        "limits_of_claim": list(manifest.get("limits_of_claim", [])),
    }


def write_memory_ledger(ledger: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(ledger, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def format_ledger_summary(ledger: dict[str, Any]) -> str:
    lines = [
        f"{FEATURE_ID} PDD topology manifest: PASS",
        "",
        "Node  Layers    Primary MoE decode  Static total  Static cap  Result",
    ]
    for node in ledger["nodes"]:
        layers = _format_layer_ranges(node["decode_layer_ranges"])
        result = "PASS" if node["passes_static_cap"] else "FAIL"
        lines.append(
            f"{node['name']:<5} "
            f"{layers:<9} "
            f"{_fmt_gb(node['primary_moe_decode_bytes']):>18} "
            f"{_fmt_gb(node['total_static_bytes']):>13} "
            f"{_fmt_gb(node['static_cap_bytes']):>11} "
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


def _validate_node(node: dict[str, Any]) -> dict[str, Any]:
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
    if runtime_headroom_bytes < expected_headroom_bytes:
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
        "decode_layer_ranges": [{"start": start, "end": end} for start, end in ranges],
        "owns_primary_moe_decode": owns_primary,
        "primary_moe_decode_bytes": primary_moe_decode_bytes,
        "dense_decode_bytes": dense_decode_bytes,
        "router_gate_mirror_bytes": router_gate_mirror_bytes,
        "other_static_bytes": other_static_bytes,
        "total_static_bytes": total_static_bytes,
        "static_headroom_bytes": static_cap_bytes - total_static_bytes,
        "passes_static_cap": total_static_bytes <= static_cap_bytes,
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
