#pragma once
#include "ScalarInterpolation.hpp"
#include <array>
namespace th143 {
struct EclVariableTweens {
 std::array<u8,0x180> scalars{};
 std::array<Instruction*,8> origins{};
 void initialize(u8 fill=0);
 i32 command(Vm&,VmHost&,AnmTimerHost&);
 bool advance(Vm&,VmHost&,AnmTimerHost&);
};
}
