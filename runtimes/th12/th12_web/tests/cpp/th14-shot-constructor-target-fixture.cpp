#include "th14-shot-sakuya-fixture.cpp"
// Target mode 2 models a live constructor receiver absent from the list.
API(constructor_hit) i32 constructor_hit(){
 auto* enemies=configure();shot.timer.previous=shot.timer.current-i32(inputs[27]);
 area.argument=inputs[8]?19:0;area.size.y=number(inputs[26]);
 const Vec3 target{shot.movement.position.x+number(inputs[23]),shot.movement.position.y+number(inputs[24]),0};const Vec2 size{24,40};
 return shot_th14_sakuya_hit(shot,player,area,target,inputs[22]?&size:nullptr,number(inputs[25]),enemies,hit_action,inputs[8]==2?&enemy:nullptr);
}
