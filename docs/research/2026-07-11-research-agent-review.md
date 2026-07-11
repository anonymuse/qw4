# Research Agent Review And Recommended DS5 Direction

Status: draft for PM and coding-team review.

Prepared: 2026-07-11.

Research inputs reviewed:

- `/Users/jessewhite/Downloads/QW3/Gemini-arch-review 20260710/Gemini-arch-review 20260710.md`
- `/Users/jessewhite/Downloads/QW3/Gemini-20260710-a/Gemini-20260710-a.md`

Repo baselines used:

- `README.md`
- `docs/assumptions.md`
- `docs/minimum-viable-finding.md`
- `docs/backlog/project-plan.md`
- `docs/backlog/README.md`
- `docs/risk-register.md`
- `docs/decisions/ADR-001-model-selection.md`
- `docs/decisions/ADR-002-phase0-transport-first.md`
- `docs/backlog/feature-000-phase0-transport-finding.md`
- `docs/backlog/feature-002-fused-gating-zero-copy-routing.md`
- `docs/backlog/feature-003-asymmetric-quantization-pipeline.md`
- `docs/backlog/feature-004-async-rolling-prefetch-buffer.md`
- `docs/backlog/feature-005-localized-metal-kernel-fragmentation.md`

## Executive Recommendation

DS5 should keep its current narrow thesis, but sharpen the public framing around an evidence-first question:

> Can a small Apple Silicon cluster produce a reproducible, useful finding about Qwen3-shaped MoE transport and placement on local hardware?

That is the viral project. The hook is not "we built another inference framework" or "we beat data-center GPUs." The hook is an audacious, inspectable experiment: three consumer/prosumer Macs, a huge Apache-licensed MoE target, Zig systems work, raw benchmark artifacts, and a willingness to publish either a surprising success or a clean negative result.

The research agent correctly identified the cultural momentum around local, model-specific inference projects such as DwarfStar/ds4 and around open-weight MoE models. It also mixed together several claims that should not enter DS5's core roadmap yet: raw Thunderbolt/RDMA assumptions, kernel-driver work, logits ensembling, speculative tree decoding, 1M context, low-bit quality, and PRM/filter-gating. Those ideas are interesting, but most of them are either not aligned with exact Qwen semantics or are blocked by DS5's already accepted gates.

Recommended approach:

1. Incorporate the ds4-style inspiration as positioning: narrow model target, serious validation, model-specific runtime, open artifacts.
2. Incorporate Thunderbolt 5 and Zig specialization only as measured engineering hypotheses.
3. Defer speculative decoding, KV/NVMe work, quantization claims, and Metal kernels until the current Phase 0 and placement gates justify them.
4. Discard logits-ensemble and perplexity-selection work from the DS5 core path because it changes the project from exact Qwen3 execution into model fusion.
5. Package the first public milestone as a polished research artifact, not a product launch.

## Refined Project Goals

### Product Goal

Make DS5 the credible home-lab benchmark for local distributed MoE inference physics: transport, scheduling, placement, and artifacts for a Qwen3-235B-A22B-shaped workload on Apple Silicon.

### Engineering Goal

Build the smallest measurable model-specific system that can answer DS5's first hard question before any full-runtime work:

> Can the M5 Pro coordinator and two M5 Max workers move Qwen3-shaped activation/result traffic without transport and scheduling overhead dominating decode-shaped work?

### Open-Source Goal

Earn attention through reproducibility and restraint:

- publish commands, configs, and machine-readable artifacts;
- show latency and throughput distributions, not cherry-picked averages;
- make negative results first-class;
- explain exactly what is measured and what is still only planned;
- compare against existing local inference projects respectfully and technically.

### Public Narrative

Recommended public phrasing:

> DS5 is an evidence-first experiment in whether a small Apple Silicon cluster can make a Qwen3-235B-A22B-shaped MoE runtime plausible. Phase 0 does not run the model. It measures the transport and scheduler physics that decide whether the runtime is worth building.

Avoid public phrasing that suggests:

- DS5 already runs the full model;
- Thunderbolt 5 behaves like real RDMA;
- three 48GB machines are a single 144GB shared-memory computer;
- 1M-token context is practical on this topology;
- speculative decoding or logits fusion are already part of the runtime;
- DS5 will outperform data-center GPUs.

## Findings Disposition

| Research-agent recommendation | Assessment | Recommended action | Gate or owner |
|---|---|---|---|
| Use antirez/ds4 as inspiration. | Strong fit at the product-positioning level. ds4's narrow, model-specific, local inference posture is the right cultural comparison. | Incorporate as a comparison and inspiration section in future public writeups. Do not clone ds4's exact model, storage, or protocol assumptions. | PM plus docs. |
| Build around a narrow model-specific runtime instead of a general framework. | Strong fit. This matches the README, ADR-001, and the risk register. | Incorporate. Preserve DS5 as Qwen3-235B-A22B-specific through Phase 0/1. | All teams. |
| Treat Thunderbolt 5 as a low-latency peer fabric. | Plausible but unproven. Apple advertises M5 Pro/Max Thunderbolt 5 up to 120Gb/s, but DS5 still needs latency, copy, jitter, and concurrency evidence. | Incorporate as the Phase 0 hypothesis only. Measure before any runtime claim. | DS5-F000. |
| Bypass POSIX sockets with IOKit or kernel-level driver work. | Too early and too risky. It creates a kernel/debugging project before DS5 proves the ordinary path is inadequate. | Discard for Phase 0. Start with OS-supported Thunderbolt networking and custom user-space framing. Revisit only if measured copy/latency data requires it. | DS5-F000, later ADR if needed. |
| Use Network.framework/custom framing. | Reasonable as a later user-space experiment if TCP results expose framing overhead. | Defer behind the basic transport run. Add only as a controlled A/B benchmark, not as the default assumption. | DS5-F000 follow-up. |
| Split by MoE expert space instead of sequential layers. | Interesting, but it conflicts with the current layer-ownership plan and would need measured routing/hotness evidence. | Defer. Keep B owning layers 0-46 and C owning 47-93 through current gates. Reconsider expert partitioning only after F001B telemetry. | DS5-F001B or later ADR. |
| Use Zig comptime specialization. | Strong fit as a later implementation style, but the research notes used stale/wrong constants in places. | Incorporate the principle, not the shown constants. Always source Qwen constants from pinned metadata and validators. | Runtime work after gates. |
| Preallocate maximum 1M context. | Does not fit the DS5 hardware envelope. Qwen's model card warns that 1M context requires roughly 1000GB total GPU memory. | Discard for DS5's initial runtime. Keep 8K-32K first, 64K stretch, 128K+ research-only. | PM guardrail. |
| Build a ring-buffer KV cache. | Technically plausible but not part of the first finding. | Defer to KV/runtime work after transport and placement evidence. | Later runtime feature. |
| Use shared-nothing logits ensembling, PackLLM, and perplexity selection. | Poor fit for DS5 core. PackLLM is model fusion, not exact execution of one Qwen3 MoE checkpoint. It would change semantics and confuse the thesis. | Discard from DS5 core. Optional separate experiment only if branded as model fusion, not DS5 runtime. | PM decision if separate project. |
| Transmit only sparse top-K logits. | Safe only if DS5 is doing an approximate/fusion demo. It is not safe for exact sampling unless the full distribution remains available where sampling occurs. | Do not adopt for the core runtime. Consider only as a measured approximate mode after exact mode exists. | Later optional experiment. |
| Use Low-Perplexity Token Selection / STM to filter low-confidence tokens. | The cited low-perplexity paper is about fine-tuning/forgetting, not a direct DS5 inference protocol. | Discard from the DS5 roadmap. | PM. |
| Add speculative tree drafting / DiP-SD on Node A. | Interesting but premature. The DiP-SD result is for a distributed edge scenario with Qwen3-1.7B/Qwen3-32B, not DS5's single-user Qwen3-235B target. | Defer to a post-baseline experiment. Do not cite the 17.89x result as a DS5 expectation. | New post-F002 feature only. |
| Put a PRM/filter-gating model on Node A. | Poor fit now. It puts Node A back on the critical path and changes generation behavior before exact correctness exists. | Discard for core Phase 0/1. Revisit as an agent-quality layer only after a correct baseline runtime. | Later product experiment. |
| Push KV/cache or cold data to NVMe. | ds4 makes this culturally relevant, but DS5 already forbids steady-state active-weight decode from NVMe. KV/storage work is later and must be measured. | Defer. Keep NVMe out of the Phase 0 story except as a future risk area. | DS5-F004 or later. |
| Claim raw DMA-like Thunderbolt/RDMA behavior. | Unsafe. DS5 must measure copy counts and OS overhead. | Discard the claim language. Use "Thunderbolt/RDMA-style hypothesis" or "high-speed local interconnect" until measured. | Docs and PM. |

## Recommended Roadmap Adjustment

The existing gate order is correct and should not be relaxed for virality:

1. Finish local artifact rehearsal if target hardware is unavailable.
2. Run DS5-F000 on the real A/B/C topology.
3. Publish the Phase 0 finding, including a go/no-go recommendation.
4. Complete DS5-F001B runtime placement evidence only if Phase 0 supports the direction.
5. Start DS5-F002 fused routing only after Phase 0 data says the transport path is worth optimizing.

The change is not the order. The change is how the team packages Phase 0.

Recommended Phase 0 public package:

- one plain-language summary with the sharp question and answer;
- one diagram of the A/B/C topology;
- one claims ledger separating measured evidence from assumptions;
- raw `run.json`, `events.jsonl`, `latency.csv`, `throughput.csv`, and `summary.md`;
- latency and throughput charts from the artifacts;
- a "negative result is still useful" section;
- a short comparison to ds4, llama.cpp, MLX-LM, vLLM, and SGLang that explains DS5's niche without denigrating existing projects.

## Coding-Team Guidance

### For DS5-F000

Keep the first benchmark boring and trustworthy:

- use OS-supported Thunderbolt networking first;
- report A-B, A-C, and B-C link behavior if the topology allows it;
- measure concurrent A-B/A-C interference;
- include p50, p95, and p99 for every relevant message size;
- include scheduler overhead per simulated token;
- include copy/checksum cost if the harness can expose it;
- emit machine-readable artifacts before writing the human summary;
- include a `claims` section in the summary that labels each result as measured, projected, or assumption.

Do not add:

- IOKit drivers;
- kernel extensions;
- speculative decoding;
- tokenizer/model loading;
- Metal kernels;
- quantization quality claims;
- top-K logits approximation;
- 1M context claims.

### For DS5-F001B

Use the research notes only as a prompt to be stricter:

- source model constants from pinned Qwen metadata;
- prove Node A is not a steady-state MoE decode bottleneck;
- report per-node memory ledgers;
- keep layer ownership visible in logs;
- do not switch to expert partitioning without a new ADR.

### For Later Runtime Work

Zig comptime specialization, ring buffers, local router mirrors, fused packets, and Metal fragments are all still plausible. Their role is to become measured implementation work after the physical path earns the right to exist.

Speculative decoding should become a separate experimental feature only after DS5 can run an exact baseline. The acceptance criterion should be "preserves target distribution or clearly labels approximation," not "matches a paper's speedup headline."

## PM Guidance

### Keep

- DS5 name and single-model thesis.
- Qwen3-235B-A22B-Instruct-2507 as the first concrete target.
- Three-node Apple Silicon topology.
- Phase 0 as the first public milestone.
- Honest artifact-first publication.

### Update

- Public positioning should lead with "measured local MoE physics" instead of "distributed inference engine."
- The README should eventually explain the relationship between local `qw4` naming and public DS5 branding.
- Public materials should include a claims ledger and a "what this does not prove" section.
- Future comparison docs should cite ds4 as the closest cultural ancestor while explaining DS5's different model, hardware envelope, and gate discipline.

### Discard Or Quarantine

- Any claim that Thunderbolt 5 gives RDMA-like semantics before copy-count evidence.
- Any claim that DS5 supports 1M context on the 48GB/node topology.
- Any claim that PackLLM/STM is a DS5 routing strategy.
- Any speculative decoding speedup headline before an exact baseline exists.
- Any kernel-driver work before user-space measurement proves it is necessary.

## Suggested Backlog Additions

These are recommendations, not changes made in this review:

| Proposed item | Purpose | Suggested timing |
|---|---|---|
| `DS5-PUB-001: Phase 0 Publication Package` | Turn F000 artifacts into a polished public research note with charts and claims ledger. | Start when F000 target hardware run is scheduled. |
| `DS5-CMP-001: Local Inference Landscape Note` | Compare DS5 against ds4, llama.cpp, MLX-LM, vLLM, SGLang, and Ollama from a positioning standpoint. | Draft after F000 results exist. |
| `DS5-EXP-001: User-Space Transport A/B` | Compare POSIX TCP over Thunderbolt against Network.framework/custom framing if baseline transport overhead is material. | Only after F000 baseline. |
| `DS5-EXP-002: Speculative Decode Feasibility` | Evaluate small-drafter speculative decoding against a correct DS5 baseline. | Post-F002 at earliest. |
| `DS5-EXP-003: Expert Partitioning Alternative` | Test expert-space partitioning against layer ownership using measured routing traces. | After F001B telemetry. |

## External Validation Notes

Qwen's official model card confirms the DS5 target shape: 235B total parameters, 22B activated parameters, 94 layers, 64 Q heads, 4 KV heads, 128 experts, and 8 activated experts. It also lists 262,144 native context and an extended 1,010,000-token mode, but warns that 1M context needs roughly 1000GB total GPU memory. Source: [Qwen/Qwen3-235B-A22B-Instruct-2507](https://huggingface.co/Qwen/Qwen3-235B-A22B-Instruct-2507).

Apple's MacBook Pro technical specifications confirm that M5 Pro and M5 Max systems expose Thunderbolt 5 ports up to 120Gb/s, with M5 Max memory bandwidth options up to 614GB/s. They also show that 48GB is a configurable memory point for both M5 Pro and M5 Max, while higher-memory M5 Max configurations exist. Source: [Apple MacBook Pro Technical Specifications](https://www.apple.com/macbook-pro/specs/).

The ds4 repository validates the open-source momentum around narrow, model-specific local inference. It also offers an important caution: its distributed notes report Thunderbolt 5 over plain TCP, long-prefill benefits, and decode slowdown versus a single local process in one two-Mac measurement. Source: [antirez/ds4](https://github.com/antirez/ds4).

PackLLM is relevant background for model fusion, not DS5 core routing. It uses perplexity optimization to weight multiple LLMs at test time, which is different from exact execution of one Qwen3 MoE checkpoint. Source: [Pack of LLMs: Model Fusion at Test-Time via Perplexity Optimization](https://arxiv.org/abs/2404.11531).

The low-perplexity token paper referenced by the research notes is about fine-tuning and catastrophic-forgetting mitigation, not a DS5 inference-time routing or token-selection method. Source: [Mitigating Forgetting in LLM Fine-Tuning via Low-Perplexity Token Learning](https://arxiv.org/abs/2501.14315).

DiP-SD is useful to watch, but its reported result is for distributed edge speculative decoding with Qwen3-1.7B/Qwen3-32B, not DS5's target topology or Qwen3-235B baseline. Source: [DiP-SD: Distributed Pipelined Speculative Decoding for Efficient LLM Inference at the Edge](https://arxiv.org/abs/2604.20919).

## Bottom Line

DS5 should become more ambitious in presentation and more conservative in claims.

The research agent's best contribution is the product insight that local, narrow, open-weight inference projects are attracting real attention. The coding roadmap should not chase every flashy technique in that research. It should turn the current Phase 0 gate into a clean public experiment that earns credibility first. Once DS5 has measured transport and placement evidence, the team can decide which advanced ideas deserve a real feature.
