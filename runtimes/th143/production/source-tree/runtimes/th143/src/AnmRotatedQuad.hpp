#pragma once
#include "AnmQuad.hpp"
namespace th143 {
// 47b0b0 rotated quad XYZ builder, preserving all non-position vertex words.
bool anm_rotated_quad_position(AnmView,const AnmViewport&,AnmTransformHost&,AnmQuad&);
}
