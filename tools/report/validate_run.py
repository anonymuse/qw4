#!/usr/bin/env python3
"""Validate a DS5 Phase 0 benchmark artifact directory.

This validator intentionally uses only the Python standard library. It is not a
complete JSON Schema implementation; it is the executable contract for
`phase0.artifacts.v1`.
"""

from __future__ import annotations

import csv
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "phase0.artifacts.v1"
REQUIRED_FILES = {
    "run.json",
    "events.jsonl",
    "latency.csv",
    "throughput.csv",
    "summary.md",
}
GIT_RE = re.compile(r"^[0-9a-f]{40}$")
RUN_ID_RE = re.compile(r"^[A-Za-z0-9._-]+$")
NODE_ID_RE = re.compile(r"^[A-Z][A-Z0-9_-]*$")
NODE_PAIR_RE = re.compile(r"^[A-Z][A-Z0-9_-]*-[A-Z][A-Z0-9_-]*$")
TIMESTAMP_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z$")

LATENCY_HEADER = [
    "schema_version",
    "run_id",
    "node_pair",
    "direction",
    "message_size_bytes",
    "sample_count",
    "warmup_count",
    "transfer_count",
    "checksum_algorithm",
    "checksum_failures",
    "p50_us",
    "p95_us",
    "p99_us",
    "min_us",
    "max_us",
    "jitter_us",
    "remote_expert_rate",
    "scenario_step",
]

THROUGHPUT_HEADER = [
    "schema_version",
    "run_id",
    "node_pair",
    "direction",
    "block_size_bytes",
    "transfer_count",
    "bytes_sent",
    "checksum_algorithm",
    "checksum_failures",
    "duration_ms",
    "mib_per_sec",
    "gbps",
    "concurrent_links",
    "remote_expert_rate",
    "scenario_step",
]

EVENT_TYPES = {
    "run_started",
    "node_discovered",
    "worker_health",
    "latency_sample",
    "throughput_sample",
    "checksum_verified",
    "retry_scheduled",
    "reconnect_succeeded",
    "failure_observed",
    "simulated_layer_transfer",
    "run_completed",
}


class ValidationError(Exception):
    """Raised when validation fails."""


def fail(message: str) -> None:
    raise ValidationError(message)


def read_json(path: Path) -> Any:
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except json.JSONDecodeError as exc:
        fail(f"{path.name}: invalid JSON at line {exc.lineno}: {exc.msg}")


def require_object(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        fail(f"{label}: expected object")
    return value


def require_array(value: Any, label: str, min_items: int = 1) -> list[Any]:
    if not isinstance(value, list):
        fail(f"{label}: expected array")
    if len(value) < min_items:
        fail(f"{label}: expected at least {min_items} item(s)")
    return value


def require_keys(obj: dict[str, Any], label: str, keys: set[str]) -> None:
    missing = sorted(keys - obj.keys())
    if missing:
        fail(f"{label}: missing required key(s): {', '.join(missing)}")


def require_str(obj: dict[str, Any], key: str, label: str) -> str:
    value = obj.get(key)
    if not isinstance(value, str) or value == "":
        fail(f"{label}.{key}: expected non-empty string")
    return value


def require_bool(obj: dict[str, Any], key: str, label: str) -> bool:
    value = obj.get(key)
    if not isinstance(value, bool):
        fail(f"{label}.{key}: expected boolean")
    return value


def require_int(obj: dict[str, Any], key: str, label: str, minimum: int = 0) -> int:
    value = obj.get(key)
    if not isinstance(value, int) or isinstance(value, bool) or value < minimum:
        fail(f"{label}.{key}: expected integer >= {minimum}")
    return value


def require_number(obj: dict[str, Any], key: str, label: str, minimum: float = 0.0) -> float:
    value = obj.get(key)
    if not isinstance(value, (int, float)) or isinstance(value, bool) or value < minimum:
        fail(f"{label}.{key}: expected number >= {minimum}")
    return float(value)


def parse_timestamp(value: str, label: str) -> datetime:
    if not TIMESTAMP_RE.match(value):
        fail(f"{label}: expected RFC 3339 UTC timestamp ending in Z")
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def validate_percentiles(obj: Any, label: str) -> None:
    data = require_object(obj, label)
    require_keys(data, label, {"p50", "p95", "p99"})
    p50 = require_number(data, "p50", label)
    p95 = require_number(data, "p95", label)
    p99 = require_number(data, "p99", label)
    if not (p50 <= p95 <= p99):
        fail(f"{label}: expected p50 <= p95 <= p99")


def validate_run_json(run_dir: Path) -> dict[str, Any]:
    run = require_object(read_json(run_dir / "run.json"), "run.json")
    require_keys(
        run,
        "run.json",
        {
            "schema_version",
            "run_id",
            "git_commit",
            "software",
            "started_at",
            "ended_at",
            "duration_ms",
            "valid",
            "environment",
            "scenario",
            "nodes",
            "checksums",
            "failure_counts",
            "metrics",
            "artifacts",
        },
    )

    if run["schema_version"] != SCHEMA_VERSION:
        fail("run.json.schema_version: unsupported schema version")
    run_id = require_str(run, "run_id", "run.json")
    if not RUN_ID_RE.match(run_id):
        fail("run.json.run_id: contains unsupported characters")
    if run_dir.name != run_id:
        fail(f"run.json.run_id: expected directory name {run_dir.name!r}")
    if not GIT_RE.match(require_str(run, "git_commit", "run.json")):
        fail("run.json.git_commit: expected 40 lowercase hex characters")

    software = require_object(run["software"], "run.json.software")
    require_keys(software, "run.json.software", {"name", "version"})
    require_str(software, "name", "run.json.software")
    require_str(software, "version", "run.json.software")

    started = parse_timestamp(require_str(run, "started_at", "run.json"), "run.json.started_at")
    ended = parse_timestamp(require_str(run, "ended_at", "run.json"), "run.json.ended_at")
    if ended < started:
        fail("run.json.ended_at: must be greater than or equal to started_at")
    require_number(run, "duration_ms", "run.json")
    require_bool(run, "valid", "run.json")

    environment = require_object(run["environment"], "run.json.environment")
    require_keys(environment, "run.json.environment", {"network_path", "clock_sync", "hardware_interpretable"})
    network_path = require_str(environment, "network_path", "run.json.environment")
    require_str(environment, "clock_sync", "run.json.environment")
    hardware_interpretable = require_bool(environment, "hardware_interpretable", "run.json.environment")
    optional_environment_strings = ("transport_mode", "socket_mode", "confirmed_network_path")
    for key in optional_environment_strings:
        if key in environment and not isinstance(environment[key], str):
            fail(f"run.json.environment.{key}: expected string when present")
    if "loopback" in environment and not isinstance(environment["loopback"], bool):
        fail("run.json.environment.loopback: expected boolean when present")
    path_lower = network_path.lower()
    mode_lower = str(environment.get("transport_mode", "")).lower()
    socket_lower = str(environment.get("socket_mode", "")).lower()
    if hardware_interpretable and (
        "loopback" in path_lower
        or "localhost" in path_lower
        or "127.0.0.1" in path_lower
        or "socket_localhost" in mode_lower
        or "localhost" in socket_lower
    ):
        fail("run.json.environment.hardware_interpretable: localhost/loopback paths cannot be hardware-interpretable")

    scenario = require_object(run["scenario"], "run.json.scenario")
    require_keys(
        scenario,
        "run.json.scenario",
        {
            "name",
            "config_path",
            "kind",
            "message_sizes_bytes",
            "block_sizes_bytes",
            "transfer_count",
            "warmup_count",
            "checksum_mode",
            "remote_expert_rates",
            "qwen_shape",
        },
    )
    if scenario["kind"] not in {"synthetic", "loopback", "socket_localhost", "real_cluster"}:
        fail("run.json.scenario.kind: expected synthetic, loopback, socket_localhost, or real_cluster")
    require_str(scenario, "name", "run.json.scenario")
    require_str(scenario, "config_path", "run.json.scenario")
    require_int(scenario, "transfer_count", "run.json.scenario", 1)
    require_int(scenario, "warmup_count", "run.json.scenario", 0)
    require_str(scenario, "checksum_mode", "run.json.scenario")
    for key in ("message_sizes_bytes", "block_sizes_bytes"):
        values = require_array(scenario[key], f"run.json.scenario.{key}")
        if any(not isinstance(item, int) or isinstance(item, bool) or item < 1 for item in values):
            fail(f"run.json.scenario.{key}: expected positive integers")
    rates = require_array(scenario["remote_expert_rates"], "run.json.scenario.remote_expert_rates")
    if any(not isinstance(rate, (int, float)) or isinstance(rate, bool) or rate < 0 or rate > 1 for rate in rates):
        fail("run.json.scenario.remote_expert_rates: expected numbers from 0 to 1")

    qwen_shape = require_object(scenario["qwen_shape"], "run.json.scenario.qwen_shape")
    require_keys(
        qwen_shape,
        "run.json.scenario.qwen_shape",
        {"layers", "hidden_size", "top_k", "packets_per_destination_per_layer", "layer_owners"},
    )
    require_int(qwen_shape, "layers", "run.json.scenario.qwen_shape", 1)
    require_int(qwen_shape, "hidden_size", "run.json.scenario.qwen_shape", 1)
    require_int(qwen_shape, "top_k", "run.json.scenario.qwen_shape", 1)
    require_int(qwen_shape, "packets_per_destination_per_layer", "run.json.scenario.qwen_shape", 1)
    layer_owners = require_array(qwen_shape["layer_owners"], "run.json.scenario.qwen_shape.layer_owners")
    for index, owner_value in enumerate(layer_owners):
        owner = require_object(owner_value, f"run.json.scenario.qwen_shape.layer_owners[{index}]")
        require_keys(owner, f"run.json.scenario.qwen_shape.layer_owners[{index}]", {"node_id", "start_layer", "end_layer"})
        if not NODE_ID_RE.match(require_str(owner, "node_id", f"run.json.scenario.qwen_shape.layer_owners[{index}]")):
            fail(f"run.json.scenario.qwen_shape.layer_owners[{index}].node_id: invalid node ID")
        start = require_int(owner, "start_layer", f"run.json.scenario.qwen_shape.layer_owners[{index}]", 0)
        end = require_int(owner, "end_layer", f"run.json.scenario.qwen_shape.layer_owners[{index}]", 0)
        if end < start:
            fail(f"run.json.scenario.qwen_shape.layer_owners[{index}]: end_layer before start_layer")

    nodes = require_array(run["nodes"], "run.json.nodes")
    roles = set()
    node_ids = set()
    for index, node_value in enumerate(nodes):
        node = require_object(node_value, f"run.json.nodes[{index}]")
        require_keys(node, f"run.json.nodes[{index}]", {"node_id", "role", "hostname", "hardware_label", "transport"})
        node_id = require_str(node, "node_id", f"run.json.nodes[{index}]")
        if not NODE_ID_RE.match(node_id):
            fail(f"run.json.nodes[{index}].node_id: invalid node ID")
        node_ids.add(node_id)
        role = require_str(node, "role", f"run.json.nodes[{index}]")
        if role not in {"coordinator", "worker"}:
            fail(f"run.json.nodes[{index}].role: expected coordinator or worker")
        roles.add(role)
        require_str(node, "hostname", f"run.json.nodes[{index}]")
        require_str(node, "hardware_label", f"run.json.nodes[{index}]")
        require_str(node, "transport", f"run.json.nodes[{index}]")
    if "coordinator" not in roles or "worker" not in roles:
        fail("run.json.nodes: expected at least one coordinator and one worker")

    checksums = require_object(run["checksums"], "run.json.checksums")
    require_keys(checksums, "run.json.checksums", {"algorithm", "total_transfers", "passed", "failed", "status"})
    require_str(checksums, "algorithm", "run.json.checksums")
    total = require_int(checksums, "total_transfers", "run.json.checksums", 0)
    passed = require_int(checksums, "passed", "run.json.checksums", 0)
    failed = require_int(checksums, "failed", "run.json.checksums", 0)
    if total != passed + failed:
        fail("run.json.checksums: total_transfers must equal passed + failed")
    if checksums["status"] not in {"pass", "fail"}:
        fail("run.json.checksums.status: expected pass or fail")
    if failed > 0 and checksums["status"] != "fail":
        fail("run.json.checksums.status: failed checksums require fail status")

    failure_counts = require_object(run["failure_counts"], "run.json.failure_counts")
    require_keys(failure_counts, "run.json.failure_counts", {"failures", "retries", "reconnects", "timeouts"})
    for key in ("failures", "retries", "reconnects", "timeouts"):
        require_int(failure_counts, key, "run.json.failure_counts", 0)

    metrics = require_object(run["metrics"], "run.json.metrics")
    require_keys(
        metrics,
        "run.json.metrics",
        {
            "latency_by_message_size",
            "throughput_by_block_size",
            "scheduler_overhead_us_per_token",
            "bytes_sent_per_simulated_token",
            "per_layer_transport_time_us",
            "concurrent_link_interference",
            "predicted_upper_bound_tokens_per_sec",
        },
    )
    validate_latency_metrics(metrics["latency_by_message_size"])
    validate_throughput_metrics(metrics["throughput_by_block_size"])
    validate_percentiles(metrics["scheduler_overhead_us_per_token"], "run.json.metrics.scheduler_overhead_us_per_token")
    validate_percentiles(metrics["per_layer_transport_time_us"], "run.json.metrics.per_layer_transport_time_us")
    require_int(metrics, "bytes_sent_per_simulated_token", "run.json.metrics", 0)
    validate_concurrent_link_metrics(metrics["concurrent_link_interference"])
    validate_token_predictions(metrics["predicted_upper_bound_tokens_per_sec"])

    artifacts = require_object(run["artifacts"], "run.json.artifacts")
    expected_artifacts = {
        "events": "events.jsonl",
        "latency": "latency.csv",
        "throughput": "throughput.csv",
        "summary": "summary.md",
    }
    require_keys(artifacts, "run.json.artifacts", set(expected_artifacts))
    for key, expected in expected_artifacts.items():
        if artifacts.get(key) != expected:
            fail(f"run.json.artifacts.{key}: expected {expected!r}")

    for owner_value in layer_owners:
        if owner_value["node_id"] not in node_ids:
            fail(f"run.json.scenario.qwen_shape.layer_owners: unknown node {owner_value['node_id']!r}")

    return run


def validate_latency_metrics(metrics: Any) -> None:
    rows = require_array(metrics, "run.json.metrics.latency_by_message_size")
    for index, metric_value in enumerate(rows):
        metric = require_object(metric_value, f"run.json.metrics.latency_by_message_size[{index}]")
        require_keys(
            metric,
            f"run.json.metrics.latency_by_message_size[{index}]",
            {"node_pair", "message_size_bytes", "sample_count", "checksum_failures", "p50_us", "p95_us", "p99_us"},
        )
        if not NODE_PAIR_RE.match(require_str(metric, "node_pair", f"run.json.metrics.latency_by_message_size[{index}]")):
            fail(f"run.json.metrics.latency_by_message_size[{index}].node_pair: invalid node pair")
        require_int(metric, "message_size_bytes", f"run.json.metrics.latency_by_message_size[{index}]", 1)
        require_int(metric, "sample_count", f"run.json.metrics.latency_by_message_size[{index}]", 1)
        require_int(metric, "checksum_failures", f"run.json.metrics.latency_by_message_size[{index}]", 0)
        p50 = require_number(metric, "p50_us", f"run.json.metrics.latency_by_message_size[{index}]")
        p95 = require_number(metric, "p95_us", f"run.json.metrics.latency_by_message_size[{index}]")
        p99 = require_number(metric, "p99_us", f"run.json.metrics.latency_by_message_size[{index}]")
        if not (p50 <= p95 <= p99):
            fail(f"run.json.metrics.latency_by_message_size[{index}]: expected p50_us <= p95_us <= p99_us")


def validate_throughput_metrics(metrics: Any) -> None:
    rows = require_array(metrics, "run.json.metrics.throughput_by_block_size")
    for index, metric_value in enumerate(rows):
        metric = require_object(metric_value, f"run.json.metrics.throughput_by_block_size[{index}]")
        require_keys(
            metric,
            f"run.json.metrics.throughput_by_block_size[{index}]",
            {
                "node_pair",
                "block_size_bytes",
                "transfer_count",
                "bytes_sent",
                "checksum_failures",
                "duration_ms",
                "mib_per_sec",
                "gbps",
            },
        )
        if not NODE_PAIR_RE.match(require_str(metric, "node_pair", f"run.json.metrics.throughput_by_block_size[{index}]")):
            fail(f"run.json.metrics.throughput_by_block_size[{index}].node_pair: invalid node pair")
        require_int(metric, "block_size_bytes", f"run.json.metrics.throughput_by_block_size[{index}]", 1)
        require_int(metric, "transfer_count", f"run.json.metrics.throughput_by_block_size[{index}]", 1)
        require_int(metric, "bytes_sent", f"run.json.metrics.throughput_by_block_size[{index}]", 1)
        require_int(metric, "checksum_failures", f"run.json.metrics.throughput_by_block_size[{index}]", 0)
        require_number(metric, "duration_ms", f"run.json.metrics.throughput_by_block_size[{index}]", 0.000001)
        require_number(metric, "mib_per_sec", f"run.json.metrics.throughput_by_block_size[{index}]")
        require_number(metric, "gbps", f"run.json.metrics.throughput_by_block_size[{index}]")


def validate_concurrent_link_metrics(metrics: Any) -> None:
    rows = require_array(metrics, "run.json.metrics.concurrent_link_interference")
    for index, metric_value in enumerate(rows):
        metric = require_object(metric_value, f"run.json.metrics.concurrent_link_interference[{index}]")
        require_keys(
            metric,
            f"run.json.metrics.concurrent_link_interference[{index}]",
            {"node_pair", "solo_mib_per_sec", "concurrent_mib_per_sec", "degradation_pct"},
        )
        if not NODE_PAIR_RE.match(require_str(metric, "node_pair", f"run.json.metrics.concurrent_link_interference[{index}]")):
            fail(f"run.json.metrics.concurrent_link_interference[{index}].node_pair: invalid node pair")
        require_number(metric, "solo_mib_per_sec", f"run.json.metrics.concurrent_link_interference[{index}]")
        require_number(metric, "concurrent_mib_per_sec", f"run.json.metrics.concurrent_link_interference[{index}]")
        require_number(metric, "degradation_pct", f"run.json.metrics.concurrent_link_interference[{index}]", -100.0)


def validate_token_predictions(predictions: Any) -> None:
    rows = require_array(predictions, "run.json.metrics.predicted_upper_bound_tokens_per_sec")
    for index, prediction_value in enumerate(rows):
        prediction = require_object(prediction_value, f"run.json.metrics.predicted_upper_bound_tokens_per_sec[{index}]")
        require_keys(
            prediction,
            f"run.json.metrics.predicted_upper_bound_tokens_per_sec[{index}]",
            {"remote_expert_rate", "tokens_per_sec"},
        )
        rate = require_number(prediction, "remote_expert_rate", f"run.json.metrics.predicted_upper_bound_tokens_per_sec[{index}]")
        if rate > 1:
            fail(f"run.json.metrics.predicted_upper_bound_tokens_per_sec[{index}].remote_expert_rate: expected <= 1")
        require_number(prediction, "tokens_per_sec", f"run.json.metrics.predicted_upper_bound_tokens_per_sec[{index}]")


def validate_events(run_dir: Path, run: dict[str, Any]) -> list[dict[str, Any]]:
    path = run_dir / "events.jsonl"
    events: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            stripped = line.strip()
            if stripped == "":
                fail(f"events.jsonl:{line_number}: blank lines are not allowed")
            try:
                event = json.loads(stripped)
            except json.JSONDecodeError as exc:
                fail(f"events.jsonl:{line_number}: invalid JSON: {exc.msg}")
            events.append(require_object(event, f"events.jsonl:{line_number}"))

    if not events:
        fail("events.jsonl: expected at least one event")

    seen_sequences = set()
    event_types = set()
    previous_sequence = -1
    for line_number, event in enumerate(events, 1):
        label = f"events.jsonl:{line_number}"
        require_keys(event, label, {"schema_version", "run_id", "sequence", "timestamp", "event_type", "severity", "details"})
        if event["schema_version"] != SCHEMA_VERSION:
            fail(f"{label}.schema_version: unsupported schema version")
        if event["run_id"] != run["run_id"]:
            fail(f"{label}.run_id: does not match run.json")
        sequence = require_int(event, "sequence", label, 0)
        if sequence in seen_sequences:
            fail(f"{label}.sequence: duplicate sequence {sequence}")
        if sequence <= previous_sequence:
            fail(f"{label}.sequence: expected monotonically increasing sequence")
        seen_sequences.add(sequence)
        previous_sequence = sequence
        parse_timestamp(require_str(event, "timestamp", label), f"{label}.timestamp")
        event_type = require_str(event, "event_type", label)
        if event_type not in EVENT_TYPES:
            fail(f"{label}.event_type: unsupported event type {event_type!r}")
        event_types.add(event_type)
        if event["severity"] not in {"debug", "info", "warn", "error"}:
            fail(f"{label}.severity: expected debug, info, warn, or error")
        if not isinstance(event["details"], dict):
            fail(f"{label}.details: expected object")
        validate_event_type_fields(event, label)

    required_types = {"run_started", "worker_health", "latency_sample", "throughput_sample", "checksum_verified", "run_completed"}
    missing_types = sorted(required_types - event_types)
    if missing_types:
        fail(f"events.jsonl: missing required event type(s): {', '.join(missing_types)}")

    failure_counts = run["failure_counts"]
    if failure_counts["failures"] > 0 and "failure_observed" not in event_types:
        fail("events.jsonl: failure_counts.failures requires failure_observed event")
    if failure_counts["retries"] > 0 and "retry_scheduled" not in event_types:
        fail("events.jsonl: failure_counts.retries requires retry_scheduled event")
    if failure_counts["reconnects"] > 0 and "reconnect_succeeded" not in event_types:
        fail("events.jsonl: failure_counts.reconnects requires reconnect_succeeded event")

    return events


def validate_event_type_fields(event: dict[str, Any], label: str) -> None:
    event_type = event["event_type"]
    if "node_id" in event and not NODE_ID_RE.match(require_str(event, "node_id", label)):
        fail(f"{label}.node_id: invalid node ID")
    if "node_pair" in event and not NODE_PAIR_RE.match(require_str(event, "node_pair", label)):
        fail(f"{label}.node_pair: invalid node pair")
    if "checksum_status" in event and event["checksum_status"] not in {"pass", "fail", "not_applicable"}:
        fail(f"{label}.checksum_status: expected pass, fail, or not_applicable")
    if "health_status" in event and event["health_status"] not in {"healthy", "degraded", "unreachable"}:
        fail(f"{label}.health_status: expected healthy, degraded, or unreachable")

    required_by_type = {
        "node_discovered": {"node_id", "hostname", "latency_us"},
        "worker_health": {"node_id", "health_status"},
        "latency_sample": {"node_pair", "message_size_bytes", "latency_us", "checksum_status"},
        "throughput_sample": {"node_pair", "block_size_bytes", "bytes_sent", "throughput_mib_s", "checksum_status"},
        "checksum_verified": {"transfer_id", "checksum_status", "bytes_sent"},
        "retry_scheduled": {"failure_kind", "retry_count"},
        "reconnect_succeeded": {"node_id", "retry_count", "latency_us"},
        "failure_observed": {"failure_kind"},
        "simulated_layer_transfer": {"layer_index", "node_pair", "bytes_sent", "latency_us"},
        "run_completed": {"valid"},
    }
    require_keys(event, label, required_by_type.get(event_type, set()))

    for key in ("message_size_bytes", "block_size_bytes", "bytes_sent", "retry_count", "layer_index"):
        if key in event:
            require_int(event, key, label, 0 if key in {"bytes_sent", "retry_count", "layer_index"} else 1)
    for key in ("latency_us", "throughput_mib_s"):
        if key in event:
            require_number(event, key, label)
    if "remote_expert_rate" in event:
        rate = require_number(event, "remote_expert_rate", label)
        if rate > 1:
            fail(f"{label}.remote_expert_rate: expected <= 1")
    if "valid" in event:
        require_bool(event, "valid", label)


def validate_csv(path: Path, expected_header: list[str], run_id: str, label: str) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != expected_header:
            fail(f"{label}: unexpected header {reader.fieldnames!r}")
        rows = list(reader)
    if not rows:
        fail(f"{label}: expected at least one data row")
    for index, row in enumerate(rows, 2):
        row_label = f"{label}:{index}"
        if row["schema_version"] != SCHEMA_VERSION:
            fail(f"{row_label}.schema_version: unsupported schema version")
        if row["run_id"] != run_id:
            fail(f"{row_label}.run_id: does not match run.json")
        if not NODE_PAIR_RE.match(row["node_pair"]):
            fail(f"{row_label}.node_pair: invalid node pair")
        parse_rate(row["remote_expert_rate"], f"{row_label}.remote_expert_rate")
        if row["scenario_step"] == "":
            fail(f"{row_label}.scenario_step: expected non-empty value")
    return rows


def parse_int_cell(value: str, label: str, minimum: int) -> int:
    try:
        parsed = int(value)
    except ValueError:
        fail(f"{label}: expected integer")
    if parsed < minimum:
        fail(f"{label}: expected integer >= {minimum}")
    return parsed


def parse_number_cell(value: str, label: str, minimum: float) -> float:
    try:
        parsed = float(value)
    except ValueError:
        fail(f"{label}: expected number")
    if parsed < minimum:
        fail(f"{label}: expected number >= {minimum}")
    return parsed


def parse_rate(value: str, label: str) -> float:
    parsed = parse_number_cell(value, label, 0.0)
    if parsed > 1:
        fail(f"{label}: expected number <= 1")
    return parsed


def validate_latency_csv(run_dir: Path, run: dict[str, Any]) -> list[dict[str, str]]:
    rows = validate_csv(run_dir / "latency.csv", LATENCY_HEADER, run["run_id"], "latency.csv")
    message_sizes = set(run["scenario"]["message_sizes_bytes"])
    for index, row in enumerate(rows, 2):
        label = f"latency.csv:{index}"
        if row["direction"] not in {"request", "response", "round_trip"}:
            fail(f"{label}.direction: expected request, response, or round_trip")
        message_size = parse_int_cell(row["message_size_bytes"], f"{label}.message_size_bytes", 1)
        if message_size not in message_sizes:
            fail(f"{label}.message_size_bytes: not listed in run.json scenario")
        parse_int_cell(row["sample_count"], f"{label}.sample_count", 1)
        parse_int_cell(row["warmup_count"], f"{label}.warmup_count", 0)
        parse_int_cell(row["transfer_count"], f"{label}.transfer_count", 1)
        if row["checksum_algorithm"] == "":
            fail(f"{label}.checksum_algorithm: expected non-empty value")
        parse_int_cell(row["checksum_failures"], f"{label}.checksum_failures", 0)
        p50 = parse_number_cell(row["p50_us"], f"{label}.p50_us", 0.0)
        p95 = parse_number_cell(row["p95_us"], f"{label}.p95_us", 0.0)
        p99 = parse_number_cell(row["p99_us"], f"{label}.p99_us", 0.0)
        min_us = parse_number_cell(row["min_us"], f"{label}.min_us", 0.0)
        max_us = parse_number_cell(row["max_us"], f"{label}.max_us", 0.0)
        jitter = parse_number_cell(row["jitter_us"], f"{label}.jitter_us", 0.0)
        if not (min_us <= p50 <= p95 <= p99 <= max_us):
            fail(f"{label}: expected min_us <= p50_us <= p95_us <= p99_us <= max_us")
        if abs(jitter - (p99 - p50)) > 0.001:
            fail(f"{label}.jitter_us: expected p99_us - p50_us")
    return rows


def validate_throughput_csv(run_dir: Path, run: dict[str, Any]) -> list[dict[str, str]]:
    rows = validate_csv(run_dir / "throughput.csv", THROUGHPUT_HEADER, run["run_id"], "throughput.csv")
    block_sizes = set(run["scenario"]["block_sizes_bytes"])
    for index, row in enumerate(rows, 2):
        label = f"throughput.csv:{index}"
        if row["direction"] not in {"send", "receive", "round_trip"}:
            fail(f"{label}.direction: expected send, receive, or round_trip")
        block_size = parse_int_cell(row["block_size_bytes"], f"{label}.block_size_bytes", 1)
        if block_size not in block_sizes:
            fail(f"{label}.block_size_bytes: not listed in run.json scenario")
        transfer_count = parse_int_cell(row["transfer_count"], f"{label}.transfer_count", 1)
        bytes_sent = parse_int_cell(row["bytes_sent"], f"{label}.bytes_sent", 1)
        if bytes_sent < block_size * transfer_count:
            fail(f"{label}.bytes_sent: expected at least block_size_bytes * transfer_count")
        if row["checksum_algorithm"] == "":
            fail(f"{label}.checksum_algorithm: expected non-empty value")
        parse_int_cell(row["checksum_failures"], f"{label}.checksum_failures", 0)
        parse_number_cell(row["duration_ms"], f"{label}.duration_ms", 0.000001)
        parse_number_cell(row["mib_per_sec"], f"{label}.mib_per_sec", 0.0)
        parse_number_cell(row["gbps"], f"{label}.gbps", 0.0)
        if row["concurrent_links"] == "":
            fail(f"{label}.concurrent_links: expected none or comma-separated node pairs")
    return rows


def validate_summary(run_dir: Path, run: dict[str, Any]) -> None:
    text = (run_dir / "summary.md").read_text(encoding="utf-8")
    if not text.startswith("# "):
        fail("summary.md: expected top-level title")
    for heading in ("## Run", "## Scenario", "## Nodes", "## Latency", "## Throughput", "## Reliability", "## Interpretation"):
        if heading not in text:
            fail(f"summary.md: missing heading {heading!r}")
    required_facts = [
        "run_id:",
        "git_commit:",
        "started_at:",
        "ended_at:",
        "valid:",
        "scenario:",
        "node roles:",
        "p50",
        "p95",
        "p99",
        "throughput",
        "checksum failures:",
        "failures:",
        "retries:",
        "reconnects:",
        "timeouts:",
        "predicted upper-bound tokens/sec",
        "data kind:",
    ]
    lower_text = text.lower()
    for fact in required_facts:
        if fact.lower() not in lower_text:
            fail(f"summary.md: missing required fact {fact!r}")
    if run["run_id"] not in text:
        fail("summary.md: missing run_id value")
    if run["git_commit"] not in text:
        fail("summary.md: missing git_commit value")


def validate_artifact_set(run_dir: Path) -> None:
    if not run_dir.exists() or not run_dir.is_dir():
        fail(f"{run_dir}: expected artifact directory")

    missing = sorted(name for name in REQUIRED_FILES if not (run_dir / name).is_file())
    if missing:
        fail(f"{run_dir}: missing required file(s): {', '.join(missing)}")

    run = validate_run_json(run_dir)
    validate_events(run_dir, run)
    validate_latency_csv(run_dir, run)
    validate_throughput_csv(run_dir, run)
    validate_summary(run_dir, run)


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: validate_run.py <artifact-run-dir>", file=sys.stderr)
        return 2
    run_dir = Path(argv[1])
    try:
        validate_artifact_set(run_dir)
    except ValidationError as exc:
        print(f"validation failed: {exc}", file=sys.stderr)
        return 1
    print(f"OK: {run_dir} conforms to {SCHEMA_VERSION}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
