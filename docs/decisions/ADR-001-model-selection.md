# ADR-001: Select Qwen3-235B-A22B As DS5 Target Model

Status: accepted.

Date: 2026-07-09.

Supersedes: dense-70B-final, Mixtral-8x22B-final, DeepSeek-V3/R1-final, Kimi-K2-final, JW4/Gemma-as-main-target, and generalized-runtime assumptions.

## Decision

DS5 will use `Qwen3-235B-A22B` as the target model.

The first runtime target is:

```text
Qwen3-235B-A22B-Instruct-2507
```

The thinking variant is deferred:

```text
Qwen3-235B-A22B-Thinking-2507
```

The thinking variant is not part of the first stable execution path.

## Rationale

Qwen3-235B-A22B is the best fit for DS5 because it combines:

- large total model capacity;
- a 22B activated-parameter path;
- sparse MoE structure;
- GQA-based KV efficiency;
- expert placement and promotion opportunities;
- enough scale to justify a narrow local distributed runtime.

Dense 32B-70B models remain useful for bring-up and comparison, but they are not the final target.

Mixtral 8x22B remains useful as an intermediate MoE comparator, but it is not the final target.

DeepSeek-V3/R1 and Kimi-K2 full checkpoints are rejected as final targets for the initial DS5 topology because they exceed safe resident-memory assumptions.

Gemma/JW4 is archived or split as a separate precursor effort.

## Consequences

The runtime must support:

- 94-layer MoE scheduling;
- 128 experts per MoE layer;
- top-8 routing;
- exact Qwen routing semantics;
- B/C worker ownership of layer ranges;
- local router mirrors after correctness validation;
- tensor-aware quantization;
- expert hotness telemetry;
- explicit placement manifests;
- KV behavior measured first at 8K-32K context.

## Non-Negotiable Rules

1. Do not alter model top-k routing to force locality.
2. Do not use NVMe as the steady-state active-weight path.
3. Do not aggressively quantize router/gate tensors without evidence.
4. Do not claim long-context or throughput targets before benchmark artifacts exist.
5. Do not treat BitNet-style conversion as a safe post-training quantization path without a separate research result.

## Review Triggers

Review this ADR only if:

- the hardware topology changes materially;
- official Qwen3-235B-A22B artifacts become unavailable or unsuitable;
- Phase 0 proves distributed decode traffic is physically implausible;
- Phase 2 or later quantization work shows unacceptable quality loss;
- a Qwen successor has a materially better active/total footprint and compatible license.

