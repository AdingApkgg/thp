#pragma once
#include "AnmState.hpp"
#include <array>
namespace th143 {
struct ApplicationCameraConfig {u32 width=1280,height=960,flags=0;float scale=2.f;};
// 445200: pixel-aligned perspective camera matrices. Preserves all other bytes.
bool initialize_pixel_camera(AnmView camera);
// 445590: four application cameras at230/35c/488/5b4 plus the second ANM
// origin globals. The input owner spans at least6e0 bytes; unused bytes survive.
bool initialize_application_cameras(AnmView owner,const ApplicationCameraConfig&,std::array<i32,2>& second_origin);
}
