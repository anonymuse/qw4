# Risk Register

Status: kickoff risk register. Re-score after each phase.

## Ranked Risks

| Rank | Risk | Category | Severity | Assessment |
|---:|---|---|---|---|
| 1 | Qwen3-235B-A22B memory feasibility | Fatal / serious | Critical | FP16/Q8 is impossible. Full-model residency only looks plausible with aggressive tensor-aware quantization and strict caps. Real artifacts may exceed budget once scales, metadata, alignment, duplicated tensors, KV, Metal heaps, transport buffers, and OS overhead are counted. |
| 2 | Quantization quality loss | Fatal / research | Critical | If the model only fits with IQ2-heavy expert quantization and quality collapses, the full runtime thesis fails. A negative result is still publishable if measured cleanly. |
| 3 | Thunderbolt/RDMA-style interconnect reality | Fatal / engineering | Critical | The link may not provide latency, copy behavior, jitter, or synchronization cost compatible with decode-shaped traffic. This must be measured before kernel work. |
| 4 | Expert placement and cold-miss behavior | Serious / research | High | MoE locality only helps if hot experts are resident and remote/cold accesses are rare enough. A flatter routing distribution can sink decode. |
| 5 | Node A bottleneck | Serious / engineering | High | Correctness mode can route through Node A. Performance mode cannot make Node A synchronous on every layer without evidence. B/C local router mirrors are required after validation. |
| 6 | Prefill versus decode bottlenecks | Serious / engineering | High | Decode may be plausible while prefill remains network or memory bound. Benchmarks must split these paths. |
| 7 | KV cache memory pressure | Serious but manageable | Medium | 8K and 32K look plausible under the planning formula. 64K is stretch. 128K+ is a separate research problem. |
| 8 | Apple Silicon, MLX, and Metal limitations | Engineering | High | Metal command-buffer overhead and small expert kernels may dominate. Fused kernels are likely needed, but only after Phase 0 proves the platform path. |
| 9 | One-week useful result | Execution | Medium | Full inference in one week is not credible. A transport plus simulated-MoE finding is credible. |
| 10 | Open-source credibility | Presentation | High | Claims that outrun measurements will make the project look unserious. Every result needs reproducible artifacts and clear limitations. |

## Fatal Risks

- Required model layout cannot fit under per-node static caps with any acceptable quality envelope.
- Inter-node transfer is too slow or jittery for decode-shaped traffic.
- Required quantization destroys Qwen routing, tool fidelity, or output quality.

## Serious But Manageable Risks

- KV pressure above 32K.
- Node A becoming a bottleneck in early designs.
- macOS storage behavior invalidating promotion assumptions.
- Metal command overhead requiring larger fused units than the first kernel plan expects.

## Research Risks

- Expert hotness may not be stable enough for placement to matter.
- Routing distribution may vary strongly by workload.
- Low-bit experts may not preserve the behaviors that make Qwen3-235B-A22B attractive.

## Engineering Risks

- Worker health, clock alignment, and trace correlation may be harder than expected.
- Packet checksums and instrumentation may perturb small-message benchmarks.
- Benchmark harness quality may lag behind runtime ambition.

## Open-Source Presentation Risks

- The repo may over-promise a full model runtime before Phase 0 validates hardware.
- The writeup may blur measured findings with planning assumptions.
- Archived alternative docs may confuse readers unless clearly marked.

