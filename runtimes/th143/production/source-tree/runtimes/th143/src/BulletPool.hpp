#pragma once
#include "EclVm.hpp"
#include <vector>

namespace th143 {
// Fixed native pool: 2000 usable bullets plus the special state-6 sentinel.
// Inline node pointers use explicit 32-bit semantic addresses in this storage.
// Backends resolve these addresses with offset(), never as host pointers.
class BulletPool {
public:
    static constexpr u32 count = 2000, stride = 0x13f4, first = 0x8c;
    static constexpr u32 bytes = 0x9bf6d0, token_base = 0x01000000;
    std::vector<u8> data;
    BulletPool() : data(bytes, 0) {}
    u32 get(u32 at) const;
    void put(u32 at, u32 value);
    static u32 token(u32 offset) { return token_base + offset; }
    static u32 bullet(u32 index) { return token(first + index * stride); }
    static u32 offset(u32 address) { return address - token_base; }

    void initialize(u32 resource_token, u32 update_token, u32 draw_token);
    // 413b30 allocation prefix ends before launch arithmetic at 413bb3.
    u32 acquire();
    // 413410: inactive bullets return without changing their links or timers.
    bool release(u32 bullet_token, u32 rate_token);
    // Storage/list portion of 4125c0. Resource-wide ANM retirement belongs to
    // the world/ANM owner and must run separately before this operation.
    void reset_storage();
private:
    void build_free_list();
    void reset_timer(u32 offset, u32 rate_token);
};
}
