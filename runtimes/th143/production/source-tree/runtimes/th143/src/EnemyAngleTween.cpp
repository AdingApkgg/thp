#include "EnemyAngleTween.hpp"
#include <cmath>
namespace th143 {
namespace {
float wrap(float a){u32 count=0;while(a>real(0x40490fdb)){a-=real(0x40c90fdb);if(count++>32)break;}while(real(0xc0490fdb)>a){a+=real(0x40c90fdb);if(count++>32)break;}return a;}
float mirror(float a){const float half=real(0x3fc90fdb);return wrap(half-wrap(a-half));}
}
i32 enemy_angle_command(Emitters& actor,Vm& vm,VmHost& host,AnmTimerHost& rates){
 const u32 op=vm.instruction->opcode;if(op<440||op>443)return -2;const u32 position=op<442?0x88:0xcc;const bool mirrored=(actor.get(0x4100)&0x80000)!=0;
 if(!(op&1)){float angle=vm.float_argument(0,host);if(vm.failed)return -2;if(mirrored)angle=mirror(angle);actor.put(position+0x1c,word(wrap(angle)));actor.put(position+0x40,actor.get(position+0x40)&~15u);return 0;}
 const u32 at=op==441?0x46c:0x4cc;float target=vm.float_argument(2,host);const i32 duration=vm.integer_argument(0,host);if(vm.failed)return -2;if(duration<=0){actor.put(at+0x28,0);return 0;}
 const u32 mode=u32(vm.integer_argument(1,host));if(mode==7)target=double(target)>-999999.?(mirrored?-target:target):0.f;else target=double(target)>-999999.?(mirrored?mirror(target):target):actor.floating(position+0x1c);
 float from=actor.floating(position+0x1c);if(std::fabs(from-target)>=real(0x40490fdb)){if(target>from)target+=real(0x40c90fdb);else from+=real(0x40c90fdb);}
 const u32 count=u32(vm.integer_argument(0,host));if(vm.failed)return -2;actor.put(at,word(from));actor.put(at+0x28,count);actor.put(at+0x2c,mode);actor.put(at+8,0);actor.put(at+12,0);actor.put(at+4,word(target));scalar_reset_timer({actor.data.data()+at},rates);actor.put(position+0x40,actor.get(position+0x40)&~15u);return 0;
}
}
