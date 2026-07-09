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

This summary validates placement-manifest constants and memory-budget arithmetic only. It does not load Qwen weights, tokenizer assets, a speculative drafter, a primary-weight loader, a KV allocator, or Metal kernels.

## Acceptance Checks

| Claim | Ledger evidence | Result | Evidence class |
|---|---|---:|---|
| Node A primary MoE decode bytes are exactly 0 | `nodes.A.primary_moe_decode_bytes = 0` | PASS | `scaffold/planning` |
| Node B owns layers 0-46 | `nodes.B.decode_layer_ranges = 0-46` | PASS | `scaffold/planning` |
| Node C owns layers 47-93 | `nodes.C.decode_layer_ranges = 47-93` | PASS | `scaffold/planning` |
| Node B stays under 33.6GB static cap and preserves 14.4GB runtime headroom | `31.00GB <= 33.60GB`; `runtime_headroom = 14.40GB` | PASS | `scaffold/planning` |
| Node C stays under 33.6GB static cap and preserves 14.4GB runtime headroom | `31.00GB <= 33.60GB`; `runtime_headroom = 14.40GB` | PASS | `scaffold/planning` |

## Memory Ledger Summary

| Node | Decode layers | Primary MoE decode bytes | Static total | Static cap | Static margin | Runtime headroom | Evidence class |
|---|---|---:|---:|---:|---:|---:|---|
| A | none | 0 | 0.30GB | 33.60GB | 33.30GB | 14.40GB | `scaffold/planning` |
| B | 0-46 | 28500000000 | 31.00GB | 33.60GB | 2.60GB | 14.40GB | `scaffold/planning` |
| C | 47-93 | 28500000000 | 31.00GB | 33.60GB | 2.60GB | 14.40GB | `scaffold/planning` |

## Limits Of Claim

- This manifest validates topology and memory-budget scaffolding only.
- It does not load Qwen weights, parse tokenizer assets, implement speculative decoding, or run Metal kernels.
- Static byte buckets are placeholders until pinned tensor metadata and quantization accounting replace them.
