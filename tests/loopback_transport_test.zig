const std = @import("std");

const transport = @import("ds5_transport");

test "single-process loopback uses framed protocol bytes" {
    var encoded: std.ArrayList(u8) = .empty;
    defer encoded.deinit(std.testing.allocator);

    const payload = "deterministic block payload";
    try transport.appendFrameBytes(std.testing.allocator, &encoded, .block, 7, payload);

    var decoded = try transport.decodeFrameBytes(std.testing.allocator, encoded.items);
    defer decoded.deinit(std.testing.allocator);

    try std.testing.expectEqual(transport.FrameKind.block, decoded.header.kind);
    try std.testing.expectEqual(@as(u64, 7), decoded.header.seq);
    try std.testing.expectEqualStrings(payload, decoded.payload);
    try std.testing.expect(transport.verifyFrame(decoded.header, decoded.payload));
}
