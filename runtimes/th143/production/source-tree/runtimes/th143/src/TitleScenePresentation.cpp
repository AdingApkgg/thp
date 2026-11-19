#include "TitleScenePresentation.hpp"
#include "CheatAnimation.hpp"
#include "AnmSignal.hpp"
namespace th143 {
namespace {
constexpr u32 starts[]={1,7,13,20,27,35,43,51,58,66},counts[]={6,6,7,7,8,8,8,7,8,10};
AnmView child(AnmView title,AnmResourceWorld& world,u32 parent,i32 script){const u32 slot=0x2c8+parent*4;if(slot+4>0xef78)return {nullptr};auto vm=world.find(title.get(slot));if(!vm.data){title.put(slot,0);return {nullptr};}return find_animation_child(world,vm,script);}
bool signal(AnmResourceWorld& world,u32 handle,i32 id){return signal_animation(world,handle,id,true);}
bool child_signal(AnmView title,AnmResourceWorld& world,u32 parent,i32 script,i32 id){auto vm=child(title,world,parent,script);return !vm.data||signal_animation_vm(world,vm,id,true);}
i32 short_signal(u32 n){const u16 v=u16(n);return v&0x8000?i32(v)-65536:i32(v);}
}
bool refresh_title_scene_choices(GameTitleRuntime& owner,AnmResourceWorld& world,SaveData& save){
    auto title=owner.view(),s=save.view();const u32 day=title.get(0x1d8);if(day>=10)return false;u32 available=counts[day];if((day==2&&!s.data[0xf088])||(day==4&&!s.data[0xf089])||(day==5&&!s.data[0xf08a])||(day==7&&!s.data[0xf08b]))available=1;
    title.put(0xfc,0);for(u32 i=0;i<10;++i){if(i>=available&&!MenuCursor{title.sub(0x28)}.disable(i32(i+1)))return false;for(u32 base:{115u,125u}){auto vm=child(title,world,110,i32(base+i));if(!vm.data)return false;vm.put(0x18,i<available?vm.get(0x18)|2:vm.get(0x18)&~2u);}}
    for(u32 i=0;i<counts[day];++i){const bool cleared=signed_word(s.get(0x40+(starts[day]+i)*0x314))>0;for(u32 row=0;row<2;++row){auto vm=child(title,world,110,i32(115+row*10+i));if(vm.data){const u32 sprite=(cleared?114u:92u)+row*11+i-((day==0&&i==0)?1:0);if(!anm_bind_sprite(vm,i32(sprite),static_cast<AnmWorld&>(world)))return false;}}}
    return world.synchronize_resources();
}
bool refresh_title_scene_selection(GameTitleRuntime& owner,GameCheatRuntime& cheat,AnmResourceWorld& world,SaveData& save){
    auto title=owner.view(),gear=cheat.view(),s=save.view();const u32 day=title.get(0x1d8),selection=title.get(0x28),parent=title.get(0xe124);if(day>=10||parent>217||selection>10)return false;
    const i32 selected=short_signal(selection+7);for(u32 handle:{title.get(0x480),title.get(0x2c8+parent*4),title.get(0x47c)})if(!signal(world,handle,3))return false;for(u32 handle:{title.get(0x480),title.get(0x2c8+parent*4),title.get(0x47c),title.get(0x514)})if(!signal(world,handle,selected))return false;
    const u32 index=gear.get(0x2b8);if(index>=9)return false;
    if(!selection){if(!signal(world,title.get(0x490),short_signal(day+7))||!signal(world,title.get(0x454),7)||!signal(world,gear.get(0x2c4+index*4),5)||!signal(world,gear.get(0x2d0),5))return false;}
    else {
        const u32 capacity=title.get(0xeb4c);if(!capacity||capacity>128)return false;if(signed_word(title.get(0xeb48))>=signed_word(capacity))title.put(0xeb48,capacity-1);const u32 n=title.get(0xeb48);if(n>=128)return false;title.put(0xe948+n*4,(day-u32(signed_word(selection)/100)+1)*100+selection);title.put(0xeb48,n+1);
        if(!signal(world,title.get(0x490),short_signal(day+27))||!signal(world,title.get(0x454),8)||!signal(world,gear.get(0x2c4+index*4),4)||!signal(world,gear.get(0x2d0),4))return false;
        const u32 record=0x18+(starts[day]+selection-1)*0x314;for(u32 i=0;i<10;++i){const i32 id=signed_word(s.get(record+i*4))>0?47:48;if(!child_signal(title,world,parent,i32(176+i),id)||(i<6&&!child_signal(title,world,parent,i32(170+i),id))||(i<3&&!child_signal(title,world,parent,i32(167+i),id)))return false;}
    }
    return world.synchronize_resources();
}
}
