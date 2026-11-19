#include "PlayerUmbrella.hpp"
namespace th143 {
namespace {
u32 truncate(float v){return v>=-2147483648.f&&v<2147483648.f?u32(i32(v)):0x80000000;}
void reset(AnmView v,u32 at,u32 value,PlayerBombHost& h){const u32 f=v.get(at+16);if(!(f&1)){v.put(at+12,h.global_rate_token());v.put(at+16,f|1);}v.put(at,value-1);v.put(at+4,value);v.put(at+8,word(float(signed_word(value))));}
bool tick(AnmView v,u32 at,bool decrement,PlayerBombHost& h){const u32 token=v.get(at+12),old=v.get(at+4);v.put(at,old);float r=1;if(token&&!h.timer_rate(token,r))return false;const bool unit=!token||(r>real(0x3f7d70a4)&&r<real(0x3f8147ae));const float value=decrement?v.floating(at+8)-(unit?1.f:r):v.floating(at+8)+(unit?1.f:r);v.put(at+8,word(value));v.put(at+4,!decrement&&unit?old+1:truncate(value));return true;}
void teleport(PlayerState& p,const std::array<float,3>& point){p.put(0x5ec,truncate(point[0]*128.f));p.put(0x5f0,truncate(point[1]*128.f));p.put(0x5e0,word(float(signed_word(p.get(0x5ec)))*real(0x3c000000)));p.put(0x5e4,word(float(signed_word(p.get(0x5f0)))*real(0x3c000000)));for(u32 i=0;i<8;++i)p.put(0xd7c0+i*0xe4,1);}
}
bool update_player_umbrella(AnmView option,bool secondary,AnmView equipment,PlayerState* player,AnmView cheat,PlayerUmbrellaGlobals& g,AnmWorld& world,PlayerUmbrellaHost& host){
    if(!player)return true;auto& p=*player;
    auto ui=[&](i32 child,i32 signal){return signal_cheat_child(cheat,cheat.get(0x2b8),child,signal,world);};
    auto death=[&](){return equipment.get(0x1c)&&g.secondary==3&&p.get(0x684)==4;};
    auto position=[&](){return std::array<float,3>{p.floating(0x5e0),p.floating(0x5e4),p.floating(0x5e8)};};
    auto neutral=[&](){for(u32 i=0;i<3;++i)p.put(0xd6e0+i*4,g.neutral_velocity[i]);};
    auto velocity=[&](float x,float y){p.put(0x1847c,p.get(0x1847c)|0x40);p.put(0xd6e0,word(x));p.put(0xd6e4,word(y));p.put(0xd6e8,0);};
    auto end=[&](){neutral();p.put(0x1847c,p.get(0x1847c)&~0x32u);option.put(0x1c,0);return !option.get(0x18)||ui(secondary?12:11,60);};
    if(!option.get(0x1c)){
        if(signed_word(option.get(0x4c))>0){option.put(0x4c,option.get(0x4c)-1);return tick(option,4,false,host);}
        const auto point=position();bool busy=false;
        const bool query=!secondary||g.primary==0||g.primary==1||g.primary==2||g.primary==4||g.primary==8;
        const u32 other=equipment.get(secondary?0x10:0x14);if(query&&other&&!host.bomb_option_busy(other,busy))return false;
        if(!busy&&(p.get(0x684)==1||(!secondary&&death()))&&signed_word(option.get(0x18))>0){
            u32 mode=0,reverse=0;
            if(point[0]<=-180.f&&(g.held&2)&&(g.held&0x40)){mode=1;reverse=0;}
            else if(point[0]>=180.f&&(g.held&2)&&(g.held&0x80)){mode=1;reverse=1;}
            else if(point[1]>=428.f&&(g.held&2)&&(g.held&0x20)){mode=2;reverse=0;}
            else if(point[1]<=36.f&&(g.held&2)&&(g.held&0x10)){mode=2;reverse=1;}
            if(mode){
                if(!secondary){
                    if(equipment.get(0x1c)&&!host.bomb_alternate_release())return false;if(!ui(11,6)||!ui(7,6))return false;
                    if(death()){p.put(0x684,1);u32 ignored;if(!world.create_at(p.get(0x10),22,-1,position(),ignored)||!ui(12,6)||!ui(8,6))return false;}
                }
                equipment.put(0x18,equipment.get(0x18)+1);option.put(0x18,option.get(0x18)-1);p.put(0x1847c,p.get(0x1847c)|0x32);option.put(0x1c,mode);option.put(0x20,0);reset(option,4,0,host);
                if(mode==1){if(!host.bomb_sound_unpositioned(82))return false;}else if(!host.bomb_sound(81,p.floating(0x5e0)))return false;
                option.put(0x44,reverse);
                if(secondary){if(!ui(12,6)||!ui(8,6)||!ui(12,59))return false;}else if(!ui(11,59))return false;
            }
        }
        return tick(option,4,false,host);
    }
    const u32 mode=option.get(0x1c),phase=option.get(0x20);const bool reverse=option.get(0x44)!=0;const i32 time=signed_word(option.get(8));
    if((mode==1||mode==2)&&phase==2){
        p.put(0x1847c,p.get(0x1847c)|0x40);neutral();
        if(!(g.held&2)||signed_word(option.get(0x58))<=0){reset(option,4,0,host);option.put(0x20,1);}
        if(!tick(option,0x54,true,host))return false;
    }else if(mode==1&&phase==0){
        velocity(reverse?2.f:-2.f,0.f);
        if(time>=14){option.put(0x20,1);if(g.held&2){reset(option,0x54,option.get(0x50),host);option.put(0x20,2);}teleport(p,{reverse?-208.f:208.f,p.floating(0x5e4),0.f});}
    }else if(mode==1&&phase==1){velocity(reverse?2.f:-2.f,0.f);if(time>=14&&!end())return false;}
    else if(mode==2&&phase==0){
        velocity(0.f,reverse?-4.f:3.f);
        if(time>=(reverse?16:12)){option.put(0x20,1);if(g.held&2){reset(option,0x54,option.get(0x50),host);option.put(0x20,2);}reset(option,4,0,host);teleport(p,{p.floating(0x5e0),reverse?472.f:-24.f,0.f});}
    }else if(mode==2&&phase==1){velocity(0.f,reverse?-3.f:4.f);if(time>=(reverse?12:16)&&!end())return false;}
    return tick(option,4,false,host);
}
}
