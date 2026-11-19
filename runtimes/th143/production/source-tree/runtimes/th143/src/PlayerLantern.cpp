#include "PlayerLantern.hpp"
#include <cmath>
namespace th143 {
namespace {
void reset(AnmView v,PlayerLanternHost& h){const u32 f=v.get(0x14);if(!(f&1)){v.put(0x10,h.global_rate_token());v.put(0x14,f|1);}v.put(4,0xffffffff);v.put(8,0);v.put(12,0);}
bool tick(AnmView v,PlayerLanternHost& h){const u32 t=v.get(0x10),old=v.get(8);v.put(4,old);float r=1;if(t&&!h.timer_rate(t,r))return false;const bool unit=!t||(r>real(0x3f7d70a4)&&r<real(0x3f8147ae));const float value=v.floating(12)+(unit?1.f:r);v.put(12,word(value));v.put(8,unit?old+1:value>=-2147483648.f&&value<2147483648.f?u32(i32(value)):0x80000000);return true;}
float wrap(float angle){u32 count=0;while(angle>real(0x40490fdb)){angle-=real(0x40c90fdb);if(count++>32)break;}while(real(0xc0490fdb)>angle){angle+=real(0x40c90fdb);if(count++>32)break;}return angle;}
u32 truncate(float v){return v>=-2147483648.f&&v<2147483648.f?u32(i32(v)):0x80000000;}
}
bool update_player_lantern(AnmView option,AnmView equipment,PlayerState* player,AnmView cheat,PlayerBombGlobals& g,SoundQueue& sounds,AnmWorld& world,PlayerLanternHost& host){
    if(!player)return true;auto& p=*player;auto ui=[&](i32 child,i32 signal){return signal_cheat_child(cheat,cheat.get(0x2b8),child,signal,world);};
    auto death=[&](){return equipment.get(0x1c)&&g.secondary==3&&p.get(0x684)==4;};
    auto position=[&](){return std::array<float,3>{p.floating(0x5e0),p.floating(0x5e4),p.floating(0x5e8)};};
    if(!option.get(0x1c)){
        bool busy=false;if(equipment.get(0x14)&&!host.bomb_option_busy(equipment.get(0x14),busy))return false;
        if(!busy&&(p.get(0x684)==1||death())&&signed_word(option.get(0x18))>0&&(g.fresh&2)){
            if(equipment.get(0x1c)&&!host.bomb_alternate_release())return false;
            if(!ui(11,6)||!ui(7,6))return false;
            if(death()){
                p.put(0x684,1);u32 ignored;if(!world.create_at(p.get(0x10),22,-1,position(),ignored)||!ui(12,6)||!ui(8,6))return false;
            }
            equipment.put(0x18,equipment.get(0x18)+1);option.put(0x18,option.get(0x18)-1);option.put(0x1c,1);reset(option,host);p.put(0x1847c,p.get(0x1847c)|0xa0);
            for(u32 i=0;i<4;++i){u32 resource,handle;if(!host.lantern_resource(resource)||!world.create_at(resource,79+i32(i)*4,-1,{0,0,0},handle))return false;option.put(0x24+i*4,handle);}
            auto last=world.find(option.get(0x30));if(!last.data)return false;last.put(0x24,14);
            u32 handle;if(!world.create_at(p.get(0x10),12,-1,{0,0,0},handle))return false;option.put(0x34,handle);option.put(0x3c,0);
            if(!host.bomb_sound(84,p.floating(0x5e0))||!ui(11,59))return false;
        }
    }
    if(option.get(0x1c)==1){
        float angle=option.floating(0x3c);
        for(u32 i=0;i<3;++i){
            float radius=float(signed_word(option.get(0x38)-option.get(8)))*48.f;radius/=float(signed_word(option.get(0x38)));radius+=16.f;
            const float sine=float(std::sin(double(angle))),cosine=float(std::cos(double(angle)));
            const std::array<float,3> point{cosine*radius-sine*0.f+p.floating(0x5e0),sine*radius+cosine*0.f+p.floating(0x5e4),0.f};
            auto vm=world.find(option.get(0x24+i*4));if(vm.data)for(u32 j=0;j<3;++j)vm.put(0x59c+j*4,word(point[j]));
            angle=wrap(angle+real(0x40060a92));
        }
        option.put(0x3c,word(wrap(option.floating(0x3c)+real(0x3e32b8c3))));
        for(u32 at:{0x30,0x34}){auto vm=world.find(option.get(at));if(vm.data)for(u32 j=0;j<3;++j)vm.put(0x59c+j*4,p.get(0x5e0+j*4));}
        const float pan=(p.floating(0x5e0)*1000.f)/192.f;if(!host.lantern_pan(signed_word(truncate(pan))))return false;
        if(signed_word(option.get(8))>=signed_word(option.get(0x38))){
            auto queue=sounds.view();for(u32 i=0;i<12;++i){const i32 id=signed_word(queue.get(i*4));if(id<0||id==84){if(id<0)queue.put(i*4,84);queue.put(0x30+i*4,0xffffffff);break;}}
            if(!host.bomb_sound(85,p.floating(0x5e0)))return false;option.put(0x1c,0);p.put(0x1847c,p.get(0x1847c)&~0xa0u);
            for(u32 at=0x24;at<=0x34;at+=4){if(!world.mark_retirement(option.get(at)))return false;option.put(at,0);}
        }
    }return tick(option,host);
}
bool draw_player_lantern(AnmView option,PlayerState* player,AnmView ascii,PlayerLanternHost& host){
    if(!option.get(0x1c))return true;if(!player)return false;auto& p=*player;ascii.put(0x191c8,2);ascii.put(0x191cc,1);
    const bool flash=signed_word(option.get(8))%8<4,remaining=option.get(0x18)!=0;
    ascii.put(0x191b0,remaining?(flash?0xffffffff:0xff808080):(flash?0xffff8080:0xffa00000));
    const std::array<float,3> point{p.floating(0x5e0)-20.f,p.floating(0x5e4)-40.f,p.floating(0x5e8)};
    const float seconds=float(signed_word(option.get(0x38)-option.get(8)))/60.f;
    if(!host.lantern_countdown(point,double(seconds)))return false;ascii.put(0x191cc,0);ascii.put(0x191c8,0);ascii.put(0x191b0,0xffffffff);return true;
}
}
