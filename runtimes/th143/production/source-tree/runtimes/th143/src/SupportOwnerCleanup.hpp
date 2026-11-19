#pragma once
#include "AnmWorld.hpp"
namespace th143 {
struct SupportOwnerCleanupHost {
    virtual ~SupportOwnerCleanupHost()=default;
    virtual bool remove_support_callback(u32)=0;
    // The virtual option destructor can clear/change its owning pointer.
    virtual bool destroy_support_option(AnmView owner,u32 offset)=0;
    virtual bool release_support_option(u32)=0;
};
// Original450570/418700. Callback words remain in the destroyed object;
// owning globals are cleared only after their respective complete sequence.
bool cleanup_player_auxiliary(AnmView,u32& owner,SupportOwnerCleanupHost&);
bool cleanup_scene_extra(AnmView,AnmWorld&,u32& owner,SupportOwnerCleanupHost&);
}
