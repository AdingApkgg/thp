#include "HudMessage.hpp"
#include <initializer_list>
namespace th143 {
bool update_hud_message(AnmView hud,AnmView save,HudMessageGlobals& g,HudMessageHost& h){
    const i32 pending=signed_word(hud.get(0x2a8));
    if(pending>=0&&g.player_state!=2){if(!g.root_mode&&!h.create_hud_message(pending))return false;hud.put(0x2a8,0xffffffff);}
    const u32 token=hud.get(0x198);
    if(token){
        i32 result;if(!h.update_hud_message_owner(token,result))return false;
        if(!result){
            AnmView message;if(!h.hud_message_view(token,message)||!message.data)return false;
            const u32 old=message.get(8),rate_token=message.get(0x10);message.put(4,old);float rate=1;
            if(rate_token&&!h.timer_rate(rate_token,rate))return false;
            const bool unit=!rate_token||(rate>real(0x3f7d70a4)&&rate<real(0x3f8147ae));const float value=message.floating(0xc)+(unit?1.f:rate);
            message.put(8,unit?old+1:value>=-2147483648.f&&value<2147483648.f?u32(i32(value)):0x80000000);message.put(0xc,word(value));
        }else if(!g.dialog){
            AnmView message;if(!hud.get(0x198)||!h.hud_message_view(hud.get(0x198),message)||!message.data)return false;
            if(message.get(0x184)&0x80)g.root_flags&=~0x10u;
            const u32 current=hud.get(0x198);if(current&&!h.destroy_hud_message_owner(current))return false;hud.put(0x198,0);
        }
    }
    if(g.dialog){
        AnmView dialog;if(!h.hud_dialog_view(g.dialog,dialog)||!dialog.data)return false;
        if(!dialog.get(0x128))return true;
        if(dialog.get(0x130)==2){
            if((g.game_flags&0xc00)==0xc00){
                if(!save.data)return false;g.presentation=6;g.transition=1;g.application_state=(g.config&0x2000)?2:4;
                for(u32 value:{3,2,1}){const u32 count=save.get(0xf16c);if(count>=16)return false;save.put(0xf170+count*4,value);save.put(0xf16c,count+1);}
            }else{
                AnmView message;if(!hud.get(0x198)||!h.hud_message_view(hud.get(0x198),message)||!message.data)return false;
                message.put(0x184,message.get(0x184)&~0x80u);if(!h.request_hud_dialog_result())return false;
            }
        }else g.root_flags&=~0x10u;
        if(g.dialog&&!h.destroy_hud_dialog(g.dialog))return false;
    }return true;
}
}
