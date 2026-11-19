#include "PlayerOrb.hpp"
#include <cmath>
namespace th143 {
namespace {
void reset(AnmView v,PlayerOrbHost& h){const u32 f=v.get(0x14);if(!(f&1)){v.put(0x10,h.global_rate_token());v.put(0x14,f|1);}v.put(4,0xffffffff);v.put(8,0);v.put(12,0);}
bool tick(AnmView v,PlayerOrbHost& h){const u32 token=v.get(0x10),old=v.get(8);v.put(4,old);float r=1;if(token&&!h.timer_rate(token,r))return false;const bool unit=!token||(r>real(0x3f7d70a4)&&r<real(0x3f8147ae));const float value=v.floating(12)+(unit?1.f:r);v.put(12,word(value));v.put(8,unit?old+1:value>=-2147483648.f&&value<2147483648.f?u32(i32(value)):0x80000000);return true;}
u32 truncate(float v){return v>=-2147483648.f&&v<2147483648.f?u32(i32(v)):0x80000000;}
float wrap(float a){u32 n=0;while(a>real(0x40490fdb)){a-=real(0x40c90fdb);if(n++>32)break;}while(real(0xc0490fdb)>a){a+=real(0x40c90fdb);if(n++>32)break;}return a;}
void teleport(PlayerState& p,const std::array<float,3>& point){p.put(0x5ec,truncate(point[0]*128.f));p.put(0x5f0,truncate(point[1]*128.f));p.put(0x5e0,word(float(signed_word(p.get(0x5ec)))*real(0x3c000000)));p.put(0x5e4,word(float(signed_word(p.get(0x5f0)))*real(0x3c000000)));for(u32 i=0;i<8;++i)p.put(0xd7c0+i*0xe4,1);}
}
bool update_player_orb(AnmView option,AnmView equipment,PlayerState* player,AnmView cheat,PlayerOrbGlobals& g,AnmWorld& world,PlayerOrbHost& host){
    if(!player)return true;auto& p=*player;std::array<float,3> target;if(!host.orb_target(target))return false;
    const u32 at=p.get(0x1847c)&0x100?0x184b4:0x5e0;const float dx=p.floating(at)-target[0],dy=p.floating(at+4)-target[1];
    const float angle=wrap(dx==0.f&&dy==0.f?real(0x3fc90fdb):float(std::atan2(double(dy),double(dx))));
    const float sine=float(std::sin(double(angle))),cosine=float(std::cos(double(angle)));
    std::array<float,3> point{cosine*64.f-sine*0.f+target[0],sine*64.f+cosine*0.f+target[1],0.f};
    auto ui=[&](i32 child,i32 signal){return signal_cheat_child(cheat,cheat.get(0x2b8),child,signal,world);};
    auto death=[&](){return equipment.get(0x1c)&&g.secondary==3&&p.get(0x684)==4;};
    auto position=[&](){return std::array<float,3>{p.floating(0x5e0),p.floating(0x5e4),p.floating(0x5e8)};};
    if(!option.get(0x1c)){
        if(option.get(8)==option.get(0x2c)&&signed_word(option.get(0x18))>0){if(!host.bomb_sound(77,p.floating(0x5e0))||!signal_animation(world,option.get(0x24),7))return false;}
        bool busy=false;if(equipment.get(0x14)&&!host.bomb_option_busy(equipment.get(0x14),busy))return false;
        if(!busy&&(p.get(0x684)==1||death())&&signed_word(option.get(8))>=signed_word(option.get(0x2c))&&signed_word(option.get(0x18))>0&&(g.fresh&2)){
            if(!ui(11,6)||!ui(7,6))return false;
            if(equipment.get(0x1c)&&!host.bomb_alternate_release())return false;
            if(death()){p.put(0x684,1);u32 ignored;if(!world.create_at(p.get(0x10),22,-1,position(),ignored)||!ui(12,6)||!ui(8,6))return false;}
            equipment.put(0x18,equipment.get(0x18)+1);option.put(0x1c,1);reset(option,host);option.put(0x30,0);
            if(!host.bomb_sound(84,p.floating(0x5e0))||!signal_animation(world,option.get(0x24),2))return false;
            p.put(0x1847c,p.get(0x1847c)|0x12);for(u32 i=0;i<3;++i)option.put(0x34+i*4,0);if(!ui(11,59))return false;
        }
    }
    if(option.get(0x1c)==1){
        const u32 keys=g.held;u32 d=(keys&0x50)==0x50?5:(keys&0x60)==0x60?7:(keys&0x90)==0x90?6:(keys&0xa0)==0xa0?8:(keys&0x20)?2:(keys&0x10)?1:(keys&0x40)?3:(keys>>5)&4;
        static constexpr float directions[9][2]={{0,0},{0,-1},{0,1},{-1,0},{1,0},{-1,-1},{1,-1},{-1,1},{1,1}};
        const float speed=d>=5?real(0x4007c5a1):3.f;
        option.put(0x34,word(speed*directions[d][0]+option.floating(0x34)));option.put(0x38,word(speed*directions[d][1]+option.floating(0x38)));
        for(u32 i=0;i<3;++i)point[i]+=option.floating(0x34+i*4);
        if(-176.f>point[0])point[0]=-176.f;else if(point[0]>176.f)point[0]=176.f;
        if(32.f>point[1])point[1]=32.f;else if(point[1]>432.f)point[1]=432.f;
        if(signed_word(option.get(8))>=20&&(signed_word(option.get(8))>=signed_word(option.get(0x28))||!(g.held&2))){
            option.put(0x18,option.get(0x18)-1);const auto old=position();teleport(p,point);option.put(0x1c,2);reset(option,host);
            if(!host.bomb_sound(85,point[0])||!host.bomb_stop_sound(84))return false;
            u32 ignored;if(!world.create_at(p.get(0x10),14,-1,old,ignored)||!world.create_at(p.get(0x10),15,-1,point,ignored)||!signal_animation(world,option.get(0x24),3))return false;
        }
    }else if(option.get(0x1c)==2&&signed_word(option.get(8))>=10){
        p.put(0x1847c,p.get(0x1847c)&~0x12u);option.put(0x1c,0);reset(option,host);if(signed_word(option.get(0x18))>0&&!ui(11,60))return false;
    }
    auto vm=world.find(option.get(0x24));if(vm.data)for(u32 i=0;i<3;++i)vm.put(0x59c+i*4,word(point[i]));return tick(option,host);
}
}
