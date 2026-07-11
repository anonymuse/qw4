# DS5 Project Plan After ARB Refresh

Status: active plan after ARB feedback incorporation.

Review input: `/Users/jessewhite/Downloads/20260609-ARB/20260609-ARB.md`.

## ARB Decision

ARB status: conditionally approved for continued Phase 1 placement-contract work.

The repo is not approved for model loading, tokenizer integration, speculative decoding, fused routing, prefetch work, or Metal kernels until the placement-contract and Phase 0 transport gates below are satisfied.

Current DS5-F001 artifacts prove a scaffold/planning claim only:

> A failing placement manifest can make tests fail before runtime code exists.

They do not prove runtime memory conformance, worker startup ownership, real Qwen tensor placement, tokenizer behavior, KV allocation, transport physics, or kernel viability.

## Goal Sequence

| Order | Goal | Status | Completion signal |
|---:|---|---|---|
| 1 | `DS5-F001A: Placement Contract Hardening` | next feature work | `make test` and `make pdd-topology-validate` reject model/placement mistakes and emit explicit planning evidence metadata. |
| 2 | `DS5-F000: Phase 0 Transport Finding` | queued after F001A | A/B/C hardware artifacts answer whether synthetic Qwen-shaped transport overhead is tolerable. |
| 3 | `DS5-F001B: Runtime Placement Evidence` | queued after F001A and the Phase 0 go/no-go | Runtime startup and warmup logs prove Node A/B/C ownership and memory ledgers without overclaiming model-load readiness. |
| 4 | `DS5-F002: Fused Gating And Zero-Copy Routing Protocol` | blocked | Start only after the Phase 0 finding supports continued distributed decode work. |
| 5 | `DS5-F003` through `DS5-F005` | deferred | Quantization, prefetch, and Metal work remain blocked until earlier evidence gates justify them. |

## Feature Goal Changes

| Previous goal | Updated feature work | Reason |
|---|---|---|
| `DS5-F001` as one runtime topology feature | Split into `DS5-F001A` and `DS5-F001B` | The current implementation is planning evidence, while runtime memory and startup ownership evidence are separate work. |
| `DS5-F002` as the next routing feature | Insert `DS5-F000` before fused routing | Transport physics should be measured before optimizing routing, tokenizer, prefetch, or kernel paths. |
| Planning byte buckets as prose-only placeholders | Make placeholder status machine-readable in F001A | Prevent future agents from treating 31GB worker totals as measured Qwen placement estimates. |
| JSON schema as apparent full validation | Document Python validator as semantic authority | The schema is structural; Phase 1 invariants currently live in Python. |

## DS5-F001A Required Work

- Enforce all Qwen constants in the Python validator: model name, variant, layer count, expert count, and active expert count.
- Add invalid tests for wrong model name, wrong variant, wrong expert count, and wrong active expert count.
- Add manifest-level evidence metadata for placeholder, measured, and derived-from-pinned-tensor states.
- Add a planning-only context-length assumption.
- Add tensor-class policy placeholders for router/gate, attention, hot experts, cold experts, and KV cache.
- Add runtime path constraints that keep Node A off the steady-state decode critical path outside correctness mode.
- Document that JSON Schema validation is structural and the Python validator is the authoritative semantic gate for Phase 1 placement invariants.

## DS5-F000 Required Work

- Run real A/B/C transport measurements on the target hardware topology.
- Keep the runtime roles explicit: Node A is the M5 Pro orchestrator/control plane; Nodes B and C are M5 Max synthetic LLM data-plane workers.
- Emit `run.json`, `events.jsonl`, `latency.csv`, `throughput.csv`, and `summary.md`.
- Report p50/p95/p99 latency, throughput by block size, jitter, checksum failures, scheduler/control-plane overhead, concurrent A-B/A-C interference, reconnect behavior, and projected decode impact.
- Decide whether to proceed, redesign packetization, reduce remote movement assumptions, or publish a negative transport finding.
- Keep model-independent SSD/NVMe measurements as optional adjunct evidence only; they do not unblock active decode-path or storage-dependent runtime claims.

## DS5-F001B Required Work

- Load the hardened placement manifest through runtime startup code.
- Emit startup and warmup memory ledgers with measured allocation classes.
- Emit worker logs proving B owns layers 0-46 and C owns layers 47-93.
- Emit a Node A allocation report proving 0 primary MoE decode bytes.
- Keep all output clearly separated from model-loading, tokenizer, speculative drafter, KV allocator, and Metal-kernel claims unless those systems exist and are measured.

## Public Readiness Note

The repository path and legacy `qw4` naming are still locally confusing. Before a public milestone, either rename the public project surface to DS5 or document `QW4` as a predecessor/codename so readers and future agents see one project identity.
