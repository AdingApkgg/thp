#pragma once
#include "AnmInterpolation.hpp"
#include "Rng.hpp"

namespace th143 {
struct AnmVmHost : AnmTimerHost {
    virtual bool read(u32 token, void* output, u32 bytes) = 0;
    virtual bool write(u32, const void*, u32) { return false; }
    virtual bool sprite(u32 resource, i32 index, u32& token, std::array<u32, 17>& descriptor) = 0;
    virtual bool fallback_sprite(u32& resource, i32& index) { return false; }
    virtual bool bullet_style(u32 owner, i32& type, i32& color) { return false; }
    virtual bool parent_slowdown(u32 parent, float& value) { return false; }
    virtual bool paused() const { return false; }
    virtual bool translation(std::array<float, 3>& value) { return false; }
    virtual Rng* script_rng() { return nullptr; }
    // A readable resource can report a null script or unfinished loading;
    // those cases clear the target VM in original473de0.
    virtual bool script(u32 resource, i32 index, u32& token, u16& file, bool& ready) { return false; }
    virtual bool script_bound() { return false; }
    virtual bool effect(AnmView, i32 type) { return false; }
    virtual bool child(AnmView parent,i32 script,u32 flags){return false;}
    virtual bool detached_child(AnmView parent,i32 script){return false;}
    virtual AnmView parameter_child(AnmView parent,i32 script,bool detached){return {nullptr};}
    virtual bool allocate_geometry(u32 bytes,u32& token){return false;}
    virtual bool update_geometry(AnmView){return false;}
    // Host callbacks execute while the native global timer has this effective
    // rate. Nested instance creation must see it, then restore the caller rate.
    virtual bool callback(u32 entry, AnmView, float rate, i32& result) { return false; }
};
// 40c980 and 40cdb0. Reset preserves layer, pool index and child position.
void anm_reset(AnmView, u32 self_token);
void anm_construct(AnmView);
// 473a00 logical sprite state; GPU texture/render submission lives elsewhere.
bool anm_bind_sprite(AnmView, i32 index, AnmVmHost&);
// 473de0 binds without resetting the VM, executes time-zero instructions and
// increments the owner's binding count even when the script terminates.
bool anm_bind_script(AnmView, u32 resource, i32 index, AnmVmHost&);
// 474710 interpreter, checked against script43 history and all43 bullet births.
// Arithmetic/reference, position/color/rotation/scale, UV and template commands.
// Unsupported meaningful opcodes, callbacks, active geometry and variable kinds return -2. Angular,
// scale and UV velocities use the native bounded wrapping/update order.
i32 anm_step(AnmView, AnmVmHost&, u32 instruction_budget = 4096);
}
