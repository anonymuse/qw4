#!/usr/bin/env sh
set -eu

RUN_DIR="${RUN_DIR:-artifacts/runs/model-metadata-smoke}"
MODEL_30B_DIR="${MODEL_30B_DIR:-/Users/jessewhite/ds5-models/qwen3-30b-a3b-instruct-2507-gguf}"
MODEL_235B_DIR="${MODEL_235B_DIR:-/Users/jessewhite/ds5-models/qwen3-235b-a22b-instruct-2507-gguf/UD-Q2_K_XL}"
INSPECTOR="${INSPECTOR:-tools/model_inspect/inspect_gguf.py}"

SUMMARY_30B="$RUN_DIR/qwen3-30b-a3b-instruct-2507.gguf-summary.json"
SUMMARY_235B="$RUN_DIR/qwen3-235b-a22b-instruct-2507-ud-q2-k-xl.gguf-summary.json"
CHECKS_JSON="$RUN_DIR/checks.json"

step() {
  printf '\n==> %s\n' "$1"
}

printf '%s\n' "DS5 local GGUF metadata smoke."
printf '%s\n' "This reads GGUF metadata and tensor tables only; it does not mmap or load tensor payloads."

mkdir -p "$RUN_DIR"

step "Inspect 30B MoE-shape GGUF metadata"
python3 -B "$INSPECTOR" --json --tensor-sample 0 "$MODEL_30B_DIR" > "$SUMMARY_30B"

step "Inspect 235B target GGUF shard metadata"
python3 -B "$INSPECTOR" --json --tensor-sample 0 "$MODEL_235B_DIR" > "$SUMMARY_235B"

step "Validate DS5 Phase 0 metadata expectations"
python3 - "$SUMMARY_30B" "$SUMMARY_235B" "$CHECKS_JSON" <<'PY'
from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any


summary_30b_path = Path(sys.argv[1])
summary_235b_path = Path(sys.argv[2])
checks_path = Path(sys.argv[3])


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def get_path(data: dict[str, Any], *keys: str) -> Any:
    current: Any = data
    for key in keys:
        if not isinstance(current, dict) or key not in current:
            return "<missing>"
        current = current[key]
    return current


checks: list[dict[str, Any]] = []
errors: list[str] = []


def expect(label: str, actual: Any, expected: Any) -> None:
    passed = actual == expected
    checks.append(
        {
            "label": label,
            "actual": actual,
            "expected": expected,
            "pass": passed,
        }
    )
    if not passed:
        errors.append(f"{label}: expected {expected!r}, got {actual!r}")


summary_30b = load_json(summary_30b_path)
summary_235b = load_json(summary_235b_path)

expect("30B architecture", get_path(summary_30b, "metadata", "general.architecture"), "qwen3moe")
expect("235B architecture", get_path(summary_235b, "metadata", "general.architecture"), "qwen3moe")

expect("30B expert count", get_path(summary_30b, "qwen_shape", "expert_count"), 128)
expect("30B active experts", get_path(summary_30b, "qwen_shape", "expert_used_count"), 8)
expect("235B expert count", get_path(summary_235b, "qwen_shape", "expert_count"), 128)
expect("235B active experts", get_path(summary_235b, "qwen_shape", "expert_used_count"), 8)

expect("30B layer count", get_path(summary_30b, "qwen_shape", "block_count"), 48)
expect("235B layer count", get_path(summary_235b, "qwen_shape", "block_count"), 94)
expect("235B shard file count", get_path(summary_235b, "file_count"), 2)
expect("235B metadata split count", get_path(summary_235b, "metadata", "split.count"), 2)

split_tensor_count = get_path(summary_235b, "metadata", "split.tensors.count")
if split_tensor_count != "<missing>":
    expect("235B split tensor count", get_path(summary_235b, "total_tensor_count"), split_tensor_count)

report = {
    "ok": not errors,
    "summaries": {
        "qwen3_30b_a3b": str(summary_30b_path),
        "qwen3_235b_a22b": str(summary_235b_path),
    },
    "checks": checks,
}
checks_path.parent.mkdir(parents=True, exist_ok=True)
with checks_path.open("w", encoding="utf-8") as handle:
    json.dump(report, handle, indent=2, sort_keys=True)
    handle.write("\n")

if errors:
    for error in errors:
        print(f"metadata smoke failed: {error}", file=sys.stderr)
    print(f"metadata smoke report: {checks_path}", file=sys.stderr)
    sys.exit(1)

print(f"metadata smoke checks passed: {checks_path}")
PY

printf '\n%s\n' "Model metadata smoke complete."
printf '%s\n' "30B summary: $SUMMARY_30B"
printf '%s\n' "235B summary: $SUMMARY_235B"
printf '%s\n' "Check report: $CHECKS_JSON"
