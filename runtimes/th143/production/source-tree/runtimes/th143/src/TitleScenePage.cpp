#include "TitleScenePage.hpp"
#include "CheatAnimation.hpp"
#include "AnmSignal.hpp"
namespace th143 {
namespace {
void clock(AnmView title,u32 value){auto t=title.sub(0x2b4);if(!(t.get(16)&1)){t.put(16,t.get(16)|1);t.put(12,0x4e40b0);}t.put(0,value-1);t.put(4,value);t.put(8,word(float(signed_word(value))));}
void phase(AnmView title,u32 value){title.put(0x24,value);clock(title,0);}
bool tick(AnmView title,AnmResourceWorld& world){auto timer=title.sub(0x2b4);const u32 previous=timer.get(4),token=timer.get(12);float rate=1;if(token&&!world.timer_rate(token,rate))return false;timer.put(0,previous);const bool unit=!token||(rate>real(0x3f7d70a4)&&rate<real(0x3f8147ae));const float value=timer.floating(8)+(unit?1.f:rate);timer.put(8,word(value));timer.put(4,unit?previous+1:value>=-2147483648.f&&value<2147483648.f?u32(i32(value)):0x80000000);return true;}
bool signal(AnmResourceWorld& world,u32 handle,i32 id){return signal_animation(world,handle,id,true);}
i32 short_signal(u32 n){const u16 v=u16(n);return v&0x8000?i32(v)-65536:i32(v);}
bool child_signal(AnmView title,AnmResourceWorld& world,u32 parent,i32 script,i32 id){const u32 slot=0x2c8+parent*4;if(slot+4>0xef78)return false;auto vm=world.find(title.get(slot));if(!vm.data){title.put(slot,0);return true;}auto child=find_animation_child(world,vm,script);return !child.data||signal_animation_vm(world,child,id,true);}
bool message(TitleScenePageBindings& b){auto& o=b.owners;auto title=o.title.view();const u32 token=title.get(0xdff0);if(token<GameTitleRuntime::self||token-GameTitleRuntime::self+0x20c>GameTitleRuntime::bytes)return false;auto row=title.sub(token-GameTitleRuntime::self);auto text=[&](u32 at){std::vector<u8> out;for(u32 i=0;i<256&&row.data[at+i];++i)out.push_back(row.data[at+i]);return out;};return show_title_dialog(o.title,o.world,b.dialog,text(8),text(0x108),1080.f,320.f,row.floating(0x208));}
bool enqueue_day(AnmView title){const u32 capacity=title.get(0xe32c);if(!capacity||capacity>128)return false;if(signed_word(title.get(0xe328))>=signed_word(capacity))title.put(0xe328,capacity-1);const u32 n=title.get(0xe328);if(n>=128)return false;title.put(0xe128+n*4,title.get(0x1d8));title.put(0xe328,n+1);title.put(0xe000,title.get(0xe000)|0x20u);return true;}
}
bool advance_title_scene_page(TitleScenePageBindings& b,const TitleMainKeys& keys,u32& result){
    auto& o=b.owners;auto& world=o.world;auto title=o.title.view(),save=o.save.view();if(!o.title.global_owner||title.get(0x1c)!=11||(title.get(0xe000)&1)||(title.get(0x24)!=1&&title.get(0x24)!=2)||title.get(0x1d8)>9)return false;
    if(title.get(0x24)==1){
        if(title.get(0x2b8)==10){const i32 id=signed_word(title.get(0x1dc))<signed_word(title.get(0x1d8))?50:49;if(!child_signal(title,world,114,i32(title.get(0x1d8)+135),id)||!signal(world,title.get(0x47c),id)||!signal(world,title.get(0x480),id)||!refresh_title_scene_choices(o.title,world,o.save))return false;}
        if(signed_word(title.get(0x2b8))>=20){const u32 day=title.get(0x1d8),parent=title.get(0xe124);if(!signal(world,title.get(0x454),short_signal(day+17))||!refresh_title_scene_selection(o.title,o.cheat,world,o.save)||!signal(world,title.get(0x490),3)||!signal(world,title.get(0x490),short_signal(day+27))||!signal(world,title.get(0x514),short_signal(title.get(0x28)+7))||!refresh_title_scene_choices(o.title,world,o.save)||!enqueue_day(title))return false;
            for(i32 i=88;i<98;++i)if(!child_signal(title,world,parent,i,5))return false;for(i32 i:{152,154,153,155})if(!child_signal(title,world,109,i,4))return false;if(!day)for(i32 i:{152,154})if(!child_signal(title,world,109,i,5))return false;if(signed_word(day)>=signed_word(title.get(0x1e0)-1))for(i32 i:{153,155})if(!child_signal(title,world,109,i,5))return false;
            const u32 count=title.get(0x5cec);if(count>64)return false;for(u32 i=0;i<count;++i)if(title.get(0x5cf0+i*0x20c)==day+1){title.put(0xdff0,GameTitleRuntime::self+0x5cf0+i*0x20c);break;}
            if(signed_word(save.get(0xf16c))<=0&&!title.get(0x28)&&!message(b))return false;phase(title,2);if(!signal(world,title.get(0x544),title.get(0x28)?3:2))return false;
        }
    }else if(signed_word(title.get(0x2b8))>=4){
        if(o.globals.trophy_owner||signed_word(save.get(0xf16c))>0)return false;const u32 pressed=keys.fresh|keys.repeated;title.put(0x2c,title.get(0x28));MenuCursor main{title.sub(0x28)},days{title.sub(0x1d8)};i32 moved;
        if((pressed&0x10)&&!main.move(-1,moved))return false;if((pressed&0x20)&&!main.move(1,moved))return false;
        if(title.get(0x28)&&(pressed&0x80)){if(!b.sound.title_sound(10))return false;phase(title,3);if(!signal(world,title.get(0x514),47)||!MenuCursor{o.cheat.view().sub(0x14)}.select(0))return false;set_cheat_state(o.cheat.view(),4);}
        else {
            bool leaving=false;if(keys.fresh&0x102){if(!b.sound.title_sound(9))return false;if(!title.get(0x28)){phase(title,6);leaving=true;}else if(!main.select(0))return false;}
            if(!leaving){if(title.get(0x2c)!=title.get(0x28)){if(!signal(world,title.get(0x544),title.get(0x28)?3:2))return false;if(!title.get(0x28)){if(!message(b))return false;}else if(!clear_title_dialog(o.title,world))return false;b.equipment[3]=b.saved_equipment[3]=title.get(0x28);if(!b.sound.title_sound(10)||!refresh_title_scene_selection(o.title,o.cheat,world,o.save))return false;}
                if(!title.get(0x28)){title.put(0x1dc,title.get(0x1d8));if((pressed&0x40)&&!days.move(-1,moved))return false;if((pressed&0x80)&&!days.move(1,moved))return false;if(title.get(0x1dc)!=title.get(0x1d8)){b.equipment[2]=b.saved_equipment[2]=title.get(0x1d8);if(!clear_title_dialog(o.title,world)||!b.sound.title_sound(10))return false;phase(title,1);const i32 id=signed_word(title.get(0x1dc))<signed_word(title.get(0x1d8))?47:48;if(!child_signal(title,world,114,i32(title.get(0x1dc)+135),id)||!signal(world,title.get(0x480),id)||!signal(world,title.get(0x47c),id))return false;}}
                if((keys.fresh&0x80001)&&signed_word(title.get(0x28))>=1){phase(title,4);if(!b.sound.title_sound(7))return false;}
            }
        }
    }
    result=1;return consume_title_scene_responses(o.title,world,b.png,b.saved)&&tick(title,world)&&world.synchronize_resources();
}
}
