#include "CameraOptionCleanup.hpp"
namespace th143 {
bool cleanup_camera_option(AnmView option,AnmWorld& world){
 for(u32 at=0x2c;at<0x40;at+=4){if(!world.mark_retirement(option.get(at)))return false;option.put(at,0);}return true;
}
}
