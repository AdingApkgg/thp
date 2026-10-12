#include "../../cpp/game/AnmResource.hpp"
#include "../../cpp/game/TextureImage.hpp"
#include <cstdlib>
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static AnmResource resource;
static TextureImage image;
API(allocate) u8* allocate(u32 size){return static_cast<u8*>(std::malloc(size));}
API(release) void release(void* p){std::free(p);}
API(open) u32 open(const u8* data,u32 size){return resource.open(data,size);}
API(load) u32 load(u32 index){return index<resource.textures.size()&&image.load(resource.textures[index]);}
API(width) u32 width(){return image.width;}
API(height) u32 height(){return image.height;}
API(pitch) u32 pitch(){return image.pitch;}
API(format) u32 format(){return u32(image.format);}
API(packed_format) u32 packed_format(){return image.packed_format;}
API(size) u32 size(){return image.pixels.size();}
API(data) const u8* data(){return image.pixels.data();}
API(error) const char* error(){return image.failure.c_str();}
