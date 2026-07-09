# Phase 0 Transport Finding Writeup Outline

Status: outline for a public technical writeup. Fill only after real run artifacts exist.

## Working Title

`[Positive result: "DS5 Phase 0: Transport Envelope For Qwen3-Shaped MoE Traffic"]`

`[Negative result: "DS5 Phase 0: Where Local Transport Breaks Down For Qwen3-Shaped MoE Traffic"]`

## Thesis

`[One sentence that states the measured result and the decision it supports. Do not claim full-model tokens/sec, quality, or production readiness.]`

## Abstract

`[4-6 sentences. Name the hardware path, scenario, artifact run IDs, strongest measured result, strongest limitation, and go/no-go decision.]`

Required caveat:

`This is a transport and simulated-MoE benchmark. It does not load Qwen3 weights or measure final model performance.`

## Reader Contract

Tell the reader:

- what was measured;
- what was not measured;
- how to reproduce the artifacts;
- which result would change the project direction.

Avoid:

- marketing language;
- benchmark claims without artifact IDs;
- charts that mix loopback and hardware-cluster results without labels;
- final performance projections that are not explicitly marked as transport-derived upper bounds.

## Suggested Structure

1. Problem

   DS5 can fail before model loading if transport, jitter, checksums, worker health, or scheduling overhead dominates decode-shaped MoE traffic.

2. Method

   Describe the A/B/C topology, transport path, scenario config, synthetic packet shapes, checksum policy, warmup policy, and artifact set.

3. Validity

   Explain how the benchmark confirmed the intended path. If the result is loopback-only, single-node-only, or path-invalid, state that before showing charts.

4. Results

   Present latency percentiles, throughput by block size, concurrent-link behavior, checksum failures, coordinator overhead, and remote expert-rate sensitivity.

5. Decision

   Choose proceed, redesign, reduce assumptions, publish limit, or rerun. Tie the choice to the measurements.

6. Limitations

   State that the run does not measure tokenizer, attention, KV cache, expert kernels, quantization quality, or final model tokens/sec.

7. Reproduction

   Link the exact command, run artifacts, schemas, summary script, and figure-generation inputs.

## Core Tables

### Run Metadata

| Field | Value |
|---|---|
| Run ID | `[run_id]` |
| Git commit | `[git_commit]` |
| Scenario | `[scenario_name]` |
| Transport path | `[confirmed path]` |
| Nodes | `[A, B, C labels]` |
| Validity | `[hardware / loopback / invalid / partial]` |

### Decision Snapshot

| Question | Answer |
|---|---|
| Did checksummed packet movement complete? | `[yes/no]` |
| Did concurrent links preserve enough throughput? | `[yes/no/partial]` |
| Did scheduler overhead dominate transfer time? | `[yes/no/partial]` |
| Did worker failure behavior remain traceable? | `[yes/no/partial]` |
| What decision follows? | `[decision]` |

## Core Figures

Use generated figures from `publication/figures/` when available:

- `phase0-latency-percentiles.<ext>`: p50/p95/p99 by message size and node pair.
- `phase0-throughput-block-size.<ext>`: sustained throughput by block size and node pair.
- `phase0-concurrent-link-interference.<ext>`: single-link baseline versus concurrent A-B/A-C traffic.
- `phase0-scheduler-overhead.<ext>`: scheduler overhead compared with simulated transfer time.
- `phase0-remote-expert-rate-sensitivity.<ext>`: transport-derived upper bound by remote expert rate.
- `phase0-health-events.<ext>`: worker timeout, retry, reconnect, and checksum-failure timeline.

Every caption should include the run ID, scenario, transport path, and whether the data is hardware-cluster or loopback-only.

## Positive Result Path

Use this framing only when artifacts support it:

`The Phase 0 transport envelope is sufficient to justify model metadata inspection and placement simulation under the measured remote expert-rate assumptions. The result does not prove full-model inference performance; it narrows the next risk to placement, memory, and runtime execution.`

Required evidence:

- hardware path confirmed;
- checksum failures are zero or explained;
- latency and throughput are repeatable across A-B and A-C;
- concurrent-link behavior does not invalidate Node A coordination;
- scheduler overhead is not material relative to transfer time for the scenario;
- remote expert-rate sensitivity has an operating region that remains plausible.

## Negative Result Path

Use this framing when transport or scheduling fails cleanly:

`The Phase 0 transport envelope is not compatible with the intended simulated decode-shaped traffic under the measured conditions. This is the publishable finding: the architecture should pivot before transformer runtime work.`

Required evidence:

- the run is valid enough to trust the negative result;
- the limiting factor is visible in latency, throughput, concurrency, checksum, scheduler, or health artifacts;
- the writeup names the next architectural response instead of hiding the failure.

## Invalid Or Partial Result Path

Use this framing when the run cannot support a positive or negative claim:

`The artifacts are useful for debugging but not sufficient for a hardware-cluster finding. The benchmark must rerun after fixing path confirmation, artifact coverage, checksums, or trace validity.`

Examples:

- traffic used loopback or Wi-Fi fallback when a hardware link was intended;
- required artifacts are missing;
- checksums were disabled or unreported;
- worker health events make trace correlation unreliable;
- schema fields are too sparse to reproduce the result.

## Reproducibility Checklist

- exact command lines;
- run artifact directory;
- schema or field spec version;
- git commit;
- scenario config path and digest;
- node labels and roles;
- transport path confirmation;
- summary script output;
- figure source data and generation command.

## Closing Decision

End with one of:

- `Proceed to model metadata inspection and placement simulation.`
- `Redesign packetization or scheduler before model work.`
- `Reduce the remote expert movement assumption and rerun.`
- `Publish the measured transport limit and pivot.`
- `Rerun because this artifact set is not valid for a finding.`

Do not end with speculative final model performance claims.
