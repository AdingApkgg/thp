#include "PauseMenuControl.hpp"
namespace th143 {
namespace {
void timer(AnmView t,u32 rate){if(!(t.get(16)&1)){t.put(12,rate);t.put(16,t.get(16)|1);}t.put(0,0xffffffff);t.put(4,0);t.put(8,0);}
bool tick(AnmView t,AnmWorld& w){const u32 old=t.get(4),token=t.get(12);float rate=1;if(token&&!w.timer_rate(token,rate))return false;t.put(0,old);const bool unit=!token||(rate>real(0x3f7d70a4)&&rate<real(0x3f8147ae));const float value=t.floating(8)+(unit?1.f:rate);t.put(8,word(value));t.put(4,unit?old+1:value>=-2147483648.f&&value<2147483648.f?u32(i32(value)):0x80000000);return true;}
struct Control {
    PauseMenu& menu;SaveData& save;GameOverGlobals& g;PauseMenuInput& keys;AnmWorld& w;AnmView hud;PauseControlHost& host;
    AnmView m(){return menu.view();}
    bool signal(u32 at,i32 id){return signal_animation(w,m().get(at),id);}
    bool child(i32 script,i32 id,bool immediate=false){auto parent=w.find(m().get(0x1e8));if(!parent.data){m().put(0x1e8,0);return true;}auto vm=find_animation_child(w,parent,script);return !vm.data||signal_animation(w,vm.get(0x540),id,immediate);}
    bool current(i32 offset=7){return signal(0x1e8,i32(std::int16_t(m().get(0x38)))+offset);}
    bool move(i32 offset){auto cursor=MenuCursor{m().sub(0x38)};cursor.begin();i32 ignored;if(((keys.fresh|keys.repeated)&0x10)&&!cursor.move(-1,ignored))return false;if(((keys.fresh|keys.repeated)&0x20)&&!cursor.move(1,ignored))return false;return m().get(0x3c)==m().get(0x38)||(current(offset)&&host.menu_sound(10));}
    bool escape(){if(!(keys.fresh&0x100))return true;MenuCursor c{m().sub(0x38)};if(!c.select(0)||!signal(0x1ec,1)||!signal(0x1e8,1))return false;menu.substate(4);return true;}
    bool opening(u32 sub){
        if(signed_word(m().get(0x14))<10)return true;auto cursor=MenuCursor{m().sub(0x38)};m().put(0x40,6);m().put(0x108,1);
        if(sub==2){for(i32 i:{0,3,4,2})if(!cursor.disable(i))return false;if(!cursor.select(1))return false;m().put(0x1fc,1);}
        else{
            if(sub==1){for(i32 i:{3,4,2})if(!cursor.disable(i))return false;}
            else{
                if(g.root_mode&&(!cursor.disable(2)||!cursor.disable(4)))return false;
                if(signed_word(keys.deaths)>0&&!cursor.disable(2))return false;
                const u32 unlock=keys.scene==13?0xf088:keys.scene==27?0xf089:keys.scene==35?0xf08a:0;
                if((g.game_flags&0xc00)==0xc00||(!g.root_mode&&unlock&&!save.data[unlock])){
                    if(!cursor.disable(2)||!cursor.disable(3)||!child(117,5,true)||!child(118,5,true))return false;
                }
            }
            if(!cursor.select(0))return false;m().put(0x1fc,0);
        }
        if(!current())return false;menu.substate(3);return true;
    }
    bool navigation(){
        auto cursor=MenuCursor{m().sub(0x38)};if(!move(7))return false;
        if(keys.fresh&0x80001){
            if(!host.menu_sound(7))return false;const u32 choice=m().get(0x38);
            if(choice==0){if(!signal(0x1ec,1)||!signal(0x1e8,1))return false;menu.substate(4);}
            else if(choice<=5){
                const i32 scripts[]={0,116,117,0,119,120};if(choice!=3&&!child(scripts[choice],6))return false;
                menu.substate(choice==1?(g.root_mode?4:5):choice==2?6:choice==3?11:choice==4?12:g.root_mode?4:5);
            }
            timer(m().sub(0x10),w.global_rate_token());
        }
        if(!m().get(0x1fc)&&(keys.fresh&0x200000)){
            if(!host.menu_sound(7)||!child(120,6))return false;menu.substate(4);if(!cursor.select(5)||!signal(0x1ec,1))return false;
        }
        if(keys.fresh&0x10000){if(!host.menu_sound(7)||!child(116,6))return false;menu.substate(4);if(!cursor.select(1))return false;}
        return m().get(0x1fc)||escape();
    }
    bool confirmation(){
        const i32 time=signed_word(m().get(0x14));if(time<20)return true;auto cursor=MenuCursor{m().sub(0x38)};
        if(time==20){if(!cursor.push())return false;m().put(0x40,2);m().put(0x108,1);if(!cursor.select(1)||!signal(0x1e8,14))return false;}
        if(time<30)return true;if(time==30&&!current(15))return false;if(!move(15))return false;
        if(keys.fresh&0x80001){const u32 choice=m().get(0x38);if(choice==1){if(!child(128,6))return false;menu.substate(7);if(!host.menu_sound(9))return false;}
            else if(!choice){if(!child(127,6))return false;const u32 sub=m().get(0x3ec);menu.substate(sub==6?8:7);if(!host.menu_sound(7))return false;}
            timer(m().sub(0x10),w.global_rate_token());}
        if(keys.fresh&0x102){if(!host.menu_sound(9))return false;const u32 choice=m().get(0x38);if(choice==1){if(!child(128,6))return false;menu.substate(7);}else if(!choice){if(!cursor.select(1)||!current(15))return false;}}
        return escape();
    }
    bool closing(){
        if(signed_word(m().get(0x14))<12)return true;menu.state(0);const u32 choice=m().get(0x38);
        if(choice==0)return resume_pause_menu(menu,g,w,hud,host);
        if(choice==1||choice==5){if(!signal(0x1ec,1)||!signal(0x1e8,1))return false;g.application_state=choice==1?(g.config&0x2000?2:4):g.root_mode?11:10;}
        return true;
    }
    bool confirm_close(){
        const u32 choice=m().get(0x38),time=m().get(0x14);auto cursor=MenuCursor{m().sub(0x38)};
        if(!choice){if(time==2&&!host.pause_exit_fade())return false;if(signed_word(time)<26)return true;if(!signal(0x1e8,1))return false;menu.substate(4);cursor.pop();timer(m().sub(0x10),w.global_rate_token());}
        else if(choice==1&&signed_word(time)>=20){cursor.pop();if(!current())return false;menu.substate(3);timer(m().sub(0x10),w.global_rate_token());}return true;
    }
    bool body(){const u32 sub=m().get(0x3ec);if(sub<=2)return opening(sub);if(sub==3)return navigation();if(sub==4)return closing();if(sub==5||sub==6)return confirmation();if(sub==7)return confirm_close();if(sub<=12)return host.other_substate(menu,sub);return true;}
};
}
bool begin_pause_menu(PauseMenu& menu,SaveData& save,GameOverGlobals& g,AnmWorld& world,AnmOverlay& overlay,AnmView hud,PauseControlHost& host){
    if(!game_statistics_time(save,g,host))return false;auto m=menu.view();menu.state(1);timer(m.sub(0x24),world.global_rate_token());m.put(0x10c,0);g.root_flags|=0x10;m.put(0x91c0,hud.get(0x2ac));u32 handle;
    world.rate=g.rate;if(!overlay.create(world,m.get(0x91c0),g.root_mode?105:104,nullptr,0,-1,4,handle))return false;m.put(0x1e8,handle);if(g.root_mode)menu.substate(1);
    if(!signal_animation(world,handle,3)||!host.pause_audio()||!host.sound_and_flush(14))return false;m.put(0x91bc,m.get(0x91bc)|1);
    if(!overlay.create(world,g.text_resource,58,nullptr,0,-1,4,handle))return false;m.put(0x1ec,handle);m.put(0x2d8,word(g.rate));g.rate=1;world.rate=1;m.put(0x200,g.presentation);g.presentation=0;
    return !hud.get(0x198)||host.pause_message_owner(hud.get(0x198),true);
}
bool resume_pause_menu(PauseMenu& menu,GameOverGlobals& g,AnmWorld& world,AnmView hud,PauseControlHost& host){
    double now;if(!g.clock.sample(host,now))return false;g.statistics_time=now;g.root_flags&=~0x10u;if(!host.resume_pause_audio())return false;g.rate=menu.view().floating(0x2d8);world.rate=g.rate;
    if(hud.get(0x198)&&!host.pause_message_owner(hud.get(0x198),false))return false;g.presentation=menu.view().get(0x200);return true;
}
i32 pause_menu_frame(PauseMenu& menu,SaveData& save,GameOverGlobals& g,PauseMenuInput& keys,AnmWorld& world,AnmOverlay& overlay,AnmView hud,PauseControlHost& host){
    auto m=menu.view();world.rate=g.rate;
    if(m.get(0x3e4)==0){if(!(g.game_flags&0x80)&&!hud.get(0x198)&&((keys.fresh&0x100)||(g.config&0x10))&&keys.root_update_enabled&&keys.root_time>=45){if(!begin_pause_menu(menu,save,g,world,overlay,hud,host))return -2;}}
    else if(m.get(0x3e4)==1){Control c{menu,save,g,keys,world,hud,host};if(!c.body())return -2;}
    else return failure_menu_frame(menu,save,g,keys,world,overlay,hud,host);
    return tick(m.sub(0x10),world)&&tick(m.sub(0x24),world)?1:-2;
}
}
