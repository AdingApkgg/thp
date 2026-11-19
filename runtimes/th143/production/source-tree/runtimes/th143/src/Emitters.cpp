#include "Emitters.hpp"
#include <cstring>

namespace th143 {
u32 Emitters::get(u32 offset) const {
    u32 v; std::memcpy(&v, data.data() + offset, 4); return v;
}
void Emitters::put(u32 offset, u32 value) { std::memcpy(data.data() + offset, &value, 4); }
i32 Emitters::command(Vm& vm, VmHost& host, EmitterSink* sink) {
    const u32 op = vm.instruction->opcode;
    if (op < 600 || op > 614 || op == 613) return -2;
    i32 index = vm.integer_argument(0, host);
    if (op >= 609 && op <= 612 && (index < 0 || index >= 18)) index = 0;
    if (index < 0 || index >= i32(count)) return -2;
    const u32 slot = u32(index) * stride;
    auto integer = [&](u32 n) { return u32(vm.integer_argument(n, host)); };
    auto value = [&](u32 n) { return word(vm.float_argument(n, host)); };
    switch (op) {
    case 600:
        std::memset(data.data() + slot + 0x63c, 0, stride);
        put(slot + 0x650, 0); put(slot + 0x658, word(2.f));
        put(slot + 0x9a0, 0x10001); put(slot + 0x9ac, 0x15);
        put(slot + 0x9b0, 0x26); put(slot + 0x9a8, 0x23);
        put(0x3e7c + index * 12, 0); put(0x3e80 + index * 12, 0);
        for (u32 i = 0; i < 3; ++i) put(0x3f3c + index * 12 + i * 4, 0);
        put(0x3e3c + index * 4, 0);
        break;
    case 601: {
        const bool absolute = floating(0x3f44 + index * 12) > .9f;
        for (u32 i = 0; i < 3; ++i) {
            const float local = floating(0x3e7c + index * 12 + i * 4);
            const float origin = floating((absolute ? 0x3f3c + index * 12 : 0x44) + i * 4);
            put(slot + 0x644 + i * 4, i == 2 && absolute ? 0 : word(local + origin));
        }
        if (!sink || !sink->launch(data.data() + slot + 0x63c, stride, get(0x4114))) return -2;
        break;
    }
    case 602:
        put(slot + 0x63c, integer(1)); put(slot + 0x640, integer(2)); break;
    case 603:
        put(0x3e7c + index * 12, value(1)); put(0x3e80 + index * 12, value(2)); break;
    case 604:
        put(slot + 0x650, value(1)); put(slot + 0x654, value(2)); break;
    case 605:
        put(slot + 0x658, value(1)); put(slot + 0x65c, value(2)); break;
    case 606: {
        const u16 first = u16(integer(1)), second = u16(integer(2));
        put(slot + 0x9a0, u32(first) | (u32(second) << 16)); break;
    }
    case 607: {
        const u16 mode = u16(integer(1));
        std::memcpy(data.data() + slot + 0x9a4, &mode, 2); break;
    }
    case 608:
        put(slot + 0x9ac, integer(1)); put(slot + 0x9b0, integer(2)); break;
    case 609: case 610: case 611: case 612: {
        const bool append = op == 611 || op == 612, extended = op == 610 || op == 612;
        const u32 cursor = 0x3e3c + index * 4;
        const i32 row = append ? signed_word(get(cursor)) : vm.integer_argument(1, host);
        // Native permits writes outside the declared emitter for malformed
        // row/index values. Fail explicitly rather than corrupt another owner.
        if (row < 0 || row >= 18) return -2;
        const u32 entry = slot + u32(row) * 0x2c;
        u32 n = append ? 1 : 2;
        put(entry + 0x688, integer(n++)); put(entry + 0x684, integer(n++));
        put(entry + 0x674, integer(n++)); put(entry + 0x678, integer(n++));
        if (extended) { put(entry + 0x67c, integer(n++)); put(entry + 0x680, integer(n++)); }
        put(entry + 0x664, value(n++)); put(entry + 0x668, value(n++));
        if (extended) { put(entry + 0x66c, value(n++)); put(entry + 0x670, value(n++)); }
        put(cursor, append ? get(cursor) + 1 : u32(row) + 1);
        break;
    }
    case 614: {
        const i32 source = vm.integer_argument(1, host);
        if (source < 0 || source >= i32(count)) return -2;
        if (source != index) {
            std::memcpy(data.data() + slot + 0x63c, data.data() + u32(source) * stride + 0x63c, stride);
            for (u32 base : {0x3e7cu, 0x3f3cu})
                std::memcpy(data.data() + base + index * 12, data.data() + base + source * 12, 12);
        }
        // 424736 copies parameters and positions, preserving the destination
        // transform cursor at +3e3c (it is not part of either copied region).
        break;
    }
    }
    return vm.failed ? -2 : 0;
}
}
