# Local Model Metadata Runbook

Status: Phase 0 local smoke path.

## Goal

Use downloaded GGUF artifacts as repeatable metadata inputs for DS5 planning without
claiming local inference capability on this machine.

The M5 Air has 24GB unified memory. The GGUF files in this runbook must be treated as
metadata and test-shape inputs unless a later task explicitly opts into functional
inference experiments.

## Local Artifacts

| Artifact | Path | Phase 0 use |
|---|---|---|
| 30B MoE-shape GGUF | `/Users/jessewhite/ds5-models/qwen3-30b-a3b-instruct-2507-gguf` | Local Qwen3 MoE-shape metadata validation. Short functional experiments are possible only when memory and runtime constraints are explicitly reviewed. |
| 235B target GGUF shards | `/Users/jessewhite/ds5-models/qwen3-235b-a22b-instruct-2507-gguf/UD-Q2_K_XL` | Exact target architecture, shard count, tensor table, and quantization metadata validation only. Do not attempt to load this model on the Air. |

Neither artifact proves DS5 can run local inference on the Air. Passing this runbook
only proves that the local files match the expected metadata shape.

## Smoke Command

Run:

```bash
sh tools/local/model-metadata-smoke.sh
```

The smoke writes JSON artifacts under:

```text
artifacts/runs/model-metadata-smoke/
```

Expected files:

- `qwen3-30b-a3b-instruct-2507.gguf-summary.json`;
- `qwen3-235b-a22b-instruct-2507-ud-q2-k-xl.gguf-summary.json`;
- `checks.json`.

The script verifies:

- both models report `general.architecture = qwen3moe`;
- both models report 128 experts and 8 active experts;
- the 30B metadata reports 48 layers;
- the 235B metadata reports 94 layers;
- the 235B target path contains 2 GGUF shard files and metadata `split.count = 2`.

The inspector reads GGUF headers, metadata records, and tensor table entries. It does
not mmap weights or read tensor payload bytes.

## Planning Input Follow-Up

Use the 235B summary JSON as the source for the next DS5 planning refresh:

1. Copy `qwen_shape` fields into a reviewed candidate update for
   `configs/qwen3_235b_a22b_planning.json`.
2. Use `tensor_type_counts`, `total_tensor_count`, per-file tensor counts, and
   `tensor_data_offset_bytes` as evidence for a tensor-table-derived quantization and
   shard accounting pass.
3. Keep dense/shared versus expert byte allocation provisional until a tensor-name
   classifier maps GGUF tensor names into embeddings, attention, routers, experts,
   normalization, and output tensors.
4. Preserve the generated smoke JSON path in any placement finding that uses these
   values so cluster results can be traced back to the exact local metadata snapshot.

That follow-up should still produce derived planning artifacts under
`artifacts/runs/` first. Checked-in planning config changes should happen only after
the derived values are reviewed against real cluster memory and transport evidence.
