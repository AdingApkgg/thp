#include "RootTransition.hpp"

namespace th143 {
bool root_transition(AnmWorld& world,u32 resource,u32& handle,float x,float y){
    if(handle)return true;
    return world.create_at(resource,17,-1,{x*2.f,y*2.f,0.f},handle);
}
}
