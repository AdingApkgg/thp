#pragma once
#include "AnmPositionedText.hpp"
#include "AnmResourceWorld.hpp"
#include "AnmTextureStore.hpp"
namespace th143 {
// GDI glyph generation is supplied by the platform; layout, CPU filters,
// persistent texture upload and surface ownership remain in the game runtime.
class GameAnmText final:public AnmTextHost {
public:
    GameAnmText(AnmResourceWorld& memory,AnmTextureStore& images,AnmTextureStoreDevice& device,TextRaster& raster,TextRasterHost& glyphs):memory(memory),images(images),device(device),raster(raster),glyph_provider(glyphs){}
    bool draw_literal(AnmView,const std::vector<u8>&,u32 foreground=0,u32 outline=0,i32 kind=0,i32 x=0,i32 pitch=0);
    bool read_text_memory(u32 p,void* out,u32 n)override{return memory.read(p,out,n);}
    bool text_texture(u32 token)override{texture=token;return images.images.find(token)!=images.images.end();}
    bool glyphs(const std::array<u8,108>& header,const TextFont& font,const std::vector<TextDraw>& draws,std::vector<u8>& bitmap)override{return glyph_provider.glyphs(header,font,draws,bitmap);}
    bool upload(const TextUpload&,const std::vector<u8>&)override;
private:
    AnmResourceWorld& memory;AnmTextureStore& images;AnmTextureStoreDevice& device;TextRaster& raster;TextRasterHost& glyph_provider;u32 texture=0;
};
}
