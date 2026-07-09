# Feature DS5-F000: Phase 0 Transport Finding

Status: next target-hardware finding after `DS5-F001A` completion in PR #19; Phase 0 scaffolding exists, target-hardware finding not complete.

Epic: `DS5-E02: Routing Transport`

Complexity Score: 7/10 for target-hardware measurement, artifact discipline, and scheduler/transport analysis.

Validation Gate: `PM-GATE-PH0-01: Phase 0 Transport And Simulated-MoE Finding`

Governing baseline: [Minimum Viable Finding](../minimum-viable-finding.md), [ADR-002](../decisions/ADR-002-phase0-transport-first.md), and [Phase 0 Transport Finding Template](../findings/phase0-transport-template.md).

## Technical Scope

Measure whether the DS5 A/B/C topology can move synthetic Qwen-shaped activation/result packets without transport and coordinator scheduling overhead dominating decode-shaped work.

This feature uses simulated MoE traffic. It does not load Qwen weights, run tokenizer assets, implement speculative decoding, allocate KV cache pages, or execute Metal kernels.

Existing implementation signals:

- Transport scaffolding and benchmark artifact schemas exist.
- The Phase 0 routing-payload scaffold validates synthetic Qwen-shaped record shape, B/C target-node bounds, and zero-copy planning assumptions as preparatory schema/test evidence for this feature.
- The repository defines the first publishable milestone in `docs/minimum-viable-finding.md`.
- Loopback and local smoke findings are useful scaffolding evidence, not acceptance-hardware proof.
- Artifact readiness prep is tracked in
  `docs/runbooks/ds5-f000-artifact-readiness.md`; it tightens schema/report
  validation but does not replace the required target A/B/C run.
- The routing-payload scaffold is not target-hardware transport evidence, measured copy-count telemetry, or DS5-F002 runtime progress.

## Rigid Acceptance Criteria

- Runs execute on the intended A/B/C hardware topology or clearly label any degraded topology.
- Output includes `run.json`, `events.jsonl`, `latency.csv`, `throughput.csv`, and `summary.md`.
- Artifacts report p50/p95/p99 latency by message size.
- Artifacts report sustained throughput by block size.
- Artifacts report scheduler overhead per simulated token.
- Artifacts report bytes sent per simulated token and per-layer simulated transport time.
- Artifacts report concurrent A-B and A-C interference.
- Artifacts report checksum failures, reconnect behavior, and worker health.
- The summary states whether the result supports continued distributed decode work, requires packetization/scheduling redesign, requires lower remote expert movement assumptions, or argues for publishing a negative finding.

## PM Validation Evidence

The merge request must attach or reference:

- command lines used for workers and coordinator;
- machine-readable run artifacts;
- human-readable finding summary;
- hardware and network topology notes;
- validation output for artifact schema checks.
- routing-payload scaffold validation only as preparatory schema/test evidence, if referenced.

## Merge Blockers

- Any claim that loopback-only evidence proves Thunderbolt or target-hardware viability.
- Any performance claim that omits p95/p99 latency or scheduler overhead.
- Any transport result without checksummed artifacts.
- Any move into fused routing, tokenizer, prefetch, model loading, or Metal kernels before this feature reaches a clear go/no-go.

## Artifact Readiness Gate

Before target-hardware evidence is attached, `tools/report/validate_run.py` must
pass on every referenced run directory. The validator is expected to reject
partial artifacts that omit A-B/A-C latency coverage, block-size throughput
coverage, concurrent-link rows, checksum-failure events, worker health,
reconnect counters, scheduler overhead, or projected decode-impact formula
inputs.

- Any reading of the routing-payload scaffold or its zero-copy design budget as measured copy-count telemetry.
