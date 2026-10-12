#include "../../cpp/game/TextRaster.hpp"
#include "../../cpp/game/TextLayoutTh14.hpp"
#include "../../cpp/game/FontBitmapTh14.hpp"
#include <cstdlib>
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static TextRaster raster;
static TextureImage destination;
static char text[1025];
static u32 layout_words[8];
static FontBitmapTh14 bitmap;
static Rng visual;
API(initialize) const u8* initialize(u32 seed,u32 calls,u32 available){visual={u16(seed),0,calls};bitmap.initialize(visual,available!=0);return bitmap.noise.data();}
API(initial_state) u32 initial_state(u32 field){return field==0?visual.seed:field==1?visual.calls:bitmap.format;}
API(layout) const u32* layout(i32 mode,i32 height,float width,u32 length,u32 flags,u32 spacing,i32 offset,i32 font){
    const auto style=th14_text_style({offset,height,font,0x123456,0x654321,spacing},width,length,flags,mode==1,mode==2);
    layout_words[0]=style.height;layout_words[1]=style.color;layout_words[2]=style.outline;layout_words[3]=style.font;
    layout_words[4]=style.spacing;layout_words[5]=!style.plain;layout_words[6]=u32(style.offset);layout_words[7]=style.height<=8;
    return layout_words;
}
API(allocate) void* allocate(u32 size){return std::malloc(size);}
API(release) void release(void* p){std::free(p);}
API(load) u32 load(u32 slot,const u8* data,u32 size){return raster.glyphs.load(slot,data,size);}
API(text_input) char* text_input(){return text;}
API(draw) u32 draw(i32 font,i32 height,i32 offset,u32 color,u32 outline,u32 spacing,u32 plain){return raster.rasterize(text,{offset,height,font,color,outline,spacing,plain!=0});}
API(pixels) const u8* pixels(){return raster.scratch.pixels.data();}
API(write) const u8* write(u32 format){
    destination.width=520;destination.height=40;destination.pitch=520*(format?4:2);
    destination.format=format?touhou::graphics::PixelFormat::Bgra8:touhou::graphics::PixelFormat::Argb4444;
    destination.pixels.assign(destination.pitch*40,0xa5);
    if(!ImageResample::copy(destination,{4,3,516,35},raster.scratch,{0,0,512,32}))return nullptr;
    return destination.pixels.data();
}
