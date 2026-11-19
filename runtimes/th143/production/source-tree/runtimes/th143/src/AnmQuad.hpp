#pragma once
#include "AnmTransform.hpp"
namespace th143 {
struct AnmQuad {
    std::array<std::array<u8,28>,4> vertices{};
};
// 47aae0 position builder. Writes XYZ only, preserving RHW/color/UV words.
// The final Z is the local VM's raw Z, after inherited XY placement.
bool anm_quad_position(AnmView,const AnmViewport&,AnmTransformHost&,AnmQuad&);
}
