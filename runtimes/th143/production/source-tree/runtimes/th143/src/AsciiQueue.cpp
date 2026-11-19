#include "AsciiQueue.hpp"
namespace th143 {
bool queue_ascii_text(AnmView owner,const std::array<float,3>& position,std::string_view text,const AnmViewport& viewport,bool interface_layer){
    if(!owner.data)return false;const auto zero=text.find('\0');if(zero!=std::string_view::npos)text=text.substr(0,zero);if(text.size()>255)return false;
    i32 count=signed_word(owner.get(0x191ac));if(count<0||count>320)return false;
    if(count<320){auto entry=owner.sub(0xbac+u32(count)*0x138);owner.put(0x191ac,u32(++count));std::memcpy(entry.data,text.data(),text.size());entry.data[text.size()]=0;
        for(u32 i=0;i<3;++i)entry.put(0x100+i*4,word(position[i]*viewport.scale));
        entry.put(0x128,owner.get(0x191cc));if(entry.get(0x128)==1){entry.put(0x100,word(float(viewport.first_origin[0])+entry.floating(0x100)));entry.put(0x104,word(float(viewport.first_origin[1])+entry.floating(0x104)));}
        static constexpr u32 fields[][2]={{0x10c,0x191b0},{0x110,0x191b4},{0x114,0x191b8},{0x11c,0x191bc},{0x120,0x191c8},{0x124,0x191c4},{0x12c,0x191d0},{0x130,0x191d4},{0x134,0x191d8}};
        for(auto& field:fields)entry.put(field[0],owner.get(field[1]));
    }
    // The original post-call store still marks entry319 when the queue is full.
    if(interface_layer&&count)owner.put(u32(count)*0x138+0xb94,1);return true;
}
std::string format_ascii_number(u32 value){
    if(value<1000)return std::to_string(value);
    std::string out=std::to_string(value%1000);out.insert(0,3-out.size(),'0');
    for(value/=1000;value>=1000;value/=1000){std::string group=std::to_string(value%1000);group.insert(0,3-group.size(),'0');out=group+","+out;}
    return std::to_string(value)+","+out;
}
}
