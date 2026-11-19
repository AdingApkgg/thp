#include "PlayerCloak.hpp"
namespace th143 {
namespace {
void reset_timer(AnmView option,u32 at,PlayerCloakHost& host){
    const u32 flags=option.get(at+16);if(!(flags&1)){option.put(at+12,host.global_rate_token());option.put(at+16,flags|1);}
    option.put(at,0xffffffff);option.put(at+4,0);option.put(at+8,0);
}
bool tick_timer(AnmView option,u32 at,PlayerCloakHost& host){
    const u32 token=option.get(at+12),old=option.get(at+4);option.put(at,old);float rate=1;
    if(token&&!host.timer_rate(token,rate))return false;
    const bool unit=!token||(rate>real(0x3f7d70a4)&&rate<real(0x3f8147ae));
    const float value=option.floating(at+8)+(unit?1.f:rate);option.put(at+8,word(value));
    option.put(at+4,unit?old+1:value>=-2147483648.f&&value<2147483648.f?u32(i32(value)):0x80000000);return true;
}
}
bool update_player_cloak(AnmView option,bool secondary,AnmView equipment,PlayerState& player,AnmView cheat,PlayerCloakGlobals& g,AnmWorld& world,PlayerCloakHost& host){
    auto clocks=[&](){return secondary?(tick_timer(option,0x2c,host)&&tick_timer(option,4,host)):(tick_timer(option,4,host)&&tick_timer(option,0x2c,host));};
    if(secondary){
        const u32 primary=equipment.get(0x10);AnmView other{nullptr};bool busy;
        if(!primary||!host.cloak_option_view(primary,other)||!other.data)return false;
        if(other.get(0x18))return clocks();
        if(!host.cloak_option_busy(primary,busy))return false;if(busy)return clocks();
    }
    auto ui=[&](i32 child,i32 signal){return signal_cheat_child(cheat,cheat.get(0x2b8),child,signal,world);};
    auto pair=[&](bool side){return ui(side?12:11,6)&&ui(side?8:7,6);};
    auto position=[&](){return std::array<float,3>{player.floating(0x5e0),player.floating(0x5e4),player.floating(0x5e8)};};
    const u32 state=option.get(0x1c);bool blocked=false;
    if(!state){
        const u32 other=equipment.get(0x14);if(other){if(!host.cloak_option_busy(other,blocked))return false;}
        const bool death=equipment.get(0x1c)&&g.secondary==3&&player.get(0x684)==4;
        if(!blocked&&(player.get(0x684)==1||death)&&signed_word(option.get(0x18))>0&&(g.fresh&2)){
            if(!pair(secondary))return false;
            if(equipment.get(0x1c)){
                if(g.secondary==3&&player.get(0x684)==4){
                    player.put(0x684,1);u32 ignored;if(!world.create_at(player.get(0x10),22,-1,position(),ignored))return false;
                    if(!pair(true))return false;
                }
                if(equipment.get(0x1c)&&!host.cloak_alternate_release())return false;
            }
            player.put(0x1847c,player.get(0x1847c)|0x32);equipment.put(0x18,equipment.get(0x18)+1);
            option.put(0x18,option.get(0x18)-1);option.put(0x1c,1);reset_timer(option,4,host);
            u32 handle;if(!world.create_at(player.get(0x10),7,-1,position(),handle))return false;option.put(0x20,handle);
            if(!host.cloak_sound(76,player.floating(0x5e0)))return false;
            reset_timer(option,0x2c,host);if(!ui(secondary?12:11,59))return false;
        }
    }else{
        bool finishing=false;
        if(state==1){
            const i32 elapsed=signed_word(option.get(8));
            const bool released=elapsed>=signed_word(option.get(0x28)-15)&&!(g.held&2);
            const bool limit=elapsed>=signed_word(option.get(0x24)-15);
            if(released||limit){
                option.put(0x1c,2);reset_timer(option,4,host);
                if(!signal_animation(world,option.get(0x20),1)||!host.cloak_sound(77,player.floating(0x5e0)))return false;
                finishing=true;
            }
        }else if(state==2)finishing=true;
        if(finishing&&signed_word(option.get(8))>=15){
            player.put(0x1847c,player.get(0x1847c)&~0x32u);option.put(0x1c,0);
            if(signed_word(option.get(0x18))>0&&!ui(secondary?12:11,60))return false;
        }
    }
    auto vm=world.find(option.get(0x20));
    if(!vm.data)option.put(0x20,0);
    else for(u32 i=0;i<3;++i)vm.put(0x59c+i*4,player.get(0x5e0+i*4));
    return clocks();
}
bool draw_player_cloak(AnmView option,PlayerState& player,AnmView ascii,PlayerCloakHost& host){
    if(!option.get(0x1c))return true;
    const i32 elapsed=signed_word(option.get(8)),remainder=elapsed%6;
    const bool late=signed_word(option.get(8)-30)>=signed_word(option.get(0x24));
    const u32 color=late?(remainder<3?0xffff8080:0xffa00000):(remainder<3?0xffffffff:0xff808080);
    ascii.put(0x191c8,2);ascii.put(0x191cc,1);ascii.put(0x191b0,color);
    const std::array<float,3> position{player.floating(0x5e0)-14.f,player.floating(0x5e4)-40.f,player.floating(0x5e8)};
    const float seconds=float(signed_word(option.get(0x24)-option.get(0x30)))/60.f;
    if(!host.cloak_countdown(position,double(seconds)))return false;
    ascii.put(0x191c8,0);ascii.put(0x191b0,0xffffffff);ascii.put(0x191cc,0);return true;
}
}
