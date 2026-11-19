#include "PlayerMallet.hpp"
namespace th143 {
namespace {
void reset(AnmView v,u32 at,u32 value,PlayerBombHost& h){const u32 f=v.get(at+16);if(!(f&1)){v.put(at+12,h.global_rate_token());v.put(at+16,f|1);}v.put(at,value-1);v.put(at+4,value);v.put(at+8,word(float(signed_word(value))));}
bool tick(AnmView v,PlayerBombHost& h){const u32 token=v.get(0x10),old=v.get(8);v.put(4,old);float r=1;if(token&&!h.timer_rate(token,r))return false;const bool unit=!token||(r>real(0x3f7d70a4)&&r<real(0x3f8147ae));const float value=v.floating(12)+(unit?1.f:r);v.put(12,word(value));v.put(8,unit?old+1:value>=-2147483648.f&&value<2147483648.f?u32(i32(value)):0x80000000);return true;}
bool attack(PlayerState& p,const std::array<float,3>& point,u32 damage,PlayerBombHost& h){
    u32 cursor=p.get(0xde14);if(cursor>256)return false;u32 at=0xde18+cursor*0xa4;
    for(u32 n=0;n<256;++n){
        if(cursor>=256){cursor=0;p.put(0xde14,0);at=0xde18;}
        if(!(p.get(at+0x10)&1)){
            p.put(at+0x10,(p.get(at+0x10)&~4u)|3);std::memset(p.data.data()+at+0x2c,0,0x44);
            for(u32 i=0;i<3;++i)p.put(at+0x2c+i*4,word(point[i]));p.put(at+0x14,word(32.f));p.put(at+0x18,word(3.f));reset({p.data.data()},at+0x70,10,h);
            p.put(at+0x84,damage);p.put(at+0x88,0);p.put(at+0x8c,9999999);p.put(at+0x90,1);p.put(at+0x94,0);p.put(at+0xa0,0);break;
        }
        p.put(0xde14,++cursor);at+=0xa4;
    }
    // Full pools still return the advanced slot; the caller sets bit4 there.
    p.put(at+0x10,p.get(at+0x10)|4);return true;
}
}
bool update_player_mallet(AnmView option,AnmView equipment,PlayerState* player,AnmView cheat,PlayerBombGlobals& g,AnmWorld& world,PlayerBombHost& host){
    if(!player)return true;auto& p=*player;auto ui=[&](i32 child,i32 signal){return signal_cheat_child(cheat,cheat.get(0x2b8),child,signal,world);};
    auto death=[&](){return equipment.get(0x1c)&&g.secondary==3&&p.get(0x684)==4;};
    auto position=[&](){return std::array<float,3>{p.floating(0x5e0),p.floating(0x5e4),p.floating(0x5e8)};};
    if(!option.get(0x1c)){
        if(signed_word(option.get(8))>=signed_word(option.get(0x38))){
            bool busy=false;if(equipment.get(0x14)&&!host.bomb_option_busy(equipment.get(0x14),busy))return false;
            if(!busy&&(p.get(0x684)==1||death())&&signed_word(option.get(0x18))>0&&(g.fresh&2)){
                if(equipment.get(0x1c)&&!host.bomb_alternate_release())return false;if(!ui(11,6)||!ui(7,6))return false;
                if(death()){p.put(0x684,1);u32 ignored;if(!world.create_at(p.get(0x10),22,-1,position(),ignored)||!ui(12,6)||!ui(8,6))return false;}
                equipment.put(0x18,equipment.get(0x18)+1);u32 flags=p.get(0x1847c)|0x12;p.put(0x1847c,(flags&~0x600u)|(((flags&0x200)|0x100)<<1));
                auto point=position();point[1]+=0.f;point[0]-=16.f;u32 handle;if(!world.create_at(p.get(0x10),29,-1,point,handle))return false;option.put(0x28,handle);
                point[1]+=8.f;point[0]-=8.f;if(!world.create_at(p.get(0x10),28,-1,point,handle))return false;option.put(0x24,handle);
                option.put(0x18,option.get(0x18)-1);option.put(0x1c,1);reset(option,4,0,host);
                if(!host.bomb_sound(84,p.floating(0x5e0))||!ui(11,59))return false;
            }
        }else if(option.get(8)==option.get(0x38)-1&&signed_word(option.get(0x18))>0){if(!ui(11,60)||!host.bomb_sound(76,p.floating(0x5e0)))return false;}
    }
    if(option.get(0x1c)==1){
        if(signed_word(option.get(8))>=60){
            if(!signal_animation(world,option.get(0x24),1)||!signal_animation(world,option.get(0x28),2))return false;
            option.put(0x1c,2);reset(option,4,0,host);const u32 flags=p.get(0x1847c);p.put(0x1847c,(flags&~0x600u)|((flags&0x200)<<1));
        }
    }else if(option.get(0x1c)==2&&signed_word(option.get(8))>=10){
        p.put(0x1847c,p.get(0x1847c)&~0x12u);if(!host.bomb_stop_sound(84)||!host.bomb_sound(27,p.floating(0x5e0)))return false;
        auto point=position();point[1]-=48.f;u32 handle;
        if(!world.create_at(p.get(0x10),30,-1,point,handle))return false;option.put(0x24,handle);
        if(!world.create_at(p.get(0x10),32,-1,point,handle))return false;option.put(0x24,handle);
        option.put(0x1c,0);reset(option,4,0,host);if(!attack(p,point,option.get(0x2c),host))return false;
    }
    return tick(option,host);
}
}
