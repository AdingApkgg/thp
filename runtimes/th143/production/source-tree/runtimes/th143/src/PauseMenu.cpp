#include "PauseMenu.hpp"
#include <cctype>

namespace th143 {
namespace {
void timer(AnmView s,u32 at,u32 rate){if(!(s.get(at+16)&1)){s.put(at+12,rate);s.put(at+16,s.get(at+16)|1);}s.put(at,0xffffffff);s.put(at+4,0);s.put(at+8,0);}
bool number(const std::vector<u8>& b,u32& at,u32 end,u32& value){
    while(at<end&&std::isspace(b[at]))++at;bool minus=false;if(at<end&&(b[at]=='+'||b[at]=='-'))minus=b[at++]=='-';
    const u32 begin=at;value=0;while(at<end&&b[at]>='0'&&b[at]<='9')value=value*10+b[at++]-'0';
    if(minus)value=0-value;return at!=begin;
}
}
void PauseMenu::construct(){data.fill(0);view().put(0,2);}
void PauseMenu::state(i32 value,u32 rate){auto s=view();s.put(0x3e8,s.get(0x3e4));s.put(0x3e4,u32(value));s.put(0x3ec,0);timer(s,0x10,rate);}
void PauseMenu::substate(i32 value,u32 rate){auto s=view();s.put(0x3ec,u32(value));timer(s,0x10,rate);}
bool PauseMenu::initialize(const u8* raw,u32 n,u32 token,u32 update,u32 draw,u32 width,PauseMenuHost& host,u32 rate){
    auto s=view();s.put(8,update);s.put(12,draw);timer(s,0x10,rate);timer(s,0x24,rate);
    hints.assign(raw,raw+n);s.put(0xfa0,token);s.put(0xfa4,0);s.put(0x91ac,0);
    u32 at=0,count=0;
    auto skip_newlines=[&](){while(at<n&&(hints[at]=='\r'||hints[at]=='\n'))++at;};
    auto end_line=[&](){u32 end=at;while(end<n&&hints[end]!='\r'&&hints[end]!='\n')++end;return end;};
    auto string=[&](u32 target){const u32 end=end_line();if(end>=n){at=n;return true;}if(end-at>=256)return false;
        std::memcpy(data.data()+target,hints.data()+at,end-at);data[target+end-at]=0;hints[end]=0;at=end+1;skip_newlines();return true;};
    while(at<n){
        if(hints[at]!='@'){at=end_line();skip_newlines();continue;}
        if(count>=64)return false;
        ++at;const u32 end=end_line();if(end>=n)return false;
        u32 cursor=at,a=0,b=0;if(!number(hints,cursor,end,a)||cursor>=end||hints[cursor++]!=','||!number(hints,cursor,end,b))return false;
        const u32 record=0xfa8+count*0x208;s.put(record,a);s.put(record+4,b);s.put(0x91ac,s.get(0x91ac)+b);
        hints[end]=0;at=end+1;skip_newlines();if(!string(record+8)||!string(record+0x108))return false;++count;
    }
    s.put(0xfa4,count);
    const i32 variant=width==640?0:width==960?1:width==1280?2:-1;
    if(variant>=0&&(!host.bind({data.data()+0x404},self+0x404,80+variant)||!host.bind({data.data()+0x9d0},self+0x9d0,83+variant)))return false;
    return true;
}
}
