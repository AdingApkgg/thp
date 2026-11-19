#include "LaserEmitterLaunch.hpp"
#include "AnmState.hpp"
namespace th143 {
namespace {float wrap(float a){u32 count=0;while(a>real(0x40490fdb)){a-=real(0x40c90fdb);if(count++>32)break;}while(real(0xc0490fdb)>a){a+=real(0x40c90fdb);if(count++>32)break;}return a;}}
i32 laser_emitter_launch(Emitters& s,Vm& vm,VmHost& host,LaserEmitterSink& sink){
 const u32 op=vm.instruction->opcode;if(op!=702&&op!=703&&op!=711&&op!=713)return -2;const i32 index=vm.integer_argument(0,host);if(vm.failed||index<0||index>=i32(Emitters::count))return -2;
 const u32 base=u32(index)*Emitters::stride,position=u32(index)*12;std::array<u8,0x374> data{};AnmView p{data.data()};const u32 kind=op==702?0:op==703?1:op==711?2:3,bytes=kind==1?0x374:0x354,transforms=kind==0?0x34:kind==1?0x5c:kind==2?0x2c:0x3c;
 std::memcpy(data.data()+transforms,s.data.data()+base+0x664,0x318);
 const bool absolute=s.floating(0x3f44+position)>real(0x3f666666);for(u32 i=0;i<3;++i){const float offset=s.floating(0x3e7c+position+i*4),origin=s.floating(absolute?0x3f3c+position+i*4:0x44+i*4);p.put(i*4,word(!absolute&&i==0&&(kind==1||kind==2)?origin+offset:offset+origin));}if(absolute)p.put(8,0);
 const u32 angle=word(wrap(s.floating(base+0x650)));auto copy=[&](u32 destination,u32 source){p.put(destination,s.get(base+source));};
 if(kind==0){p.put(0xc,angle);copy(0x10,0x648);copy(0x14,0x644);copy(0x18,0x64c);copy(0x1c,0x97c);copy(0x20,0x658);copy(0x24,0x63c);copy(0x28,0x640);copy(0x2c,0x660);p.put(0x30,1);copy(0x34c,0x9ac);copy(0x350,0x9b0);}
 else if(kind==1){p.put(0x18,angle);copy(0x20,0x648);copy(0x24,0x644);copy(0x28,0x97c);copy(0x2c,0x658);for(u32 i=0;i<4;++i)copy(0x30+i*4,0x98c+i*4);copy(0x40,0x9ac);copy(0x44,0x9b0);p.put(0x48,u32(vm.integer_argument(1,host)));copy(0x4c,0x660);copy(0x50,0x63c);copy(0x54,0x640);p.put(0x58,s.get(base+0x99c)|2u);}
 else if(kind==2){p.put(0xc,angle);copy(0x10,0x97c);copy(0x14,0x658);copy(0x18,0x63c);copy(0x1c,0x640);copy(0x20,0x98c);copy(0x24,0x660);p.put(0x28,1);copy(0x344,0x9ac);copy(0x348,0x9b0);}
 else{p.put(0x18,angle);copy(0x20,0x64c);copy(0x24,0x97c);p.put(0x28,u32(vm.integer_argument(1,host)));copy(0x2c,0x640);copy(0x30,0x660);copy(0x34,0x98c);}
 return !vm.failed&&sink.launch_laser(kind,data.data(),bytes)?0:-2;
}
}
