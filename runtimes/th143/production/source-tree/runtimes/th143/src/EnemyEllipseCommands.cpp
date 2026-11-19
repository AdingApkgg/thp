#include "EnemyEllipseCommands.hpp"
#include "EnemyEllipseMotion.hpp"
#include <array>
#include <cmath>
namespace th143 {
namespace {float wrap(float value){u32 count=0;while(value>real(0x40490fdb)){value-=real(0x40c90fdb);if(count++>32)break;}while(real(0xc0490fdb)>value){value+=real(0x40c90fdb);if(count++>32)break;}return value;}}
i32 enemy_ellipse_command(AnmView actor,Vm& vm,VmHost& host){
    const u32 op=vm.instruction->opcode;if(op!=420&&op!=422)return -2;
    const u32 base=op==420?0x88:0xcc;std::array<float,6> args;
    for(u32 i=0;i<6;++i){args[i]=vm.float_argument(i,host);if(vm.failed)return -2;}
    if((actor.get(base+0x40)&15)!=2)for(u32 i=0;i<3;++i)actor.put(base+0x34+i*4,actor.get(base+i*4));
    if(double(args[0])>-999999.)actor.put(base+0x1c,word(wrap(args[0])));
    if(double(args[1])>-999999.)actor.put(base+0x18,word(args[1]));
    if(double(args[2])>-999999.)actor.put(base+0x20,word(args[2]));
    if(double(args[3])>-999999.)actor.put(base+0x24,word(args[3]));
    if(double(args[4])>-999999.)actor.put(base+0x28,word(wrap(wrap(args[4]))));
    if(double(args[5])>-999999.)actor.put(base+0x2c,word(args[5]));
    actor.put(base+0x40,(actor.get(base+0x40)&0xfffffff3u)|3);
    if(!evaluate_enemy_ellipse({actor.data+base})||(actor.get(0x84)&15))return -2;
    for(u32 i=0;i<3;++i){const float delta=actor.floating(0xcc+i*4)+actor.floating(0x88+i*4)-actor.floating(0x44+i*4);actor.put(0x78+i*4,word(delta));const float value=actor.floating(0x44+i*4)+delta;actor.put(0x44+i*4,word(i<2?float(std::floor(double(value*100.f)))/100.f:value));}
    if(actor.get(0x4100)&0x20000){for(u32 i=0;i<2;++i){const float center=actor.floating(0x4004+i*4),half=actor.floating(0x400c+i*4)*.5f,value=actor.floating(0x44+i*4);if(center-half>value)actor.put(0x44+i*4,word(center-half));else if(value>center+half)actor.put(0x44+i*4,word(center+half));}for(u32 i=0;i<3;++i)actor.put(0x88+i*4,word(actor.floating(0x44+i*4)-actor.floating(0xcc+i*4)));}
    return 0;
}
}
