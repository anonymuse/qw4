# DS5-F001 PDD Topology Acceptance Summary

Status: pass as scaffold/planning evidence. This is not measured full-runtime evidence.

## Reproduction

```bash
make pdd-topology-validate
```

The command emits:

- `artifacts/pdd/ds5-f001-memory-ledger.json`
- `docs/findings/ds5-f001-pdd-topology-acceptance.md`

## Evidence Classification

| Field | Value |
|---|---|
| Evidence class | `scaffold/planning` |
| Measured full runtime | `false` |
| Evidence source | placement manifest constants and validator arithmetic |
| Memory byte source state | `placeholder_cap_test` |
| Placeholder cap-test bytes | `true` |
| Measured runtime bytes | `false` |
| Derived from pinned tensor metadata | `false` |
| Context assumption evidence | `planning_only` |
| Node A steady-state decode critical path | `forbidden_outside_correctness_mode` |

This summary validates placement-manifest constants and memory-budget arithmetic only. It does not load Qwen weights, tokenizer assets, a speculative drafter, a primary-weight loader, a KV allocator, or Metal kernels.

## Acceptance Checks

| Claim | Ledger evidence | Result | Evidence class |
|---|---|---:|---|
| Model constants match Qwen3-235B-A22B-Instruct-2507 | `layers = 94`; `experts = 128`; `active_experts = 8` | PASS | `scaffold/planning` |
| Node A primary MoE decode bytes are exactly 0 | `nodes.A.primary_moe_decode_bytes = 0` | PASS | `scaffold/planning` |
| Node B owns layers 0-46 | `nodes.B.decode_layer_ranges = 0-46` | PASS | `scaffold/planning` |
| Node C owns layers 47-93 | `nodes.C.decode_layer_ranges = 47-93` | PASS | `scaffold/planning` |
| Node B stays under 33.6GB static cap and preserves 14.4GB runtime headroom | `31.00GB <= 33.60GB`; `runtime_headroom = 14.40GB` | PASS | `scaffold/planning` |
| Node C stays under 33.6GB static cap and preserves 14.4GB runtime headroom | `31.00GB <= 33.60GB`; `runtime_headroom = 14.40GB` | PASS | `scaffold/planning` |
| Memory byte buckets are placeholder cap-test bytes | `byte_source_state = placeholder_cap_test`; `measured_runtime = false`; `derived_from_pinned_tensor_metadata = false` | PASS | `scaffold/planning` |
| Node A stays off the steady-state decode critical path outside correctness mode | `node_a_steady_state_decode_critical_path = forbidden_outside_correctness_mode` | PASS | `scaffold/planning` |

## Memory Ledger Summary

| Node | Decode layers | Primary MoE decode bytes | Static total | Static cap | Static margin | Runtime headroom | Byte source state | Evidence class |
|---|---|---:|---:|---:|---:|---:|---|---|
| A | none | 0 | 0.30GB | 33.60GB | 33.30GB | 14.40GB | `placeholder_cap_test` | `scaffold/planning` |
| B | 0-46 | 28500000000 | 31.00GB | 33.60GB | 2.60GB | 14.40GB | `placeholder_cap_test` | `scaffold/planning` |
| C | 47-93 | 28500000000 | 31.00GB | 33.60GB | 2.60GB | 14.40GB | `placeholder_cap_test` | `scaffold/planning` |

## Planning Assumptions

| Field | Value |
|---|---|
| Context evidence class | `planning_only` |
| Runtime validated | `false` |
| First performance context tokens | `8192`-`32768` |
| Stretch context tokens | `65536` |
| Research-only context tokens | `131072`-`262144` |

## Tensor-Class Policy Placeholders

| Tensor class | Runtime implemented | Policy placeholder |
|---|---:|---|
| `router_gate` | `false` | Keep router/gate tensors at FP16 or Q8 until evidence supports a lower precision; B/C local mirrors are required before performance-mode routing. |
| `attention` | `false` | Attention tensors remain a layer-owner worker policy placeholder and are not counted from pinned tensor metadata in this manifest. |
| `hot_moe_experts` | `false` | Hot MoE expert residency is a future worker-local placement policy and must preserve Qwen top-8 expert semantics. |
| `cold_moe_experts` | `false` | Cold MoE experts may be modeled as future backing or promotion candidates, but not as steady-state active-weight decode traffic from Node A or NVMe. |
| `kv_cache` | `false` | KV cache ownership is a planning placeholder for B/C worker-owned decode state and remains inside runtime headroom. |

## Runtime Path Constraints

| Constraint | Value |
|---|---|
| Node A steady-state decode critical path | `forbidden_outside_correctness_mode` |
| Correctness-mode Node A routing allowed | `true` |
| Performance mode requires B/C local router mirrors | `true` |
| Steady-state decode runtime implemented | `false` |

## Limits Of Claim

- This manifest validates topology and memory-budget scaffolding only.
- It does not load Qwen weights, parse tokenizer assets, implement speculative decoding, or run Metal kernels.
- Static byte buckets are placeholder cap tests until measured runtime bytes or pinned tensor metadata replace them.
- Context-length values are planning assumptions only and are not runtime KV allocation evidence.
- Node A must stay off the steady-state decode critical path outside correctness mode.
