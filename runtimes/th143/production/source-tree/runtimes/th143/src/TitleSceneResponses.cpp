#include "TitleSceneResponses.hpp"
#include "CheatAnimation.hpp"
#include "AnmSignal.hpp"
namespace th143 {
namespace {
u32 first(AnmView q){return signed_word(q.get(0x200))>0?q.get(0):0;}
void pop(AnmView q){if(signed_word(q.get(0x200))>0){q.put(0x200,q.get(0x200)-1);std::memmove(q.data,q.data+4,127*4);}}
bool child_signal(AnmView title,AnmResourceWorld& world,i32 script,i32 signal){const u32 slot=0x2c8+title.get(0xe124)*4;if(slot+4>0xef78)return false;auto parent=world.find(title.get(slot));if(!parent.data){title.put(slot,0);return true;}auto child=find_animation_child(world,parent,script);return !child.data||signal_animation_vm(world,child,signal,true);}
}
bool consume_title_scene_responses(GameTitleRuntime& owner,AnmResourceWorld& world,GameTitlePreviewImages& png,GameTitleSavedPreviewImages& saved){
    auto title=owner.view();if(title.get(0xe940)>128||title.get(0xef58)>128)return false;
    for(u32 budget=0;title.get(0xe940);){if(++budget>128)return false;auto data=title.sub(0xe330),sizes=title.sub(0xe538),ids=title.sub(0xe740);if(title.get(0xe940)==1){u32 table,texture,flags;if(!world.read(title.get(0x14)+0x124,&table,4)||!world.read(table+0x18,&texture,4)||!world.read(table+0x2c,&flags,4))return false;flags&=~1u;const u32 bytes=first(sizes),kind=2;if(!world.write(table+0x2c,&flags,4)||!world.write(table+0x20,&bytes,4)||!png.upload_png(texture,first(data),bytes)||!world.write(table+0x24,&kind,4)||!png.preload(texture))return false;}
        if(first(data)&&!world.release_enemy_storage(first(data),true))return false;pop(data);pop(sizes);pop(ids);
    }
    if((title.get(0xe000)&0x20)&&!title.get(0xe328)&&!title.get(0xe940)){for(i32 i=88;i<98;++i)if(!child_signal(title,world,i,4))return false;title.put(0xe000,title.get(0xe000)&~0x20u);}
    for(u32 budget=0;title.get(0xef58);){if(++budget>128)return false;auto objects=title.sub(0xeb50),ids=title.sub(0xed58);const u32 object=first(objects);if(title.get(0xef58)==1){const u32 selection=title.get(0x28),day=title.get(0x1d8),wanted=(day-u32(signed_word(selection)/100)+1)*100+selection;if(first(ids)==wanted){bool valid=false;if(object){u8 header[10];if(!world.read(object,header,sizeof header))return false;valid=(u32(header[6])|(u32(header[7])<<8))==day&&(u32(header[8])|(u32(header[9])<<8))==selection-1;}
            if(valid){u32 table,texture;if(!world.read(title.get(0x14)+0x124,&table,4)||!world.read(table+0x30,&texture,4)||!saved.upload(texture,object)||!saved.preload(texture)||!child_signal(title,world,98,2))return false;}else if(!child_signal(title,world,98,57))return false;
        }}if(object){u32 pixels;if(!world.read(object+0x74,&pixels,4)||(pixels&&!world.release_enemy_storage(pixels,true))||!world.release_enemy_storage(object,true))return false;}pop(objects);pop(ids);
    }
    return world.synchronize_resources();
}
}
