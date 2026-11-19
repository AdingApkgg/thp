#include "MenuCursor.hpp"

namespace th143 {
namespace {
bool skip(AnmView s,u32& budget){
    const i32 count=signed_word(s.get(8)),n=signed_word(s.get(0xd4));if(n<0||n>16)return false;
    for(;;){bool disabled=false;for(i32 i=0;i<n;++i)if(s.get(0x90+u32(i)*4)==s.get(0)){disabled=true;break;}
        if(!disabled)return true;if(!budget--)return false;s.put(0,s.get(0)+1);if(signed_word(s.get(0))>=count)s.put(0,0);
    }
}
}
bool MenuCursor::select(i32 value,u32 budget){
    const i32 count=signed_word(state.get(8));if(count==0){state.put(0,u32(value));return true;}
    state.put(0,u32(value>=count?count-1:value<0?0:value));return skip(state,budget);
}
bool MenuCursor::move(i32 amount,i32& result,u32 budget){
    const i32 count=signed_word(state.get(8));if(count<=0){result=signed_word(state.get(0));return true;}
    const i32 n=signed_word(state.get(0xd4));if(n<0||n>16)return false;
    for(;;){
        if(!budget--)return false;state.put(0,state.get(0)+u32(amount));
        while(signed_word(state.get(0))>=count){if(!budget--)return false;state.put(0,state.get(0xd0)?state.get(0)-u32(count):u32(count-1));}
        while(signed_word(state.get(0))<0){if(!budget--)return false;state.put(0,state.get(0xd0)?state.get(0)+u32(count):0);}
        bool blocked=false;for(i32 i=0;i<n;++i)if(state.get(0x90+u32(i)*4)==state.get(0)){blocked=true;break;}
        if(!blocked){result=signed_word(state.get(0));return true;}
    }
}
bool MenuCursor::disable(i32 value,u32 budget){
    const u32 n=state.get(0xd4);if(n>=16)return false;state.put(0x90+n*4,u32(value));state.put(0xd4,n+1);return skip(state,budget);
}
bool MenuCursor::push(){
    const u32 depth=state.get(0x8c);if(depth>=16)return false;state.put(12+depth*4,state.get(0));state.put(0x4c+depth*4,state.get(8));
    state.put(0x8c,depth+1>=16?15:depth+1);state.put(0xd4,0);return true;
}
void MenuCursor::pop(){
    const i32 depth=signed_word(state.get(0x8c)-1);state.put(0x8c,u32(depth));
    if(depth<0){state.put(0x8c,0);state.put(0,0);}else if(depth<16){state.put(0,state.get(12+u32(depth)*4));state.put(8,state.get(0x4c+u32(depth)*4));}
    state.put(0xd4,0);
}
}
