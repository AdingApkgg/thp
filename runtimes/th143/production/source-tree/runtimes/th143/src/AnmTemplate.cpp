#include "AnmTemplate.hpp"

namespace th143 {
namespace {
void set_timer(AnmView t, u32 value, u32 rate) {
    t.put(0, value-1); t.put(4, value); t.put(8, word(float(signed_word(value))));
    t.put(12, rate); t.put(16, t.get(16) | 1);
}
}
bool anm_template(AnmView s, u32 self, u32 resource, i32 index, AnmVmHost& host) {
    u32 token; u16 file; bool ready;
    if (!host.script(resource, index, token, file, ready) || !ready) return false;
    anm_construct(s);
    // Null script473cb6 clears the already zero VM, including its sprite ID.
    if (!token) { std::memset(s.data, 0, AnmView::bytes); return true; }
    anm_reset(s, self);
    s.put(0x4a8, u32(u16(index)) << 16); s.put(0x34, u32(file) << 16);
    s.put(0x18, s.get(0x18) & ~0x1801u);
    s.put(0x1c, (s.get(0x1c) & ~0x2000u) | 0x4000);
    s.put(0x30, resource); s.put(0x38, token); s.put(0x28, token);
    set_timer(s.sub(0x548), 0xffffffff, host.global_rate_token());
    set_timer(s.sub(0x55c), 0xffffffff, host.global_rate_token());
    return anm_step(s, host) != -2;
}
}
