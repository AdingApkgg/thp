#include "EnemyAnimationLayer.hpp"
namespace th143 {
i32 enemy_animation_layer(AnmView actor,Vm& vm,VmHost& host,EnemyAnimationAlphaHost& animations){
 const u32 slot=u32(vm.integer_argument(0,host));if(vm.failed)return -2;if(slot>23)return 0;
 AnmView image{nullptr};if(!animations.find_alpha_animation(actor.get(0x124+slot*4),image)){actor.put(0x124+slot*4,0);return 0;}
 const u32 layer=u32(vm.integer_argument(1,host));if(vm.failed)return -2;image.put(0x24,layer);return 0;
}
}
