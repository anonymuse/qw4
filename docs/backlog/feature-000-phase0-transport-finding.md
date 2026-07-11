# Feature DS5-F000: Phase 0 Transport Finding

Status: next target-hardware finding after `DS5-F001A` completion in PR #19; Phase 0 scaffolding exists, target-hardware finding not complete.

Epic: `DS5-E02: Routing Transport`

Complexity Score: 7/10 for target-hardware measurement, artifact discipline, and scheduler/transport analysis.

Validation Gate: `PM-GATE-PH0-01: Phase 0 Transport And Simulated-MoE Finding`

Governing baseline: [Minimum Viable Finding](../minimum-viable-finding.md), [ADR-002](../decisions/ADR-002-phase0-transport-first.md), and [Phase 0 Transport Finding Template](../findings/phase0-transport-template.md).

## Technical Scope

Measure whether the DS5 A/B/C topology can move synthetic Qwen-shaped activation/result packets while Node A acts as the M5 Pro orchestrator/control plane and Nodes B/C act as M5 Max synthetic LLM data-plane workers.

The refined Phase 0 question is:

> Can an M5 Pro orchestrator agent keep two M5 Max synthetic LLM data-plane workers fed with Qwen3-shaped activation/result traffic without transport, scheduling, or control-plane overhead dominating decode-shaped work?

This feature uses simulated MoE traffic. It does not load Qwen weights, run tokenizer assets, implement speculative decoding, allocate KV cache pages, or execute Metal kernels.
It also does not make active SSD/NVMe decode-path claims. Model-independent
storage measurements may be collected only as separate adjunct evidence for
future cold backing, promotion, artifact movement, or long-context backing.

Existing implementation signals:

- Transport scaffolding and benchmark artifact schemas exist.
- The Phase 0 routing-payload scaffold validates synthetic Qwen-shaped record shape, B/C target-node bounds, and zero-copy planning assumptions as preparatory schema/test evidence for this feature.
- The repository defines the first publishable milestone in `docs/minimum-viable-finding.md`.
- Loopback and local smoke findings are useful scaffolding evidence, not acceptance-hardware proof.
- Artifact readiness prep is tracked in
  `docs/runbooks/ds5-f000-artifact-readiness.md`; it tightens schema/report
  validation but does not replace the required target A/B/C run.
- The target-hardware operator sequence is tracked in
  `docs/runbooks/ds5-f000-cluster-operator-packet.md`; it turns the Phase 0
  plan into exact A/B/C preflight, worker, coordinator, validation, and
  publication commands.
- The routing-payload scaffold is not target-hardware transport evidence, measured copy-count telemetry, or DS5-F002 runtime progress.

## Rigid Acceptance Criteria

- Runs execute on the intended A/B/C hardware topology or clearly label any degraded topology.
- Output includes `run.json`, `events.jsonl`, `latency.csv`, `throughput.csv`, and `summary.md`.
- Artifacts report p50/p95/p99 latency by message size.
- Artifacts report sustained throughput by block size.
- Artifacts report scheduler overhead per simulated token.
- Artifacts report control-plane overhead or explicitly state when scheduler
  overhead is the current control-plane proxy.
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
- Any use of SSD/NVMe measurements as proof that active decode can depend on
  storage in the steady-state hot path.

## Artifact Readiness Gate

Before target-hardware evidence is attached, `tools/report/validate_run.py` must
pass on every referenced run directory. The validator is expected to reject
partial artifacts that omit A-B/A-C latency coverage, block-size throughput
coverage, concurrent-link rows, checksum-failure events, worker health,
reconnect counters, scheduler overhead, or projected decode-impact formula
inputs.

- Any reading of the routing-payload scaffold or its zero-copy design budget as measured copy-count telemetry.
