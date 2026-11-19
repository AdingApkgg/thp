#pragma once
#include "AnmState.hpp"
#include <array>

namespace th143 {
struct AnmViewport {
    float scale=1.f;
    std::array<i32,2> first_origin{},second_origin{};
};
struct AnmTransformHost {
    virtual ~AnmTransformHost()=default;
    virtual AnmView transform_parent(u32 token)=0;
};
// 431cd0 ->431af0, including inherited position, optional parent rotation,
// viewport scale and the two logical viewport origins.
bool anm_position(AnmView,const AnmViewport&,AnmTransformHost&,std::array<float,3>&,u32 budget=64);
}
