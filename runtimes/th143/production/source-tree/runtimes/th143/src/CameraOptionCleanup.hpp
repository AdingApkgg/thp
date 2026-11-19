#pragma once
#include "AnmWorld.hpp"
namespace th143 {
//459120, invoked by equipment cleanup before releasing the camera option.
bool cleanup_camera_option(AnmView option,AnmWorld&);
}
