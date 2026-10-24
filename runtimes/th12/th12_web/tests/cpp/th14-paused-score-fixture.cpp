#include "../../cpp/game/Hud.hpp"
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
API(run) u32 run(u32 current,u32 displayed,u32 speed,u32 high,u32 continues,u32 high_continues,u32 flags,u32 field){
    HudScore s{};s.displayed=signed_bits(displayed);s.speed=signed_bits(speed);s.high=signed_bits(high);
    s.continues=signed_bits(continues);s.high_continues=signed_bits(high_continues);s.flags=flags;s.update(signed_bits(current));
    const u32 values[]={u32(s.displayed),u32(s.speed),u32(s.high),u32(s.high_continues),s.flags};
    return field<5?values[field]:0;
}
