#pragma once
#include "StageProjection.hpp"
#include "Matrix4.hpp"
namespace th143 {
// D3DXVec3Project scalar path: world/view/projection combination, paired SSE
// coordinate sums and reference-CPU reciprocal; viewport conversion is last.
StageVector project_stage_point(AnmView camera,const Matrix4& world,const StageVector&);
}
