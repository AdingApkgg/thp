#include "FailureMenu.hpp"

namespace th143 {
namespace {
bool signal_one(AnmWorld& world,AnmView vm,i32 signal,bool immediate){
    if(vm.get(0x5c4)){
        if(vm.get(0x5c4)!=0x408230)return false;
        bool found=false;for(auto& e:world.extras)if(e->token==vm.get(0x5b4)){if(!anm_effect7_signal(e->data.data(),signal,world))return false;found=true;break;}if(!found)return false;
    }
    vm.put(0x4a0,u32(signal));return !immediate||anm_step(vm,world)!=-2;
}
bool signal(AnmWorld& world,u32 handle,i32 value,bool immediate=false){
    auto vm=world.find(handle);if(!vm.data)return true;if(!signal_one(world,vm,value,immediate))return false;if(vm.get(0x588))return true;
    u32 child=vm.get(0x584),budget=0;
    while(child){auto i=world.instances.registry.nodes.find(child-0x580);if(i==world.instances.registry.nodes.end()||++budget>world.states.size())return false;
        if(!signal_one(world,i->second,value,immediate))return false;child=i->second.get(0x584);
    }return true;
}
bool child_handle(AnmWorld& world,u32& parent,i32 id,u32& result){
    auto vm=world.find(parent);result=0;if(!vm.data){parent=0;return true;}
    u32 node=vm.get(0x584),budget=0;
    while(node){auto i=world.instances.registry.nodes.find(node-0x580);if(i==world.instances.registry.nodes.end()||++budget>world.states.size())return false;
        std::int16_t name;std::memcpy(&name,i->second.data+0x4aa,2);if(name==id){result=i->second.get(0x540);return true;}node=i->second.get(0x584);
    }return true;
}
bool child_signal(PauseMenu& menu,AnmWorld& world,i32 id,i32 value,bool immediate){
    u32 parent=menu.view().get(0x1e8),child=0;if(!child_handle(world,parent,id,child))return false;menu.view().put(0x1e8,parent);return signal(world,child,value,immediate);
}
bool tick(AnmView timer,AnmWorld& world){
    const u32 token=timer.get(12),old=timer.get(4);float rate=1;if(token&&!world.timer_rate(token,rate))return false;
    const bool unit=!token||(rate>real(0x3f7d70a4)&&rate<real(0x3f8147ae));const float value=timer.floating(8)+(unit?1.f:rate);
    timer.put(0,old);timer.put(8,word(value));timer.put(4,unit?old+1:value>=-2147483648.f&&value<2147483648.f?u32(i32(value)):0x80000000);return true;
}
bool opening(PauseMenu& menu,SaveData& save,GameOverGlobals& g,FailureMenuGlobals& keys,AnmWorld& world,AnmOverlay& overlay,AnmView hud,FailureMenuHost& host){
    auto m=menu.view();if(signed_word(m.get(0x14))<10)return true;
    hud.put(0x144,keys.score);if(keys.high_score<keys.score)keys.high_score=keys.score;
    if(keys.scene>=77)return false;auto record=save.view().sub(8+keys.scene*0x314);if(record.get(0x68)<keys.score)record.put(0x68,keys.score);m.put(0x1f8,1);
    const u32 count=m.get(0xfa4);if(count>64)return false;u32 total=0;
    for(u32 i=0;i<count;++i)if(i32(save.data[0xefac])>=signed_word(m.get(0xfa8+i*0x208)))total+=m.get(0xfac+i*0x208);
    if(!total)return false;u32 pick=world.animation_rng.next32()%total,index=0;
    for(;index<count;++index){const u32 at=0xfa8+index*0x208;if(i32(save.data[0xefac])<signed_word(m.get(at)))continue;const u32 weight=m.get(at+4);if(signed_word(pick)<signed_word(weight))break;pick-=weight;}
    if(index>=count)return false;const u32 at=0xfa8+index*0x208;m.put(0x91a8,menu.self+at);
    const bool special=(g.game_flags&0xc00)==0xc00;
    if(!special){for(u32 i=0;i<2;++i){u32 handle=m.get(0x3f8+i*4);if(!world.find(handle).data){handle=0;m.put(0x3f8+i*4,0);}if(!host.hint_text(handle,m.data+at+8+i*256))return false;}}
    u32 handle;if(!overlay.create(world,m.get(0x91c0),m.get(0x91b0)?108:107,nullptr,0,-1,4,handle))return false;m.put(0x1e8,handle);menu.substate(1);
    m.put(0x40,5);m.put(0x108,1);MenuCursor cursor{m.sub(0x38)};
    if(signed_word(keys.deaths)>0&&!cursor.disable(2))return false;
    bool restricted=special;
    if(!special&&g.root_mode==0){const u32 unlock=keys.scene==13?0xf088:keys.scene==27?0xf089:keys.scene==35?0xf08a:0;restricted=unlock&&!save.data[unlock];}
    if(restricted){if(!cursor.disable(2)||!cursor.disable(3)||!child_signal(menu,world,133,5,true)||!child_signal(menu,world,134,5,true))return false;}
    if(signed_word(keys.retry_credits)<=0&&!cursor.disable(0))return false;
    if(!cursor.select(signed_word(keys.retry_credits)>0?0:1)||!signal(world,handle,3))return false;
    return signal(world,handle,i32(std::int16_t(m.get(0x38)))+7);
}
bool navigation(PauseMenu& menu,FailureMenuGlobals& keys,AnmWorld& world,FailureMenuHost& host){
    auto m=menu.view();MenuCursor cursor{m.sub(0x38)};cursor.begin();i32 ignored;
    if(((keys.fresh|keys.repeated)&0x10)&&!cursor.move(-1,ignored))return false;
    if(((keys.fresh|keys.repeated)&0x20)&&!cursor.move(1,ignored))return false;
    if(m.get(0x3c)!=m.get(0x38)){if(!signal(world,m.get(0x1e8),i32(std::int16_t(m.get(0x38)))+7)||!host.menu_sound(10))return false;}
    if(keys.fresh&0x80001){
        if(!child_signal(menu,world,i32(m.get(0x38)+131),6,false)||!host.menu_sound(7))return false;
        menu.substate(2); //447680 again updates the visible score/high score.
        // Caller applied447680 during opening; refresh both on confirmation.
        if(m.get(0x38)==2){menu.substate(7);if(!world.flag(m.get(0x1e8),false)||!cursor.push())return false;m.put(0x40,25);m.put(0x108,1);if(!cursor.select(0))return false;return host.other_substate(menu,7);}
        if(m.get(0x38)==1){menu.substate(2);if(!host.menu_sound(7))return false;}
        else if(m.get(0x38)==3){menu.substate(10);if(!host.menu_sound(7))return false;}
        else if(m.get(0x38)==4)menu.substate(11);
    }
    if(keys.fresh&0x102){if(!host.menu_sound(9))return false;if(m.get(0x38)!=1){if(!cursor.select(1)||!signal(world,m.get(0x1e8),i32(std::int16_t(m.get(0x38)))+7))return false;}}
    return true;
}
bool closing(PauseMenu& menu,GameOverGlobals& g,AnmWorld& world,FailureMenuHost& host){
    auto m=menu.view();const u32 choice=m.get(0x38),time=m.get(0x14);const bool fade=choice==1||choice==2;
    if(time==2&&fade){if(!host.other_substate(menu,2))return false;}
    if(signed_word(time)<(fade?38:12))return true;
    double now;if(!g.clock.sample(host,now))return false;g.statistics_time=now;
    for(u32 at:{0x1ec,0x1e8,0x3f8,0x3fc,0x400})if(!signal(world,m.get(at),1))return false;
    g.rate=m.floating(0x2d8);world.rate=g.rate;m.put(0x3e4,4);
    if(choice==0)g.application_state=10;else if(fade)g.application_state=(g.config&0x2000)?2:4;return true;
}
}
i32 failure_menu_frame(PauseMenu& menu,SaveData& save,GameOverGlobals& g,FailureMenuGlobals& keys,AnmWorld& world,AnmOverlay& overlay,AnmView hud,FailureMenuHost& host){
    auto m=menu.view();world.rate=g.rate;
    if(m.get(0x3e4)<=3){
        if(m.get(0x3e4)==0){
            // 447dc5: the idle menu still advances both timers. A real pause
            // request needs 44b960/448290, which is a separate menu service.
            if(!(g.game_flags&0x80)&&!hud.get(0x198)&&((keys.fresh&0x100)||(g.config&0x10)))return -2;
            return tick(m.sub(0x10),world)&&tick(m.sub(0x24),world)?1:-2;
        }
        if(m.get(0x3e4)!=2)return -2;const u32 sub=m.get(0x3ec);bool okay;
        if(sub==0)okay=opening(menu,save,g,keys,world,overlay,hud,host);
        else if(sub==1){okay=navigation(menu,keys,world,host);if(keys.fresh&0x80001){hud.put(0x144,keys.score);if(keys.high_score<keys.score)keys.high_score=keys.score;}}
        else if(sub==2)okay=closing(menu,g,world,host);
        else if(sub<=6)okay=true;else okay=host.other_substate(menu,sub);
        if(!okay)return -2;
    }
    return tick(m.sub(0x10),world)&&tick(m.sub(0x24),world)?1:-2;
}
}
