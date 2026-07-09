const std = @import("std");
const Io = std.Io;

const common = @import("ds5_common");
const transport = @import("ds5_transport");

pub fn main(init: std.process.Init) !void {
    const arena = init.arena.allocator();
    const raw_args = try init.minimal.args.toSlice(arena);
    const parsed = common.args.parseCoordinator(raw_args[1..]);

    switch (parsed) {
        .help => {
            var buffer: [4096]u8 = undefined;
            var file_writer: Io.File.Writer = .init(.stdout(), init.io, &buffer);
            const writer = &file_writer.interface;
            try common.args.writeCoordinatorUsage(writer);
            try writer.flush();
        },
        .run => |options| {
            const heap_allocator = std.heap.smp_allocator;
            var result = transport.runCoordinator(heap_allocator, init.io, options) catch |err| {
                var err_buffer: [4096]u8 = undefined;
                var err_file_writer: Io.File.Writer = .init(.stderr(), init.io, &err_buffer);
                const err_writer = &err_file_writer.interface;
                try err_writer.print("error: transport smoke failed: {s}\n", .{@errorName(err)});
                try err_writer.flush();
                std.process.exit(1);
            };
            defer result.deinit(heap_allocator);

            var buffer: [2048]u8 = undefined;
            var file_writer: Io.File.Writer = .init(.stdout(), init.io, &buffer);
            const writer = &file_writer.interface;
            try writer.print(
                "ds5 coordinator phase0 transport smoke\nmodel={s}\nmode={s}\nconfig={s}\nscenario={s}\nout={s}\ntransfers={d}\nbytes_sent={d}\nchecksum_failures={d}\n",
                .{
                    common.protocol.target_model,
                    transport.RunMode.label(result.mode),
                    options.config,
                    options.scenario,
                    options.out,
                    result.total_transfers,
                    result.total_bytes_sent,
                    result.checksum_failures,
                },
            );
            try writer.flush();
        },
        .invalid => |invalid| {
            var buffer: [4096]u8 = undefined;
            var file_writer: Io.File.Writer = .init(.stderr(), init.io, &buffer);
            const writer = &file_writer.interface;
            try common.args.writeInvalid(writer, invalid);
            try common.args.writeCoordinatorUsage(writer);
            try writer.flush();
            std.process.exit(2);
        },
    }
}

test "coordinator main imports DS5 common parser" {
    const argv = [_][]const u8{"--help"};
    const parsed = common.args.parseCoordinator(argv[0..]);
    try std.testing.expect(parsed == .help);
}
