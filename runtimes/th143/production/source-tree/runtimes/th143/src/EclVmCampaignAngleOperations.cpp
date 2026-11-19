#include "EclAngleOperations.hpp"
#include "EclPolar.hpp"
#include "EclVariableTweenRuntime.hpp"
#include <map>
#include "EclVm.hpp"
#include <cmath>
#include <limits>

namespace th143 {
namespace {
std::map<const Vm*,EclVariableTweens> campaign_tweens;
struct CampaignRates:AnmTimerHost{bool timer_rate(u32,float& value)override{return campaign_vm_rate(value);}}campaign_rates;
}
void campaign_tweens_reset(Vm& vm,u8 fill){campaign_tweens[&vm].initialize(fill);}
void campaign_tweens_forget(const Vm& vm){campaign_tweens.erase(&vm);}
const EclVariableTweens* campaign_tweens_state(const Vm& vm){auto i=campaign_tweens.find(&vm);return i==campaign_tweens.end()?nullptr:&i->second;}
i32 campaign_tweens_command(Vm& vm,VmHost& host){auto i=campaign_tweens.find(&vm);return i==campaign_tweens.end()?-2:i->second.command(vm,host,campaign_rates);}
bool campaign_tweens_advance(Vm& vm,VmHost& host){auto i=campaign_tweens.find(&vm);return i==campaign_tweens.end()||i->second.advance(vm,host,campaign_rates);}

namespace {
i32 cvtt(float v) {
    // CVTTSS2SI's indefinite integer is part of the native VM semantics.
    if (!(v >= -2147483648.f && v < 2147483648.f)) return INT32_MIN;
    return i32(v);
}
Instruction* advance(Instruction* p, i32 bytes) {
    return reinterpret_cast<Instruction*>(reinterpret_cast<u8*>(p) + bytes);
}
}
u32 Vm::load(i32 at) {
    if (at < 0 || at > 4092) { failed = true; return 0; }
    u32 v; std::memcpy(&v, stack + at, 4); return v;
}
void Vm::store(i32 at, u32 value) {
    if (at < 0 || at > 4092) { failed = true; return; }
    std::memcpy(stack + at, &value, 4);
}
bool Vm::push(u8 type, u32 value) {
    if (top < 0 || top > 4088) { failed = true; return false; }
    // Native writes only the tag byte, retaining the other three bytes.
    stack[top] = type; top += 4;
    store(top, value); top += 4;
    return !failed;
}
u32 Vm::pop_raw() {
    if (top < 4) { failed = true; return 0; }
    top -= 4;
    return load(top);
}
i32 Vm::pop_integer() {
    const u32 value = pop_raw();
    if (top < 4) { failed = true; return 0; }
    top -= 4;
    return stack[top] == 'f' ? cvtt(real(value)) : signed_word(value);
}
float Vm::pop_float() {
    const u32 value = pop_raw();
    if (top < 4) { failed = true; return 0; }
    top -= 4;
    return stack[top] == 'i' ? float(signed_word(value)) : real(value);
}
i32 Vm::integer_argument(u32 index, VmHost& host, bool consume) {
    return integer_operand(instruction->argument(index), index, host, consume);
}
i32 Vm::integer_operand(u32 bits, u32 parameter, VmHost& host, bool consume) {
    const i32 value = signed_word(bits);
    if (!(instruction->references & (1u << (parameter & 31)))) return value;
    return resolve_integer(value, host, consume);
}
i32 Vm::local_offset(i32 value) {
    const std::int64_t at = std::int64_t(frame) + value;
    if (at < 0 || at > 4092) { failed = true; return -1; }
    return i32(at);
}
i32 Vm::resolve_integer(i32 value, VmHost& host, bool consume) {
    if (value >= 0) return signed_word(load(local_offset(value)));
    if (value >= -100) {
        if (consume) return pop_integer();
        const i32 at = top + value * 8;
        const u32 bits = load(at + 4), type = load(at);
        return (type & 255) == 'f' ? cvtt(real(bits)) : signed_word(bits);
    }
    i32 result = 0;
    if (!host.integer(value, result)) failed = true;
    return result;
}
float Vm::float_argument(u32 index, VmHost& host, bool consume) {
    return float_operand(instruction->argument(index), index, host, consume);
}
float Vm::float_operand(u32 bits, u32 parameter, VmHost& host, bool consume) {
    const float value = real(bits);
    if (!(instruction->references & (1u << (parameter & 31)))) return value;
    return resolve_float(value, host, consume);
}
float Vm::resolve_float(float value, VmHost& host, bool consume) {
    if (value >= 0) return real(load(local_offset(cvtt(value))));
    if (value >= -100 && value <= -1) {
        if (consume) return pop_float();
        const i32 at = top + cvtt(value * 8.f);
        const u32 bits = load(at + 4), type = load(at);
        return (type & 255) == 'i' ? float(signed_word(bits)) : real(bits);
    }
    float result = 0;
    if (!host.floating(cvtt(value), result)) failed = true;
    return result;
}
u8* Vm::reference(u32 index, VmHost& host, bool floating) {
    if (!(instruction->references & (1u << (index & 31)))) { failed = true; return nullptr; }
    const u32 bits = instruction->argument(index);
    const i32 offset = floating ? cvtt(real(bits)) : signed_word(bits);
    if (offset < 0) {
        u8* result = host.reference(offset, floating);
        if (!result) failed = true;
        return result;
    }
    const i32 at = local_offset(offset);
    if (failed) return nullptr;
    return stack + at;
}
i32 Vm::call(Vm& source, VmHost& host, u32 skipped) {
    // TH143 487240. Argument evaluation can pop the source stack before the
    // saved stack cursor is written. Initial calls use four raw words.
    const i32 old_top = top;
    const auto* args = reinterpret_cast<const u8*>(source.instruction) + 16;
    u32 descriptor = source.instruction->argument(0) + (skipped + 1) * 4;
    i32 destination = old_top ? old_top + 12 : 16;
    if (!old_top) { store(0, 0); top = 4; }
    for (u32 index = skipped + 1; index < source.instruction->parameter_count;
         ++index, descriptor += 8, destination += 4) {
        if (descriptor + 8 > source.instruction->length - 16u) { failed = true; return -2; }
        const u8 from = args[descriptor], to = args[descriptor + 1];
        const u32 raw = source.instruction->argument((descriptor + 4) / 4);
        const bool ref = source.instruction->references & (1u << (index & 31));
        u32 value;
        if (from == 'f' || from == 'g') {
            const float v = ref ? source.resolve_float(real(raw), host, true) : real(raw);
            value = to == 'f' ? word(v) : u32(cvtt(v));
        } else {
            const i32 v = ref ? source.resolve_integer(signed_word(raw), host, true) : signed_word(raw);
            value = to == 'f' ? word(float(v)) : u32(v);
        }
        store(destination, value);
    }
    const i32 argument_top = top;
    if (old_top) {
        const u32 last = pop_raw();
        top = old_top;
        store(old_top - 4, last);
    } else top = 4;
    store(top, u32(argument_top)); top += 4;
    store(top, old_top ? word(source.time) : 0); top += 4;
    store(top, old_top ? u32(reinterpret_cast<std::uintptr_t>(source.instruction)) : 0); top += 4;
    instruction = host.find_subroutine(reinterpret_cast<const char*>(source.instruction) + 20);
    time = 0;
    if (!instruction) { source.instruction = nullptr; return -1; }
    return failed || source.failed ? -2 : 0;
}
i32 Vm::update(float elapsed, VmHost& host, u32 budget) {
    if (!instruction) return -1;
    while (time >= float(instruction->time)) {
        if (!budget--) { failed = true; return -2; }
        const u16 op = instruction->opcode;
        error_opcode = op;
        if (instruction->difficulty & difficulty) {
            bool cleanup = true, jump = false, clear_cleanup = false;
            auto output = [&](u32 index, bool floating, u32 value) {
                u8* p = reference(index, host, floating);
                if (p) std::memcpy(p, &value, 4);
            };
            switch (op) {
            case 0: case 22: case 30: case 31: break;
            case 1: instruction = nullptr; return -1;
            case 10: {
                const i32 previous = frame;
                frame = signed_word(pop_raw()); top = previous;
                if (!top) { instruction = nullptr; return -1; }
                instruction = reinterpret_cast<Instruction*>(std::uintptr_t(pop_raw()));
                time = real(pop_raw());
                const i32 saved_top = signed_word(pop_raw());
                top = saved_top;
                if (!instruction) return -1;
                break;
            }
            case 11: {
                instruction->stack_adjustment &= 0xffffff00u;
                const i32 result = call(*this, host);
                if (result) return result;
                jump = true; break;
            }
            case 15: case 16: {
                i32 id = -1;
                if (op == 16) {
                    const u32 index = (instruction->argument(0) + 4) / 4;
                    const i32 raw = signed_word(instruction->argument(index));
                    id = instruction->references & 2 ? resolve_integer(raw, host, true) : raw;
                }
                if (!host.spawn(*this, id, op == 16 ? 1 : 0)) failed = true;
                cleanup = false; break;
            }
            case 17: case 18: case 19: case 20: {
                Vm* target = host.thread(integer_argument(0, host));
                if (target) {
                    if (op == 17) target->instruction = nullptr;
                    if (op == 18) target->flags |= 1;
                    if (op == 19) target->flags &= ~1u;
                    if (op == 20) target->state = u32(integer_argument(1, host));
                }
                break;
            }
            case 21: host.cancel_secondary(); cleanup = false; break;
            case 12: case 13: case 14: {
                const bool take = op == 12 || ((pop_integer() != 0) == (op == 14));
                if (take) {
                    time = float(signed_word(instruction->argument(1)));
                    instruction = advance(instruction, signed_word(instruction->argument(0)));
                    jump = true;
                }
                break;
            }
            case 23: time -= float(integer_argument(0, host)); break;
            case 24: time -= float_argument(0, host); break;
            case 40: {
                const i32 previous = top;
                const std::int64_t next = std::int64_t(top) + integer_argument(0, host);
                if (next < 0 || next >= 4096) { failed = true; break; }
                top = i32(next); store(top, u32(frame)); top += 4; frame = previous;
                break;
            }
            case 41: {
                const i32 previous = frame;
                frame = signed_word(pop_raw()); top = previous;
                break;
            }
            case 42: { const i32 v = integer_argument(0, host, true); push('i', u32(v)); cleanup = false; break; }
            case 44: { const float v = float_argument(0, host, true); push('f', word(v)); cleanup = false; break; }
            case 43: case 45: {
                u8* p = reference(0, host, op == 45);
                const u32 bits = pop_raw();
                if (top < 4) { failed = true; break; }
                top -= 4;
                const u8 type = stack[top];
                u32 result = bits;
                if (op == 43 && type == 'f') result = u32(cvtt(real(bits)));
                if (op == 45 && type == 'i') result = word(float(signed_word(bits)));
                if (p) std::memcpy(p, &result, 4);
                cleanup = false; break;
            }
            case 50: case 52: case 54: case 56: case 58:
            case 59: case 61: case 63: case 65: case 67: case 69:
            case 73: case 74: case 75: case 76: case 77: {
                const i32 right = pop_integer(), left = pop_integer();
                u32 value = 0;
                switch (op) {
                case 50: value = u32(left) + u32(right); break;
                case 52: value = u32(left) - u32(right); break;
                case 54: value = u32(left) * u32(right); break;
                case 56: case 58:
                    if (!right || (left == INT32_MIN && right == -1)) { failed = true; break; }
                    value = u32(op == 56 ? left / right : left % right); break;
                case 59: value = left == right; break;
                case 61: value = left != right; break;
                case 63: value = left < right; break;
                case 65: value = left <= right; break;
                case 67: value = left > right; break;
                case 69: value = left >= right; break;
                case 73: value = left || right; break;
                case 74: value = left && right; break;
                case 75: value = u32(left) ^ u32(right); break;
                case 76: value = u32(left) | u32(right); break;
                case 77: value = u32(left) & u32(right); break;
                }
                push('i', value);
                clear_cleanup = op == 50 || op == 52 || op == 54 || op == 56 || op == 58;
                cleanup = false; break;
            }
            case 51: case 53: case 55: case 57: {
                const float right = pop_float(), left = pop_float();
                const float v = op == 51 ? left + right : op == 53 ? left - right : op == 55 ? left * right : left / right;
                push('f', word(v)); clear_cleanup = true; cleanup = false; break;
            }
            case 60: case 62: case 64: case 66: case 68: case 70: {
                const float right = pop_float(), left = pop_float();
                const bool v = op == 60 ? left == right : op == 62 ? left != right :
                    op == 64 ? left < right : op == 66 ? left <= right : op == 68 ? left > right : left >= right;
                push('i', v); cleanup = false; break;
            }
            case 71: { const i32 v = pop_integer(); push('i', v == 0); cleanup = false; break; }
            case 72: { const float v = pop_float(); push('i', v == 0); cleanup = false; break; }
            case 78: {
                const i32 v = integer_argument(0, host);
                output(0, false, u32(v) - 1); push('i', u32(v)); cleanup = false; break;
            }
            case 83: { const i32 v = pop_integer(); push('i', 0u - u32(v)); cleanup = false; break; }
            case 84: { const float v = pop_float(); push('f', word(v) ^ 0x80000000u); cleanup = false; break; }
            case 82: case 87: case 89: {if(ecl_angle_operation(*this,host)!=0){failed=true;return -2;}break;}
            case 81: {if(ecl_polar_command(*this,host)!=0){failed=true;return -2;}break;}
            case 85: {
                const float x = float_argument(1, host), y = float_argument(2, host);
                output(0, true, word(float(y * y) + float(x * x))); break;
            }
            default: {
                const i32 result = host.command(*this);
                if (result == -2) { failed = true; break; }
                if (result == -1) return 0;
                if (result == 1) jump = true;
                break;
            }
            }
            if (failed) return -2;
            if (clear_cleanup) instruction->stack_adjustment &= 0xffffff00u;
            if (jump) continue;
            if (cleanup) {
                const u32 n = instruction->stack_adjustment & 255;
                if (n > u32(top)) { failed = true; return -2; }
                top -= i32(n);
            }
        }
        instruction = advance(instruction, instruction->length);
    }
    time += elapsed;
    if(!campaign_tweens_advance(*this,host)){failed=true;return -2;}
    return 0;
}
}
