#include "PlayerEquipmentFrame.hpp"
namespace th143 {
bool update_player_equipment(PlayerEquipmentState& state,float rate,const u32& fresh,PlayerEquipmentFrameHost& host){
    if(0.f>=rate)return true;auto s=state.view();
    if(signed_word(s.get(0x2c))>=20){
        const u32 first=s.get(0x24)?0x14:0x10,second=first==0x10?0x14:0x10;
        for(u32 at:{first,second})if(u32 token=s.get(at))if(!host.update_equipment_option(token))return false;
        bool active=false;
        for(u32 at:{0x10,0x14})if(u32 token=s.get(at)){
            bool busy;if(!host.equipment_option_busy(token,busy))return false;
            if(busy){active=true;break;}
        }
        if(!active){
            bool remaining=false;
            for(u32 at:{0x10,0x14})if(u32 token=s.get(at)){
                u32 count;if(!host.equipment_option_count(token,count))return false;
                if(count){remaining=true;break;}
            }
            if(!remaining&&(fresh&2)&&!host.equipment_empty_sound(16))return false;
        }
    }
    const u32 token=s.get(0x34),old=s.get(0x2c);s.put(0x28,old);float clock=1;
    if(token&&!host.timer_rate(token,clock))return false;
    const bool unit=!token||(clock>real(0x3f7d70a4)&&clock<real(0x3f8147ae));
    const float value=s.floating(0x30)+(unit?1.f:clock);s.put(0x30,word(value));
    s.put(0x2c,unit?old+1:value>=-2147483648.f&&value<2147483648.f?u32(i32(value)):0x80000000);return true;
}
bool draw_player_equipment(PlayerEquipmentState& state,PlayerEquipmentFrameHost& host){
    auto s=state.view();for(u32 at:{0x10,0x14})if(u32 token=s.get(at))if(!host.draw_equipment_option(token))return false;return true;
}
}
