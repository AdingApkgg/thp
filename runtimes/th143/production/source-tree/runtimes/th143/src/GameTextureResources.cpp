#include "GameTextureResources.hpp"
namespace th143 {
bool GameTextureResources::create_animation_texture(const AnmTextureRequest& request,ResourceLoaderHost& memory,i32& result,u32& width,u32& height){return textures.create(request,memory,scale,backbuffer_format,result,width,height);}
}
