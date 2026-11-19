#include "EnemyEllipseTween.hpp"
#include "EnemyEllipseMotion.hpp"
#include <array>
#include <cmath>
namespace th143 {
namespace {
void timer(AnmView s,u32 at,u32 rate){if(!(s.get(at+16)&1)){s.put(at+12,rate);s.put(at+16,s.get(at+16)|1);}s.put(at,0xffffffff);s.put(at+4,0);s.put(at+8,0);}
void vec2(AnmView s,u32 duration,u32 mode,u32 start_x,u32 start_y,u32 target_x,u32 target_y,u32 rate){s.put(0x3c,duration);s.put(0x40,mode);s.put(0,start_x);s.put(4,start_y);s.put(8,target_x);s.put(12,target_y);for(u32 i=0;i<4;++i)s.put(0x10+i*4,0);timer(s,0x28,rate);}
}
i32 enemy_ellipse_tween(AnmView actor,Vm& vm,VmHost& host,u32 rate){
    const u32 op=vm.instruction->opcode;if(op!=421&&op!=423)return -2;
    const u32 base=op==421?0x88:0xcc,speed=op==421?0x49c:0x4fc,radius=op==421?0x52c:0x570,orientation=op==421?0x5b4:0x5f8;
    std::array<float,5> values;for(u32 i=0;i<5;++i)values[i]=vm.float_argument(i+2,host);
    const i32 duration=vm.integer_argument(0,host),mode=vm.integer_argument(1,host);if(vm.failed)return -2;
    if(duration<=0){actor.put(speed+0x28,0);actor.put(radius+0x3c,0);actor.put(orientation+0x3c,0);return 0;}
    const u32 offsets[]={0x18,0x20,0x24,0x28,0x2c};std::array<u32,5> target;
    for(u32 i=0;i<5;++i)target[i]=double(values[i])>-999999.?word(values[i]):actor.get(base+offsets[i]);
    auto scalar=actor.sub(speed);scalar.put(0,actor.get(base+0x18));scalar.put(4,target[0]);scalar.put(8,0);scalar.put(12,0);scalar.put(0x28,u32(duration));scalar.put(0x2c,u32(mode));timer(scalar,0x14,rate);
    vec2(actor.sub(radius),u32(duration),u32(mode),actor.get(base+0x20),actor.get(base+0x24),target[1],target[2],rate);
    vec2(actor.sub(orientation),u32(duration),u32(mode),actor.get(base+0x28),actor.get(base+0x2c),target[3],target[4],rate);
    for(u32 i=0;i<3;++i)actor.put(base+0x34+i*4,actor.get(base+i*4));actor.put(base+0x40,(actor.get(base+0x40)&0xfffffff3u)|3);
    if(!evaluate_enemy_ellipse(actor.sub(base))||(actor.get(0x84)&15))return -2;
    for(u32 i=0;i<3;++i){const float delta=actor.floating(0xcc+i*4)+actor.floating(0x88+i*4)-actor.floating(0x44+i*4);actor.put(0x78+i*4,word(delta));const float value=actor.floating(0x44+i*4)+delta;actor.put(0x44+i*4,word(i<2?float(std::floor(double(value*100.f)))/100.f:value));}
    if(actor.get(0x4100)&0x20000){for(u32 i=0;i<2;++i){const float center=actor.floating(0x4004+i*4),half=actor.floating(0x400c+i*4)*.5f,value=actor.floating(0x44+i*4);if(center-half>value)actor.put(0x44+i*4,word(center-half));else if(value>center+half)actor.put(0x44+i*4,word(center+half));}for(u32 i=0;i<3;++i)actor.put(0x88+i*4,word(actor.floating(0x44+i*4)-actor.floating(0xcc+i*4)));}
    return 0;
}
}
