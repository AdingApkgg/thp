#pragma once
#include "AnmResourceWorld.hpp"
namespace th143 {
struct GameResourceWaitHost {
    virtual ~GameResourceWaitHost()=default;
    // The application pumps its main-thread resource work before resuming the
    // loading worker. A missing service rejects instead of spinning forever.
    virtual bool resource_wait(u32 milliseconds)=0;
};
// 482140's config0 request/wait boundary. The application owns the declared
// cooperative schedule; resource constructors/chunks/templates remain real.
bool request_game_animation_ready(AnmResourceWorld&,u32 slot,const char*,GameResourceWaitHost&,u32& token,u32 wait_budget=100000);
}
