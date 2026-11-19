#include "PlayerEquipment.hpp"

namespace th143 {
namespace {
void timer(AnmView v,u32 at,u32 value=0){
    const u32 flags=v.get(at+0x10);
    if(!(flags&1)){v.put(at+12,0x4e40b0);v.put(at+16,flags|1);}
    v.put(at+4,value);v.put(at+8,word(float(signed_word(value))));v.put(at,value-1);
}
bool flag(PlayerEquipmentHost& h,u32 token,bool enabled){
    if(!token)return false;u32 flags;return h.equipment_read(token+4,flags)&&h.equipment_write(token+4,enabled?flags|2:flags&~2u);
}
bool option(AnmView owner,bool secondary,u32 index,const PlayerEquipmentGlobals& g,PlayerEquipmentHost& host){
    static constexpr std::array<u32,9> sizes{0x40,0x64,0x6c,0x44,0x44,0x48,0x48,0x48,0x54};
    static constexpr std::array<u32,9> vtables{0x4c6d08,0x4c6cec,0x4c6cd0,0x4c6cb4,0x4c6c98,0x4c6c7c,0x4c6c60,0x4c6c44,0x4c6c28};
    if(index>8)return false;
    u32 token;AnmView v{nullptr};if(!host.equipment_allocate(sizes[index],token,v)||!token||!v.data)return false;
    v.put(0,0x4c6c0c);v.put(0x14,v.get(0x14)&~1u);timer(v,4);
    v.put(0,secondary?(index==0?0x4c6d5c:index==2?0x4c6d40:0x4c6d24):vtables[index]);
    if(index==0)v.put(0x3c,v.get(0x3c)&~1u);
    if(index==2)v.put(0x64,v.get(0x64)&~1u);
    owner.put(secondary?0x14:0x10,token);
    if(index==1||index==4)return host.equipment_visual_initialize(index,v,g);
    timer(v,4,index==8?120:0);v.put(0x1c,0);v.put(0x18,secondary?(index==0?2:index==2?3:1):g.initial_count);
    switch(index){
    case 0:timer(v,0x2c);v.put(0x1c,0);v.put(0x24,secondary?60:g.initial_parameter);v.put(0x28,45);break;
    case 2:v.put(0x48,20);v.put(0x4c,secondary?0:60);v.put(0x50,secondary?0:g.initial_parameter);timer(v,0x54);break;
    case 3:v.put(0x38,g.initial_parameter);break;
    case 5:v.put(0x2c,0);v.put(0x28,180);v.put(0x38,word(float(signed_word(g.initial_parameter))));break;
    case 6:case 7:v.put(0x28,180);v.put(0x2c,secondary?40:g.initial_parameter);break;
    case 8:v.put(0x30,180);v.put(0x38,120);v.put(0x2c,g.initial_parameter);break;
    }
    return true;
}
}
bool initialize_player_equipment(PlayerEquipmentState& state,u32 self,PlayerEquipmentHost& host){
    auto s=state.view();
    for(auto entry:{std::array<u32,4>{0x450820,22,0,8},{0x450830,29,1,12}}){
        u32 callback;if(!host.equipment_register(entry[0],i32(entry[1]),entry[2]!=0,self,callback))return false;s.put(entry[3],callback);
    }
    if(!flag(host,s.get(8),false)||!flag(host,s.get(12),false))return false;
    timer(s,0x28);return true;
}
bool activate_player_equipment(PlayerEquipmentState& state,PlayerState& player,
                               const PlayerEquipmentGlobals& g,PlayerEquipmentHost& host){
    auto s=state.view();s.put(0x18,0);
    if(!flag(host,s.get(8),true)||!flag(host,s.get(12),true))return false;
    s.put(0x1c,g.alternate);
    if(g.alternate&&g.secondary<=6){
        switch(g.secondary){
        case 0:case 2:case 6:
            if(!option(s,true,g.secondary,g,host))return false;s.put(0x20,1);
            if(g.secondary==2&&g.primary!=2)s.put(0x24,1);break;
        case 1:case 4:
            if(g.secondary==1){player.put(0x5f4,0x300);player.put(0x5f8,0x100);player.put(0x5fc,0x21f);player.put(0x600,0xb5);}
            else{player.put(0x64c,0x3f333333);player.put(0x648,0x3f333333);player.put(0x650,0x40a00000);}
            if(!host.equipment_secondary_visual(12,58)||!host.equipment_secondary_visual(8,58))return false;break;
        }
    }
    return g.primary>8||option(s,false,g.primary,g,host);
}
}
