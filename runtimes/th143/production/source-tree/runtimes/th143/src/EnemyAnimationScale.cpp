#include "EnemyAnimationScale.hpp"
namespace th143 {
i32 enemy_animation_scale(AnmView actor,Vm& vm,VmHost& host,EnemyAnimationAlphaHost& animations,u32 rate){
 const u32 op=vm.instruction->opcode;if(op!=329&&op!=330&&op!=335)return -2;
 const u32 slot=u32(vm.integer_argument(0,host));if(vm.failed)return -2;if(slot>23)return 0;
 AnmView image{nullptr};if(!animations.find_alpha_animation(actor.get(0x124+slot*4),image)){actor.put(0x124+slot*4,0);return 0;}
 if(op==329||op==335){const float y=vm.float_argument(2,host),x=vm.float_argument(1,host);if(vm.failed)return -2;image.put(0x18,image.get(0x18)|8);image.put(op==329?0x60:0x68,word(x));image.put(op==329?0x64:0x6c,word(y));return 0;}
 const float y=vm.float_argument(4,host),x=vm.float_argument(3,host);const u32 mode=u32(vm.integer_argument(2,host)),duration=u32(vm.integer_argument(1,host));if(vm.failed)return -2;
 image.put(0x240,duration);image.put(0x244,mode);image.put(0x204,image.get(0x60));image.put(0x208,image.get(0x64));image.put(0x20c,word(x));image.put(0x210,word(y));
 if(!(image.get(0x23c)&1)){image.put(0x238,rate);image.put(0x23c,image.get(0x23c)|1);}
 image.put(0x22c,0xffffffff);image.put(0x230,0);image.put(0x234,0);return 0;
}
}
