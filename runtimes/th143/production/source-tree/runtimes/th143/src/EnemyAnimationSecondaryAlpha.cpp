#include "EnemyAnimationSecondaryAlpha.hpp"
namespace th143 {
i32 enemy_animation_secondary_alpha(AnmView actor,Vm& vm,VmHost& host,EnemyAnimationAlphaHost& animations,u32 rate){
    const u32 op=vm.instruction->opcode;if(op!=331&&op!=332)return -2;
    const u32 slot=u32(vm.integer_argument(0,host));if(vm.failed)return -2;if(slot>23)return 0;
    AnmView image{nullptr};if(!animations.find_alpha_animation(actor.get(0x124+slot*4),image)){actor.put(0x124+slot*4,0);return 0;}
    if(op==331){const u32 value=u32(vm.integer_argument(1,host));if(vm.failed)return -2;image.data[0x53b]=u8(value);return 0;}
    const u32 alpha=u32(vm.integer_argument(3,host)),mode=u32(vm.integer_argument(2,host)),duration=u32(vm.integer_argument(1,host));if(vm.failed)return -2;
    image.put(0x350,duration);image.put(0x354,mode);image.put(0x328,image.data[0x53b]);image.put(0x32c,alpha&255);
    if(!(image.get(0x34c)&1)){image.put(0x348,rate);image.put(0x34c,image.get(0x34c)|1);}
    image.put(0x33c,0xffffffff);image.put(0x340,0);image.put(0x344,0);image.put(0x18,(image.get(0x18)&~0x40000u)|0x20000u);return 0;
}
}
