# Agent E: Qwen Placement And Memory Feasibility Tools

## Objective

Create the first model metadata and placement feasibility scaffold without downloading or loading the full model.

## Read First

- `docs/assumptions.md`
- `docs/risk-register.md`
- `docs/decisions/ADR-001-model-selection.md`
- `docs/repository-architecture.md`

## Owned Paths

- `src/model/`
- `tools/model_inspect/`
- `tools/quant/`
- `docs/findings/placement-feasibility.md`

## Deliverables

Create a small, deterministic memory estimator for Qwen3 planning assumptions.

Inputs may be a local TOML/JSON file with:

- model name;
- layers;
- hidden size;
- experts;
- active experts;
- KV heads;
- head dim;
- per-tensor quant classes;
- per-node static cap;
- runtime reserve.

Outputs should include:

- per-node static estimate;
- runtime reserve estimate;
- KV estimate at 8K, 32K, 64K, 128K, and 262K;
- explicit pass/fail against 33.6GB per-node static cap;
- list of assumptions that require real tensor metadata.

Use standard library tooling. Python is acceptable for the first estimator if it avoids dependencies.

## Acceptance Checks

Run a local command such as:

```bash
python3 tools/quant/estimate_qwen3_memory.py \
  --config configs/qwen3_235b_a22b_planning.json
```

The command should print a human-readable summary and emit machine-readable JSON if possible.

## Do Not

- Do not download model weights.
- Do not claim a final quantization recipe.
- Do not treat IQ2 or BitNet quality as proven.
- Do not silently ignore metadata, scale, alignment, or duplication overhead.

## Handoff Notes

Report:

- estimator command;
- output example;
- assumptions still unresolved;
- which real metadata fields are needed next.

