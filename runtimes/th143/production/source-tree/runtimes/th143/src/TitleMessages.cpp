#include "TitleMessages.hpp"
#include <array>
namespace th143 {
namespace {bool newline(u8 ch){return ch==10||ch==13;}bool whitespace(u8 ch){return ch==32||(ch>=9&&ch<=13);}}
bool load_title_messages(AnmView title,u32 source,u32 size,std::vector<u8>& backing){
    if(!title.data||size>backing.size())return false;title.put(0x5ce8,source);title.put(0x5cec,0);u32 at=0,count=0;i32 remaining=signed_word(size);
    auto line=[&](u8* out)->bool{if(at>=backing.size())return false;u32 end=at;while(!newline(backing[end])){if(!remaining)return false;if(++end>=backing.size())return false;--remaining;}if(!remaining)return false;backing[end]=0;u32 n=0;while(at+n<end&&backing[at+n])++n;if(n>=256)return false;std::memcpy(out,backing.data()+at,n);out[n]=0;at=end+1;--remaining;while(at<backing.size()&&newline(backing[at])&&remaining){++at;--remaining;}return true;};
    auto skip=[&](){while(at<backing.size()&&!newline(backing[at])&&remaining){++at;--remaining;}while(at<backing.size()&&newline(backing[at])&&remaining){++at;--remaining;}return !remaining||at<backing.size();};
    while(remaining>0){if(at>=backing.size())return false;if(backing[at]!='@'){if(!skip())return false;continue;}if(count>=64)return false;++at;std::array<u8,256> header{};if(!line(header.data()))return false;auto record=title.sub(0x5cf0+count*0x20c);u32 p=0;
        // Original "%d%d" accepts whitespace, not a comma separator.
        for(u32 field=0;field<2;++field){while(p<header.size()&&whitespace(header[p]))++p;bool negative=false;if(p<header.size()&&(header[p]=='+'||header[p]=='-'))negative=header[p++]=='-';u32 value=0,digits=0;while(p<header.size()&&header[p]>='0'&&header[p]<='9'){value=value*10+header[p++]-'0';++digits;}if(!digits)break;record.put(field*4,negative?0-value:value);}
        if(!line(record.data+8)||!line(record.data+0x108))return false;float widths[2];for(u32 i=0;i<2;++i){const auto* text=record.data+8+i*256;u32 n=0;while(n<256&&text[n])++n;float w=float(n)*8.f;w*=.0625f;w*=16.f;w-=28.f;w*=2.f;widths[i]=w;}record.put(0x208,word(widths[0]>widths[1]?widths[0]:widths[1]));++count;
    }title.put(0x5cec,count);return true;
}
}
