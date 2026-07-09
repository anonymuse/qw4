# Agent C: Loopback Transport Prototype

## Objective

Create the first transport smoke path. It may run on localhost, but it must use the same artifact shape intended for the real A/B/C cluster.

## Read First

- `docs/minimum-viable-finding.md`
- `docs/runbooks/cluster-setup.md`
- Agent A handoff if available
- Agent B schemas if available

## Owned Paths

- `src/transport/`
- transport-specific tests under `tests/`
- small edits to `src/coordinator/` and `src/worker/` only to wire the transport command

## Deliverables

Implement or stub a loopback transport command that can exercise:

- worker listener;
- coordinator connection;
- ping/pong;
- fixed-size block transfer;
- checksum;
- per-message timing;
- JSON/CSV artifact writing through the agreed schema.

Target commands:

```bash
zig build run-worker -- --node B --listen 127.0.0.1:7555
zig build run-coordinator -- \
  --config configs/cluster.local.example.toml \
  --scenario benchmarks/scenarios/loopback_transport_smoke.toml \
  --out artifacts/runs/loopback-smoke
```

If concurrent processes are awkward in the first pass, create a single-process loopback test that uses the same protocol and output artifact formats.

## Metrics To Capture

- message size;
- transfer count;
- bytes sent;
- checksum failures;
- min latency;
- p50 latency;
- p95 latency;
- p99 latency;
- elapsed time;
- throughput bytes/sec.

## Acceptance Checks

Run the smallest local smoke command available and ensure artifacts are written under `artifacts/runs/`.

If the benchmark only runs as a test:

```bash
zig build test
```

## Do Not

- Do not claim real Thunderbolt performance from localhost.
- Do not implement per-expert packetization.
- Do not introduce async complexity before a blocking path works.
- Do not add external networking libraries.

## Handoff Notes

Report:

- exact command run;
- artifact path;
- known limitations;
- how to move from loopback to two real worker nodes.

