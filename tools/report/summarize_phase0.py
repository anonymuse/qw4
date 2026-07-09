#!/usr/bin/env python3
"""Summarize DS5 Phase 0 transport artifacts as Markdown.

This script is intentionally conservative. It does not validate schemas and it
does not infer measurements that are absent from the artifact directory.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Iterable


REQUIRED_FILES = (
    "run.json",
    "events.jsonl",
    "latency.csv",
    "throughput.csv",
    "summary.md",
)

MISSING = "not reported"


def load_json(path: Path) -> tuple[dict[str, Any], list[str]]:
    warnings: list[str] = []
    if not path.exists():
        return {}, [f"missing {path.name}"]
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {}, [f"could not parse {path.name}: {exc}"]
    if not isinstance(data, dict):
        return {}, [f"{path.name} did not contain a JSON object"]
    return data, warnings


def load_jsonl(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    events: list[dict[str, Any]] = []
    warnings: list[str] = []
    if not path.exists():
        return events, [f"missing {path.name}"]
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                event = json.loads(stripped)
            except json.JSONDecodeError as exc:
                warnings.append(f"{path.name}:{line_number} could not parse JSON: {exc}")
                continue
            if isinstance(event, dict):
                events.append(event)
            else:
                warnings.append(f"{path.name}:{line_number} was not a JSON object")
    return events, warnings


def load_csv(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    warnings: list[str] = []
    if not path.exists():
        return [], [f"missing {path.name}"]
    with path.open("r", encoding="utf-8", newline="") as handle:
        try:
            reader = csv.DictReader(handle)
            rows = list(reader)
        except csv.Error as exc:
            return [], [f"could not parse {path.name}: {exc}"]
    if not rows and not reader.fieldnames:
        warnings.append(f"{path.name} had no header row")
    return rows, warnings


def get_path(data: dict[str, Any], *paths: str) -> Any:
    for path in paths:
        current: Any = data
        found = True
        for part in path.split("."):
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                found = False
                break
        if found and current not in (None, ""):
            return current
    return None


def value_or_missing(value: Any) -> str:
    if value is None or value == "":
        return MISSING
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, (list, tuple)):
        return ", ".join(value_or_missing(item) for item in value) if value else MISSING
    if isinstance(value, dict):
        return json.dumps(value, sort_keys=True)
    return str(value)


def row_value(row: dict[str, str], *names: str) -> str:
    by_lower = {key.lower(): key for key in row}
    for name in names:
        key = by_lower.get(name.lower())
        if key is not None and row.get(key, "") != "":
            return row[key]
    return MISSING


def table(headers: Iterable[str], rows: Iterable[Iterable[Any]]) -> list[str]:
    header_list = list(headers)
    lines = [
        "| " + " | ".join(header_list) + " |",
        "| " + " | ".join("---" for _ in header_list) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(value_or_missing(cell) for cell in row) + " |")
    return lines


def event_type(event: dict[str, Any]) -> str:
    value = get_path(event, "event_type", "type", "name", "kind")
    return value_or_missing(value)


def event_node(event: dict[str, Any]) -> str:
    value = get_path(event, "node", "node_id", "node.id", "worker", "worker_id")
    return value_or_missing(value)


def checksum_failure_count(run: dict[str, Any], events: list[dict[str, Any]]) -> str:
    explicit = get_path(
        run,
        "checksum_failures",
        "checksums.failures",
        "checksums.failed",
        "checksums.failure_count",
        "metrics.checksum_failures",
    )
    if explicit is not None:
        return value_or_missing(explicit)

    count = 0
    for event in events:
        event_name = event_type(event).lower()
        status = value_or_missing(get_path(event, "status", "checksum.status")).lower()
        failed = get_path(event, "checksum_failed", "checksum.failed", "failed")
        if "checksum" in event_name and ("fail" in event_name or status in {"fail", "failed", "error"}):
            count += 1
        elif failed is True:
            count += 1
    return str(count) if count else MISSING


def classify_transport(run: dict[str, Any]) -> tuple[str, str]:
    path = get_path(
        run,
        "transport_path",
        "hardware_path",
        "network_path",
        "environment.network_path",
        "transport.path",
        "network.path",
        "link.path",
    )
    loopback = get_path(run, "loopback", "transport.loopback", "network.loopback")
    validity = get_path(run, "validity", "validity.status", "run_validity", "status", "valid")

    path_text = value_or_missing(path)
    validity_text = value_or_missing(validity)
    path_lower = path_text.lower()
    if loopback is True or "loopback" in path_lower or "127.0.0.1" in path_lower:
        validity_text = "loopback-only"
    return path_text, validity_text


def latency_rows(rows: list[dict[str, str]], limit: int = 24) -> list[list[str]]:
    rendered: list[list[str]] = []
    for row in rows[:limit]:
        rendered.append(
            [
                row_value(row, "node_pair", "pair", "link", "route"),
                row_value(row, "message_size_bytes", "message_bytes", "size_bytes", "bytes"),
                row_value(row, "transfer_count", "transfers", "round_trips", "samples", "count"),
                row_value(row, "p50_ms", "latency_p50_ms", "p50_us", "p50"),
                row_value(row, "p95_ms", "latency_p95_ms", "p95_us", "p95"),
                row_value(row, "p99_ms", "latency_p99_ms", "p99_us", "p99"),
            ]
        )
    if len(rows) > limit:
        rendered.append([f"truncated after {limit} rows", MISSING, MISSING, MISSING, MISSING, MISSING])
    return rendered


def throughput_rows(rows: list[dict[str, str]], limit: int = 24) -> list[list[str]]:
    rendered: list[list[str]] = []
    for row in rows[:limit]:
        rendered.append(
            [
                row_value(row, "node_pair", "pair", "link", "route"),
                row_value(row, "block_size_bytes", "block_bytes", "size_bytes", "bytes"),
                row_value(row, "concurrent_links"),
                row_value(row, "transfer_count", "transfers", "samples", "count"),
                row_value(
                    row,
                    "throughput_mib_s",
                    "throughput_mbps",
                    "throughput_gbps",
                    "mib_per_sec",
                    "gbps",
                    "bytes_per_second",
                    "throughput",
                ),
                row_value(row, "checksum_cost_ms", "checksum_ms", "checksum_cost", "checksum_overhead"),
            ]
        )
    if len(rows) > limit:
        rendered.append([f"truncated after {limit} rows", MISSING, MISSING, MISSING, MISSING, MISSING])
    return rendered


def interference_rows(run: dict[str, Any], limit: int = 24) -> list[list[str]]:
    interference = get_path(run, "metrics.concurrent_link_interference")
    if not isinstance(interference, list):
        return []

    rows: list[list[str]] = []
    for item in interference[:limit]:
        if not isinstance(item, dict):
            continue
        rows.append(
            [
                value_or_missing(get_path(item, "node_pair")),
                value_or_missing(get_path(item, "solo_mib_per_sec")),
                value_or_missing(get_path(item, "concurrent_mib_per_sec")),
                value_or_missing(get_path(item, "degradation_pct")),
            ]
        )
    if len(interference) > limit:
        rows.append([f"truncated after {limit} rows", MISSING, MISSING, MISSING])
    return rows


def sensitivity_rows(run: dict[str, Any], limit: int = 24) -> list[list[str]]:
    candidates = (
        get_path(run, "remote_expert_rate_sensitivity"),
        get_path(run, "simulated_moe.remote_expert_rate_sensitivity"),
        get_path(run, "metrics.remote_expert_rate_sensitivity"),
        get_path(run, "metrics.predicted_upper_bound_tokens_per_sec"),
        get_path(run, "sensitivity.remote_expert_rates"),
    )
    sensitivity = next((item for item in candidates if isinstance(item, list)), None)
    if not sensitivity:
        return []

    rows: list[list[str]] = []
    for item in sensitivity[:limit]:
        if not isinstance(item, dict):
            continue
        rows.append(
            [
                value_or_missing(get_path(item, "remote_expert_rate", "remote_rate", "rate")),
                value_or_missing(get_path(item, "bytes_per_token", "bytes_per_simulated_token")),
                value_or_missing(
                    get_path(
                        item,
                        "transport_time_ms_per_token",
                        "simulated_transport_time_ms",
                        "transport_time_us_per_token",
                        "simulated_transport_time_us_per_token",
                    )
                ),
                value_or_missing(
                    get_path(
                        item,
                        "upper_bound_tokens_per_sec",
                        "predicted_upper_bound_tokens_per_sec",
                        "tokens_per_sec_upper_bound",
                        "tokens_per_sec",
                    )
                ),
            ]
        )
    if sensitivity and len(sensitivity) > limit:
        rows.append([f"truncated after {limit} rows", MISSING, MISSING, MISSING])
    return rows


def event_summary(events: list[dict[str, Any]]) -> list[list[str]]:
    counts = Counter(event_type(event) for event in events)
    rows: list[list[str]] = []
    for name, count in sorted(counts.items()):
        nodes = sorted({event_node(event) for event in events if event_type(event) == name})
        rows.append([name, count, ", ".join(nodes) if nodes else MISSING])
    return rows


def run_summary(run_dir: Path) -> tuple[str, int]:
    warnings: list[str] = []
    run, run_warnings = load_json(run_dir / "run.json")
    events, event_warnings = load_jsonl(run_dir / "events.jsonl")
    latency, latency_warnings = load_csv(run_dir / "latency.csv")
    throughput, throughput_warnings = load_csv(run_dir / "throughput.csv")
    warnings.extend(run_warnings)
    warnings.extend(event_warnings)
    warnings.extend(latency_warnings)
    warnings.extend(throughput_warnings)
    for name in REQUIRED_FILES:
        warning = f"missing {name}"
        if not (run_dir / name).exists() and warning not in warnings:
            warnings.append(warning)

    run_id = get_path(run, "run_id", "id", "metadata.run_id")
    scenario = get_path(run, "scenario_name", "scenario.name", "scenario")
    git_commit = get_path(run, "git_commit", "git.commit", "metadata.git_commit")
    started_at = get_path(run, "started_at", "start_time", "start_timestamp")
    ended_at = get_path(run, "ended_at", "end_time", "end_timestamp")
    decision = get_path(run, "go_no_go", "decision", "result.decision", "summary.decision")
    invalid_reason = get_path(run, "invalid_reason", "validity.reason", "run_validity_reason")
    scheduler_overhead = get_path(
        run,
        "scheduler_overhead_per_token",
        "scheduler_overhead_us_per_token",
        "scheduler_overhead_ms_per_token",
        "metrics.scheduler_overhead_us_per_token",
        "metrics.scheduler_overhead_per_token",
        "metrics.coordinator_overhead_per_token",
    )
    bytes_per_token = get_path(
        run,
        "bytes_per_token",
        "bytes_per_simulated_token",
        "metrics.bytes_sent_per_simulated_token",
        "metrics.bytes_per_token",
    )
    per_layer_transport = get_path(
        run,
        "per_layer_transport_time",
        "simulated_moe.per_layer_transport_time",
        "metrics.per_layer_transport_time_us",
        "metrics.per_layer_transport_time",
    )
    path_text, validity_text = classify_transport(run)

    artifact_rows = []
    for name in REQUIRED_FILES:
        artifact_path = run_dir / name
        artifact_rows.append([name, "yes", "yes" if artifact_path.exists() else "no"])

    lines: list[str] = []
    lines.append("# Phase 0 Transport Run Summary")
    lines.append("")
    lines.extend(
        table(
            ["Field", "Value"],
            [
                ["Run directory", str(run_dir)],
                ["Run ID", value_or_missing(run_id)],
                ["Scenario", value_or_missing(scenario)],
                ["Git commit", value_or_missing(git_commit)],
                ["Started", value_or_missing(started_at)],
                ["Ended", value_or_missing(ended_at)],
                ["Transport path", path_text],
                ["Validity", validity_text],
                ["Go/no-go decision", value_or_missing(decision)],
                ["Invalidation reason", value_or_missing(invalid_reason)],
            ],
        )
    )
    lines.append("")
    lines.append("## Artifact Completeness")
    lines.append("")
    lines.extend(table(["Artifact", "Required", "Present"], artifact_rows))
    lines.append("")
    lines.append("## Scope Note")
    lines.append("")
    if validity_text == "loopback-only":
        lines.append(
            "This run is loopback-only. It can exercise artifact and scheduler paths, but it is not evidence for cluster hardware transport."
        )
    else:
        lines.append(
            "This summary reports transport and simulated-MoE measurements only. It does not measure final model performance."
        )
    lines.append("")
    lines.append("## Latency Percentiles")
    lines.append("")
    if latency:
        lines.extend(
            table(
                ["Node pair", "Message bytes", "Transfers", "p50", "p95", "p99"],
                latency_rows(latency),
            )
        )
    else:
        lines.append(MISSING)
    lines.append("")
    lines.append("## Throughput By Block Size")
    lines.append("")
    if throughput:
        lines.extend(
            table(
                ["Node pair", "Block bytes", "Concurrent links", "Transfers", "Throughput", "Checksum cost"],
                throughput_rows(throughput),
            )
        )
    else:
        lines.append(MISSING)
    lines.append("")
    lines.append("## Concurrent Link Interference")
    lines.append("")
    interference = interference_rows(run)
    if interference:
        lines.extend(
            table(
                ["Node pair", "Solo MiB/s", "Concurrent MiB/s", "Degradation pct"],
                interference,
            )
        )
    else:
        lines.append(MISSING)
    lines.append("")
    lines.append("## Checksums And Failures")
    lines.append("")
    lines.extend(
        table(
            ["Metric", "Value"],
            [
                [
                    "Checksum algorithm",
                    value_or_missing(get_path(run, "checksum_algorithm", "checksums.algorithm")),
                ],
                [
                    "Packets checked",
                    value_or_missing(get_path(run, "packets_checked", "checksums.packets_checked", "checksums.total_transfers")),
                ],
                ["Checksum failures", checksum_failure_count(run, events)],
            ],
        )
    )
    lines.append("")
    lines.append("## Coordinator Overhead")
    lines.append("")
    lines.extend(
        table(
            ["Metric", "Value"],
            [
                ["Scheduler overhead per simulated token", value_or_missing(scheduler_overhead)],
                ["Bytes per simulated token", value_or_missing(bytes_per_token)],
                ["Per-layer simulated transport time", value_or_missing(per_layer_transport)],
            ],
        )
    )
    lines.append("")
    lines.append("## Remote Expert-Rate Sensitivity")
    lines.append("")
    sensitivity = sensitivity_rows(run)
    if sensitivity:
        lines.extend(
            table(
                [
                    "Remote expert rate",
                    "Bytes per simulated token",
                    "Transport time per token",
                    "Upper-bound tokens/sec",
                ],
                sensitivity,
            )
        )
    else:
        lines.append(MISSING)
    lines.append("")
    lines.append("## Event Counts")
    lines.append("")
    if events:
        lines.extend(table(["Event type", "Count", "Nodes"], event_summary(events)))
    else:
        lines.append(MISSING)
    if warnings:
        lines.append("")
        lines.append("## Warnings")
        lines.append("")
        for warning in warnings:
            lines.append(f"- {warning}")

    exit_code = 0
    if not run_dir.exists() or not run_dir.is_dir():
        exit_code = 2
    return "\n".join(lines) + "\n", exit_code


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Summarize DS5 Phase 0 transport artifacts.")
    parser.add_argument("run_dir", type=Path, help="Path to artifacts/runs/<run-id>")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    summary, exit_code = run_summary(args.run_dir)
    sys.stdout.write(summary)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
