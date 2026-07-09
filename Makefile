ZIG_CACHE_DIR ?= /private/tmp/qw4-zig-cache
ZIG_GLOBAL_CACHE_DIR ?= /private/tmp/qw4-zig-global-cache
ZIG_PREFIX ?= /private/tmp/qw4-zig-out
PYTHONPYCACHEPREFIX ?= /private/tmp/qw4-pycache
RUN_ID ?= local-smoke
RUN_DIR ?= artifacts/runs/$(RUN_ID)

.PHONY: build test loopback-smoke socket-workers socket-smoke socket-localhost-smoke validate-artifacts memory-estimate memory-sweep pdd-topology-validate phase0-routing-payload-validate summarize-report aggregate-report qwen-moe-sim

build:
	zig build --cache-dir $(ZIG_CACHE_DIR) --global-cache-dir $(ZIG_GLOBAL_CACHE_DIR) --prefix $(ZIG_PREFIX)

test:
	zig build test --cache-dir $(ZIG_CACHE_DIR) --global-cache-dir $(ZIG_GLOBAL_CACHE_DIR) --prefix $(ZIG_PREFIX)
	PYTHONPYCACHEPREFIX=$(PYTHONPYCACHEPREFIX) python3 -m unittest tests.report.test_validate_run tests.model.test_pdd_topology tests.model.test_phase0_routing_payload

loopback-smoke:
	zig build run-coordinator -- --config configs/cluster.loopback.toml --scenario benchmarks/scenarios/loopback_transport_smoke.toml --out $(RUN_DIR)

socket-workers:
	@echo "Run these in two terminals before socket-smoke:"
	@echo "zig build run-worker -- --node B --listen 127.0.0.1:7555"
	@echo "zig build run-worker -- --node C --listen 127.0.0.1:7556"

socket-smoke:
	zig build run-coordinator -- --config configs/cluster.socket-localhost.toml --scenario benchmarks/scenarios/loopback_transport_smoke.toml --out $(RUN_DIR)

socket-localhost-smoke:
	RUN_DIR=$(RUN_DIR) ZIG_CACHE_DIR=$(ZIG_CACHE_DIR) ZIG_GLOBAL_CACHE_DIR=$(ZIG_GLOBAL_CACHE_DIR) ZIG_PREFIX=$(ZIG_PREFIX) tools/local/socket-localhost-smoke.sh

validate-artifacts:
	python3 tools/report/validate_run.py $(RUN_DIR)

memory-estimate:
	python3 tools/quant/estimate_qwen3_memory.py --config configs/qwen3_235b_a22b_planning.json --mode a-static-owner

memory-sweep:
	python3 tools/quant/estimate_qwen3_memory.py --config configs/qwen3_235b_a22b_planning.json --mode bc-worker-only --sweep-expert-bits 2,3,4,6,8

pdd-topology-validate:
	python3 tools/model_inspect/validate_pdd_topology.py --manifest configs/qwen3_pdd_topology_phase1.json --ledger-out artifacts/pdd/ds5-f001-memory-ledger.json --summary-out docs/findings/ds5-f001-pdd-topology-acceptance.md

phase0-routing-payload-validate:
	python3 tools/model_inspect/validate_phase0_routing_payload.py --manifest configs/qwen3_phase0_routing_payload.json --artifact-out artifacts/routing/phase0-routing-payload.json --summary-out docs/findings/phase0-routing-payload-scaffold.md

summarize-report:
	python3 tools/report/summarize_phase0.py $(RUN_DIR)

aggregate-report:
	python3 tools/report/aggregate_phase0.py --root artifacts/runs

qwen-moe-sim:
	python3 tools/model_inspect/simulate_qwen3_moe.py --run-dir $(RUN_DIR)
