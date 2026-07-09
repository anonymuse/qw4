# Feature DS5-F005: Localized Metal Kernel Fragmentation

Status: deferred until placement-contract, Phase 0 transport, and worker-runtime gates justify Metal kernel work; runtime goal not met.

Epic: `DS5-E05: Metal Worker Kernels`

Complexity Score: 9/10 for Zig 1.0 bare-metal implementation difficulty.

PM Validation Gate: `PM-GATE-MTL-01: Metal Kernel Stability And Long-Run TDR Evidence`

Governing baseline: `DS5_System_Architecture_v0.2_Qwen3_235B_A22B.md`, `DS5_Benchmark_and_Acceptance_Spec_v0.2_Qwen3_235B_A22B.md`, [DS5 Assumptions](../assumptions.md), [Risk Register](../risk-register.md), and [Project Plan After ARB Refresh](project-plan.md).

## Technical Scope

Segment large MoE multi-expert calculations on Nodes B and C into localized, non-blocking Metal command fragments:

- Implement Metal command planning for worker-local expert execution.
- Split large multi-expert matrix multiplications into bounded fragments that yield command lanes predictably.
- Keep B/C worker execution independent so one node's Metal command queue cannot block the other node's scheduling path.
- Expose command-buffer duration, queue depth, memory-lane occupancy, fragment size, and worker health telemetry.
- Ensure fragment sizing cooperates with UMA reserve, KV cache pressure, and transport buffer pressure.

Existing implementation signals:

- `docs/repository-architecture.md` reserves `src/kernels/` for future Metal runtime and shaders.
- No `src/kernels/` implementation exists yet.
- Current code is Phase 0 transport and planning only.

## Rigid Acceptance Criteria

- Worker kernels must fragment MoE multi-expert matrix multiplications into localized Metal command buffers with bounded execution duration.
- Fragment scheduling must be non-blocking with respect to worker health reporting, transport receive loops, and result emission.
- Matrix multiplications must physically yield memory lanes fast enough to guarantee zero macOS WindowServer hardware command buffer timeouts during extended generation loops.
- The acceptance run must report zero WindowServer hardware command buffer timeout, GPU reset, command queue loss, or equivalent Metal device-removal event.
- Kernel telemetry must include command-buffer duration distribution, p50/p95/p99 fragment time, queue depth, active fragments, bytes read/written, and worker stall reasons.
- The fragment planner must adapt to B/C memory pressure and must refuse fragment sizes that would violate the 30% runtime reserve.
- Tests must cover fragment planner bounds, queue backpressure, command failure propagation, worker cancellation, and long-run health reporting.

## PM Validation Evidence

The merge request must attach or reference:

- Metal fragment planner tests and fixtures;
- worker-local kernel benchmark artifacts for Nodes B and C;
- long-run generation-loop artifact with command-buffer timing and zero timeout evidence;
- macOS system log excerpt or structured check proving no WindowServer hardware command buffer timeout occurred;
- memory-reserve telemetry showing B/C remain above 30% headroom during kernel execution.

## Merge Blockers

- Any long-running monolithic expert matmul that can monopolize Metal command execution.
- Any missing command-buffer timing telemetry.
- Any WindowServer hardware command buffer timeout, GPU reset, or device loss during the acceptance run.
- Any kernel path that violates B/C memory headroom or blocks worker health/transport loops.
