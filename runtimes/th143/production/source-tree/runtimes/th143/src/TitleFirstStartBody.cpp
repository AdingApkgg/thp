#include "TitleFirstStartBody.hpp"
namespace th143 {
bool advance_title_first_start_body(TitleFirstStartBindings& b,TitleFirstStartHost& h,u32& result){
    if(!b.title.data||!b.application.data||!b.game.data||b.title.get(0x24)!=5)return false;
    if(b.title.get(0x2b8)==2){
        u32 handle=0;if(!h.first_start_transition(handle))return false;b.application.put(0x1d0,handle);
        if(!h.first_start_signal(handle,7)||!h.first_start_ascii(0x43f00000,0x43c40000))return false;
    }
    if(signed_word(b.title.get(0x2b8))>=38){
        if(!h.first_start_title_state(2)||!h.first_start_clear_title()||!h.first_start_fade(0x40000000))return false;
        b.game.put(0x28,0);b.game.put(0x44,0);b.game.put(0x2c,0);b.game.put(0x48,0);b.scene_descriptor=0x4ddf6c;
        b.game.put(0xac,1);b.game.put(0xb0,1);b.application.put(0x6ec,7);
        b.game.put(0x20,0);b.game.put(0x3c,0);b.game.put(0x24,0);b.game.put(0x40,0);b.game.put(0,0);b.game.put(4,0);b.game.put(12,0);
        if(!h.first_start_initialize_game(0))return false;b.game.put(0x1c,0xffffffff);
        if(!h.first_start_message(1))return false;
    }
    result=1;return true;
}
}
