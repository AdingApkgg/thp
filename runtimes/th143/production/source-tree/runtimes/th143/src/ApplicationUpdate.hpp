#pragma once
#include "AnmState.hpp"
namespace th143 {
struct ApplicationUpdateGlobals {u32 countdown=0,width=0,height=0,center_x=0,center_y=0;};
struct ApplicationUpdateServices {
    virtual ~ApplicationUpdateServices()=default;
    //472df0,446920,401fa0,4827d0,then4458a0. The first four are
    // non-thiscall entries;4458a0 receives the actual Application identity.
    virtual bool application_update_call(u32 entry,u32 owner,u32& result)=0;
};
//443740: application update before the remaining registered game callbacks.
bool update_application(AnmView app,ApplicationUpdateGlobals&,ApplicationUpdateServices&,i32& result);
}
