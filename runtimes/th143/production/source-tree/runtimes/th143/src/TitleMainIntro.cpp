#include "TitleMainIntro.hpp"
#include "AnmSignal.hpp"
namespace th143 {
namespace {
void clock(AnmView title,u32 value){auto t=title.sub(0x2b4);if(!(t.get(16)&1)){t.put(16,t.get(16)|1);t.put(12,0x4e40b0);}t.put(0,value-1);t.put(4,value);t.put(8,word(float(signed_word(value))));}
void substate(AnmView title,u32 value){title.put(0x24,value);clock(title,0);}
bool spawn(AnmView title,AnmResourceWorld& world,u32 script){u32 handle;if(!world.create_at(title.get(0x14),i32(script),-1,{0,0,0},handle))return false;title.put(0x2c8+script*4,handle);return true;}
bool tick(AnmView title,AnmResourceWorld& world){auto timer=title.sub(0x2b4);const u32 previous=timer.get(4),token=timer.get(12);float rate=1;if(token&&!world.timer_rate(token,rate))return false;timer.put(0,previous);const bool unit=!token||(rate>real(0x3f7d70a4)&&rate<real(0x3f8147ae));const float value=timer.floating(8)+(unit?1.f:rate);timer.put(8,word(value));timer.put(4,unit?previous+1:value>=-2147483648.f&&value<2147483648.f?u32(i32(value)):0x80000000);return true;}
}
bool select_title_state(GameTitleRuntime& owner,i32 state){if(!owner.global_owner)return false;auto title=owner.view();title.put(0x20,title.get(0x1c));title.put(0x1c,u32(state));substate(title,0);return true;}
bool advance_title_main_intro(GameTitleRuntime& owner,AnmResourceWorld& world,u32& result){
    auto title=owner.view();if(!owner.global_owner||title.get(0x1c)!=1||title.get(0x24)>1)return false;result=1;
    if(!title.get(0x24)){
        title.put(0x30,7);title.put(0xf8,1);substate(title,1);
        if(title.get(0xe000)&2){if(!spawn(title,world,99)||!spawn(title,world,108))return false;title.put(0xe000,title.get(0xe000)&~2u);}
        else{
            if(!world.find(title.get(0x454)).data){if(!spawn(title,world,99)||!signal_animation(world,title.get(0x454),2,true))return false;}
            if(!world.find(title.get(0x478)).data){if(!spawn(title,world,108)||!signal_animation(world,title.get(0x478),2,true))return false;}
            if(title.get(0x20)!=3&&!signal_animation(world,title.get(0x454),2,true))return false;clock(title,90);
        }
    }
    // Native tests the integer clock every update: a slow/zero rate can
    // create scripts0/78 repeatedly at90; only the title_v handle is cached.
    if(title.get(0x2b8)==90){if(!spawn(title,world,0)||!spawn(title,world,78))return false;if(!world.find(title.get(0x7f0)).data){title.put(0x7f0,0);u32 handle;if(!world.create_at(title.get(0x18),0,-1,{0,0,0},handle))return false;title.put(0x7f0,handle);}}
    if(signed_word(title.get(0x2b8))>100){substate(title,2);if(!signal_animation(world,title.get(0x2c8),3,true))return false;const u16 a=u16(u16(title.get(0x28))+27),b=u16(u16(title.get(0x28))+7);const i32 first=a&0x8000?i32(a)-65536:i32(a),second=b&0x8000?i32(b)-65536:i32(b);if(!signal_animation(world,title.get(0x2c8),first,false)||!signal_animation(world,title.get(0x400),second,false))return false;}
    return tick(title,world)&&world.synchronize_resources();
}
}
