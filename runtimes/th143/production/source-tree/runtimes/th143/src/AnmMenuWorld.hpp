#pragma once
#include "AnmResourceWorld.hpp"
#include "AnmEffect0.hpp"
#include "AnmOverlay.hpp"
#include "AnmSignal.hpp"
namespace th143 {
// Adds the screen-transition effect table's row0 to the shared resource world.
class AnmMenuWorld:public AnmResourceWorld,public AnmSignalHost {
public:
    using AnmResourceWorld::AnmResourceWorld;
    bool create_screen_transition(u32 resource,u32& handle);
    bool callback(u32,AnmView,float,i32&)override;
    bool animation_signal_callback(u32,AnmView,i32)override;
    bool screen_transition_signal(u32 handle,i32 signal,bool immediate=false){return signal_animation(*this,handle,signal,immediate,this);}
    u8* transition_data(u32 token);
};
}
