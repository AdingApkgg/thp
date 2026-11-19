#include "EnemyVisualScaleDecay.hpp"
namespace th143 {
bool decay_enemy_visual_scale(AnmView v,float rate,EnemyVisualScaleDecayHost& host,i32& result){
 if(!v.data)return false;const float difference=1.f-v.floating(0x340),step=(difference/20.f)*rate,next=v.floating(0x344)-step;v.put(0x344,word(next));
 auto animation=host.enemy_scale_animation(v.get(0x124));result=0;if(!animation.data){v.put(0x124,0);return true;}
 animation.put(0x18,animation.get(0x18)|8u);animation.put(0x60,word(next));animation.put(0x18,animation.get(0x18)|8u);animation.put(0x64,v.get(0x344));return true;
}
}
