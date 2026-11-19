#include "FontInitialize.hpp"
#include <algorithm>
namespace th143 {
bool observe_font_family(FontInitializeState& s,const std::array<u8,124>& record,const std::vector<u8>& wanted){
    if(wanted.size()>=64)return true;
    for(u32 i=0;i<wanted.size();++i)if(record[60+i]!=wanted[i])return true;
    if(record[60+wanted.size()])return true;s.alternative=1;return false;
}
bool initialize_fonts(FontInitializeState& s,const FontFamilyNames& names,FontInitializeHost& host){
    if(names[1].size()>31)return false;u32 dc;if(!host.font_screen_dc(dc))return false;
    std::array<u8,60> query{};query[23]=1;std::copy(names[1].begin(),names[1].end(),query.begin()+28);
    std::vector<std::array<u8,124>> records;
    if(!host.enumerate_font_families(dc,query,records))return false;
    for(const auto& r:records)if(!observe_font_family(s,r,names[1]))break;
    if(!host.release_font_screen_dc(dc))return false;
    u32 result;if(!host.initialize_font_bitmap(26,result))return false;
    if(!(result&255)&&!host.initialize_font_bitmap(21,result))return false;
    for(auto& n:s.noise)n=u8(s.animation.next16()>>9);
    // Calls are deliberately kept in native creation order. The ten stored
    // handles have a different order from the CreateFontA requests.
    for(auto row:{std::array<u32,4>{0,0,24,36},{1,0,28,42},{2,0,32,48},{6,0,40,60},
        {4,2,32,32},{8,2,40,40},{3,0,15,16},{5,2,15,15},{7,0,15,16},{9,2,15,15}}){
        const u32 index=row[0];const bool alternative=s.alternative!=0&&row[1]==0;TextFont font;
        font.face=names[alternative?1:row[1]];font.arguments={i32(s.alternative?row[3]:row[2]),0,0,0,
            index==4||index==8?600:index==5||index==9||(!s.alternative&&(index==3||index==7))?700:400,
            0,0,0,128,0,0,2,alternative?1:17};
        u32 handle;if(!host.create_initialized_font(font,handle))return false;s.fonts[index]=std::move(font);s.handles[index]=handle;
    }
    return true;
}
}
