#pragma once
#include <cstdint>
#include <cstring>

namespace th143 {
using u8 = std::uint8_t;
using u16 = std::uint16_t;
using u32 = std::uint32_t;
using i32 = std::int32_t;
inline float real(u32 bits) { float v; std::memcpy(&v, &bits, 4); return v; }
inline u32 word(float v) { u32 bits; std::memcpy(&bits, &v, 4); return bits; }
inline i32 signed_word(u32 bits) { i32 v; std::memcpy(&v, &bits, 4); return v; }

struct Instruction {
    i32 time;
    u16 opcode, length, references;
    u8 difficulty, parameter_count;
    u32 stack_adjustment;
    u32 argument(u32 n) const {
        u32 value;
        std::memcpy(&value, reinterpret_cast<const u8*>(this) + 16 + n * 4, 4);
        return value;
    }
};
static_assert(sizeof(Instruction) == 16);

struct Vm;
struct VmHost {
    virtual ~VmHost() = default;
    virtual bool integer(i32 id, i32& value) { return false; }
    virtual bool floating(i32 id, float& value) { return false; }
    virtual u8* reference(i32 id, bool floating) { return nullptr; }
    virtual Instruction* find_subroutine(const char* name) { return nullptr; }
    virtual bool spawn(Vm& source, i32 id, u32 skipped) { return false; }
    virtual Vm* thread(i32 id) { return nullptr; }
    virtual void cancel_secondary() {}
    // 0: consume command, 1: instruction changed, -1: finish update,
    // -2: unsupported. Unknown gameplay commands must stop, not vanish.
    virtual i32 command(Vm&) { return -2; }
};

struct Vm {
    float time = 0;
    Instruction* instruction = nullptr;
    u8 stack[4096]{};
    i32 top = 0, frame = 0;
    u8 difficulty = 255;
    i32 thread_id = -1;
    u32 state = 0, flags = 0;
    i32 error_opcode = -1;
    bool failed = false;

    i32 integer_argument(u32 index, VmHost&, bool consume = false);
    float float_argument(u32 index, VmHost&, bool consume = false);
    i32 integer_operand(u32 bits, u32 parameter, VmHost&, bool consume = false);
    float float_operand(u32 bits, u32 parameter, VmHost&, bool consume = false);
    u8* reference(u32 index, VmHost&, bool floating);
    i32 update(float elapsed, VmHost&, u32 instruction_budget = 100000);
    i32 call(Vm& source, VmHost&, u32 skipped = 0);

private:
    u32 load(i32 at);
    void store(i32 at, u32 value);
    bool push(u8 type, u32 bits);
    i32 pop_integer();
    float pop_float();
    u32 pop_raw();
    i32 resolve_integer(i32, VmHost&, bool consume);
    float resolve_float(float, VmHost&, bool consume);
    i32 local_offset(i32);
};
}
