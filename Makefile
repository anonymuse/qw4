ZIG_CACHE_DIR ?= /private/tmp/qw4-zig-cache
ZIG_GLOBAL_CACHE_DIR ?= /private/tmp/qw4-zig-global-cache
ZIG_PREFIX ?= /private/tmp/qw4-zig-out
PYTHONPYCACHEPREFIX ?= /private/tmp/qw4-pycache
RUN_ID ?= local-smoke
RUN_DIR ?= artifacts/runs/$(RUN_ID)

.PHONY: build test loopback-smoke socket-workers socket-smoke validate-artifacts memory-estimate memory-sweep summarize-report aggregate-report qwen-moe-sim

build:
	zig build --cache-dir $(ZIG_CACHE_DIR) --global-cache-dir $(ZIG_GLOBAL_CACHE_DIR) --prefix $(ZIG_PREFIX)

test:
	zig build test --cache-dir $(ZIG_CACHE_DIR) --global-cache-dir $(ZIG_GLOBAL_CACHE_DIR) --prefix $(ZIG_PREFIX)
	PYTHONPYCACHEPREFIX=$(PYTHONPYCACHEPREFIX) python3 -m unittest tests.report.test_validate_run

loopback-smoke:
	zig build run-coordinator -- --config configs/cluster.loopback.toml --scenario benchmarks/scenarios/loopback_transport_smoke.toml --out $(RUN_DIR)

socket-workers:
	@echo "Run these in two terminals before socket-smoke:"
	@echo "zig build run-worker -- --node B --listen 127.0.0.1:7555"
	@echo "zig build run-worker -- --node C --listen 127.0.0.1:7556"

socket-smoke:
	zig build run-coordinator -- --config configs/cluster.socket-localhost.toml --scenario benchmarks/scenarios/loopback_transport_smoke.toml --out $(RUN_DIR)

validate-artifacts:
	python3 tools/report/validate_run.py $(RUN_DIR)

memory-estimate:
	python3 tools/quant/estimate_qwen3_memory.py --config configs/qwen3_235b_a22b_planning.json --mode a-static-owner

memory-sweep:
	python3 tools/quant/estimate_qwen3_memory.py --config configs/qwen3_235b_a22b_planning.json --mode bc-worker-only --sweep-expert-bits 2,3,4,6,8

summarize-report:
	python3 tools/report/summarize_phase0.py $(RUN_DIR)

aggregate-report:
	python3 tools/report/aggregate_phase0.py --root artifacts/runs

qwen-moe-sim:
	python3 tools/model_inspect/simulate_qwen3_moe.py --run-dir $(RUN_DIR)
