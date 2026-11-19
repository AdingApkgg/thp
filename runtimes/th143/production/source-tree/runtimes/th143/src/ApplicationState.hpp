#pragma once
#include "AnmState.hpp"
namespace th143 {
struct ApplicationStateGlobals {bool threaded=false;u8 critical_depth=0;u32 menu_selection=0;};
struct ApplicationStateServices {
    virtual ~ApplicationStateServices()=default;
    virtual bool lock_application_state(bool acquire)=0;
    virtual bool application_state_call(u32 entry,u32 ecx,u32 stack_argument,u32& result)=0;
    virtual bool application_root_mode(u32&)=0;
};
//4458a0: application state transition ordering and owner factory selection.
// Factories/destructors, Root mode memory and OS critical sections are services.
bool transition_application_state(AnmView,ApplicationStateGlobals&,ApplicationStateServices&,i32& result);
}
