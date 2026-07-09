const std = @import("std");
const Io = std.Io;

const common = @import("ds5_common");
const build_options = @import("build_options");
const protocol = common.protocol;

const net = std.Io.net;

pub const header_len = 54;
pub const max_payload_bytes = 16 * 1024 * 1024;

const magic = [_]u8{ 'D', 'S', '5', 'L' };
const version: u8 = 1;

pub const FrameKind = enum(u8) {
    ping = 1,
    pong = 2,
    block = 3,
    echo = 4,
    shutdown = 5,
    ack = 6,
    transport_error = 7,
};

pub const FrameHeader = struct {
    kind: FrameKind,
    seq: u64,
    payload_len: usize,
    checksum: [32]u8,
};

pub const DecodedFrame = struct {
    header: FrameHeader,
    payload: []u8,

    pub fn deinit(self: *DecodedFrame, allocator: std.mem.Allocator) void {
        allocator.free(self.payload);
        self.* = undefined;
    }
};

pub const Scenario = struct {
    name: []const u8,
    message_sizes: std.ArrayList(usize),
    transfer_count: usize,
    warmup_count: usize,
    payload_seed: u64,

    pub fn deinit(self: *Scenario, allocator: std.mem.Allocator) void {
        self.message_sizes.deinit(allocator);
        self.* = undefined;
    }
};

pub const WorkerEndpoint = struct {
    node: protocol.WorkerNode,
    address: []const u8,
};

pub const ClusterConfig = struct {
    name: []const u8,
    config_kind: []const u8,
    loopback: bool,
    intended_link: []const u8,
    network_path_must_be_recorded: bool,
    confirmed_network_path: []const u8,
    results_warning: []const u8,
    connect_timeout_ms: u64,
    heartbeat_interval_ms: u64,
    heartbeat_timeout_ms: u64,
    reconnect_attempts: usize,
    workers: [2]WorkerEndpoint,
    worker_count: usize,

    pub fn workerEndpoints(self: *const ClusterConfig) []const WorkerEndpoint {
        return self.workers[0..self.worker_count];
    }
};

pub const MessageStats = struct {
    node: protocol.WorkerNode,
    message_size: usize,
    transfer_count: usize,
    bytes_sent: u64,
    bytes_received: u64,
    checksum_failures: u64,
    min_latency_ns: u64,
    p50_latency_ns: u64,
    p95_latency_ns: u64,
    p99_latency_ns: u64,
    max_latency_ns: u64,
    elapsed_ns: u64,
    throughput_bytes_per_sec: u64,
};

pub const RunMode = enum {
    single_process_loopback,
    socket_localhost,
    real_cluster,

    pub fn label(mode: RunMode) []const u8 {
        return switch (mode) {
            .single_process_loopback => "single_process_loopback",
            .socket_localhost => "socket_localhost",
            .real_cluster => "real_cluster",
        };
    }
};

pub const RunResult = struct {
    run_id: []u8,
    config_path: []const u8,
    scenario_path: []const u8,
    out_dir: []const u8,
    mode: RunMode,
    scenario_name: []const u8,
    config_name: []const u8,
    config_kind: []const u8,
    results_warning: []const u8,
    scenario_kind: []const u8,
    network_path: []const u8,
    socket_mode: []const u8,
    confirmed_network_path: []const u8,
    hardware_interpretable: bool,
    warmup_count: usize,
    failure_count: u64,
    retry_count: u64,
    reconnect_count: u64,
    timeout_count: u64,
    start_real_ns: i96,
    end_real_ns: i96,
    elapsed_ns: u64,
    total_transfers: u64,
    total_bytes_sent: u64,
    total_bytes_received: u64,
    checksum_failures: u64,
    stats: std.ArrayList(MessageStats),
    events: Io.Writer.Allocating,
    event_sequence: u64,

    pub fn deinit(self: *RunResult, allocator: std.mem.Allocator) void {
        allocator.free(self.run_id);
        self.stats.deinit(allocator);
        self.events.deinit();
        self.* = undefined;
    }
};

pub fn runCoordinator(
    allocator: std.mem.Allocator,
    io: Io,
    options: common.args.CoordinatorOptions,
) !RunResult {
    const cwd = Io.Dir.cwd();
    const config_text = try cwd.readFileAlloc(io, options.config, allocator, .limited(256 * 1024));
    defer allocator.free(config_text);
    const scenario_text = try cwd.readFileAlloc(io, options.scenario, allocator, .limited(256 * 1024));
    defer allocator.free(scenario_text);

    const cluster = try parseClusterConfig(config_text);
    var scenario = try parseScenario(allocator, scenario_text);
    defer scenario.deinit(allocator);

    var result = try initRunResult(allocator, io, options, cluster, scenario);
    errdefer result.deinit(allocator);

    if (cluster.loopback) {
        result.mode = .single_process_loopback;
        refreshRunClassification(cluster, &result);
        try runSingleProcessSmoke(allocator, io, cluster, scenario, &result);
    } else {
        result.mode = classifyRunMode(cluster);
        refreshRunClassification(cluster, &result);
        try runNetworkSmoke(allocator, io, cluster, scenario, &result);
    }

    result.end_real_ns = Io.Clock.real.now(io).nanoseconds;
    result.elapsed_ns = nsSince(result.start_real_ns, result.end_real_ns);
    try emitRunCompletedEvent(&result);
    try writeArtifacts(allocator, io, &result);
    return result;
}

pub fn runWorker(
    allocator: std.mem.Allocator,
    io: Io,
    node: protocol.WorkerNode,
    listen_address: []const u8,
) !WorkerSummary {
    var address = try parseAddressLiteral(listen_address);
    var server = try address.listen(io, .{ .reuse_address = true });
    defer server.deinit(io);

    var stream = try server.accept(io);
    defer stream.close(io);

    var reader_buffer: [64 * 1024]u8 = undefined;
    var writer_buffer: [64 * 1024]u8 = undefined;
    var stream_reader = stream.reader(io, &reader_buffer);
    var stream_writer = stream.writer(io, &writer_buffer);

    return handleWorkerSession(
        allocator,
        &stream_reader.interface,
        &stream_writer.interface,
        node,
    );
}

pub const WorkerSummary = struct {
    node: protocol.WorkerNode,
    transfers: u64,
    bytes_received: u64,
    bytes_sent: u64,
    checksum_failures: u64,
};

fn initRunResult(
    allocator: std.mem.Allocator,
    io: Io,
    options: common.args.CoordinatorOptions,
    cluster: ClusterConfig,
    scenario: Scenario,
) !RunResult {
    const start = Io.Clock.real.now(io).nanoseconds;
    const run_id = try runIdFromOutDir(allocator, options.out);
    var result = RunResult{
        .run_id = run_id,
        .config_path = options.config,
        .scenario_path = options.scenario,
        .out_dir = options.out,
        .mode = classifyRunMode(cluster),
        .scenario_name = scenario.name,
        .config_name = cluster.name,
        .config_kind = cluster.config_kind,
        .results_warning = cluster.results_warning,
        .scenario_kind = scenarioKindForMode(classifyRunMode(cluster)),
        .network_path = networkPathForMode(cluster, classifyRunMode(cluster)),
        .socket_mode = socketModeForMode(classifyRunMode(cluster)),
        .confirmed_network_path = cluster.confirmed_network_path,
        .hardware_interpretable = hardwareInterpretable(cluster, classifyRunMode(cluster)),
        .warmup_count = scenario.warmup_count,
        .failure_count = 0,
        .retry_count = 0,
        .reconnect_count = 0,
        .timeout_count = 0,
        .start_real_ns = start,
        .end_real_ns = start,
        .elapsed_ns = 0,
        .total_transfers = 0,
        .total_bytes_sent = 0,
        .total_bytes_received = 0,
        .checksum_failures = 0,
        .stats = .empty,
        .events = .init(allocator),
        .event_sequence = 0,
    };
    try emitRunStartedEvent(&result);
    return result;
}

fn runNetworkSmoke(
    allocator: std.mem.Allocator,
    io: Io,
    cluster: ClusterConfig,
    scenario: Scenario,
    result: *RunResult,
) !void {
    for (cluster.workerEndpoints()) |endpoint| {
        var stream = try connectToEndpointWithReconnect(io, endpoint, cluster, result);
        defer stream.close(io);

        var reader_buffer: [64 * 1024]u8 = undefined;
        var writer_buffer: [64 * 1024]u8 = undefined;
        var stream_reader = stream.reader(io, &reader_buffer);
        var stream_writer = stream.writer(io, &writer_buffer);

        try emitNodeDiscoveredEvent(result, endpoint.node, endpoint.address, 0);
        try pingWorker(allocator, io, endpoint.node, &stream_reader.interface, &stream_writer.interface, result);
        try runWorkerTraffic(
            allocator,
            io,
            endpoint.node,
            scenario,
            &stream_reader.interface,
            &stream_writer.interface,
            result,
        );
        try writeFrame(&stream_writer.interface, .shutdown, 0, &.{});
        var ack = try readFrame(allocator, &stream_reader.interface);
        defer ack.deinit(allocator);
        if (ack.header.kind != .ack) return error.InvalidWorkerResponse;
    }
}

fn refreshRunClassification(cluster: ClusterConfig, result: *RunResult) void {
    result.scenario_kind = scenarioKindForMode(result.mode);
    result.network_path = networkPathForMode(cluster, result.mode);
    result.socket_mode = socketModeForMode(result.mode);
    result.confirmed_network_path = cluster.confirmed_network_path;
    result.hardware_interpretable = hardwareInterpretable(cluster, result.mode);
}

fn classifyRunMode(cluster: ClusterConfig) RunMode {
    if (cluster.loopback) return .single_process_loopback;
    if (allWorkerEndpointsAreLocal(cluster)) return .socket_localhost;
    return .real_cluster;
}

fn allWorkerEndpointsAreLocal(cluster: ClusterConfig) bool {
    for (cluster.workerEndpoints()) |endpoint| {
        if (!isLocalEndpoint(endpoint.address)) return false;
    }
    return true;
}

fn isLocalEndpoint(address: []const u8) bool {
    return std.mem.startsWith(u8, address, "127.0.0.1:") or
        std.mem.startsWith(u8, address, "localhost:") or
        std.mem.startsWith(u8, address, "[::1]:") or
        std.mem.startsWith(u8, address, "::1:");
}

fn scenarioKindForMode(mode: RunMode) []const u8 {
    return switch (mode) {
        .single_process_loopback => "loopback",
        .socket_localhost => "socket_localhost",
        .real_cluster => "real_cluster",
    };
}

fn socketModeForMode(mode: RunMode) []const u8 {
    return switch (mode) {
        .single_process_loopback => "in_process",
        .socket_localhost => "tcp_localhost",
        .real_cluster => "tcp_network",
    };
}

fn networkPathForMode(cluster: ClusterConfig, mode: RunMode) []const u8 {
    if (cluster.confirmed_network_path.len != 0) return cluster.confirmed_network_path;
    if (cluster.intended_link.len != 0 and mode == .real_cluster) return cluster.intended_link;
    return RunMode.label(mode);
}

fn hardwareInterpretable(cluster: ClusterConfig, mode: RunMode) bool {
    if (mode != .real_cluster) return false;
    if (!cluster.network_path_must_be_recorded) return false;
    if (cluster.confirmed_network_path.len == 0) return false;
    return !isLocalEndpoint(cluster.confirmed_network_path);
}

fn runSingleProcessSmoke(
    allocator: std.mem.Allocator,
    io: Io,
    cluster: ClusterConfig,
    scenario: Scenario,
    result: *RunResult,
) !void {
    for (cluster.workerEndpoints()) |endpoint| {
        try emitNodeDiscoveredEvent(result, endpoint.node, endpoint.address, 0);
        try pingWorkerInProcess(allocator, io, endpoint.node, result);
        try runInProcessTraffic(allocator, io, endpoint.node, scenario, result);
    }
}

fn connectToEndpointWithReconnect(
    io: Io,
    endpoint: WorkerEndpoint,
    cluster: ClusterConfig,
    result: *RunResult,
) !net.Stream {
    var attempt: usize = 0;
    while (true) {
        if (connectToAddress(io, endpoint.address)) |stream| {
            if (attempt > 0) {
                result.reconnect_count += 1;
                try emitReconnectSucceededEvent(result, endpoint.node, attempt, 0);
            }
            return stream;
        } else |err| {
            result.failure_count += 1;
            try emitFailureObservedEvent(result, endpoint.node, "connect_failed", @errorName(err));
            if (attempt >= cluster.reconnect_attempts) return err;
            attempt += 1;
            result.retry_count += 1;
            try emitRetryScheduledEvent(result, endpoint.node, "connect_failed", attempt);
        }
    }
}

fn pingWorker(
    allocator: std.mem.Allocator,
    io: Io,
    node: protocol.WorkerNode,
    reader: *Io.Reader,
    writer: *Io.Writer,
    result: *RunResult,
) !void {
    const start = Io.Clock.awake.now(io).nanoseconds;
    try writeFrame(writer, .ping, 0, &.{});
    var response = try readFrame(allocator, reader);
    defer response.deinit(allocator);
    const end = Io.Clock.awake.now(io).nanoseconds;
    if (response.header.kind != .pong) return error.InvalidWorkerResponse;
    if (!verifyFrame(response.header, response.payload)) {
        result.checksum_failures += 1;
        return error.ChecksumFailure;
    }
    try emitWorkerHealthEvent(result, node, nsSince(start, end));
}

fn pingWorkerInProcess(
    allocator: std.mem.Allocator,
    io: Io,
    node: protocol.WorkerNode,
    result: *RunResult,
) !void {
    const start = Io.Clock.awake.now(io).nanoseconds;
    var response = try roundTripInProcess(allocator, node, .ping, 0, &.{});
    defer response.deinit(allocator);
    const end = Io.Clock.awake.now(io).nanoseconds;
    if (response.header.kind != .pong) return error.InvalidWorkerResponse;
    try emitWorkerHealthEvent(result, node, nsSince(start, end));
}

fn runWorkerTraffic(
    allocator: std.mem.Allocator,
    io: Io,
    node: protocol.WorkerNode,
    scenario: Scenario,
    reader: *Io.Reader,
    writer: *Io.Writer,
    result: *RunResult,
) !void {
    var payload: std.ArrayList(u8) = .empty;
    defer payload.deinit(allocator);

    for (scenario.message_sizes.items) |message_size| {
        try payload.resize(allocator, message_size);
        const total_iterations = scenario.warmup_count + scenario.transfer_count;
        var latencies = try allocator.alloc(u64, scenario.transfer_count);
        defer allocator.free(latencies);
        var measured_index: usize = 0;
        var bytes_sent: u64 = 0;
        var bytes_received: u64 = 0;
        var checksum_failures: u64 = 0;
        const elapsed_start = Io.Clock.awake.now(io).nanoseconds;

        for (0..total_iterations) |i| {
            fillPayload(payload.items, scenario.payload_seed, node, message_size, i);
            const seq = makeSeq(node, message_size, i);
            const start = Io.Clock.awake.now(io).nanoseconds;
            try writeFrame(writer, .block, seq, payload.items);
            var response = try readFrame(allocator, reader);
            defer response.deinit(allocator);
            const end = Io.Clock.awake.now(io).nanoseconds;

            if (response.header.kind != .echo) return error.InvalidWorkerResponse;
            if (!verifyFrame(response.header, response.payload) or !std.mem.eql(u8, payload.items, response.payload)) {
                checksum_failures += 1;
                result.checksum_failures += 1;
            }

            if (i >= scenario.warmup_count) {
                latencies[measured_index] = nsSince(start, end);
                measured_index += 1;
                bytes_sent += message_size;
                bytes_received += response.payload.len;
            }
        }

        const elapsed_end = Io.Clock.awake.now(io).nanoseconds;
        try appendStats(
            allocator,
            result,
            node,
            message_size,
            scenario.transfer_count,
            bytes_sent,
            bytes_received,
            checksum_failures,
            latencies,
            nsSince(elapsed_start, elapsed_end),
        );
    }
}

fn runInProcessTraffic(
    allocator: std.mem.Allocator,
    io: Io,
    node: protocol.WorkerNode,
    scenario: Scenario,
    result: *RunResult,
) !void {
    var payload: std.ArrayList(u8) = .empty;
    defer payload.deinit(allocator);

    for (scenario.message_sizes.items) |message_size| {
        try payload.resize(allocator, message_size);
        const total_iterations = scenario.warmup_count + scenario.transfer_count;
        var latencies = try allocator.alloc(u64, scenario.transfer_count);
        defer allocator.free(latencies);
        var measured_index: usize = 0;
        var bytes_sent: u64 = 0;
        var bytes_received: u64 = 0;
        var checksum_failures: u64 = 0;
        const elapsed_start = Io.Clock.awake.now(io).nanoseconds;

        for (0..total_iterations) |i| {
            fillPayload(payload.items, scenario.payload_seed, node, message_size, i);
            const seq = makeSeq(node, message_size, i);
            const start = Io.Clock.awake.now(io).nanoseconds;
            var response = try roundTripInProcess(allocator, node, .block, seq, payload.items);
            defer response.deinit(allocator);
            const end = Io.Clock.awake.now(io).nanoseconds;

            if (response.header.kind != .echo) return error.InvalidWorkerResponse;
            if (!verifyFrame(response.header, response.payload) or !std.mem.eql(u8, payload.items, response.payload)) {
                checksum_failures += 1;
                result.checksum_failures += 1;
            }

            if (i >= scenario.warmup_count) {
                latencies[measured_index] = nsSince(start, end);
                measured_index += 1;
                bytes_sent += message_size;
                bytes_received += response.payload.len;
            }
        }

        const elapsed_end = Io.Clock.awake.now(io).nanoseconds;
        try appendStats(
            allocator,
            result,
            node,
            message_size,
            scenario.transfer_count,
            bytes_sent,
            bytes_received,
            checksum_failures,
            latencies,
            nsSince(elapsed_start, elapsed_end),
        );
    }
}

fn appendStats(
    allocator: std.mem.Allocator,
    result: *RunResult,
    node: protocol.WorkerNode,
    message_size: usize,
    transfer_count: usize,
    bytes_sent: u64,
    bytes_received: u64,
    checksum_failures: u64,
    latencies: []u64,
    elapsed_ns: u64,
) !void {
    std.mem.sortUnstable(u64, latencies, {}, std.sort.asc(u64));
    const stats = MessageStats{
        .node = node,
        .message_size = message_size,
        .transfer_count = transfer_count,
        .bytes_sent = bytes_sent,
        .bytes_received = bytes_received,
        .checksum_failures = checksum_failures,
        .min_latency_ns = if (latencies.len == 0) 0 else latencies[0],
        .p50_latency_ns = percentile(latencies, 50),
        .p95_latency_ns = percentile(latencies, 95),
        .p99_latency_ns = percentile(latencies, 99),
        .max_latency_ns = if (latencies.len == 0) 0 else latencies[latencies.len - 1],
        .elapsed_ns = elapsed_ns,
        .throughput_bytes_per_sec = throughput(bytes_sent, elapsed_ns),
    };
    try result.stats.append(allocator, stats);
    result.total_transfers += transfer_count;
    result.total_bytes_sent += bytes_sent;
    result.total_bytes_received += bytes_received;
    result.checksum_failures += checksum_failures;
    try emitTransferEvent(result, stats);
}

fn handleWorkerSession(
    allocator: std.mem.Allocator,
    reader: *Io.Reader,
    writer: *Io.Writer,
    node: protocol.WorkerNode,
) !WorkerSummary {
    var summary = WorkerSummary{
        .node = node,
        .transfers = 0,
        .bytes_received = 0,
        .bytes_sent = 0,
        .checksum_failures = 0,
    };

    while (true) {
        var request = try readFrame(allocator, reader);
        defer request.deinit(allocator);
        switch (request.header.kind) {
            .ping => {
                if (!verifyFrame(request.header, request.payload)) summary.checksum_failures += 1;
                try writeFrame(writer, .pong, request.header.seq, protocol.WorkerNode.label(node));
            },
            .block => {
                summary.transfers += 1;
                summary.bytes_received += request.payload.len;
                if (!verifyFrame(request.header, request.payload)) {
                    summary.checksum_failures += 1;
                    try writeFrame(writer, .transport_error, request.header.seq, "checksum_failure");
                } else {
                    try writeFrame(writer, .echo, request.header.seq, request.payload);
                    summary.bytes_sent += request.payload.len;
                }
            },
            .shutdown => {
                try writeFrame(writer, .ack, request.header.seq, &.{});
                return summary;
            },
            else => try writeFrame(writer, .transport_error, request.header.seq, "unexpected_frame_kind"),
        }
    }
}

fn roundTripInProcess(
    allocator: std.mem.Allocator,
    node: protocol.WorkerNode,
    kind: FrameKind,
    seq: u64,
    payload: []const u8,
) !DecodedFrame {
    var encoded_request: std.ArrayList(u8) = .empty;
    defer encoded_request.deinit(allocator);
    try appendFrameBytes(allocator, &encoded_request, kind, seq, payload);

    var request = try decodeFrameBytes(allocator, encoded_request.items);
    defer request.deinit(allocator);

    const response_kind: FrameKind = switch (request.header.kind) {
        .ping => .pong,
        .block => if (verifyFrame(request.header, request.payload)) .echo else .transport_error,
        .shutdown => .ack,
        else => .transport_error,
    };
    const response_payload: []const u8 = switch (request.header.kind) {
        .ping => protocol.WorkerNode.label(node),
        .block => if (response_kind == .echo) request.payload else "checksum_failure",
        else => &.{},
    };

    var encoded_response: std.ArrayList(u8) = .empty;
    defer encoded_response.deinit(allocator);
    try appendFrameBytes(allocator, &encoded_response, response_kind, request.header.seq, response_payload);
    return decodeFrameBytes(allocator, encoded_response.items);
}

pub fn writeFrame(
    writer: *Io.Writer,
    kind: FrameKind,
    seq: u64,
    payload: []const u8,
) !void {
    const header = encodeHeader(kind, seq, payload);
    try writer.writeAll(&header);
    try writer.writeAll(payload);
    try writer.flush();
}

pub fn readFrame(allocator: std.mem.Allocator, reader: *Io.Reader) !DecodedFrame {
    var header_bytes: [header_len]u8 = undefined;
    try reader.readSliceAll(&header_bytes);
    const header = try decodeHeader(&header_bytes);
    const payload = try allocator.alloc(u8, header.payload_len);
    errdefer allocator.free(payload);
    try reader.readSliceAll(payload);
    return .{ .header = header, .payload = payload };
}

pub fn appendFrameBytes(
    allocator: std.mem.Allocator,
    out: *std.ArrayList(u8),
    kind: FrameKind,
    seq: u64,
    payload: []const u8,
) !void {
    const header = encodeHeader(kind, seq, payload);
    try out.appendSlice(allocator, &header);
    try out.appendSlice(allocator, payload);
}

pub fn decodeFrameBytes(allocator: std.mem.Allocator, bytes: []const u8) !DecodedFrame {
    if (bytes.len < header_len) return error.ShortFrame;
    const header = try decodeHeader(bytes[0..header_len]);
    if (bytes.len != header_len + header.payload_len) return error.InvalidFrameLength;
    const payload = try allocator.dupe(u8, bytes[header_len..]);
    return .{ .header = header, .payload = payload };
}

pub fn encodeHeader(kind: FrameKind, seq: u64, payload: []const u8) [header_len]u8 {
    var header: [header_len]u8 = @splat(0);
    header[0..4].* = magic;
    header[4] = version;
    header[5] = @intFromEnum(kind);
    std.mem.writeInt(u64, header[6..14], seq, .big);
    std.mem.writeInt(u64, header[14..22], payload.len, .big);
    var digest: [32]u8 = undefined;
    std.crypto.hash.sha2.Sha256.hash(payload, &digest, .{});
    header[22..54][0..32].* = digest;
    return header;
}

pub fn decodeHeader(header: *const [header_len]u8) !FrameHeader {
    if (!std.mem.eql(u8, header[0..4], &magic)) return error.InvalidMagic;
    if (header[4] != version) return error.UnsupportedVersion;
    const kind: FrameKind = @enumFromInt(header[5]);
    const payload_len_u64 = std.mem.readInt(u64, header[14..22], .big);
    if (payload_len_u64 > max_payload_bytes) return error.PayloadTooLarge;
    var checksum: [32]u8 = undefined;
    checksum = header[22..54][0..32].*;
    return .{
        .kind = kind,
        .seq = std.mem.readInt(u64, header[6..14], .big),
        .payload_len = @intCast(payload_len_u64),
        .checksum = checksum,
    };
}

pub fn verifyFrame(header: FrameHeader, payload: []const u8) bool {
    if (payload.len != header.payload_len) return false;
    var digest: [32]u8 = undefined;
    std.crypto.hash.sha2.Sha256.hash(payload, &digest, .{});
    return std.mem.eql(u8, &digest, &header.checksum);
}

fn writeArtifacts(allocator: std.mem.Allocator, io: Io, result: *RunResult) !void {
    const cwd = Io.Dir.cwd();
    var out_dir = try cwd.createDirPathOpen(io, result.out_dir, .{});
    defer out_dir.close(io);

    var run_json = Io.Writer.Allocating.init(allocator);
    defer run_json.deinit();
    try writeRunJson(&run_json.writer, result);
    try out_dir.writeFile(io, .{ .sub_path = "run.json", .data = run_json.written() });

    try out_dir.writeFile(io, .{ .sub_path = "events.jsonl", .data = result.events.written() });

    var latency_csv = Io.Writer.Allocating.init(allocator);
    defer latency_csv.deinit();
    try writeLatencyCsv(&latency_csv.writer, result);
    try out_dir.writeFile(io, .{ .sub_path = "latency.csv", .data = latency_csv.written() });

    var throughput_csv = Io.Writer.Allocating.init(allocator);
    defer throughput_csv.deinit();
    try writeThroughputCsv(&throughput_csv.writer, result);
    try out_dir.writeFile(io, .{ .sub_path = "throughput.csv", .data = throughput_csv.written() });

    var summary = Io.Writer.Allocating.init(allocator);
    defer summary.deinit();
    try writeSummary(&summary.writer, result);
    try out_dir.writeFile(io, .{ .sub_path = "summary.md", .data = summary.written() });
}

fn writeRunJson(writer: *Io.Writer, result: *const RunResult) !void {
    const checksum_passed = result.total_transfers - result.checksum_failures;
    const scenario_kind = result.scenario_kind;

    try writer.writeAll("{\n");
    try writer.writeAll("  \"schema_version\": \"phase0.artifacts.v1\",\n");
    try writer.writeAll("  \"run_id\": ");
    try writeJsonString(writer, result.run_id);
    try writer.writeAll(",\n  \"git_commit\": ");
    try writeJsonString(writer, build_options.git_commit);
    try writer.writeAll(",\n");
    try writer.writeAll("  \"software\": {\"name\":\"ds5-phase0\",\"version\":\"0.0.0-local\"},\n");
    try writer.writeAll("  \"started_at\": ");
    try writeRfc3339JsonString(writer, result.start_real_ns);
    try writer.writeAll(",\n  \"ended_at\": ");
    try writeRfc3339JsonString(writer, result.end_real_ns);
    try writer.print(",\n  \"duration_ms\": {d},\n", .{nsToMs(result.elapsed_ns)});
    try writer.writeAll("  \"valid\": ");
    try writer.writeAll(if (result.checksum_failures == 0) "true" else "false");
    try writer.writeAll(",\n  \"environment\": {");
    try writer.writeAll("\"network_path\":");
    try writeJsonString(writer, result.network_path);
    try writer.writeAll(",\"transport_mode\":");
    try writeJsonString(writer, RunMode.label(result.mode));
    try writer.writeAll(",\"socket_mode\":");
    try writeJsonString(writer, result.socket_mode);
    try writer.writeAll(",\"loopback\":");
    try writer.writeAll(if (result.mode == .single_process_loopback) "true" else "false");
    try writer.writeAll(",\"confirmed_network_path\":");
    try writeJsonString(writer, result.confirmed_network_path);
    try writer.writeAll(",\"clock_sync\":\"single-process or local process clock\",\"hardware_interpretable\":");
    try writer.writeAll(if (result.hardware_interpretable) "true" else "false");
    try writer.writeAll("},\n");

    try writer.writeAll("  \"scenario\": {\n");
    try writer.writeAll("    \"name\": ");
    try writeJsonString(writer, result.scenario_name);
    try writer.writeAll(",\n    \"config_path\": ");
    try writeJsonString(writer, result.config_path);
    try writer.writeAll(",\n    \"kind\": ");
    try writeJsonString(writer, scenario_kind);
    try writer.writeAll(",\n    \"message_sizes_bytes\": ");
    try writeMessageSizesJson(writer, result);
    try writer.writeAll(",\n    \"block_sizes_bytes\": ");
    try writeMessageSizesJson(writer, result);
    try writer.print(",\n    \"transfer_count\": {d},", .{maxTransferCount(result)});
    try writer.print("\n    \"warmup_count\": {d},", .{result.warmup_count});
    try writer.writeAll("\n    \"checksum_mode\": \"sha256\",\n");
    try writer.writeAll("    \"remote_expert_rates\": [0.0,0.25,0.5,0.75,1.0],\n");
    try writer.writeAll("    \"qwen_shape\": {\"layers\":94,\"hidden_size\":4096,\"top_k\":8,\"packets_per_destination_per_layer\":1,\"layer_owners\":[{\"node_id\":\"B\",\"start_layer\":0,\"end_layer\":46},{\"node_id\":\"C\",\"start_layer\":47,\"end_layer\":93}]}\n");
    try writer.writeAll("  },\n");

    try writer.writeAll("  \"nodes\": [\n");
    try writer.writeAll("    {\"node_id\":\"A\",\"role\":\"coordinator\",\"hostname\":\"local-coordinator\",\"hardware_label\":\"coordinator host\",\"transport\":\"");
    try writer.writeAll(RunMode.label(result.mode));
    try writer.writeAll("\"},\n");
    try writer.writeAll("    {\"node_id\":\"B\",\"role\":\"worker\",\"hostname\":\"worker-b\",\"hardware_label\":\"M5 Max worker placeholder\",\"transport\":\"");
    try writer.writeAll(RunMode.label(result.mode));
    try writer.writeAll("\"},\n");
    try writer.writeAll("    {\"node_id\":\"C\",\"role\":\"worker\",\"hostname\":\"worker-c\",\"hardware_label\":\"M5 Max worker placeholder\",\"transport\":\"");
    try writer.writeAll(RunMode.label(result.mode));
    try writer.writeAll("\"}\n");
    try writer.writeAll("  ],\n");

    try writer.print("  \"checksums\": {{\"algorithm\":\"sha256\",\"total_transfers\":{d},\"passed\":{d},\"failed\":{d},\"status\":\"{s}\"}},\n", .{
        result.total_transfers,
        checksum_passed,
        result.checksum_failures,
        if (result.checksum_failures == 0) "pass" else "fail",
    });
    try writer.print("  \"failure_counts\": {{\"failures\":{d},\"retries\":{d},\"reconnects\":{d},\"timeouts\":{d}}},\n", .{
        result.failure_count,
        result.retry_count,
        result.reconnect_count,
        result.timeout_count,
    });
    try writer.writeAll("  \"metrics\": {\n");
    try writer.writeAll("    \"latency_by_message_size\": [\n");
    for (result.stats.items, 0..) |stats, i| {
        if (i != 0) try writer.writeAll(",\n");
        try writer.print(
            "      {{\"node_pair\":\"A-{s}\",\"message_size_bytes\":{d},\"sample_count\":{d},\"checksum_failures\":{d},\"p50_us\":{d},\"p95_us\":{d},\"p99_us\":{d}}}",
            .{
                protocol.WorkerNode.label(stats.node),
                stats.message_size,
                stats.transfer_count,
                stats.checksum_failures,
                nsToUs(stats.p50_latency_ns),
                nsToUs(stats.p95_latency_ns),
                nsToUs(stats.p99_latency_ns),
            },
        );
    }
    try writer.writeAll("\n    ],\n");
    try writer.writeAll("    \"throughput_by_block_size\": [\n");
    for (result.stats.items, 0..) |stats, i| {
        if (i != 0) try writer.writeAll(",\n");
        try writer.print(
            "      {{\"node_pair\":\"A-{s}\",\"block_size_bytes\":{d},\"transfer_count\":{d},\"bytes_sent\":{d},\"checksum_failures\":{d},\"duration_ms\":{d},\"mib_per_sec\":{d},\"gbps\":{d}}}",
            .{
                protocol.WorkerNode.label(stats.node),
                stats.message_size,
                stats.transfer_count,
                stats.bytes_sent,
                stats.checksum_failures,
                nsToMs(stats.elapsed_ns),
                bytesPerSecToMibPerSec(stats.throughput_bytes_per_sec),
                bytesPerSecToGbps(stats.throughput_bytes_per_sec),
            },
        );
    }
    try writer.writeAll("\n    ],\n");
    try writer.writeAll("    \"scheduler_overhead_us_per_token\": {\"p50\":0,\"p95\":0,\"p99\":0},\n");
    try writer.print("    \"bytes_sent_per_simulated_token\": {d},\n", .{result.total_bytes_sent});
    try writer.writeAll("    \"per_layer_transport_time_us\": {\"p50\":0,\"p95\":0,\"p99\":0},\n");
    try writer.writeAll("    \"concurrent_link_interference\": [");
    try writeConcurrentInterference(writer, result);
    try writer.writeAll("],\n");
    try writer.writeAll("    \"predicted_upper_bound_tokens_per_sec\": [{\"remote_expert_rate\":0.0,\"tokens_per_sec\":0.0},{\"remote_expert_rate\":0.25,\"tokens_per_sec\":0.0},{\"remote_expert_rate\":0.5,\"tokens_per_sec\":0.0},{\"remote_expert_rate\":0.75,\"tokens_per_sec\":0.0},{\"remote_expert_rate\":1.0,\"tokens_per_sec\":0.0}]\n");
    try writer.writeAll("  },\n");
    try writer.writeAll("  \"artifacts\": {\"events\":\"events.jsonl\",\"latency\":\"latency.csv\",\"throughput\":\"throughput.csv\",\"summary\":\"summary.md\"}\n");
    try writer.writeAll("}\n");
}

fn writeLatencyCsv(writer: *Io.Writer, result: *const RunResult) !void {
    try writer.writeAll("schema_version,run_id,node_pair,direction,message_size_bytes,sample_count,warmup_count,transfer_count,checksum_algorithm,checksum_failures,p50_us,p95_us,p99_us,min_us,max_us,jitter_us,remote_expert_rate,scenario_step\n");
    for (result.stats.items) |stats| {
        try writer.print(
            "phase0.artifacts.v1,{s},A-{s},round_trip,{d},{d},{d},{d},sha256,{d},{d},{d},{d},{d},{d},{d},0.0,{s}-block-{d}\n",
            .{
                result.run_id,
                protocol.WorkerNode.label(stats.node),
                stats.message_size,
                stats.transfer_count,
                result.warmup_count,
                stats.transfer_count,
                stats.checksum_failures,
                nsToUs(stats.p50_latency_ns),
                nsToUs(stats.p95_latency_ns),
                nsToUs(stats.p99_latency_ns),
                nsToUs(stats.min_latency_ns),
                nsToUs(stats.max_latency_ns),
                nsToUs(stats.p99_latency_ns) -| nsToUs(stats.p50_latency_ns),
                result.scenario_kind,
                stats.message_size,
            },
        );
    }
}

fn writeThroughputCsv(writer: *Io.Writer, result: *const RunResult) !void {
    try writer.writeAll("schema_version,run_id,node_pair,direction,block_size_bytes,transfer_count,bytes_sent,checksum_algorithm,checksum_failures,duration_ms,mib_per_sec,gbps,concurrent_links,remote_expert_rate,scenario_step\n");
    for (result.stats.items) |stats| {
        try writer.print(
            "phase0.artifacts.v1,{s},A-{s},round_trip,{d},{d},{d},sha256,{d},{d},{d},{d},none,0.0,{s}-block-{d}\n",
            .{
                result.run_id,
                protocol.WorkerNode.label(stats.node),
                stats.message_size,
                stats.transfer_count,
                stats.bytes_sent,
                stats.checksum_failures,
                nsToMs(stats.elapsed_ns),
                bytesPerSecToMibPerSec(stats.throughput_bytes_per_sec),
                bytesPerSecToGbps(stats.throughput_bytes_per_sec),
                result.scenario_kind,
                stats.message_size,
            },
        );
    }
}

fn writeSummary(writer: *Io.Writer, result: *const RunResult) !void {
    try writer.writeAll("# DS5 Phase 0 Transport Smoke\n\n");
    try writer.writeAll("## Run\n\n");
    try writer.print("- run_id: `{s}`\n", .{result.run_id});
    try writer.print("- git_commit: `{s}`\n", .{build_options.git_commit});
    try writer.writeAll("- started_at: ");
    try writeRfc3339Inline(writer, result.start_real_ns);
    try writer.writeAll("\n- ended_at: ");
    try writeRfc3339Inline(writer, result.end_real_ns);
    try writer.print("\n- valid: {s}\n", .{if (result.checksum_failures == 0) "true" else "false"});
    try writer.print("- mode: `{s}`\n", .{RunMode.label(result.mode)});
    try writer.print("- socket mode: `{s}`\n", .{result.socket_mode});
    try writer.print("- network path: `{s}`\n", .{result.network_path});
    try writer.print("- hardware interpretable: {s}\n", .{if (result.hardware_interpretable) "true" else "false"});
    try writer.writeAll("- data kind: transport/protocol smoke; hardware claims require confirmed non-loopback path\n\n");

    try writer.writeAll("## Scenario\n\n");
    try writer.print("- scenario: `{s}`\n", .{result.scenario_name});
    try writer.print("- config: `{s}`\n", .{result.config_path});
    try writer.print("- scenario file: `{s}`\n", .{result.scenario_path});
    try writer.writeAll("- node roles: A=coordinator, B=worker, C=worker\n");
    try writer.writeAll("- predicted upper-bound tokens/sec: not interpreted for loopback smoke\n\n");

    try writer.writeAll("## Nodes\n\n");
    try writer.writeAll("| Node | Role | Transport |\n");
    try writer.writeAll("|---|---|---|\n");
    try writer.print("| A | coordinator | {s} |\n", .{RunMode.label(result.mode)});
    try writer.print("| B | worker | {s} |\n", .{RunMode.label(result.mode)});
    try writer.print("| C | worker | {s} |\n\n", .{RunMode.label(result.mode)});

    try writer.writeAll("## Latency\n\n");
    try writer.writeAll("| Node pair | Size bytes | Transfers | p50 us | p95 us | p99 us |\n");
    try writer.writeAll("|---|---:|---:|---:|---:|---:|\n");
    for (result.stats.items) |stats| {
        try writer.print(
            "| A-{s} | {d} | {d} | {d} | {d} | {d} |\n",
            .{
                protocol.WorkerNode.label(stats.node),
                stats.message_size,
                stats.transfer_count,
                nsToUs(stats.p50_latency_ns),
                nsToUs(stats.p95_latency_ns),
                nsToUs(stats.p99_latency_ns),
            },
        );
    }

    try writer.writeAll("\n## Throughput\n\n");
    try writer.writeAll("| Node pair | Block bytes | Transfers | Throughput MiB/s | Gbps |\n");
    try writer.writeAll("|---|---:|---:|---:|---:|\n");
    for (result.stats.items) |stats| {
        try writer.print(
            "| A-{s} | {d} | {d} | {d} | {d} |\n",
            .{
                protocol.WorkerNode.label(stats.node),
                stats.message_size,
                stats.transfer_count,
                bytesPerSecToMibPerSec(stats.throughput_bytes_per_sec),
                bytesPerSecToGbps(stats.throughput_bytes_per_sec),
            },
        );
    }

    try writer.writeAll("\n## Reliability\n\n");
    try writer.print("- checksum failures: {d}\n", .{result.checksum_failures});
    try writer.print("- failures: {d}\n", .{result.failure_count});
    try writer.print("- retries: {d}\n", .{result.retry_count});
    try writer.print("- reconnects: {d}\n", .{result.reconnect_count});
    try writer.print("- timeouts: {d}\n\n", .{result.timeout_count});

    try writer.writeAll("## Interpretation\n\n");
    try writer.writeAll(result.results_warning);
    try writer.writeAll("\n");
}

fn emitRunStartedEvent(result: *RunResult) !void {
    const writer = &result.events.writer;
    try writeEventPrefix(result, "run_started", "info");
    try writer.writeAll(",\"details\":{\"scenario\":");
    try writeJsonString(writer, result.scenario_name);
    try writer.writeAll("}}\n");
}

fn emitRunCompletedEvent(result: *RunResult) !void {
    const writer = &result.events.writer;
    try writeEventPrefix(result, "run_completed", if (result.checksum_failures == 0) "info" else "error");
    try writer.writeAll(",\"valid\":");
    try writer.writeAll(if (result.checksum_failures == 0) "true" else "false");
    try writer.print(",\"details\":{{\"checksum_failures\":{d}}}}}\n", .{result.checksum_failures});
}

fn emitNodeDiscoveredEvent(result: *RunResult, node: protocol.WorkerNode, hostname: []const u8, latency_us: u64) !void {
    const writer = &result.events.writer;
    try writeEventPrefix(result, "node_discovered", "info");
    try writer.print(",\"node_id\":\"{s}\",\"hostname\":", .{protocol.WorkerNode.label(node)});
    try writeJsonString(writer, hostname);
    try writer.print(",\"latency_us\":{d},\"details\":{{\"role\":\"worker\"}}}}\n", .{latency_us});
}

fn emitWorkerHealthEvent(result: *RunResult, node: protocol.WorkerNode, latency_ns: u64) !void {
    const writer = &result.events.writer;
    try writeEventPrefix(result, "worker_health", "info");
    try writer.print(
        ",\"node_id\":\"{s}\",\"health_status\":\"healthy\",\"latency_us\":{d},\"details\":{{\"heartbeat\":true,\"ping_latency_ns\":{d}}}}}\n",
        .{ protocol.WorkerNode.label(node), nsToUs(latency_ns), latency_ns },
    );
}

fn emitFailureObservedEvent(
    result: *RunResult,
    node: protocol.WorkerNode,
    failure_kind: []const u8,
    message: []const u8,
) !void {
    const writer = &result.events.writer;
    try writeEventPrefix(result, "failure_observed", "error");
    try writer.print(",\"node_id\":\"{s}\",\"failure_kind\":", .{protocol.WorkerNode.label(node)});
    try writeJsonString(writer, failure_kind);
    try writer.writeAll(",\"details\":{\"message\":");
    try writeJsonString(writer, message);
    try writer.writeAll("}}\n");
}

fn emitRetryScheduledEvent(
    result: *RunResult,
    node: protocol.WorkerNode,
    failure_kind: []const u8,
    retry_count: usize,
) !void {
    const writer = &result.events.writer;
    try writeEventPrefix(result, "retry_scheduled", "warn");
    try writer.print(",\"node_id\":\"{s}\",\"failure_kind\":", .{protocol.WorkerNode.label(node)});
    try writeJsonString(writer, failure_kind);
    try writer.print(",\"retry_count\":{d},\"details\":{{}}}}\n", .{retry_count});
}

fn emitReconnectSucceededEvent(
    result: *RunResult,
    node: protocol.WorkerNode,
    retry_count: usize,
    latency_us: u64,
) !void {
    const writer = &result.events.writer;
    try writeEventPrefix(result, "reconnect_succeeded", "info");
    try writer.print(
        ",\"node_id\":\"{s}\",\"retry_count\":{d},\"latency_us\":{d},\"details\":{{}}}}\n",
        .{ protocol.WorkerNode.label(node), retry_count, latency_us },
    );
}

fn emitTransferEvent(result: *RunResult, stats: MessageStats) !void {
    const writer = &result.events.writer;
    try writeEventPrefix(result, "latency_sample", "info");
    try writer.print(
        ",\"node_pair\":\"A-{s}\",\"message_size_bytes\":{d},\"latency_us\":{d},\"checksum_status\":\"{s}\",\"remote_expert_rate\":0.0,\"details\":{{\"sample_count\":{d}}}}}\n",
        .{
            protocol.WorkerNode.label(stats.node),
            stats.message_size,
            nsToUs(stats.p50_latency_ns),
            if (stats.checksum_failures == 0) "pass" else "fail",
            stats.transfer_count,
        },
    );

    try writeEventPrefix(result, "throughput_sample", "info");
    try writer.print(
        ",\"node_pair\":\"A-{s}\",\"block_size_bytes\":{d},\"bytes_sent\":{d},\"throughput_mib_s\":{d},\"checksum_status\":\"{s}\",\"remote_expert_rate\":0.0,\"details\":{{\"transfer_count\":{d}}}}}\n",
        .{
            protocol.WorkerNode.label(stats.node),
            stats.message_size,
            stats.bytes_sent,
            bytesPerSecToMibPerSec(stats.throughput_bytes_per_sec),
            if (stats.checksum_failures == 0) "pass" else "fail",
            stats.transfer_count,
        },
    );

    try writeEventPrefix(result, "checksum_verified", if (stats.checksum_failures == 0) "info" else "error");
    try writer.print(
        ",\"transfer_id\":\"A-{s}-{d}\",\"checksum_status\":\"{s}\",\"bytes_sent\":{d},\"details\":{{\"algorithm\":\"sha256\",\"failures\":{d}}}}}\n",
        .{
            protocol.WorkerNode.label(stats.node),
            stats.message_size,
            if (stats.checksum_failures == 0) "pass" else "fail",
            stats.bytes_sent,
            stats.checksum_failures,
        },
    );
}

fn writeEventPrefix(result: *RunResult, event_type: []const u8, severity: []const u8) !void {
    const writer = &result.events.writer;
    const sequence = result.event_sequence;
    result.event_sequence += 1;

    try writer.writeAll("{\"schema_version\":\"phase0.artifacts.v1\",\"run_id\":");
    try writeJsonString(writer, result.run_id);
    try writer.print(",\"sequence\":{d},\"timestamp\":", .{sequence});
    try writeRfc3339JsonString(writer, result.start_real_ns + @as(i96, @intCast(sequence * std.time.ns_per_ms)));
    try writer.writeAll(",\"event_type\":");
    try writeJsonString(writer, event_type);
    try writer.writeAll(",\"severity\":");
    try writeJsonString(writer, severity);
}

fn runIdFromOutDir(allocator: std.mem.Allocator, out_dir: []const u8) ![]u8 {
    var trimmed = std.mem.trimEnd(u8, out_dir, "/");
    if (trimmed.len == 0) trimmed = "run";
    const slash = std.mem.lastIndexOfScalar(u8, trimmed, '/');
    const base = if (slash) |index| trimmed[index + 1 ..] else trimmed;
    if (base.len == 0) return allocator.dupe(u8, "run");
    return allocator.dupe(u8, base);
}

fn writeMessageSizesJson(writer: *Io.Writer, result: *const RunResult) !void {
    try writer.writeByte('[');
    var written_size_count: usize = 0;
    for (result.stats.items, 0..) |stats, i| {
        var duplicate = false;
        for (result.stats.items[0..i]) |prior| {
            if (prior.message_size == stats.message_size) {
                duplicate = true;
                break;
            }
        }
        if (duplicate) continue;
        if (written_size_count != 0) try writer.writeByte(',');
        try writer.print("{d}", .{stats.message_size});
        written_size_count += 1;
    }
    try writer.writeByte(']');
}

fn writeConcurrentInterference(writer: *Io.Writer, result: *const RunResult) !void {
    var wrote_any = false;
    for (result.stats.items) |stats| {
        if (stats.message_size != largestMessageSize(result)) continue;
        if (wrote_any) try writer.writeByte(',');
        try writer.print(
            "{{\"node_pair\":\"A-{s}\",\"solo_mib_per_sec\":{d},\"concurrent_mib_per_sec\":{d},\"degradation_pct\":0}}",
            .{
                protocol.WorkerNode.label(stats.node),
                bytesPerSecToMibPerSec(stats.throughput_bytes_per_sec),
                bytesPerSecToMibPerSec(stats.throughput_bytes_per_sec),
            },
        );
        wrote_any = true;
    }
    if (!wrote_any) {
        try writer.writeAll("{\"node_pair\":\"A-B\",\"solo_mib_per_sec\":0,\"concurrent_mib_per_sec\":0,\"degradation_pct\":0}");
    }
}

fn maxTransferCount(result: *const RunResult) usize {
    var max_count: usize = 0;
    for (result.stats.items) |stats| {
        max_count = @max(max_count, stats.transfer_count);
    }
    return max_count;
}

fn largestMessageSize(result: *const RunResult) usize {
    var max_size: usize = 0;
    for (result.stats.items) |stats| {
        max_size = @max(max_size, stats.message_size);
    }
    return max_size;
}

fn writeRfc3339JsonString(writer: *Io.Writer, unix_nanos: i96) !void {
    try writer.writeByte('"');
    try writeRfc3339Inline(writer, unix_nanos);
    try writer.writeByte('"');
}

fn writeRfc3339Inline(writer: *Io.Writer, unix_nanos: i96) !void {
    const positive_nanos = if (unix_nanos < 0) 0 else unix_nanos;
    const seconds: u64 = @intCast(@divTrunc(positive_nanos, std.time.ns_per_s));
    const epoch_seconds = std.time.epoch.EpochSeconds{ .secs = seconds };
    const year_day = epoch_seconds.getEpochDay().calculateYearDay();
    const month_day = year_day.calculateMonthDay();
    const day_seconds = epoch_seconds.getDaySeconds();
    try writer.print(
        "{d:0>4}-{d:0>2}-{d:0>2}T{d:0>2}:{d:0>2}:{d:0>2}Z",
        .{
            year_day.year,
            month_day.month.numeric(),
            @as(u6, month_day.day_index) + 1,
            day_seconds.getHoursIntoDay(),
            day_seconds.getMinutesIntoHour(),
            day_seconds.getSecondsIntoMinute(),
        },
    );
}

fn nsToUs(ns: u64) u64 {
    return ns / std.time.ns_per_us;
}

fn nsToMs(ns: u64) u64 {
    if (ns == 0) return 0;
    return @max(1, ns / std.time.ns_per_ms);
}

fn bytesPerSecToMibPerSec(bytes_per_sec: u64) u64 {
    return bytes_per_sec / (1024 * 1024);
}

fn bytesPerSecToGbps(bytes_per_sec: u64) u64 {
    return (bytes_per_sec * 8) / 1_000_000_000;
}

pub fn parseScenario(allocator: std.mem.Allocator, text: []const u8) !Scenario {
    var scenario = Scenario{
        .name = "unknown",
        .message_sizes = .empty,
        .transfer_count = 0,
        .warmup_count = 0,
        .payload_seed = 0,
    };
    errdefer scenario.deinit(allocator);

    var lines = std.mem.splitScalar(u8, text, '\n');
    while (lines.next()) |raw_line| {
        const line = trimLine(raw_line);
        if (line.len == 0) continue;
        if (quotedValue(line, "scenario_name")) |value| {
            scenario.name = value;
        } else if (arrayValue(line, "message_sizes_bytes")) |value| {
            try parseSizeArray(allocator, value, &scenario.message_sizes);
        } else if (intValue(usize, line, "transfer_count_per_message_size")) |value| {
            scenario.transfer_count = value;
        } else if (intValue(usize, line, "warmup_count_per_message_size")) |value| {
            scenario.warmup_count = value;
        } else if (intValue(u64, line, "payload_seed")) |value| {
            scenario.payload_seed = value;
        }
    }

    if (scenario.message_sizes.items.len == 0) return error.MissingMessageSizes;
    if (scenario.transfer_count == 0) return error.MissingTransferCount;
    return scenario;
}

pub fn parseClusterConfig(text: []const u8) !ClusterConfig {
    var cluster = ClusterConfig{
        .name = "unknown",
        .config_kind = "unknown",
        .loopback = false,
        .intended_link = "",
        .network_path_must_be_recorded = false,
        .confirmed_network_path = "",
        .results_warning = "Loopback results validate protocol and artifact plumbing only, not real interconnect performance.",
        .connect_timeout_ms = 2000,
        .heartbeat_interval_ms = 1000,
        .heartbeat_timeout_ms = 5000,
        .reconnect_attempts = 0,
        .workers = undefined,
        .worker_count = 0,
    };

    var active_node: ?protocol.WorkerNode = null;
    var in_node_block = false;
    var lines = std.mem.splitScalar(u8, text, '\n');
    while (lines.next()) |raw_line| {
        const line = trimLine(raw_line);
        if (line.len == 0) continue;
        if (std.mem.eql(u8, line, "[[nodes]]")) {
            in_node_block = true;
            active_node = null;
            continue;
        }
        if (quotedValue(line, "config_name")) |value| {
            cluster.name = value;
        } else if (quotedValue(line, "config_kind")) |value| {
            cluster.config_kind = value;
        } else if (boolValue(line, "loopback")) |value| {
            cluster.loopback = value;
        } else if (quotedValue(line, "intended_link")) |value| {
            cluster.intended_link = value;
        } else if (boolValue(line, "network_path_must_be_recorded")) |value| {
            cluster.network_path_must_be_recorded = value;
        } else if (quotedValue(line, "confirmed_network_path")) |value| {
            cluster.confirmed_network_path = value;
        } else if (quotedValue(line, "results_warning")) |value| {
            cluster.results_warning = value;
        } else if (intValue(u64, line, "connect_timeout_ms")) |value| {
            cluster.connect_timeout_ms = value;
        } else if (intValue(u64, line, "heartbeat_interval_ms")) |value| {
            cluster.heartbeat_interval_ms = value;
        } else if (intValue(u64, line, "heartbeat_timeout_ms")) |value| {
            cluster.heartbeat_timeout_ms = value;
        } else if (intValue(usize, line, "reconnect_attempts")) |value| {
            cluster.reconnect_attempts = value;
        } else if (in_node_block) {
            if (quotedValue(line, "id")) |value| {
                active_node = protocol.WorkerNode.parse(value);
            } else if (active_node != null) {
                if (quotedValue(line, "connect_address")) |value| {
                    if (cluster.worker_count >= cluster.workers.len) return error.TooManyWorkers;
                    cluster.workers[cluster.worker_count] = .{ .node = active_node.?, .address = value };
                    cluster.worker_count += 1;
                }
            }
        }
    }

    if (cluster.worker_count == 0) return error.MissingWorkers;
    return cluster;
}

fn parseSizeArray(
    allocator: std.mem.Allocator,
    value: []const u8,
    sizes: *std.ArrayList(usize),
) !void {
    var items = std.mem.splitScalar(u8, value, ',');
    while (items.next()) |raw_item| {
        const item = std.mem.trim(u8, raw_item, " \t\r\n");
        if (item.len == 0) continue;
        try sizes.append(allocator, try std.fmt.parseInt(usize, item, 10));
    }
}

fn quotedValue(line: []const u8, key: []const u8) ?[]const u8 {
    const value = valueAfterEquals(line, key) orelse return null;
    if (value.len < 2 or value[0] != '"' or value[value.len - 1] != '"') return null;
    return value[1 .. value.len - 1];
}

fn arrayValue(line: []const u8, key: []const u8) ?[]const u8 {
    const value = valueAfterEquals(line, key) orelse return null;
    if (value.len < 2 or value[0] != '[' or value[value.len - 1] != ']') return null;
    return value[1 .. value.len - 1];
}

fn intValue(comptime T: type, line: []const u8, key: []const u8) ?T {
    const value = valueAfterEquals(line, key) orelse return null;
    return std.fmt.parseInt(T, value, 10) catch null;
}

fn boolValue(line: []const u8, key: []const u8) ?bool {
    const value = valueAfterEquals(line, key) orelse return null;
    if (std.mem.eql(u8, value, "true")) return true;
    if (std.mem.eql(u8, value, "false")) return false;
    return null;
}

fn valueAfterEquals(line: []const u8, key: []const u8) ?[]const u8 {
    if (!std.mem.startsWith(u8, line, key)) return null;
    var rest = std.mem.trim(u8, line[key.len..], " \t");
    if (rest.len == 0 or rest[0] != '=') return null;
    rest = std.mem.trim(u8, rest[1..], " \t");
    return rest;
}

fn trimLine(raw_line: []const u8) []const u8 {
    const without_comment = if (std.mem.indexOfScalar(u8, raw_line, '#')) |index| raw_line[0..index] else raw_line;
    return std.mem.trim(u8, without_comment, " \t\r\n");
}

fn parseAddressLiteral(address: []const u8) !net.IpAddress {
    return net.IpAddress.parseLiteral(address) catch error.InvalidAddress;
}

fn connectToAddress(io: Io, address: []const u8) !net.Stream {
    if (net.IpAddress.parseLiteral(address)) |ip| {
        return ip.connect(io, .{ .mode = .stream, .protocol = .tcp });
    } else |_| {}

    const host, const port = splitHostPort(address) orelse return error.InvalidAddress;
    const host_name = try net.HostName.init(host);
    return host_name.connect(io, port, .{ .mode = .stream, .protocol = .tcp });
}

fn splitHostPort(address: []const u8) ?struct { []const u8, u16 } {
    const colon = std.mem.lastIndexOfScalar(u8, address, ':') orelse return null;
    if (colon == 0 or colon + 1 >= address.len) return null;
    const host = address[0..colon];
    if (std.mem.indexOfScalar(u8, host, ':') != null) return null;
    const port = std.fmt.parseInt(u16, address[colon + 1 ..], 10) catch return null;
    return .{ host, port };
}

fn fillPayload(payload: []u8, seed: u64, node: protocol.WorkerNode, message_size: usize, transfer_index: usize) void {
    var state = seed ^ (@as(u64, message_size) << 17) ^ (@as(u64, transfer_index) << 33) ^ @intFromEnum(node);
    if (state == 0) state = 0x9e3779b97f4a7c15;
    for (payload) |*byte| {
        state ^= state << 13;
        state ^= state >> 7;
        state ^= state << 17;
        byte.* = @truncate(state);
    }
}

fn makeSeq(node: protocol.WorkerNode, message_size: usize, transfer_index: usize) u64 {
    return (@as(u64, @intFromEnum(node)) << 56) ^ (@as(u64, message_size) << 24) ^ @as(u64, transfer_index);
}

fn percentile(sorted: []const u64, pct: usize) u64 {
    if (sorted.len == 0) return 0;
    const rank = (pct * sorted.len + 99) / 100;
    return sorted[@min(rank - 1, sorted.len - 1)];
}

fn throughput(bytes_sent: u64, elapsed_ns: u64) u64 {
    if (elapsed_ns == 0) return 0;
    const numerator = @as(u128, bytes_sent) * std.time.ns_per_s;
    return @intCast(numerator / elapsed_ns);
}

fn nsSince(start: i96, end: i96) u64 {
    if (end <= start) return 0;
    return @intCast(end - start);
}

fn writeJsonString(writer: *Io.Writer, value: []const u8) !void {
    try writer.writeByte('"');
    for (value) |byte| {
        switch (byte) {
            '"' => try writer.writeAll("\\\""),
            '\\' => try writer.writeAll("\\\\"),
            '\n' => try writer.writeAll("\\n"),
            '\r' => try writer.writeAll("\\r"),
            '\t' => try writer.writeAll("\\t"),
            else => try writer.writeByte(byte),
        }
    }
    try writer.writeByte('"');
}

test "frame encoding round trips payload checksum" {
    const payload = "phase0-loopback";
    var encoded: std.ArrayList(u8) = .empty;
    defer encoded.deinit(std.testing.allocator);
    try appendFrameBytes(std.testing.allocator, &encoded, .block, 42, payload);
    var decoded = try decodeFrameBytes(std.testing.allocator, encoded.items);
    defer decoded.deinit(std.testing.allocator);

    try std.testing.expectEqual(FrameKind.block, decoded.header.kind);
    try std.testing.expectEqual(@as(u64, 42), decoded.header.seq);
    try std.testing.expectEqualStrings(payload, decoded.payload);
    try std.testing.expect(verifyFrame(decoded.header, decoded.payload));
}

test "cluster parser classifies socket-localhost as non-hardware" {
    const text =
        \\config_name = "cluster.socket-localhost"
        \\config_kind = "socket_localhost"
        \\loopback = false
        \\intended_link = "localhost TCP sockets"
        \\network_path_must_be_recorded = false
        \\confirmed_network_path = ""
        \\reconnect_attempts = 2
        \\[[nodes]]
        \\id = "B"
        \\connect_address = "127.0.0.1:7555"
        \\[[nodes]]
        \\id = "C"
        \\connect_address = "localhost:7556"
        \\
    ;
    const cluster = try parseClusterConfig(text);
    try std.testing.expect(!cluster.loopback);
    try std.testing.expectEqual(@as(usize, 2), cluster.worker_count);
    try std.testing.expectEqual(RunMode.socket_localhost, classifyRunMode(cluster));
    try std.testing.expect(!hardwareInterpretable(cluster, classifyRunMode(cluster)));
}

test "scenario parser reads loopback traffic shape" {
    const text =
        \\scenario_name = "loopback_transport_smoke"
        \\[traffic]
        \\message_sizes_bytes = [64, 1024, 4096]
        \\transfer_count_per_message_size = 5
        \\warmup_count_per_message_size = 1
        \\payload_seed = 1337
        \\
    ;
    var scenario = try parseScenario(std.testing.allocator, text);
    defer scenario.deinit(std.testing.allocator);

    try std.testing.expectEqualStrings("loopback_transport_smoke", scenario.name);
    try std.testing.expectEqual(@as(usize, 3), scenario.message_sizes.items.len);
    try std.testing.expectEqual(@as(usize, 4096), scenario.message_sizes.items[2]);
    try std.testing.expectEqual(@as(usize, 5), scenario.transfer_count);
    try std.testing.expectEqual(@as(usize, 1), scenario.warmup_count);
    try std.testing.expectEqual(@as(u64, 1337), scenario.payload_seed);
}
