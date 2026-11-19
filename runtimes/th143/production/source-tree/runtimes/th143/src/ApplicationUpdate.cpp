#include "ApplicationUpdate.hpp"
#include <initializer_list>
namespace th143 {
bool update_application(AnmView app,ApplicationUpdateGlobals& g,ApplicationUpdateServices& host,i32& result){
    if(!app.data)return false;
    if((app.get(0x724)&0x180)==0x80&&!app.get(0x99c))app.put(0x6ec,3);
    u32 value;for(u32 entry:{0x472df0u,0x446920u,0x401fa0u,0x4827d0u})if(!host.application_update_call(entry,0,value))return false;
    if(value){result=4;return true;}
    if(g.countdown)--g.countdown;
    if(const u32 state=app.get(0x9a8)){result=state==2?4:1;return true;}
    if(!host.application_update_call(0x4458a0,0x4e47d0,value))return false;
    result=signed_word(value);
    if(result==1){g.center_x=u32(signed_word(g.width)/2);g.center_y=u32(signed_word(g.height-448)/2);}
    return true;
}
}
