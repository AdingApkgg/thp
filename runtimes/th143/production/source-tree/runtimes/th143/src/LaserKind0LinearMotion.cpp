#include "LaserKind0LinearMotion.hpp"
#include <cmath>
#include <initializer_list>
namespace th143 {
bool advance_laser_kind0_linear(AnmView v,float rate,bool& expired){
 if(!v.data||!std::isfinite(rate))return false;
 for(u32 offset:{0x54u,0x58u,0x5cu,0x60u,0x64u,0x68u,0x70u,0x78u,0x7cu,0x5d0u,0x5d8u})if(!std::isfinite(v.floating(offset)))return false;
 expired=false;
 const float increment=v.floating(0x78)*rate,length=v.floating(0x70),target=v.floating(0x5d0);
 if(target>length){const float next=length+increment;v.put(0x70,word(next>target?target:next));return true;}
 const float travelled=increment+v.floating(0x7c);v.put(0x7c,word(travelled));
 for(u32 i=0;i<3;++i){const float delta=v.floating(0x60+i*4)*rate;v.put(0x54+i*4,word(v.floating(0x54+i*4)+delta));}
 const float cap=v.floating(0x5d8);
 if(cap>0.f&&travelled+length>cap){const float next=cap-travelled;v.put(0x70,word(next));v.put(0x5d0,word(next));expired=0.f>=next;}
 return true;
}
}
