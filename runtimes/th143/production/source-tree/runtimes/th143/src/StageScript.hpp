#pragma once
#include "StageActivation.hpp"
#include "StageFog.hpp"

namespace th143 {
struct StageScriptGlobals {u32 render_option=0,error_pc=0,error_opcode=0;std::array<u32,21> executed{};};
// 40f320: STD instruction scheduling, camera/fog interpolation and shake.
// Opcode17 warp ownership and shake modes2..9 remain explicit unsupported
// paths; none occurs in the ten original day STD programs.
bool advance_stage_script(StageState&,u32 self,StageScriptGlobals&,StageAnimationMemory&,AnmVmHost&,u32 budget=4096);
}
