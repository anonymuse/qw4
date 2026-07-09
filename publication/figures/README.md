# Phase 0 Figure Guidelines

Figures in this directory must be generated from real Phase 0 artifacts. Do not draw target curves, estimated hardware numbers, or placeholder charts that could be mistaken for measurements.

## Inputs

Expected source artifacts:

- `artifacts/runs/<run-id>/run.json`;
- `artifacts/runs/<run-id>/events.jsonl`;
- `artifacts/runs/<run-id>/latency.csv`;
- `artifacts/runs/<run-id>/throughput.csv`;
- `artifacts/runs/<run-id>/summary.md`.

Each figure should record:

- run ID;
- scenario name;
- git commit;
- transport path;
- whether the data is hardware-cluster, loopback-only, or invalid/partial;
- source artifact file names.

## Required Labels

Every figure caption must make these distinctions clear:

- hardware-cluster data versus loopback data;
- measured transport metrics versus simulated MoE sensitivity;
- valid runs versus partial or invalid runs;
- upper-bound transport estimates versus final model performance.

## Suggested Figures

| File name | Source | Purpose |
|---|---|---|
| `phase0-latency-percentiles.<ext>` | `latency.csv` | p50/p95/p99 round-trip latency by message size and node pair |
| `phase0-throughput-block-size.<ext>` | `throughput.csv` | sustained throughput by block size and node pair |
| `phase0-concurrent-link-interference.<ext>` | `throughput.csv`, `events.jsonl` | single-link baseline compared with concurrent A-B and A-C transfers |
| `phase0-scheduler-overhead.<ext>` | `run.json`, `events.jsonl` | coordinator overhead per simulated token compared with transfer time |
| `phase0-remote-expert-rate-sensitivity.<ext>` | `run.json`, scenario summary | transport-derived upper-bound tokens/sec by remote expert rate |
| `phase0-health-events.<ext>` | `events.jsonl` | worker timeout, retry, reconnect, and checksum-failure timeline |

Use `.svg` for editable vector plots or `.png` for bitmap exports. Keep the source data and generation command in the writeup or adjacent notes.

## Caption Template

```text
Figure N. [Metric being shown]. Run: [run_id]. Scenario: [scenario_name].
Transport path: [hardware path]. Validity: [hardware-cluster / loopback-only / partial / invalid].
Source: [artifact file]. This figure shows [measured transport / simulated sensitivity] and does not measure final model performance.
```

## Review Checklist

- No fake or hand-drawn measurement data.
- Axes include units.
- Node pairs and message or block sizes are visible.
- Loopback-only charts are labeled in the title or caption.
- Error, retry, checksum, or invalid-run notes are not hidden.
- Remote expert-rate plots are labeled as simulation or upper-bound analysis.
- A reader can trace each plotted value back to a machine-readable artifact.
