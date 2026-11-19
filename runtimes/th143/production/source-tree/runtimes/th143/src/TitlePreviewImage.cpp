#include "TitlePreviewImage.hpp"
#include "PngTextureDecode.hpp"
#include "AnmTextureBleed.hpp"
namespace th143 {
namespace {
u32 first(AnmView q){return signed_word(q.get(0x200))>0?q.get(0):0;}
void pop(AnmView q){if(signed_word(q.get(0x200))>0){q.put(0x200,q.get(0x200)-1);std::memmove(q.data,q.data+4,127*4);}}
bool tick(AnmView title,AnmResourceWorld& world){auto timer=title.sub(0x2b4);const u32 previous=timer.get(4),token=timer.get(12);float rate=1;if(token&&!world.timer_rate(token,rate))return false;timer.put(0,previous);const bool unit=!token||(rate>real(0x3f7d70a4)&&rate<real(0x3f8147ae));const float value=timer.floating(8)+(unit?1.f:rate);timer.put(8,word(value));timer.put(4,unit?previous+1:value>=-2147483648.f&&value<2147483648.f?u32(i32(value)):0x80000000);return true;}
}
bool GameTitlePreviewImages::upload_png(u32 texture,u32 source,u32 bytes){
    u32 surface;i32 status;if(!images.surface(texture,0,surface,status)||status<0)return false;auto found=images.images.find(surface);if(found==images.images.end())return false;
    std::vector<u8> encoded(bytes);if(bytes&&!memory.read(source,encoded.data(),bytes))return false;AnmTexturePixels decoded;
    if(decode_png_texture(encoded.data(),bytes,decoded)){auto& target=found->second.pixels;if(!upload_anm_texture_region(target,{0,0,i32(target.width),i32(target.height)},21,decoded.width,decoded.height,decoded.data.data(),decoded.data.size(),{0,0,i32(decoded.width),i32(decoded.height)},1,status)||status<0||!notifications.texture_uploaded(surface,target))return false;}
    if(!images.release(surface)||!images.surface(texture,0,surface,status)||status<0)return false;found=images.images.find(surface);if(found==images.images.end())return false;auto& target=found->second.pixels;const u32 pitch=target.width*anm_texture_pixel_bytes(target.format);
    return bleed_anm_texture_alpha(target.format,target.width,target.height,pitch,target.data.data(),target.data.size())&&notifications.texture_uploaded(surface,target)&&images.release(surface);
}
bool advance_title_scene_png_pending(GameTitleRuntime& owner,AnmResourceWorld& world,GameTitlePreviewImages& images,u32& result){
    auto title=owner.view();if(!owner.global_owner||title.get(0x1c)!=11||title.get(0x24)!=1||(title.get(0xe000)&0x21)||title.get(0x2b8)==10||signed_word(title.get(0x2b8))>=20||title.get(0xef58)||title.get(0xe940)>128)return false;
    for(u32 budget=0;title.get(0xe940);){if(++budget>128)return false;auto data=title.sub(0xe330),sizes=title.sub(0xe538),ids=title.sub(0xe740);if(title.get(0xe940)==1){u32 table;if(!world.read(title.get(0x14)+0x124,&table,4))return false;u32 texture,flags;if(!world.read(table+0x18,&texture,4)||!world.read(table+0x2c,&flags,4))return false;flags&=~1u;const u32 bytes=first(sizes),kind=2;if(!world.write(table+0x2c,&flags,4)||!world.write(table+0x20,&bytes,4)||!images.upload_png(texture,first(data),bytes)||!world.write(table+0x24,&kind,4)||!images.preload(texture))return false;}
        if(signed_word(data.get(0x200))>0&&data.get(0)&&!world.release_enemy_storage(first(data),true))return false;pop(data);pop(sizes);pop(ids);
    }
    result=1;return tick(title,world)&&world.synchronize_resources();
}
}
