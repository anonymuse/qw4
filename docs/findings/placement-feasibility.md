# Qwen Placement And Memory Feasibility

Status: Phase 0 planning scaffold. This is not a final placement, quantization, throughput, quality, or long-context claim.

## Estimator

Run:

```bash
python3 tools/quant/estimate_qwen3_memory.py \
  --config configs/qwen3_235b_a22b_planning.json
```

The estimator uses only local JSON planning metadata and the Python standard library. It does not download model files, parse tensor payloads, mmap weights, or load model weights.

Machine-readable output is available with:

```bash
python3 tools/quant/estimate_qwen3_memory.py \
  --config configs/qwen3_235b_a22b_planning.json \
  --json
```

## Default Planning Scenario

The checked-in config models:

- model: `Qwen3-235B-A22B-Instruct-2507`;
- total parameters: 235B;
- activated parameters: 22B;
- layers: 94;
- experts: 128;
- active experts: 8;
- hidden size: 4096;
- KV heads: 4;
- head dimension: 128;
- static cap: 33.6GB per 48GB node;
- runtime reserve: 14.4GB per node;
- static placement: A/B/C each hold one third of sharded static weights;
- KV placement: B/C each hold one half of KV cache;
- router/gate mirrors: FP16 and replicated on A/B/C;
- dense/shared bucket: Q8 planning class;
- expert bucket: aggressive `iq2_planning` placeholder with block metadata;
- static unmodeled safety margin: 8%.

The dense/shared and expert buckets are algebraically inferred from:

```text
activated = dense_shared + moe_experts * (active_experts / experts)
total = dense_shared + moe_experts
```

Under the current planning inputs, that gives:

| Bucket | Estimate |
|---|---:|
| Dense/shared | 7.800B parameters |
| MoE experts | 227.200B parameters |
| Router/gate mirror | 0.049B parameters |

## Acceptance Output Summary

Command:

```bash
python3 tools/quant/estimate_qwen3_memory.py --config configs/qwen3_235b_a22b_planning.json
```

Static placement estimate:

| Node | Role | Estimate | Cap | Result |
|---|---|---:|---:|---|
| A | coordinator / static-owner planning | 28.63GB | 33.60GB | PASS |
| B | primary worker | 28.63GB | 33.60GB | PASS |
| C | primary worker | 28.63GB | 33.60GB | PASS |

Aggregate static estimate: 85.90GB.

KV cache estimate, batch 1, KV-only:

| Context | Aggregate KV | Worst-node KV | Runtime reserve result |
|---:|---:|---:|---|
| 8,192 | 1.58GB | 0.79GB | PASS |
| 32,768 | 6.31GB | 3.15GB | PASS |
| 65,536 | 12.62GB | 6.31GB | PASS |
| 131,072 | 25.23GB | 12.62GB | PASS |
| 262,144 | 50.47GB | 25.23GB | FAIL |

The KV PASS values are KV-only. The 14.4GB runtime reserve also has to cover Metal heaps, staging buffers, transport rings, allocator fragmentation, OS pressure, telemetry, and promotion scratch.

## Interpretation

The default scenario passes the per-node static cap only because it assumes a three-node static placement and aggressive expert-only low-bit quantization. That is useful as a feasibility bound, not a recipe.

If Node A remains control-only for static weights, the B/C-only placement must be rerun with A's static fraction set to zero. That scenario is expected to be much tighter and may fail once real metadata and runtime overheads are included.

The 262K context target fails the configured B/C runtime reserve from KV alone. 128K is still research-only because the remaining runtime reserve after KV is too small to treat as proven.

## Real Metadata Needed Next

- Pinned model config fields: layer count, hidden size, attention heads, KV heads, head dimension, expert count, active experts, intermediate sizes, vocab size, RoPE settings, and tying rules.
- Safetensors index fields: complete tensor names, shapes, dtypes, file membership, per-file offsets, and total bytes.
- Exact dense/shared versus expert tensor split, including embeddings, lm_head, normalization tensors, router weights, router bias, shared experts if present, and any non-MoE MLP tensors.
- Real quantization metadata: per-tensor quant class, block size, scale and zero-point storage, padding, alignment, and tensor header overhead.
- Duplication policy: which tensors are replicated on A/B/C for correctness routing, local router mirrors, scheduler state, promotion caches, and fault recovery.
- Runtime reserve evidence: Metal heap sizes, staging buffers, transport rings, allocator fragmentation, telemetry overhead, and OS memory pressure at the cap boundary.
- KV ownership policy for prefill and decode, including whether KV is layer-sharded, replicated, paged, or backed by slower storage in any mode.
- Quality evidence for the low-bit expert planning class. `iq2_planning` is a placeholder, not an accepted quantization recipe.

