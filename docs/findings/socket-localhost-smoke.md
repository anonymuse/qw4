# Socket-Localhost Smoke Finding

Status: local socket-only validation. Fill concrete metrics from generated
artifacts after each run.

## Scope

The socket-localhost smoke starts worker B and worker C as separate local
processes and sends coordinator traffic over TCP localhost. This validates
process boundaries, framed socket IO, worker lifecycle, artifact emission, and
reporting around `socket_localhost` mode.

It is not Thunderbolt, RDMA-style, multi-host, or model inference data.

## Command

```bash
make socket-localhost-smoke RUN_ID=socket-localhost-smoke
```

Equivalent helper:

```bash
RUN_DIR=artifacts/runs/socket-localhost-smoke \
tools/local/socket-localhost-smoke.sh
```

## Required Interpretation

Expected artifact fields:

| Field | Expected value |
|---|---|
| `environment.transport_mode` | `socket_localhost` |
| `environment.socket_mode` | `tcp_localhost` |
| `environment.hardware_interpretable` | `false` |
| `scenario.kind` | `socket_localhost` |

If any generated artifact marks the run as hardware-interpretable, the run is
invalid and the classification code must be fixed before publishing results.

## Result Template

| Field | Value |
|---|---|
| Run ID | `[artifact run id]` |
| Git commit | `[run.json git_commit]` |
| Transfers | `[checksums.total_transfers]` |
| Bytes sent | `[sum throughput.csv bytes_sent]` |
| Checksum failures | `[checksums.failed]` |
| Worker health events | `[count]` |
| Failure events | `[count]` |
| Artifact validation | `[pass/fail]` |

## Next Boundary

Passing socket-localhost smoke earns the right to run a real two-node smoke with
an explicitly recorded non-loopback network path. It does not justify model
runtime work or hardware transport claims by itself.
