const std = @import("std");
const Io = std.Io;

const protocol = @import("protocol.zig");

pub const CoordinatorOptions = struct {
    config: []const u8,
    scenario: []const u8,
    out: []const u8,
};

pub const WorkerOptions = struct {
    node: protocol.WorkerNode,
    listen: []const u8,
};

pub const InvalidReason = enum {
    no_arguments,
    help_must_stand_alone,
    unknown_argument,
    missing_value,
    duplicate_argument,
    missing_required_argument,
    invalid_node,
    invalid_listen,
};

pub const InvalidArgument = struct {
    reason: InvalidReason,
    argument: []const u8 = "",
};

pub const CoordinatorParseResult = union(enum) {
    help,
    run: CoordinatorOptions,
    invalid: InvalidArgument,
};

pub const WorkerParseResult = union(enum) {
    help,
    run: WorkerOptions,
    invalid: InvalidArgument,
};

pub const coordinator_usage =
    \\DS5 coordinator stub
    \\
    \\Usage:
    \\  ds5-coordinator --config <path> --scenario <path> --out <dir>
    \\  ds5-coordinator --help
    \\
    \\Options:
    \\  --config <path>    Cluster TOML config path.
    \\  --scenario <path>  Qwen3 MoE transport scenario TOML path.
    \\  --out <dir>        Output directory for Phase 0 benchmark artifacts.
    \\  --help             Print this help text.
    \\
    \\Phase 0 scope:
    \\  Runs the DS5/Qwen3 loopback transport smoke; no model loading or expert kernels.
    \\
;

pub const worker_usage =
    \\DS5 worker stub
    \\
    \\Usage:
    \\  ds5-worker --node <B|C> --listen <host:port>
    \\  ds5-worker --help
    \\
    \\Options:
    \\  --node <B|C>          DS5 decode worker identity.
    \\  --listen <host:port>  Planned worker listen address.
    \\  --help                Print this help text.
    \\
    \\Phase 0 scope:
    \\  Listens for the loopback transport smoke; no model loading or Metal work.
    \\
;

pub fn parseCoordinator(argv: anytype) CoordinatorParseResult {
    if (argv.len == 0) {
        return .{ .invalid = .{ .reason = .no_arguments } };
    }
    if (argv.len == 1 and isFlag(argv[0], "--help")) {
        return .help;
    }

    var config: ?[]const u8 = null;
    var scenario: ?[]const u8 = null;
    var out: ?[]const u8 = null;

    var i: usize = 0;
    while (i < argv.len) {
        const flag = argv[i];
        if (isFlag(flag, "--help")) {
            return .{ .invalid = .{ .reason = .help_must_stand_alone, .argument = flag } };
        }

        const value = nextValue(argv, i) orelse {
            return .{ .invalid = .{ .reason = .missing_value, .argument = flag } };
        };

        if (isFlag(flag, "--config")) {
            if (config != null) return .{ .invalid = .{ .reason = .duplicate_argument, .argument = flag } };
            config = value;
        } else if (isFlag(flag, "--scenario")) {
            if (scenario != null) return .{ .invalid = .{ .reason = .duplicate_argument, .argument = flag } };
            scenario = value;
        } else if (isFlag(flag, "--out")) {
            if (out != null) return .{ .invalid = .{ .reason = .duplicate_argument, .argument = flag } };
            out = value;
        } else if (std.mem.startsWith(u8, flag, "--")) {
            return .{ .invalid = .{ .reason = .unknown_argument, .argument = flag } };
        } else {
            return .{ .invalid = .{ .reason = .unknown_argument, .argument = flag } };
        }

        i += 2;
    }

    return .{ .run = .{
        .config = config orelse return .{ .invalid = .{ .reason = .missing_required_argument, .argument = "--config" } },
        .scenario = scenario orelse return .{ .invalid = .{ .reason = .missing_required_argument, .argument = "--scenario" } },
        .out = out orelse return .{ .invalid = .{ .reason = .missing_required_argument, .argument = "--out" } },
    } };
}

pub fn parseWorker(argv: anytype) WorkerParseResult {
    if (argv.len == 0) {
        return .{ .invalid = .{ .reason = .no_arguments } };
    }
    if (argv.len == 1 and isFlag(argv[0], "--help")) {
        return .help;
    }

    var node_raw: ?[]const u8 = null;
    var listen: ?[]const u8 = null;

    var i: usize = 0;
    while (i < argv.len) {
        const flag = argv[i];
        if (isFlag(flag, "--help")) {
            return .{ .invalid = .{ .reason = .help_must_stand_alone, .argument = flag } };
        }

        const value = nextValue(argv, i) orelse {
            return .{ .invalid = .{ .reason = .missing_value, .argument = flag } };
        };

        if (isFlag(flag, "--node")) {
            if (node_raw != null) return .{ .invalid = .{ .reason = .duplicate_argument, .argument = flag } };
            node_raw = value;
        } else if (isFlag(flag, "--listen")) {
            if (listen != null) return .{ .invalid = .{ .reason = .duplicate_argument, .argument = flag } };
            listen = value;
        } else if (std.mem.startsWith(u8, flag, "--")) {
            return .{ .invalid = .{ .reason = .unknown_argument, .argument = flag } };
        } else {
            return .{ .invalid = .{ .reason = .unknown_argument, .argument = flag } };
        }

        i += 2;
    }

    const parsed_node = protocol.WorkerNode.parse(node_raw orelse {
        return .{ .invalid = .{ .reason = .missing_required_argument, .argument = "--node" } };
    }) orelse {
        return .{ .invalid = .{ .reason = .invalid_node, .argument = node_raw.? } };
    };

    const parsed_listen = listen orelse {
        return .{ .invalid = .{ .reason = .missing_required_argument, .argument = "--listen" } };
    };
    if (!isListenAddress(parsed_listen)) {
        return .{ .invalid = .{ .reason = .invalid_listen, .argument = parsed_listen } };
    }

    return .{ .run = .{
        .node = parsed_node,
        .listen = parsed_listen,
    } };
}

pub fn writeCoordinatorUsage(writer: *Io.Writer) Io.Writer.Error!void {
    try writer.writeAll(coordinator_usage);
}

pub fn writeWorkerUsage(writer: *Io.Writer) Io.Writer.Error!void {
    try writer.writeAll(worker_usage);
}

pub fn writeInvalid(writer: *Io.Writer, invalid: InvalidArgument) Io.Writer.Error!void {
    try writer.print("error: {s}", .{invalidReasonText(invalid.reason)});
    if (invalid.argument.len != 0) {
        try writer.print(": {s}", .{invalid.argument});
    }
    try writer.writeAll("\n\n");
}

pub fn invalidReasonText(reason: InvalidReason) []const u8 {
    return switch (reason) {
        .no_arguments => "missing required arguments",
        .help_must_stand_alone => "--help must be the only argument",
        .unknown_argument => "unknown argument",
        .missing_value => "missing value",
        .duplicate_argument => "duplicate argument",
        .missing_required_argument => "missing required argument",
        .invalid_node => "invalid worker node",
        .invalid_listen => "invalid listen address",
    };
}

fn isFlag(value: []const u8, expected: []const u8) bool {
    return std.mem.eql(u8, value, expected);
}

fn nextValue(argv: anytype, flag_index: usize) ?[]const u8 {
    const value_index = flag_index + 1;
    if (value_index >= argv.len) return null;

    const value = argv[value_index];
    if (value.len == 0) return null;
    if (std.mem.startsWith(u8, value, "--")) return null;
    return value;
}

fn isListenAddress(value: []const u8) bool {
    const colon_index = std.mem.lastIndexOfScalar(u8, value, ':') orelse return false;
    if (colon_index == 0 or colon_index + 1 >= value.len) return false;

    const port = value[colon_index + 1 ..];
    _ = std.fmt.parseInt(u16, port, 10) catch return false;
    return true;
}

test "coordinator parser accepts the Phase 0 command shape" {
    const argv = [_][]const u8{
        "--config",
        "configs/cluster.local.toml",
        "--scenario",
        "benchmarks/scenarios/qwen3_moe_transport_smoke.toml",
        "--out",
        "artifacts/runs/transport-smoke",
    };
    const parsed = parseCoordinator(argv[0..]);

    switch (parsed) {
        .run => |options| {
            try std.testing.expect(std.mem.eql(u8, options.config, "configs/cluster.local.toml"));
            try std.testing.expect(std.mem.eql(u8, options.scenario, "benchmarks/scenarios/qwen3_moe_transport_smoke.toml"));
            try std.testing.expect(std.mem.eql(u8, options.out, "artifacts/runs/transport-smoke"));
        },
        else => return error.ExpectedRunOptions,
    }
}

test "coordinator parser rejects unknown and incomplete arguments" {
    const unknown = [_][]const u8{ "--config", "x", "--bogus", "y" };
    try expectCoordinatorInvalid(unknown[0..], .unknown_argument);

    const missing_value = [_][]const u8{ "--config", "x", "--scenario" };
    try expectCoordinatorInvalid(missing_value[0..], .missing_value);

    const mixed_help = [_][]const u8{ "--help", "--config", "x" };
    try expectCoordinatorInvalid(mixed_help[0..], .help_must_stand_alone);
}

test "worker parser accepts B and C decode workers" {
    const b_argv = [_][]const u8{ "--node", "B", "--listen", protocol.default_worker_b_listen };
    const b = parseWorker(b_argv[0..]);
    switch (b) {
        .run => |options| {
            try std.testing.expectEqual(protocol.WorkerNode.B, options.node);
            try std.testing.expect(std.mem.eql(u8, options.listen, protocol.default_worker_b_listen));
        },
        else => return error.ExpectedWorkerOptions,
    }

    const c_argv = [_][]const u8{ "--node", "C", "--listen", protocol.default_worker_c_listen };
    const c = parseWorker(c_argv[0..]);
    switch (c) {
        .run => |options| {
            try std.testing.expectEqual(protocol.WorkerNode.C, options.node);
            try std.testing.expect(std.mem.eql(u8, options.listen, protocol.default_worker_c_listen));
        },
        else => return error.ExpectedWorkerOptions,
    }
}

test "worker parser rejects invalid workers and listen addresses" {
    const invalid_node = [_][]const u8{ "--node", "A", "--listen", "0.0.0.0:7555" };
    try expectWorkerInvalid(invalid_node[0..], .invalid_node);

    const missing_port = [_][]const u8{ "--node", "B", "--listen", "0.0.0.0" };
    try expectWorkerInvalid(missing_port[0..], .invalid_listen);

    const port_overflow = [_][]const u8{ "--node", "B", "--listen", "0.0.0.0:99999" };
    try expectWorkerInvalid(port_overflow[0..], .invalid_listen);

    const missing_node = [_][]const u8{ "--listen", "0.0.0.0:7555" };
    try expectWorkerInvalid(missing_node[0..], .missing_required_argument);
}

fn expectCoordinatorInvalid(argv: anytype, reason: InvalidReason) !void {
    switch (parseCoordinator(argv)) {
        .invalid => |invalid| try std.testing.expectEqual(reason, invalid.reason),
        else => return error.ExpectedInvalidArguments,
    }
}

fn expectWorkerInvalid(argv: anytype, reason: InvalidReason) !void {
    switch (parseWorker(argv)) {
        .invalid => |invalid| try std.testing.expectEqual(reason, invalid.reason),
        else => return error.ExpectedInvalidArguments,
    }
}
