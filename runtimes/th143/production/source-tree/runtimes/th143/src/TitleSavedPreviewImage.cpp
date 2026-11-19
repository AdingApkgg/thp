#include "TitleSavedPreviewImage.hpp"
#include "AnmTextureDefault.hpp"
#include "CheatAnimation.hpp"
#include "AnmSignal.hpp"
namespace th143 {
namespace {
u32 first(AnmView q){return signed_word(q.get(0x200))>0?q.get(0):0;}
void pop(AnmView q){if(signed_word(q.get(0x200))>0){q.put(0x200,q.get(0x200)-1);std::memmove(q.data,q.data+4,127*4);}}
bool tick(AnmView title,AnmResourceWorld& world){auto timer=title.sub(0x2b4);const u32 previous=timer.get(4),token=timer.get(12);float rate=1;if(token&&!world.timer_rate(token,rate))return false;timer.put(0,previous);const bool unit=!token||(rate>real(0x3f7d70a4)&&rate<real(0x3f8147ae));const float value=timer.floating(8)+(unit?1.f:rate);timer.put(8,word(value));timer.put(4,unit?previous+1:value>=-2147483648.f&&value<2147483648.f?u32(i32(value)):0x80000000);return true;}
bool signal_child(AnmView title,AnmResourceWorld& world,i32 signal){const u32 slot=0x2c8+title.get(0xe124)*4;if(slot+4>0xef78)return false;auto parent=world.find(title.get(slot));if(!parent.data){title.put(slot,0);return true;}auto child=find_animation_child(world,parent,98);return !child.data||signal_animation_vm(world,child,signal,true);}
}
bool GameTitleSavedPreviewImages::upload(u32 texture,u32 object){
    u8 header[0x78];if(!memory.read(object,header,sizeof header))return false;auto get16=[&](u32 at){return u32(header[at])|(u32(header[at+1])<<8);};u32 pixels;std::memcpy(&pixels,header+0x74,4);const u32 width=get16(0xc),height=get16(0xe);if(!width||!height||th11::u64(width)*height*4>0x4000000)return false;
    u32 surface;i32 status;if(!images.surface(texture,0,surface,status)||status<0)return false;auto found=images.images.find(surface);if(found==images.images.end())return false;auto& target=found->second.pixels;if(target.format!=21||target.width<288||target.height<336)return false;
    std::vector<u8> source(width*height*4);if(!memory.read(pixels,source.data(),source.size()))return false;AnmTexturePixels scaled;if(!filter_anm_texture_default(width,height,source.data(),source.size(),288,336,scaled))return false;for(u32 y=0;y<336;++y)std::memcpy(target.data.data()+y*target.width*4,scaled.data.data()+y*288*4,288*4);
    return notifications.texture_uploaded(surface,target)&&images.release(surface);
}
bool advance_title_scene_saved_pending(GameTitleRuntime& owner,AnmResourceWorld& world,GameTitleSavedPreviewImages& images,u32& result){
    auto title=owner.view();if(!owner.global_owner||title.get(0x1c)!=11||title.get(0x24)!=1||(title.get(0xe000)&0x21)||title.get(0x2b8)==10||signed_word(title.get(0x2b8))>=20||title.get(0xe940)||title.get(0xef58)>128)return false;
    for(u32 budget=0;title.get(0xef58);){if(++budget>128)return false;auto objects=title.sub(0xeb50),ids=title.sub(0xed58);const u32 object=first(objects);if(title.get(0xef58)==1){const u32 selection=title.get(0x28),day=title.get(0x1d8),wanted=(day-u32(signed_word(selection)/100)+1)*100+selection;if(first(ids)==wanted){bool valid=false;if(object){u8 header[10];if(!world.read(object,header,sizeof header))return false;const u32 header_day=u32(header[6])|(u32(header[7])<<8),header_scene=u32(header[8])|(u32(header[9])<<8);valid=header_day==day&&header_scene==selection-1;}
            if(valid){u32 table,texture;if(!world.read(title.get(0x14)+0x124,&table,4)||!world.read(table+0x30,&texture,4)||!images.upload(texture,object)||!images.preload(texture)||!signal_child(title,world,2))return false;}
            else if(!signal_child(title,world,57))return false;
        }}
        if(object){u32 pixels;if(!world.read(object+0x74,&pixels,4)||(pixels&&!world.release_enemy_storage(pixels,true))||!world.release_enemy_storage(object,true))return false;}pop(objects);pop(ids);
    }
    result=1;return tick(title,world)&&world.synchronize_resources();
}
}
