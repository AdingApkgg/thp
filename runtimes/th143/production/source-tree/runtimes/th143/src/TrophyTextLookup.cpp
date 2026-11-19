#include "TrophyTextLookup.hpp"
namespace th143 {
namespace {
bool lookup(AnmView catalog,u32 index,u32 slot,AnmView scratch,u32& result){
 if(!catalog.data||!scratch.data||index>=70||slot>=7)return false;auto record=catalog.sub(index*0x704);result=0;if(record.get(0)!=index)return true;u8 key=0x77,step=7;
 for(u32 i=0;i<256;++i){const u8 value=record.data[4+slot*256+i]^key;key+=step;step+=0x10;scratch.data[i]=value;if(!value){result=0x541360;return true;}}return false;
}
}
bool lookup_trophy_name(AnmView c,u32 index,AnmView scratch,u32& result){return lookup(c,index,0,scratch,result);}
bool lookup_trophy_description(AnmView c,u32 index,u32 unlocked,u32 line,AnmView scratch,u32& result){if(unlocked>1||line>2)return false;return lookup(c,index,1+unlocked*3+line,scratch,result);}
}
