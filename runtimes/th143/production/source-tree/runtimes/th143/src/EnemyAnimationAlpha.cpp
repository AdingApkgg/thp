#include "EnemyAnimationAlpha.hpp"
namespace th143 {
i32 enemy_animation_alpha(AnmView actor,Vm& vm,VmHost& host,EnemyAnimationAlphaHost& animations,u32 rate){
 if(vm.instruction->opcode!=328)return -2;
 const u32 slot=u32(vm.integer_argument(0,host));if(vm.failed)return -2;
 if(slot>23)return 0;
 AnmView image{nullptr};if(!animations.find_alpha_animation(actor.get(0x124+slot*4),image)){actor.put(0x124+slot*4,0);return 0;}
 const u32 alpha=u32(vm.integer_argument(3,host)),mode=u32(vm.integer_argument(2,host)),duration=u32(vm.integer_argument(1,host));if(vm.failed)return -2;
 image.put(0x174,duration);image.put(0x178,mode);image.put(0x14c,image.data[0x537]);image.put(0x150,alpha&255);image.put(0x154,0);image.put(0x158,0);
 if(!(image.get(0x170)&1)){image.put(0x16c,rate);image.put(0x170,image.get(0x170)|1);}
 image.put(0x160,0xffffffff);image.put(0x164,0);image.put(0x168,0);return 0;
}
}
