const std = @import("std");
const Io = std.Io;

const common = @import("ds5_common");
const transport = @import("ds5_transport");

pub fn main(init: std.process.Init) !void {
    const arena = init.arena.allocator();
    const raw_args = try init.minimal.args.toSlice(arena);
    const parsed = common.args.parseWorker(raw_args[1..]);

    switch (parsed) {
        .help => {
            var buffer: [4096]u8 = undefined;
            var file_writer: Io.File.Writer = .init(.stdout(), init.io, &buffer);
            const writer = &file_writer.interface;
            try common.args.writeWorkerUsage(writer);
            try writer.flush();
        },
        .run => |options| {
            var buffer: [2048]u8 = undefined;
            var file_writer: Io.File.Writer = .init(.stdout(), init.io, &buffer);
            const writer = &file_writer.interface;
            try writer.print(
                "ds5 worker phase0 transport listener\nmodel={s}\nnode={s}\nlisten={s}\n",
                .{
                    common.protocol.target_model,
                    common.protocol.WorkerNode.label(options.node),
                    options.listen,
                },
            );
            try writer.flush();

            const heap_allocator = std.heap.smp_allocator;
            const summary = transport.runWorker(
                heap_allocator,
                init.io,
                options.node,
                options.listen,
            ) catch |err| {
                var err_buffer: [4096]u8 = undefined;
                var err_file_writer: Io.File.Writer = .init(.stderr(), init.io, &err_buffer);
                const err_writer = &err_file_writer.interface;
                try err_writer.print("error: worker transport failed: {s}\n", .{@errorName(err)});
                try err_writer.flush();
                std.process.exit(1);
            };

            try writer.print(
                "worker session complete\nnode={s}\ntransfers={d}\nbytes_received={d}\nbytes_sent={d}\nchecksum_failures={d}\n",
                .{
                    common.protocol.WorkerNode.label(summary.node),
                    summary.transfers,
                    summary.bytes_received,
                    summary.bytes_sent,
                    summary.checksum_failures,
                },
            );
            try writer.flush();
        },
        .invalid => |invalid| {
            var buffer: [4096]u8 = undefined;
            var file_writer: Io.File.Writer = .init(.stderr(), init.io, &buffer);
            const writer = &file_writer.interface;
            try common.args.writeInvalid(writer, invalid);
            try common.args.writeWorkerUsage(writer);
            try writer.flush();
            std.process.exit(2);
        },
    }
}

test "worker main imports DS5 common parser" {
    const argv = [_][]const u8{"--help"};
    const parsed = common.args.parseWorker(argv[0..]);
    try std.testing.expect(parsed == .help);
}
