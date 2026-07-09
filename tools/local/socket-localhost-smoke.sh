#!/usr/bin/env sh
set -eu

RUN_DIR="${RUN_DIR:-artifacts/runs/socket-localhost-smoke}"
CONFIG="${CONFIG:-configs/cluster.socket-localhost.toml}"
SCENARIO="${SCENARIO:-benchmarks/scenarios/loopback_transport_smoke.toml}"
B_LISTEN="${B_LISTEN:-127.0.0.1:17555}"
C_LISTEN="${C_LISTEN:-127.0.0.1:17556}"
STARTUP_SLEEP_SECONDS="${STARTUP_SLEEP_SECONDS:-1}"
ZIG_CACHE_DIR="${ZIG_CACHE_DIR:-/private/tmp/qw4-zig-cache}"
ZIG_GLOBAL_CACHE_DIR="${ZIG_GLOBAL_CACHE_DIR:-/private/tmp/qw4-zig-global-cache}"
ZIG_PREFIX="${ZIG_PREFIX:-/private/tmp/qw4-zig-out}"

B_LOG="${B_LOG:-/tmp/ds5-worker-b-socket-localhost.log}"
C_LOG="${C_LOG:-/tmp/ds5-worker-c-socket-localhost.log}"
COORDINATOR_BIN="$ZIG_PREFIX/bin/ds5-coordinator"
WORKER_BIN="$ZIG_PREFIX/bin/ds5-worker"
EFFECTIVE_CONFIG="${EFFECTIVE_CONFIG:-/private/tmp/ds5-socket-localhost-$$.toml}"

worker_b_pid=""
worker_c_pid=""

cleanup() {
  if [ -n "$worker_b_pid" ] && kill -0 "$worker_b_pid" 2>/dev/null; then
    kill "$worker_b_pid" 2>/dev/null || true
  fi
  if [ -n "$worker_c_pid" ] && kill -0 "$worker_c_pid" 2>/dev/null; then
    kill "$worker_c_pid" 2>/dev/null || true
  fi
  rm -f "$EFFECTIVE_CONFIG"
}
trap cleanup EXIT INT TERM

step() {
  printf '\n==> %s\n' "$1"
}

printf '%s\n' "DS5 socket-localhost smoke."
printf '%s\n' "This uses separate local worker processes over TCP localhost."
printf '%s\n' "It is not Thunderbolt, RDMA, multi-host, or model inference data."

step "Build binaries"
zig build --cache-dir "$ZIG_CACHE_DIR" --global-cache-dir "$ZIG_GLOBAL_CACHE_DIR" --prefix "$ZIG_PREFIX"

step "Prepare socket-localhost config"
sed \
  -e "s/127.0.0.1:7555/$B_LISTEN/g" \
  -e "s/127.0.0.1:7556/$C_LISTEN/g" \
  "$CONFIG" >"$EFFECTIVE_CONFIG"
printf 'effective config=%s\n' "$EFFECTIVE_CONFIG"

step "Start worker B"
"$WORKER_BIN" --node B --listen "$B_LISTEN" >"$B_LOG" 2>&1 &
worker_b_pid="$!"
printf 'worker B pid=%s log=%s\n' "$worker_b_pid" "$B_LOG"

step "Start worker C"
"$WORKER_BIN" --node C --listen "$C_LISTEN" >"$C_LOG" 2>&1 &
worker_c_pid="$!"
printf 'worker C pid=%s log=%s\n' "$worker_c_pid" "$C_LOG"

sleep "$STARTUP_SLEEP_SECONDS"

if ! kill -0 "$worker_b_pid" 2>/dev/null; then
  printf '%s\n' "worker B exited before coordinator run" >&2
  cat "$B_LOG" >&2 || true
  exit 1
fi
if ! kill -0 "$worker_c_pid" 2>/dev/null; then
  printf '%s\n' "worker C exited before coordinator run" >&2
  cat "$C_LOG" >&2 || true
  exit 1
fi

step "Run coordinator"
"$COORDINATOR_BIN" \
  --config "$EFFECTIVE_CONFIG" \
  --scenario "$SCENARIO" \
  --out "$RUN_DIR"

step "Validate generated artifacts"
python3 -B tools/report/validate_run.py "$RUN_DIR"

step "Summarize generated artifacts"
python3 -B tools/report/summarize_phase0.py "$RUN_DIR"

step "Worker logs"
cat "$B_LOG"
cat "$C_LOG"

printf '\n%s\n' "Socket-localhost smoke complete."
printf '%s\n' "Run artifacts: $RUN_DIR"
