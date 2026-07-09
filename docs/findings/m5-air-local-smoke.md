# M5 Air Local Smoke Finding

Status: local M5 Air loopback-only result.
Date: 2026-07-09.

## Scope

This finding validates the repo, artifact contract, loopback smoke path, memory estimator, reporting scripts, and local developer ergonomics on a MacBook Air with Apple M5.

This is not a Thunderbolt cluster result, not a worker-node result, not a final model inference result, and not evidence that full Qwen3-235B-A22B weights can run on this machine.

## Source Under Test

| Field | Value |
|---|---|
| Repository | `https://github.com/anonymuse/qw4.git` |
| Validation worktree | `/private/tmp/qw4-m5-air-verify` |
| Exact commit tested | `d9efe4e88e61500eb8fc1056489aadae6799ae56` |
| Validation worktree state | detached HEAD, clean except ignored generated artifacts |
| Run artifact ID | `m5-air-loopback-smoke` |
| Artifact schema | `phase0.artifacts.v1` |

The primary checkout also had unrelated local edits after the first local commit. The final smoke was therefore run from a detached worktree at the exact commit above so the result is attributable.

## Machine And Toolchain

| Item | Result |
|---|---|
| macOS | `ProductVersion: 26.5`, `BuildVersion: 25F71` |
| Hardware | MacBook Air, `Mac17,4`, Apple M5 |
| CPU layout | 10 cores, 4 performance and 6 efficiency |
| Memory | 24 GB |
| Zig | `0.16.0` |
| Python | `Python 3.14.6` |
| Git | `git version 2.50.1 (Apple Git-155)` |
| GitHub CLI | `gh version 2.96.0 (2026-07-02)` |
| GitHub auth | token invalid; local tests did not require authenticated GitHub access |

## Commands And Results

| Command | Result | Notes |
|---|---:|---|
| `git fetch --prune origin` | PASS | Updated `origin/main` from `682a16c` to `1d21d1c`. |
| `zig version` | PASS | `0.16.0`. |
| `python3 --version` | PASS | `Python 3.14.6`. |
| `git --version` | PASS | `git version 2.50.1 (Apple Git-155)`. |
| `gh --version` | PASS | `gh version 2.96.0 (2026-07-02)`. |
| `gh auth status` | FAIL | Invalid GitHub token; did not block local validation. |
| `sw_vers` | PASS | macOS 26.5 build 25F71. |
| `system_profiler SPHardwareDataType` | PASS | Reported MacBook Air `Mac17,4`, Apple M5, 24 GB. |
| `sysctl -n hw.model` | FAIL | Sandbox denied this query. |
| `sysctl -n hw.memsize` | FAIL | Sandbox denied this query. |
| `zig build test` | PASS | Initial sandbox run failed, approved rerun passed. |
| `python3 -B tools/report/validate_run.py tests/fixtures/artifacts/transport-smoke` | PASS | Fixture conforms to `phase0.artifacts.v1`. |
| `python3 -B tools/quant/estimate_qwen3_memory.py --config configs/qwen3_235b_a22b_planning.json --json-out /tmp/qwen3_memory_estimate.json` | PASS | Human summary printed and JSON emitted. |
| `zig build run-coordinator -- --config configs/cluster.loopback.toml --scenario benchmarks/scenarios/loopback_transport_smoke.toml --out artifacts/runs/m5-air-loopback-smoke` | PASS | 1,000 transfers, 223,859,200 bytes sent, 0 checksum failures. |
| `python3 -B tools/report/validate_run.py artifacts/runs/m5-air-loopback-smoke` | PASS | Generated artifacts conform to `phase0.artifacts.v1`. |
| `python3 -B tools/report/summarize_phase0.py artifacts/runs/m5-air-loopback-smoke` | PASS | Summary parsed generated artifacts and marked result loopback-only. |
| `tools/local/m5-air-local-smoke.sh` | PASS | Passed after approving Zig cache access in the detached worktree. |

## Exact Failure Text

`gh auth status`:

```text
github.com
  X Failed to log in to github.com account anonymuse (default)
  - Active account: true
  - The token in default is invalid.
  - To re-authenticate, run: gh auth login -h github.com
  - To forget about this account, run: gh auth logout -h github.com -u anonymuse
```

`sysctl -n hw.model` and `sysctl -n hw.memsize`:

```text
sysctl: sysctl fmt -1 1024 1: Operation not permitted
```

Initial sandboxed `zig build test` in the primary checkout:

```text
error: PermissionDenied
```

Initial sandboxed smoke helper run in the detached worktree:

```text
error: sub-compilation of compiler_rt failed
    note: failed to check cache: manifest_create PermissionDenied
/opt/homebrew/Cellar/zig/0.16.0_1/lib/zig/std/std.zig:1:1: error: unable to load 'std.zig': PermissionDenied
/opt/homebrew/Cellar/zig/0.16.0_1/lib/zig/ubsan_rt.zig:1:1: error: unable to load 'ubsan_rt.zig': PermissionDenied
```

The same Zig commands passed when rerun with normal local cache access.

## Loopback Smoke Summary

| Field | Value |
|---|---|
| Run ID | `m5-air-loopback-smoke` |
| Git commit in artifact | `d9efe4e88e61500eb8fc1056489aadae6799ae56` |
| Started | `2026-07-09T13:00:23Z` |
| Ended | `2026-07-09T13:00:28Z` |
| Duration | 5,180 ms |
| Transport path | `single_process_loopback` |
| Hardware interpretable | `false` |
| Transfers | 1,000 |
| Bytes sent | 223,859,200 |
| Checksum algorithm | `sha256` |
| Checksum failures | 0 |
| Artifact validation | PASS |

Selected loopback latency rows:

| Node pair | Message bytes | p50 us | p95 us | p99 us |
|---|---:|---:|---:|---:|
| A-B | 64 | 2 | 2 | 2 |
| A-B | 1,048,576 | 11,980 | 12,305 | 12,884 |
| A-C | 64 | 2 | 2 | 2 |
| A-C | 1,048,576 | 12,016 | 12,326 | 12,918 |

Selected loopback throughput rows:

| Node pair | Block bytes | Transfers | MiB/s |
|---|---:|---:|---:|
| A-B | 1,048,576 | 100 | 41 |
| A-C | 1,048,576 | 100 | 41 |

These latency and throughput values are only useful as local loopback regression signals. They are not cluster transport measurements.

## Memory Estimator Summary

The estimator ran without downloading model weights.

| Area | Result |
|---|---|
| Model planning target | Qwen3-235B-A22B-Instruct-2507 |
| Total parameters | 235.000B |
| Activated parameters | 22.000B |
| Dense/shared estimate | 7.800B |
| MoE expert estimate | 227.200B |
| Router/gate mirror estimate | 0.049B |
| Static estimate per node | 28.63 GB |
| Static cap per node | 33.60 GB |
| Aggregate static estimate | 85.90 GB |
| Static safety margin | 8.0% |

KV reserve result at batch 1:

| Context | Aggregate KV | Worst node | Result |
|---:|---:|---:|---:|
| 8,192 | 1.58 GB | 0.79 GB | PASS |
| 32,768 | 6.31 GB | 3.15 GB | PASS |
| 65,536 | 12.62 GB | 6.31 GB | PASS |
| 131,072 | 25.23 GB | 12.62 GB | PASS |
| 262,144 | 50.47 GB | 25.23 GB | FAIL |

This is a planning estimate only. It does not prove final placement, quality, throughput, long-context feasibility, or a valid quantization recipe.

## Actionable Findings

1. Artifact provenance was too weak: generated loopback artifacts previously used an all-zero Git SHA that passed schema validation. The local commit under test embeds the actual build commit and keeps an all-zero fallback only for non-Git source snapshots.
2. The repo now has a single local smoke command at `tools/local/m5-air-local-smoke.sh`, which reduces setup friction and makes repeated M5 Air checks less error-prone.
3. The artifact contract, fixture validator, generated artifact validator, and summary script all work on this M5 Air for loopback smoke.
4. The memory estimator is useful for pruning design space now: 262,144 context fails KV reserve in the planning model, while 131,072 is still inside the configured reserve. That should guide the next placement discussion before runtime work.
5. Local sandboxing can look like Zig or hardware failure. The exact `PermissionDenied` errors above were cache/sandbox access issues and passed with normal local cache access.

## What This Proves

- The Zig test suite can pass on the M5 Air with Zig 0.16.0.
- The checked-in fixture validates against `phase0.artifacts.v1`.
- The coordinator can generate a complete loopback run artifact set.
- Generated loopback artifacts validate and summarize correctly.
- The memory estimator runs locally and emits machine-readable JSON.
- Local provenance is now strong enough to tie artifacts to a real Git commit.

## What This Does Not Prove

- It does not prove Thunderbolt Bridge performance.
- It does not prove final three-node M5 Pro/M5 Max cluster behavior.
- It does not prove worker-node throughput or failure behavior.
- It does not prove model inference performance.
- It does not prove that full Qwen3-235B-A22B weights fit or run.
- It does not validate Metal kernels, tokenizer behavior, sampling, quality, or serving latency.

## Next Recommended Test From This Machine

Run a two-process socket-localhost smoke next: start worker B and worker C as separate local processes on `127.0.0.1`, then run the coordinator against a localhost TCP config. That would exercise process boundaries, socket IO, worker lifecycle, and reconnect/error reporting while still being clearly labeled non-hardware and non-cluster.
