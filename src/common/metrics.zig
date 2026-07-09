const std = @import("std");

pub const required_artifacts = [_][]const u8{
    "run.json",
    "events.jsonl",
    "latency.csv",
    "throughput.csv",
    "summary.md",
};

pub const RequiredMetric = enum {
    node_discovery_latency,
    worker_health_status,
    latency_percentiles_by_message_size,
    sustained_throughput_by_block_size,
    checksum_failures,
    scheduler_overhead_per_simulated_token,
    bytes_sent_per_simulated_token,
    per_layer_simulated_transport_time,
    concurrent_link_interference,
    reconnect_behavior,
    predicted_upper_bound_tokens_per_second,
};

pub fn artifactCount() usize {
    return required_artifacts.len;
}

test "Phase 0 artifact manifest includes the accepted output set" {
    try std.testing.expectEqual(@as(usize, 5), artifactCount());
    try std.testing.expect(std.mem.eql(u8, required_artifacts[0], "run.json"));
    try std.testing.expect(std.mem.eql(u8, required_artifacts[4], "summary.md"));
}
