#include "../../cpp/game/PlayerCollision.hpp"
using namespace th11;
extern "C" __attribute__((export_name("test"))) i32 test(i32 circle,float px,float py,float x,float y,float width,float height,float radius,float factor,i32 scaled,i32 state,i32 inv,i32 dialogue,i32 probe){
 PlayerCollision shape;shape.position={px,py};shape.minimum={px-.75f,py-1.25f};shape.maximum={px+.75f,py+1.25f};
 shape.radius=scaled?(factor*3.5999999046325684f)*radius:radius;shape.state=state;shape.invincibility_frames=inv;shape.dialogue_active=dialogue;
 const auto r=circle?shape.circle({x,y},width,probe):shape.rectangle({x,y},{width,height},probe);
 return i32(r.kind)|(r.trigger_hit?0x100:0);
}
