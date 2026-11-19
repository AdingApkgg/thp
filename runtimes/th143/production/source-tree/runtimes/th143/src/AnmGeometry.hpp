#pragma once
#include "AnmState.hpp"
#include <array>
#include <vector>

namespace th143 {
struct AnmGeometryContext {
    std::array<float,3> position{};
    std::array<float,2> parent_scale{1.f,1.f};
    float viewport_scale=1.f;
};
// 477c60 CPU vertex generation. Position431cd0 is a separate transform;
// the context supplies its result and the parent's declared scale fields.
// Buffer storage belongs to the animation instance, including untouched bytes.
bool anm_geometry(AnmView,std::vector<u8>& buffer,const AnmGeometryContext&);
}
