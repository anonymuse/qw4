# Model Inspect Tools

This directory is reserved for local Qwen3 metadata inspection tools.

Phase 0 tools should inspect only lightweight local metadata such as `config.json`,
`model.safetensors.index.json`, tensor names, tensor shapes, dtypes, shard membership,
and byte offsets. They must not download checkpoints or load tensor payloads.

Fields needed by the placement estimator are tracked in
`docs/findings/placement-feasibility.md`.

Validate the Phase 1 DS5-F001 PDD topology scaffold and emit a stub memory
ledger with:

```bash
python3 tools/model_inspect/validate_pdd_topology.py \
  --manifest configs/qwen3_pdd_topology_phase1.json \
  --ledger-out artifacts/pdd/ds5-f001-memory-ledger.json
```
