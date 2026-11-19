#pragma once
#include "StageCamera.hpp"
namespace th143 {
using StageVector=std::array<float,3>;
using StageCorners=std::array<StageVector,16>;
// D3DXVec3ProjectArray's sixteen-vector SSE path, as called by 40e880.
void project_stage_corners(const StageCamera&,const StageVector& translation,const StageCorners&,StageCorners&);
struct StageVisibility {
    bool distance_rejected=false,projected=false,culled=false;
    StageCorners corners{},screen{};
    std::array<float,4> bounds{}; // minX,maxX,minY,maxY
};
// 40e880. Object is the raw0x1c STD object header; instance is its XYZ offset.
StageVisibility stage_object_visibility(AnmView object,const StageVector& instance,StageCamera&,float maximum_distance_squared,i32 origin_x,i32 origin_y);
}
