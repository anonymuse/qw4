# Phase 0 Reporting Tools

This directory contains local reporting utilities for DS5 Phase 0 benchmark artifacts. Reporting tools must summarize measurements without inventing missing fields or turning transport simulations into final model performance claims.

Agent B may add `tools/report/validate_run.py`. If present, treat it as the schema validator and do not replace it from this reporting path.

## Expected Artifact Directory

```text
artifacts/runs/<run-id>/
  run.json
  events.jsonl
  latency.csv
  throughput.csv
  summary.md
```

## Summarize A Run

```bash
python3 tools/report/summarize_phase0.py artifacts/runs/<run-id>
```

The script writes a Markdown summary to stdout. It is intentionally not a validator; it reports missing files or fields as missing.

Useful redirect:

```bash
python3 tools/report/summarize_phase0.py artifacts/runs/<run-id> > artifacts/runs/<run-id>/report-summary.md
```

## What The Summary Surfaces

- run identity and scenario;
- hardware or loopback transport path;
- artifact completeness;
- why loopback results are not hardware-cluster claims;
- latency percentiles by message size;
- throughput by block size;
- checksum failures;
- coordinator or scheduler overhead when present;
- remote expert-rate sensitivity when present;
- health, retry, reconnect, and failure event counts;
- go/no-go decision when present.

## Fields Needed From Schemas

The reporting path works best when Agent B/C artifacts include:

- `run_id`, `schema_version`, `git_commit`, `started_at`, `ended_at`;
- `scenario_name`, scenario config path or digest, message sizes, block sizes, transfer counts;
- node IDs, roles, host labels, hardware labels, OS versions, memory, and transport addresses;
- confirmed transport path and a loopback or hardware-path flag;
- run validity status and invalidation reason;
- latency CSV columns for node pair, message size bytes, transfer count, p50, p95, and p99;
- throughput CSV columns for node pair, block size bytes, transfer count, and sustained throughput;
- checksum algorithm, packets checked, failure count, and checksum-failure events;
- scheduler overhead per simulated token, bytes per simulated token, and per-layer simulated transport time;
- remote expert-rate sensitivity rows with remote expert rate, local expert rate, bytes per token, simulated transport time, scheduler overhead input, formula text, and transport-derived upper-bound tokens/sec;
- event records with timestamp, event type, node ID, severity, retry count, timeout duration, bytes sent, bytes acknowledged, and validity impact.

If a field is absent, reporting should show `not reported` rather than guessing.


## Aggregate And Comparison Reports

Use the aggregate helper to compare repeated runs or to show missing result
classes explicitly:

```bash
python3 tools/report/aggregate_phase0.py --root artifacts/runs
```

The report always keeps loopback, socket-localhost, and real-cluster categories
separate so local smoke data cannot be mistaken for hardware transport data.
