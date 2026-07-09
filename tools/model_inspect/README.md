# Model Inspect Tools

This directory contains local Qwen3 metadata inspection tools.

Phase 0 tools should inspect only lightweight local metadata such as `config.json`,
`model.safetensors.index.json`, GGUF metadata, tensor names, tensor shapes, dtypes,
shard membership, and byte offsets. They must not download checkpoints or load tensor
payloads.

## GGUF Metadata Inspector

Use `inspect_gguf.py` to read GGUF headers, metadata key/value records, and tensor
tables without reading the tensor payloads:

```bash
python3 -B tools/model_inspect/inspect_gguf.py \
  /Users/jessewhite/ds5-models/qwen3-30b-a3b-instruct-2507-gguf

python3 -B tools/model_inspect/inspect_gguf.py \
  /Users/jessewhite/ds5-models/qwen3-235b-a22b-instruct-2507-gguf/UD-Q2_K_XL
```

Machine-readable output:

```bash
python3 -B tools/model_inspect/inspect_gguf.py --json <gguf-file-or-directory>
```

## Local Metadata Smoke

Run the repeatable DS5 Phase 0 metadata smoke with:

```bash
sh tools/local/model-metadata-smoke.sh
```

It writes summaries under `artifacts/runs/model-metadata-smoke/` and verifies the
local 30B and 235B GGUF metadata shape. The 30B artifact is for MoE-shape metadata
and carefully scoped short experiments only. The 235B shard directory is for exact
target metadata, shard, and tensor-table validation only. Neither artifact is proof
of local inference on the 24GB Air.

The next planning step is to derive reviewed DS5 placement/scenario inputs from the
235B smoke JSON, especially `qwen_shape`, `tensor_type_counts`,
`total_tensor_count`, and per-file tensor table offsets.

Fields needed by the placement estimator are tracked in
`docs/findings/placement-feasibility.md`.

Validate the Phase 1 DS5-F001 PDD topology scaffold and emit a stub memory
ledger with:

```bash
python3 tools/model_inspect/validate_pdd_topology.py \
  --manifest configs/qwen3_pdd_topology_phase1.json \
  --ledger-out artifacts/pdd/ds5-f001-memory-ledger.json \
  --summary-out docs/findings/ds5-f001-pdd-topology-acceptance.md
```

The shorter coordinator path is:

```bash
make pdd-topology-validate
```

This is scaffold/planning evidence only. It validates manifest constants and byte
arithmetic; it does not load model weights or claim full runtime support.

`configs/schemas/pdd-placement-manifest.schema.json` is a structural contract:
required objects, field types, and no unexpected keys. The semantic authority is
`src/model/pdd_topology.py`, which enforces the exact Qwen target constants,
A/B/C layer ownership, memory cap arithmetic, planning-only evidence metadata,
tensor-class policy placeholders, and Node A runtime-path constraints.

## Phase 0 Routing Payload Scaffold

Validate the DS5-F000 Phase 0 routing-payload scaffold and emit a
machine-readable routing artifact with:

```bash
make phase0-routing-payload-validate
```

Equivalent direct command:

```bash
python3 tools/model_inspect/validate_phase0_routing_payload.py \
  --manifest configs/qwen3_phase0_routing_payload.json \
  --artifact-out artifacts/routing/phase0-routing-payload.json \
  --summary-out docs/findings/phase0-routing-payload-scaffold.md
```

This validates the exact top-8 routing record field shape, B/C target-node
bounds, block ordering, and zero-copy assumptions as planning data only. It does
not load weights, implement a production routing packet runtime, measure copy
counts, make transport benchmark claims, or unblock DS5-F002.
