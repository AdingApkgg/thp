#include "CheatDraw.hpp"
namespace th143 {
bool draw_cheat_owner(AnmView owner,AnmView save,AnmView ascii,AnmWorld& graphics,CheatDrawHost& host){
    const u32 state=owner.get(0x2b0);
    if(state<3||state>5||((state==4||state==5)&&owner.get(0x14)==1))return true;
    static constexpr u32 inverse[9]={0,3,6,2,5,7,1,4,8};
    static constexpr u32 fields[9][3]={{43,45,44},{50,53,51},{57,60,58},{64,67,65},{73,75,74},{82,85,83},{91,94,92},{98,101,99},{105,107,106}};
    const u32 selected=owner.get(0xec);if(selected>8)return false;const u32 id=inverse[selected];
    auto child=[&](u32 script)->AnmView{
        auto parent=graphics.find(owner.get(0x2d0));if(!parent.data){owner.put(0x2d0,0);return {nullptr};}
        auto v=find_animation_child(graphics,parent,i32(script));return v.data?graphics.find(v.get(0x540)):AnmView{nullptr};
    };
    auto level=child(fields[id][0]);if(!level.data)return false;if(!(level.get(0x18)&2))return true;
    ascii.put(0x191c8,4);ascii.put(0x191b0,0xffe0d0ff);
    ascii.data[0x191b3]=u8(level.get(0x534)>>24);
    auto position=[&](u32 script,std::array<float,3>& out){
        auto vm=child(script);if(!vm.data||!anm_position(vm,graphics.viewport,graphics,out))return false;
        const float scale=graphics.viewport.scale;const float offset=scale*160.f;
        out[0]=(offset+out[0])/scale;out[1]=out[1]/scale;return true;
    };
    std::array<float,3> p;const auto item=save.sub(0xed0c+id*0x34);
    if(!position(fields[id][0],p))return false;
    if(signed_word(item.get(0x1c))>=signed_word(item.get(0x20))){if(!host.cheat_draw_format(p,"M",0))return false;}
    else if(!host.cheat_draw_format(p,"%d",double(signed_word(item.get(0x1c)))))return false;
    if(!position(fields[id][1],p)||!host.cheat_draw_number(p,signed_word(item.get(0x18))))return false;
    if(item.get(0x2c))ascii.put(0x191b0,0xffffe080);
    if(!position(fields[id][2],p)||!host.cheat_draw_number(p,signed_word(item.get(0x24))))return false;
    ascii.put(0x191b0,item.get(0x30)?0xffffe080:0xffe0d0ff);
    if(id<8&&id!=4){
        static constexpr u32 scripts[8]={46,52,59,66,0,84,93,100};
        if(id==1){
            if(!position(52,p))return false;
            const i32 product=signed_word(item.get(0x28)*100);
            if(!host.cheat_draw_format(p,"%d%%",double(product/100)))return false;
        }else if(id==5){
            if(!position(84,p))return false;
            float value=float(signed_word(item.get(0x28)));value*=100.f;value*=real(0x3c000000);
            if(!host.cheat_draw_format(p,"%.0f%%",double(value)))return false;
        }else{
            if(!position(scripts[id],p))return false;
            const float value=float(signed_word(item.get(0x28)))/60.f;
            if(!host.cheat_draw_format(p,"%.2fs",double(value)))return false;
        }
    }
    ascii.put(0x191b0,0xffffffff);ascii.data[0x191b3]=0xff;ascii.put(0x191c8,0);return true;
}
}
