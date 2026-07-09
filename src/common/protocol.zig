const std = @import("std");

pub const ds5_version = "0.0.0-phase0";
pub const target_model = "Qwen3-235B-A22B-Instruct-2507";
pub const deferred_model = "Qwen3-235B-A22B-Thinking-2507";

pub const qwen3 = struct {
    pub const total_parameters_b = 235;
    pub const activated_parameters_b = 22;
    pub const layers = 94;
    pub const experts = 128;
    pub const activated_experts = 8;
    pub const hidden_size = 4096;
    pub const attention_heads = 64;
    pub const kv_heads = 4;
    pub const head_dimension = 128;
    pub const worker_b_first_layer = 0;
    pub const worker_b_last_layer = 46;
    pub const worker_c_first_layer = 47;
    pub const worker_c_last_layer = 93;
};

pub const NodeRole = enum {
    coordinator,
    worker,
};

pub const WorkerNode = enum {
    B,
    C,

    pub fn parse(value: []const u8) ?WorkerNode {
        if (std.mem.eql(u8, value, "B")) return .B;
        if (std.mem.eql(u8, value, "C")) return .C;
        return null;
    }

    pub fn label(node: WorkerNode) []const u8 {
        return switch (node) {
            .B => "B",
            .C => "C",
        };
    }
};

pub const default_worker_b_listen = "0.0.0.0:7555";
pub const default_worker_c_listen = "0.0.0.0:7556";

test "Qwen3 Phase 0 constants match the DS5 planning shape" {
    try std.testing.expectEqual(@as(comptime_int, 94), qwen3.layers);
    try std.testing.expectEqual(@as(comptime_int, 4096), qwen3.hidden_size);
    try std.testing.expectEqual(@as(comptime_int, 128), qwen3.experts);
    try std.testing.expectEqual(@as(comptime_int, 8), qwen3.activated_experts);
    try std.testing.expectEqual(@as(comptime_int, 46), qwen3.worker_b_last_layer);
    try std.testing.expectEqual(@as(comptime_int, 47), qwen3.worker_c_first_layer);
}

test "worker node parser only accepts DS5 decode workers" {
    try std.testing.expectEqual(WorkerNode.B, WorkerNode.parse("B").?);
    try std.testing.expectEqual(WorkerNode.C, WorkerNode.parse("C").?);
    try std.testing.expectEqual(@as(?WorkerNode, null), WorkerNode.parse("A"));
}
