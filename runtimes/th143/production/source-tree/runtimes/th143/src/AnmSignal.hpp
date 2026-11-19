#pragma once
#include "AnmWorld.hpp"
namespace th143 {
struct AnmSignalHost {
    virtual ~AnmSignalHost()=default;
    virtual bool animation_signal_callback(u32 entry,AnmView,i32 signal)=0;
};
bool signal_animation_vm(AnmWorld&,AnmView,i32 signal,bool immediate=false,AnmSignalHost* callbacks=nullptr);
// 484320 and484390. A signal callback precedes the signal write; immediate
// execution and callbacks can change parent/child links, which are reread.
bool signal_animation(AnmWorld&,u32 handle,i32 signal,bool immediate=false,AnmSignalHost* callbacks=nullptr);
}
