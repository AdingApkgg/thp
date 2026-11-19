#include "TrophyCatalog.hpp"
namespace th143 {
namespace {
bool newline(u8 c){return c==10||c==13;}
void initialize(AnmView record,Rng& rng){
    record.put(0,0xffffffff);
    for(u32 i=0;i<256;++i)for(u32 s:{0u,1u,4u,2u,5u,3u,6u})record.data[4+s*256+i]=u8(rng.next32());
}
bool encrypt(u8* p){u8 key=0x77,step=7;for(u32 i=0;i<256;++i){const u8 ch=p[i];p[i]=ch^key;key+=step;step+=0x10;if(!ch)return true;}return false;}
}
bool TrophyCatalog::load(const u8* raw,u32 size,Rng& rng){
    if(!raw&&size)return false;source.clear();if(size)source.assign(raw,raw+size);
    u32 at=0; i32 remaining=i32(size);
    //468160/inline line reads keep an independent remaining count. In the
    // @header path native skips '@' without decrementing that count.
    auto line=[&](u8* out)->bool{
        if(at>=source.size())return false;u32 end=at;
        while(!newline(source[end])){if(!remaining)return false;if(++end>=source.size())return false;--remaining;}
        if(!remaining)return false;source[end]=0;u32 n=0;
        while(n<end-at&&source[at+n])++n;if(n>=256)return false;
        std::memcpy(out,source.data()+at,n);out[n]=0;at=end+1;--remaining;
        while(at<source.size()&&newline(source[at])&&remaining){++at;--remaining;}return true;
    };
    auto skip=[&]()->bool{while(at<source.size()&&!newline(source[at])&&remaining){++at;--remaining;}while(at<source.size()&&newline(source[at])&&remaining){++at;--remaining;}return at<source.size()||!remaining;};
    while(remaining>0){
        if(at>=source.size())return false;const u8 ch=source[at];if(ch=='\\')return true;
        if(ch=='#'){if(!skip())return false;continue;}
        if(ch!='@'){if(!skip())return false;continue;}
        ++at;std::array<u8,256> header{};if(!line(header.data()))return false;
        u32 p=0;while(p<header.size()&&(header[p]==' '||(header[p]>=9&&header[p]<=13)))++p;
        bool negative=false;if(p<header.size()&&(header[p]=='+'||header[p]=='-'))negative=header[p++]=='-';
        u32 id=0,digits=0;while(p<header.size()&&header[p]>='0'&&header[p]<='9'){id=id*10+header[p++]-'0';++digits;}if(negative)id=0-id;
        if(!digits||id>=count)return false;AnmView record{data.data()+id*stride};initialize(record,rng);record.put(0,id);
        for(u32 i=0;i<7;++i){auto* text=record.data+4+i*256;if(!line(text)||!encrypt(text))return false;}
    }return true;
}
}
