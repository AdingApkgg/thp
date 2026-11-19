#include "PlayerBomb.hpp"
namespace th143 {
namespace {
void reset(AnmView v,PlayerBombHost& host){const u32 flags=v.get(0x14);if(!(flags&1)){v.put(0x10,host.global_rate_token());v.put(0x14,flags|1);}v.put(4,0xffffffff);v.put(8,0);v.put(12,0);}
bool tick(AnmView v,PlayerBombHost& host){const u32 token=v.get(0x10),old=v.get(8);v.put(4,old);float rate=1;if(token&&!host.timer_rate(token,rate))return false;const bool unit=!token||(rate>real(0x3f7d70a4)&&rate<real(0x3f8147ae));const float value=v.floating(12)+(unit?1.f:rate);v.put(12,word(value));v.put(8,unit?old+1:value>=-2147483648.f&&value<2147483648.f?u32(i32(value)):0x80000000);return true;}
}
bool update_player_bomb(AnmView option,AnmView equipment,PlayerState* player,AnmView cheat,PlayerBombGlobals& g,AnmWorld& world,PlayerBombHost& host){
    if(!player)return true;auto& p=*player;auto ui=[&](i32 child,i32 signal){return signal_cheat_child(cheat,cheat.get(0x2b8),child,signal,world);};
    auto death=[&](){return equipment.get(0x1c)&&g.secondary==3&&p.get(0x684)==4;};
    auto player_position=[&](){return std::array<float,3>{p.floating(0x5e0),p.floating(0x5e4),p.floating(0x5e8)};};
    auto stored_position=[&](){return std::array<float,3>{option.floating(0x3c),option.floating(0x40),option.floating(0x44)};};
    if(!option.get(0x1c)){
        bool busy=false;if(equipment.get(0x14)&&!host.bomb_option_busy(equipment.get(0x14),busy))return false;
        if(!busy&&(p.get(0x684)==1||death())&&signed_word(option.get(8))>=signed_word(option.get(0x2c))&&signed_word(option.get(0x18))>0&&(g.fresh&2)){
            if(!ui(11,6)||!ui(7,6))return false;
            if(equipment.get(0x1c)&&!host.bomb_alternate_release())return false;
            if(death()){
                p.put(0x684,1);u32 ignored;if(!world.create_at(p.get(0x10),22,-1,player_position(),ignored)||!ui(12,6)||!ui(8,6))return false;
            }
            equipment.put(0x18,equipment.get(0x18)+1);option.put(0x18,option.get(0x18)-1);
            for(u32 i=0;i<3;++i)option.put(0x3c+i*4,p.get(0x5e0+i*4));option.put(0x1c,1);reset(option,host);option.put(0x30,0);
            if(!host.bomb_sound(84,p.floating(0x5e0)))return false;
            u32 handle;if(!world.create_at(p.get(0x10),20,-1,stored_position(),handle))return false;option.put(0x24,handle);if(!ui(11,59))return false;
        }
    }
    if(option.get(0x1c)==1&&signed_word(option.get(8))>=120){
        option.put(0x1c,2);reset(option,host);
        if(!signal_animation(world,option.get(0x24),1)||!host.bomb_stop_sound(84))return false;
        u32 handle;if(!world.create_at(p.get(0x10),16,-1,stored_position(),handle))return false;option.put(0x24,handle);
        const float scale=(option.floating(0x38)-128.f)*.0078125f+1.f;auto vm=world.find(handle);if(!vm.data)return false;
        vm.put(0x18,vm.get(0x18)|8);vm.put(0x60,word(scale));vm.put(0x64,word(scale));
        if(!host.bomb_sound(44,option.floating(0x3c)))return false;option.put(0x34,word(64.f));
    }
    if(option.get(0x1c)==2){
        if(!host.bomb_bullets(option.sub(0x3c),option.floating(0x34))||!host.bomb_lasers(option.sub(0x3c),option.floating(0x34)))return false;
        if(option.floating(0x38)>option.floating(0x34))option.put(0x34,word(option.floating(0x34)+8.f));
        if(signed_word(option.get(8))>=90){option.put(0x1c,0);reset(option,host);if(signed_word(option.get(0x18))>0&&!ui(11,60))return false;}
    }return tick(option,host);
}
}
