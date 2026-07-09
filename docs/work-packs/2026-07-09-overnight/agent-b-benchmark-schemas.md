# Agent B: Benchmark Schemas And Fixtures

## Objective

Define the machine-readable artifact contract for Phase 0 and create small sample fixtures. The transport and simulated-MoE benchmark should be impossible to run without producing structured output.

## Read First

- `docs/minimum-viable-finding.md`
- `docs/decisions/ADR-002-phase0-transport-first.md`
- `docs/runbooks/cluster-setup.md`

## Owned Paths

- `benchmarks/schemas/`
- `tests/fixtures/artifacts/`
- `tests/fixtures/scenarios/`
- `tools/report/validate_run.py` if useful and coordinated with Agent F

## Deliverables

Define schemas or documented field specs for:

- `run.json`;
- `events.jsonl`;
- `latency.csv`;
- `throughput.csv`;
- `summary.md` minimum content.

The schemas must include:

- run ID;
- git commit;
- start and end timestamps;
- node roles;
- hostnames or stable node labels;
- scenario name;
- message sizes;
- transfer counts;
- checksum status;
- p50/p95/p99 latency;
- throughput;
- failure and retry events.

Create at least one valid sample fixture:

```text
tests/fixtures/artifacts/transport-smoke/run.json
tests/fixtures/artifacts/transport-smoke/events.jsonl
tests/fixtures/artifacts/transport-smoke/latency.csv
tests/fixtures/artifacts/transport-smoke/throughput.csv
tests/fixtures/artifacts/transport-smoke/summary.md
```

## Acceptance Checks

If a validator is created:

```bash
python3 tools/report/validate_run.py tests/fixtures/artifacts/transport-smoke
```

If no validator is created, include exact validation rules in `benchmarks/schemas/README.md`.

## Do Not

- Do not make schemas so loose that missing metrics pass silently.
- Do not use binary-only artifact formats.
- Do not depend on cloud services, databases, or external packages.
- Do not include real credentials, host secrets, or private paths in fixtures.

## Handoff Notes

Report:

- schema decisions;
- sample fixture paths;
- validator command, if any;
- fields that remain provisional.

