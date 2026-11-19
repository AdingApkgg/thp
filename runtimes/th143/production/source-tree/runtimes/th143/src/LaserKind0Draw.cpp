#include "LaserKind0Draw.hpp"
#include "DirectionVector.hpp"
#include <cmath>
namespace th143 {
bool draw_laser_kind0(AnmView v,u32 token,LaserKind0DrawHost& host){
 if(!v.data)return false;AnmView main=v.sub(0x914);for(u32 i=0;i<3;++i)main.put(0x3c+i*4,v.get(0x54+i*4));
 float angle=v.floating(0x6c)+real(0x3fc90fdb);if(!std::isfinite(angle))return false;const float pi=real(0x40490fdb),tau=real(0x40c90fdb);u32 count=0;
 while(angle>pi){angle-=tau;if(count++>32)break;}while(-pi>angle){angle+=tau;if(count++>32)break;}
 main.put(0x18,main.get(0x18)|4);main.put(0x50,word(angle));if(!host.laser_draw_animation(token+0x914,main))return false;
 DirectionVector direction;if(!direction_vector(v.floating(0x6c),v.floating(0x70),direction))return false;AnmView end=v.sub(0x14ac);
 end.put(0x3c,word(direction.x+v.floating(0x54)));end.put(0x40,word(v.floating(0x58)+direction.y));end.put(0x44,0);if(!host.laser_draw_animation(token+0x14ac,end))return false;
 if(v.floating(0x7c)==0.f){auto secondary=v.sub(0xee0);for(u32 i=0;i<3;++i)secondary.put(0x3c+i*4,v.get(0x54+i*4));if(!host.laser_draw_animation(token+0xee0,secondary))return false;}
 return true;
}
}
