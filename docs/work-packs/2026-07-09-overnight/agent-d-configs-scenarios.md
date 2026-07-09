# Agent D: Cluster Configs And Scenario Definitions

## Objective

Create deterministic configuration files for the Phase 0 cluster and benchmark scenarios. The configs should make assumptions explicit and keep command lines reproducible.

## Read First

- `docs/assumptions.md`
- `docs/minimum-viable-finding.md`
- `docs/runbooks/cluster-setup.md`

## Owned Paths

- `configs/`
- `benchmarks/scenarios/`
- small edits to `docs/runbooks/cluster-setup.md`

## Deliverables

Create:

```text
configs/cluster.local.example.toml
configs/cluster.loopback.toml
benchmarks/scenarios/loopback_transport_smoke.toml
benchmarks/scenarios/qwen3_moe_transport_smoke.toml
benchmarks/scenarios/block_size_sweep.toml
```

Each scenario should specify:

- scenario name;
- node roles;
- message sizes;
- transfer counts;
- warmup count;
- checksum mode;
- output artifact directory;
- whether results may be interpreted as real hardware data.

The Qwen-shaped scenario should include:

- 94 layers;
- hidden size 4096;
- top-k 8;
- B layer range 0-46;
- C layer range 47-93;
- local and remote expert-rate sweep values;
- one packet per destination node per layer.

## Acceptance Checks

Configs are accepted if:

- a human can read them without hidden defaults;
- every scenario says whether it is synthetic, loopback, or real cluster;
- the runbook includes the intended commands.

## Do Not

- Do not put personal IPs or secrets in committed configs.
- Do not assume Thunderbolt Bridge is active without a user-provided config.
- Do not encode performance targets as expected results.

## Handoff Notes

Report:

- config files created;
- fields the runtime must parse first;
- any assumptions that need a later ADR.

