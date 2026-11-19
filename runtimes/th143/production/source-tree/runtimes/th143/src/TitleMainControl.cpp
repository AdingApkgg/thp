#include "TitleMainControl.hpp"
#include "AnmSignal.hpp"
namespace th143 {
namespace {
void clock(AnmView title){auto t=title.sub(0x2b4);if(!(t.get(16)&1)){t.put(16,t.get(16)|1);t.put(12,0x4e40b0);}t.put(0,0xffffffff);t.put(4,0);t.put(8,0);}
void substate(AnmView title,u32 value){title.put(0x24,value);clock(title);}
bool tick(AnmView title,AnmResourceWorld& world){auto timer=title.sub(0x2b4);const u32 previous=timer.get(4),token=timer.get(12);float rate=1;if(token&&!world.timer_rate(token,rate))return false;timer.put(0,previous);const bool unit=!token||(rate>real(0x3f7d70a4)&&rate<real(0x3f8147ae));const float value=timer.floating(8)+(unit?1.f:rate);timer.put(8,word(value));timer.put(4,unit?previous+1:value>=-2147483648.f&&value<2147483648.f?u32(i32(value)):0x80000000);return true;}
i32 signal_id(u32 value){const u16 v=u16(value);return v&0x8000?i32(v)-65536:i32(v);}
bool selection(AnmView title,AnmResourceWorld& world){return signal_animation(world,title.get(0x2c8),3,true)&&signal_animation(world,title.get(0x2c8),signal_id(title.get(0x28)+7),false)&&signal_animation(world,title.get(0x400),signal_id(title.get(0x28)+7),false);}
bool confirm(AnmView title,AnmResourceWorld& world,const TitleMainKeys& keys,TitleMainHost& host){
    if(!signal_animation(world,title.get(0x2c8),6,false)||!signal_animation(world,title.get(0x400),6,false))return false;
    const u32 choice=title.get(0x28);if(choice>6)return true;if(!host.title_sound(choice==6?9:7))return false;
    if(!choice&&!keys.started_before){if(!signal_animation(world,title.get(0x7f0),1,false))return false;substate(title,5);return true;}
    if(choice==0||choice==1||choice==2||choice==4||choice==5){if(!signal_animation(world,title.get(0x478),1,false))return false;title.put(0x478,0);if(!signal_animation(world,title.get(0x7f0),1,false))return false;}
    substate(title,4);return true;
}
}
bool advance_title_main_control(GameTitleRuntime& owner,AnmResourceWorld& world,const TitleMainKeys& keys,TitleMainHost& host,u32& result){
    auto title=owner.view();const u32 phase=title.get(0x24);if(!owner.global_owner||title.get(0x1c)!=1||(title.get(0xe000)&1)||(phase!=2&&phase!=4))return false;result=1;MenuCursor cursor{title.sub(0x28)};
    if(phase==2){
        cursor.begin();i32 ignored;if(((keys.fresh|keys.repeated)&0x10)&&!cursor.move(-1,ignored))return false;if(((keys.fresh|keys.repeated)&0x20)&&!cursor.move(1,ignored))return false;
        if(title.get(0x2c)!=title.get(0x28)&&(!host.title_sound(10)||!selection(title,world)))return false;
        bool cancel_exit=false;if(keys.fresh&0x102){if(!host.title_sound(9))return false;if(title.get(0x28)==6){substate(title,4);cancel_exit=true;}else if(!cursor.select(6)||!selection(title,world))return false;}
        if(!cancel_exit&&(keys.fresh&0x80001)&&!confirm(title,world,keys,host))return false;
    }else if(signed_word(title.get(0x2b8))>=20){
        const u32 choice=title.get(0x28);if(choice<=6){static constexpr i32 states[]={11,7,6,3,5,12,2};if(!select_title_state(owner,states[choice]))return false;if(choice!=3&&choice!=6&&!signal_animation(world,title.get(0x454),3,true))return false;if(choice!=6&&!cursor.push())return false;}
    }
    return tick(title,world)&&world.synchronize_resources();
}
}
