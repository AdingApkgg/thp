#include "ApplicationLoading.hpp"
namespace th143 {
bool finish_application_loading(ApplicationLoading& s,AnmWorld& world){
    if(s.state==1){
        for(u32 h:s.visuals)if(!signal_animation(world,h,1))return false;
        s.visuals.fill(0);s.state=0;
    }
    s.context=0;return true;
}
}
