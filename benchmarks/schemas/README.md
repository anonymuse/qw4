# Phase 0 Benchmark Artifact Schemas

Schema version: `phase0.artifacts.v1`.

Every Phase 0 benchmark run emits exactly these required artifact names in one
run directory:

- `run.json`
- `events.jsonl`
- `latency.csv`
- `throughput.csv`
- `summary.md`

All timestamps are UTC RFC 3339 strings with a trailing `Z`. Latency values are
microseconds unless the field name says otherwise. Throughput rows report both
MiB/s and Gbit/s to avoid hidden unit conversions in later reporting.

## `run.json`

`run.json` is the run-level manifest. It must be valid UTF-8 JSON and conform to
`run.schema.json`.

Required content:

| Field | Meaning |
|---|---|
| `schema_version` | Must be `phase0.artifacts.v1`. |
| `run_id` | Stable run directory identifier. |
| `git_commit` | Forty-character lowercase hex commit for the code that emitted artifacts. |
| `software` | Benchmark binary/tool name and version string. |
| `started_at`, `ended_at`, `duration_ms` | Run wall-clock bounds and elapsed duration. |
| `valid` | Whether the run may be interpreted for technical findings. |
| `environment` | Network path, clock sync note, and whether results are real hardware data. |
| `scenario` | Scenario name, config path, message sizes, block sizes, transfer counts, checksum mode, and Qwen-shaped MoE parameters. |
| `nodes` | Node IDs, roles, hostnames or stable labels, hardware labels, and transport labels. |
| `checksums` | Algorithm, total transfers, passed/failed counts, and status. |
| `failure_counts` | Count of failures, retries, reconnects, and timeouts. |
| `metrics` | Required latency, throughput, scheduler, per-layer, concurrent-link, and predicted token/sec metrics. |
| `artifacts` | File names for the other four artifacts. |

The schema is intentionally strict. Missing required metrics should fail
validation instead of becoming empty report cells.

## `events.jsonl`

`events.jsonl` is newline-delimited JSON. Each line is one event object and must
conform to `event.schema.json`.

Every event requires:

| Field | Meaning |
|---|---|
| `schema_version` | Must be `phase0.artifacts.v1`. |
| `run_id` | Same value as `run.json`. |
| `sequence` | Zero-based monotonically increasing integer. |
| `timestamp` | UTC RFC 3339 event timestamp. |
| `event_type` | One of the event types in `event.schema.json`. |
| `severity` | `debug`, `info`, `warn`, or `error`. |
| `details` | Object for extra structured context. |

Important type-specific requirements:

| Event type | Required additional fields |
|---|---|
| `node_discovered` | `node_id`, `hostname`, `latency_us` |
| `worker_health` | `node_id`, `health_status` |
| `latency_sample` | `node_pair`, `message_size_bytes`, `latency_us`, `checksum_status` |
| `throughput_sample` | `node_pair`, `block_size_bytes`, `bytes_sent`, `throughput_mib_s`, `checksum_status` |
| `checksum_verified` | `transfer_id`, `checksum_status`, `bytes_sent` |
| `retry_scheduled` | `failure_kind`, `retry_count` |
| `reconnect_succeeded` | `node_id`, `retry_count`, `latency_us` |
| `simulated_layer_transfer` | `layer_index`, `node_pair`, `bytes_sent`, `latency_us` |
| `run_completed` | `valid` |

Failure and retry behavior is represented as events. A clean run may have zero
failure/retry events, but any non-zero counters in `run.json.failure_counts`
must be backed by matching event rows.

## `latency.csv`

`latency.csv` must use the exact header described in
`latency.csv.schema.json`.

Columns:

| Column | Meaning |
|---|---|
| `schema_version` | Must be `phase0.artifacts.v1`. |
| `run_id` | Same value as `run.json`. |
| `node_pair` | Ordered pair such as `A-B`. |
| `direction` | `request`, `response`, or `round_trip`. |
| `message_size_bytes` | Payload size measured. |
| `sample_count` | Samples included in percentile calculation. |
| `warmup_count` | Warmup transfers excluded from samples. |
| `transfer_count` | Total measured transfers. |
| `checksum_algorithm` | Algorithm used for checked payloads. |
| `checksum_failures` | Failed checksum count for this row. |
| `p50_us`, `p95_us`, `p99_us` | Percentile latency. |
| `min_us`, `max_us`, `jitter_us` | Bounds and `p99_us - p50_us`. |
| `remote_expert_rate` | Simulated remote expert rate for this row. |
| `scenario_step` | Human-stable step label. |

## `throughput.csv`

`throughput.csv` must use the exact header described in
`throughput.csv.schema.json`.

Columns:

| Column | Meaning |
|---|---|
| `schema_version` | Must be `phase0.artifacts.v1`. |
| `run_id` | Same value as `run.json`. |
| `node_pair` | Ordered pair such as `A-C`. |
| `direction` | `send`, `receive`, or `round_trip`. |
| `block_size_bytes` | Payload block size. |
| `transfer_count` | Count of measured transfers. |
| `bytes_sent` | Total bytes sent for this row. |
| `checksum_algorithm` | Algorithm used for checked payloads. |
| `checksum_failures` | Failed checksum count for this row. |
| `duration_ms` | Measured transfer window. |
| `mib_per_sec` | Sustained throughput in MiB/s. |
| `gbps` | Sustained throughput in decimal Gbit/s. |
| `concurrent_links` | Comma-separated active ordered pairs, or `none`. |
| `remote_expert_rate` | Simulated remote expert rate for this row. |
| `scenario_step` | Human-stable step label. |

## `summary.md`

`summary.md` is the human-readable run summary. It must include the headings and
minimum facts described in `summary.md.schema.json`.

Minimum headings:

- `# <run title>`
- `## Run`
- `## Scenario`
- `## Nodes`
- `## Latency`
- `## Throughput`
- `## Reliability`
- `## Interpretation`

Minimum facts:

- run ID;
- git commit;
- start and end timestamps;
- validity;
- scenario name;
- node roles and labels;
- p50/p95/p99 latency summary;
- sustained throughput summary;
- checksum failure count;
- failure, retry, reconnect, and timeout counts;
- predicted upper-bound tokens/sec by remote-expert-rate scenario;
- whether the result is synthetic, loopback, or real cluster data.

## Validation

The standard-library validator checks the artifact set:

```bash
python3 tools/report/validate_run.py tests/fixtures/artifacts/transport-smoke
```

The validator intentionally duplicates the v1 contract in Python instead of
depending on a third-party JSON Schema package.

## Provisional Fields

These fields may evolve once the Zig coordinator exists:

- exact `software.version` format;
- detailed `environment.network_path` vocabulary;
- names of `scenario_step` labels;
- predicted token/sec model inputs.

Changing a required field name or unit requires a new schema version.


## Schema Evolution Notes

`phase0.artifacts.v1` now distinguishes transport interpretation from transport
mechanics:

- `environment.transport_mode` may be `single_process_loopback`,
  `socket_localhost`, or `real_cluster`.
- `environment.socket_mode` records whether the run used in-process framing,
  TCP localhost sockets, or TCP network sockets.
- `environment.confirmed_network_path` is empty unless the operator records the
  actual non-loopback path used for the run.
- `environment.hardware_interpretable` must be false for loopback and localhost
  paths, even when real TCP sockets were used.

Adding optional fields inside `environment` is compatible with
`phase0.artifacts.v1`. Renaming required fields or changing units requires a new
schema version.
