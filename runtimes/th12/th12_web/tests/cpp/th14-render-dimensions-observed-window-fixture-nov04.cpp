// Read-only access to the two identified render-dimension words.
#include "th14-observed-perspective-window-fixture-nov04.cpp"

API(render_dimensions_camera_word) u32 render_dimensions_camera_word(u32 index){
 if(index==22)return full_camera_sample.render_width;
 if(index==23)return full_camera_sample.render_height;
 return full_camera_word(index);
}
