# Model Inspect Tools

This directory is reserved for local Qwen3 metadata inspection tools.

Phase 0 tools should inspect only lightweight local metadata such as `config.json`,
`model.safetensors.index.json`, tensor names, tensor shapes, dtypes, shard membership,
and byte offsets. They must not download checkpoints or load tensor payloads.

Fields needed by the placement estimator are tracked in
`docs/findings/placement-feasibility.md`.

