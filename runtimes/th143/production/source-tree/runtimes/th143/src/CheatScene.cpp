#include "CheatScene.hpp"
namespace th143 {
namespace {
bool select(AnmView s,i32 value){
    const i32 count=signed_word(s.get(8));
    if(count){if(value>=count)value=count-1;else if(value<0)value=0;}
    s.put(0,u32(value));
    if(!count)return true;
    // Original loops indefinitely if every entry is disabled. Reject that
    // malformed selector rather than hanging the portable event loop.
    for(u32 budget=0;budget<100000;++budget){
        const i32 disabled=signed_word(s.get(0xd4));if(disabled>16)return false;
        bool found=false;
        for(i32 i=0;i<disabled;++i)if(s.get(0x90+u32(i)*4)==s.get(0)){found=true;break;}
        if(!found)return true;
        u32 next=s.get(0)+1;if(signed_word(next)>=count)next=0;s.put(0,next);
    }return false;
}
bool exclude(AnmView s,u32 value){
    const u32 n=s.get(0xd4);if(n>=16)return false;s.put(0x90+n*4,value);s.put(0xd4,n+1);
    // 4385a0 only checks disabled entries; it does not clamp the selection.
    for(u32 budget=0;budget<100000;++budget){
        bool found=false;for(u32 i=0;i<=n;++i)if(s.get(0x90+i*4)==s.get(0)){found=true;break;}
        if(!found)return true;u32 next=s.get(0)+1;if(signed_word(next)>=signed_word(s.get(8)))next=0;s.put(0,next);
    }return false;
}
}
void construct_cheat_owner(AnmView owner){std::memset(owner.data,0,0x498);owner.put(0,2);}
void set_cheat_state(AnmView owner,i32 state){
    owner.put(0x2b0,u32(state));const u32 flags=owner.get(0x2ac);
    if(!(flags&1)){owner.put(0x2a8,0x4e40b0);owner.put(0x2ac,flags|1);}
    owner.put(0x29c,0xffffffff);owner.put(0x2a0,0);owner.put(0x2a4,0);
}
bool position_cheat_scene(AnmView owner,AnmWorld& world){
    const u32 index=owner.get(0x2b8);if(index>8)return false;
    for(u32 at:{0x2c4+index*4,0x2d0u,0x2f8u}){
        auto vm=world.find(owner.get(at));if(!vm.data)continue;
        for(u32 i=0;i<3;++i)vm.put(0x59c+i*4,owner.get(0x484+i*4));
    }return true;
}
bool begin_cheat_scene(AnmView owner,i32 mode,const CheatSceneGlobals& g,AnmWorld& world,AnmOverlay& overlay){
    if(g.primary>8||g.secondary>8)return false;
    if(!select(owner.sub(0x14),0)||!select(owner.sub(0xec),0)||!select(owner.sub(0x1c4),0))return false;
    owner.put(0xf4,9);owner.put(0x1cc,9);set_cheat_state(owner,1);owner.put(0x2b4,u32(mode));owner.put(0x494,g.alternate);
    if(g.menu_present&&!g.menu_state&&mode==3){
        if(g.scene==35&&!g.scene35_record)owner.put(0x494,0);
        mode=1;owner.put(0x2b4,1);
    }
    owner.put(0x1c,1+(owner.get(0x494)!=0));
    if(!select(owner.sub(0xec),signed_word(g.selection[g.primary]))||!select(owner.sub(0x1c4),signed_word(g.selection[g.secondary])))return false;
    owner.put(0x1c0,0);owner.put(0x298,0);owner.put(0x1bc,1);owner.put(0x294,1);
    const u32 index=mode==1?0:g.unlock==0?1:g.unlock==1?2:0;
    owner.put(0x2b8,index);
    if(!create_cheat_animation(owner,index,world,overlay))return false;
    if(index){
        for(u32 at:{0xecu,0x1c4u})for(u32 i=0;i<9;++i)
            if(index==1?(i==1||i==2||i==4||i==5||i==7||i==8):(i==2||i==5||i==8))
                if(!exclude(owner.sub(at),i))return false;
    }
    return !owner.get(0x2b0)||position_cheat_scene(owner,world);
}
bool return_cheat_scene(AnmView owner){if(!select(owner.sub(0x14),0))return false;set_cheat_state(owner,4);return true;}
bool end_cheat_scene(AnmView owner,AnmWorld& world,AnmSignalHost* callbacks){
    const u32 index=owner.get(0x2b8);if(index>8)return false;
    for(u32 at:{0x2c4+index*4,0x2d0u}){
        if(!signal_animation(world,owner.get(at),1,false,callbacks))return false;owner.put(at,0);
    }
    set_cheat_state(owner,0);
    for(u32 at:{0x308u,0x30cu}){
        if(!signal_animation(world,owner.get(at),1,false,callbacks))return false;owner.put(at,0);
    }return true;
}
}
