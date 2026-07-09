const std = @import("std");

pub fn build(b: *std.Build) void {
    const target = b.standardTargetOptions(.{});
    const optimize = b.standardOptimizeOption(.{});

    const common = b.addModule("ds5_common", .{
        .root_source_file = b.path("src/common/root.zig"),
        .target = target,
        .optimize = optimize,
    });

    const transport = b.addModule("ds5_transport", .{
        .root_source_file = b.path("src/transport/root.zig"),
        .target = target,
        .optimize = optimize,
        .imports = &.{
            .{ .name = "ds5_common", .module = common },
        },
    });

    const coordinator = b.addExecutable(.{
        .name = "ds5-coordinator",
        .root_module = b.createModule(.{
            .root_source_file = b.path("src/coordinator/main.zig"),
            .target = target,
            .optimize = optimize,
            .imports = &.{
                .{ .name = "ds5_common", .module = common },
                .{ .name = "ds5_transport", .module = transport },
            },
        }),
    });

    const worker = b.addExecutable(.{
        .name = "ds5-worker",
        .root_module = b.createModule(.{
            .root_source_file = b.path("src/worker/main.zig"),
            .target = target,
            .optimize = optimize,
            .imports = &.{
                .{ .name = "ds5_common", .module = common },
                .{ .name = "ds5_transport", .module = transport },
            },
        }),
    });

    b.installArtifact(coordinator);
    b.installArtifact(worker);

    const run_coordinator = b.addRunArtifact(coordinator);
    run_coordinator.step.dependOn(b.getInstallStep());
    if (b.args) |args| {
        run_coordinator.addArgs(args);
    }

    const run_coordinator_step = b.step("run-coordinator", "Run the DS5 coordinator transport smoke");
    run_coordinator_step.dependOn(&run_coordinator.step);

    const run_worker = b.addRunArtifact(worker);
    run_worker.step.dependOn(b.getInstallStep());
    if (b.args) |args| {
        run_worker.addArgs(args);
    }

    const run_worker_step = b.step("run-worker", "Run the DS5 worker transport listener");
    run_worker_step.dependOn(&run_worker.step);

    const common_tests = b.addTest(.{
        .root_module = common,
    });
    const run_common_tests = b.addRunArtifact(common_tests);

    const transport_tests = b.addTest(.{
        .root_module = transport,
    });
    const run_transport_tests = b.addRunArtifact(transport_tests);

    const coordinator_tests = b.addTest(.{
        .root_module = coordinator.root_module,
    });
    const run_coordinator_tests = b.addRunArtifact(coordinator_tests);

    const worker_tests = b.addTest(.{
        .root_module = worker.root_module,
    });
    const run_worker_tests = b.addRunArtifact(worker_tests);

    const loopback_transport_tests = b.addTest(.{
        .root_module = b.createModule(.{
            .root_source_file = b.path("tests/loopback_transport_test.zig"),
            .target = target,
            .optimize = optimize,
            .imports = &.{
                .{ .name = "ds5_common", .module = common },
                .{ .name = "ds5_transport", .module = transport },
            },
        }),
    });
    const run_loopback_transport_tests = b.addRunArtifact(loopback_transport_tests);

    const test_step = b.step("test", "Run unit tests");
    test_step.dependOn(&run_common_tests.step);
    test_step.dependOn(&run_transport_tests.step);
    test_step.dependOn(&run_coordinator_tests.step);
    test_step.dependOn(&run_worker_tests.step);
    test_step.dependOn(&run_loopback_transport_tests.step);
}
