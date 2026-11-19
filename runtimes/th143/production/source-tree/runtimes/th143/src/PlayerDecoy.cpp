#include "PlayerDecoy.hpp"
namespace th143 {
namespace {
void reset(AnmView v,PlayerDecoyHost& host){const u32 flags=v.get(0x14);if(!(flags&1)){v.put(0x10,host.global_rate_token());v.put(0x14,flags|1);}v.put(4,0xffffffff);v.put(8,0);v.put(12,0);}
bool tick(AnmView v,PlayerDecoyHost& host){const u32 token=v.get(0x10),old=v.get(8);v.put(4,old);float rate=1;if(token&&!host.timer_rate(token,rate))return false;const bool unit=!token||(rate>real(0x3f7d70a4)&&rate<real(0x3f8147ae));const float value=v.floating(12)+(unit?1.f:rate);v.put(12,word(value));v.put(8,unit?old+1:value>=-2147483648.f&&value<2147483648.f?u32(i32(value)):0x80000000);return true;}
}
bool update_player_decoy(AnmView option,AnmView equipment,PlayerState* player,AnmView cheat,PlayerBombGlobals& g,AnmWorld& world,PlayerDecoyHost& host){
    if(!player)return true;auto& p=*player;auto ui=[&](i32 child,i32 signal){return signal_cheat_child(cheat,cheat.get(0x2b8),child,signal,world);};
    auto death=[&](){return equipment.get(0x1c)&&g.secondary==3&&p.get(0x684)==4;};
    auto current_position=[&](){return std::array<float,3>{p.floating(0x5e0),p.floating(0x5e4),p.floating(0x5e8)};};
    if(!option.get(0x1c)){
        bool busy=false;if(equipment.get(0x14)&&!host.bomb_option_busy(equipment.get(0x14),busy))return false;
        if(!busy&&(p.get(0x684)==1||death())&&signed_word(option.get(0x18))>0&&(g.fresh&2)){
            if(equipment.get(0x1c)&&!host.bomb_alternate_release())return false;
            if(!ui(11,6)||!ui(7,6))return false;
            if(death()){
                p.put(0x684,1);u32 ignored;if(!world.create_at(p.get(0x10),22,-1,current_position(),ignored)||!ui(12,6)||!ui(8,6))return false;
            }
            equipment.put(0x18,equipment.get(0x18)+1);
            for(u32 i=0;i<3;++i)option.put(0x3c+i*4,p.get(0x5e0+i*4));
            u32 handle;if(!world.create_at(p.get(0x10),25,-1,current_position(),handle))return false;option.put(0x24,handle);
            p.put(0x1847c,p.get(0x1847c)|0x100);for(u32 i=0;i<3;++i)p.put(0x184b4+i*4,option.get(0x3c+i*4));
            option.put(0x18,option.get(0x18)-1);option.put(0x1c,1);reset(option,host);
            if(!host.bomb_sound(76,p.floating(0x5e0))||!ui(11,59))return false;
        }
    }
    if(option.get(0x1c)==1){
        auto vm=world.find(option.get(0x24));if(vm.data)for(u32 i=0;i<3;++i)vm.put(0x59c+i*4,option.get(0x3c+i*4));
        for(u32 i=0;i<3;++i)p.put(0x184b4+i*4,option.get(0x3c+i*4));
        if(signed_word(option.get(8))%10==0){if(!host.bomb_bullets(option.sub(0x3c),3.f)||!host.bomb_lasers(option.sub(0x3c),3.f))return false;}
        if(signed_word(option.get(8))>=signed_word(option.get(0x2c))){
            p.put(0x1847c,p.get(0x1847c)&~0x100u);
            if(!signal_animation(world,option.get(0x24),1))return false;option.put(0x1c,0);
            if(!host.bomb_sound(77,option.floating(0x3c)))return false;
            if(signed_word(option.get(0x18))>0&&(!host.bomb_sound(76,p.floating(0x5e0))||!ui(11,60)))return false;
        }
    }return tick(option,host);
}
bool draw_player_decoy(AnmView option,AnmView ascii,PlayerDecoyHost& host){
    if(!option.get(0x1c))return true;ascii.put(0x191c8,2);ascii.put(0x191cc,1);
    const bool remaining=option.get(0x18)!=0,flash=signed_word(option.get(8))%8<4;
    ascii.put(0x191b0,remaining?(flash?0xffffffff:0xff808080):(flash?0xffff8080:0xffa00000));
    const std::array<float,3> p{option.floating(0x3c)-20.f,option.floating(0x40)-40.f,option.floating(0x44)};
    const float seconds=float(signed_word(option.get(0x2c)-option.get(8)))/60.f;
    if(!host.decoy_countdown(p,double(seconds)))return false;
    ascii.put(0x191c8,0);ascii.put(0x191b0,0xffffffff);ascii.put(0x191cc,0);return true;
}
}
