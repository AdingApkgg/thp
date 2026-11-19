#include "GameAnmText.hpp"
namespace th143 {
bool GameAnmText::draw_literal(AnmView vm,const std::vector<u8>& bytes,u32 foreground,u32 outline,i32 kind,i32 x,i32 pitch){return vm.data&&anm_positioned_text_literal(vm,raster,foreground,outline,kind,x,pitch,bytes.data(),bytes.size(),*this);}
bool GameAnmText::upload(const TextUpload& request,const std::vector<u8>& bitmap){
    const u32 bpp=anm_texture_pixel_bytes(request.format);if(!bpp||!request.stride||request.stride%bpp||bitmap.size()%request.stride)return false;u32 surface;i32 status;if(!images.surface(texture,0,surface,status)||status<0)return false;auto found=images.images.find(surface);if(found==images.images.end())return false;auto& target=found->second.pixels;
    return upload_anm_texture_region(target,request.destination,request.format,request.stride/bpp,bitmap.size()/request.stride,bitmap.data(),bitmap.size(),request.source,1,status)&&status>=0&&device.texture_uploaded(surface,target)&&images.release(surface);
}
}
