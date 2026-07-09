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
  --ledger-out artifacts/pdd/ds5-f001-memory-ledger.json
```
