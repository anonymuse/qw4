# DS5-F002 Routing Payload Scaffold

Status: pass as Phase 0 scaffold/planning evidence. This is not fused routing runtime evidence.

## Reproduction

```bash
make routing-plan-validate
```

The command emits:

- `artifacts/routing/ds5-f002-routing-payload.json`
- `docs/findings/ds5-f002-routing-scaffold.md`

## Evidence Classification

| Field | Value |
|---|---|
| Evidence class | `scaffold/planning` |
| Model weights loaded | `false` |
| Runtime packet implemented | `false` |
| Copy counts measured | `false` |
| Benchmark claim | `false` |

This summary validates routing payload shape, Qwen top-8 record constraints, DS5 B/C target-node bounds, and zero-copy assumptions as machine-readable planning data only. It does not load Qwen weights, tokenizer assets, Metal kernels, a KV allocator, or a primary-weight loader.

## Payload Contract

| Field | Value |
|---|---|
| Record shape | `layer_id, active_expert_ids, weight_coefficients, target_nodes` |
| Layer range | `0-93` |
| Active experts per record | `8` |
| Valid target nodes | `B, C` |
| Encoding status | `json_contract_only` |

## Payload Summary

| Metric | Value |
|---|---:|
| Blocks | 1 |
| Routing records | 4 |
| Min layer | 0 |
| Max layer | 93 |
| Unique expert IDs referenced | 32 |

## Target Node Sets

| Target nodes | Record count |
|---|---:|
| `B` | 2 |
| `B,C` | 1 |
| `C` | 1 |

## Zero-Copy Assumption Status

| Assumption | Value |
|---|---|
| Runtime implemented | `false` |
| Measured copy counts available | `false` |
| Hot-path heap-to-heap copy budget | `0` |

## Limits Of Claim

- This manifest validates routing payload shape and topology assumptions only.
- It does not load Qwen weights or tokenizer assets.
- It does not implement a fused runtime packet decoder, Metal kernels, a KV allocator, or a primary-weight loader.
- It does not provide copy-count telemetry or benchmark evidence for a zero-copy transport path.
- It preserves Qwen top-8 routing semantics and does not substitute topology-aware expert choices.
