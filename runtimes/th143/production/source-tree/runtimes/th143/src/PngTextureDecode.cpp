#include "PngTextureDecode.hpp"
#define STB_IMAGE_IMPLEMENTATION
#define STBI_ONLY_PNG
#define STBI_NO_STDIO
#define STBI_NO_HDR
#define STBI_NO_LINEAR
#define STBI_MAX_DIMENSIONS 16384
#include "../third_party/stb_image.h"
namespace th143 {
bool decode_png_texture(const u8* source,u32 bytes,AnmTexturePixels& output){
    if(!source||bytes<8||bytes>0x7fffffff||std::memcmp(source,"\x89PNG\r\n\x1a\n",8))return false;int width=0,height=0,channels=0;if(!stbi_info_from_memory(source,int(bytes),&width,&height,&channels)||width<=0||height<=0||std::uint64_t(width)*u32(height)*4>0x10000000)return false;
    auto* rgba=stbi_load_from_memory(source,int(bytes),&width,&height,&channels,4);if(!rgba)return false;AnmTexturePixels decoded;decoded.format=21;decoded.width=u32(width);decoded.height=u32(height);decoded.data.resize(u32(width)*u32(height)*4);
    for(u32 p=0;p<decoded.data.size();p+=4){decoded.data[p]=rgba[p+2];decoded.data[p+1]=rgba[p+1];decoded.data[p+2]=rgba[p];decoded.data[p+3]=rgba[p+3];}stbi_image_free(rgba);output=std::move(decoded);return true;
}
}
