#include "TitleFinalNoticeV141.hpp"
#include "AnmSignal.hpp"
namespace th143 {
bool advance_title_final_notice_v141(TitleActivationBindings& b,AnmMenuWorld& menu,AnmView notice,TitleFinalNoticeHost& host,bool& handled,u32& result){
 handled=false;auto title=b.title.view(),save=b.save.view();auto& g=b.globals;
 if(title.get(0x1c))return true;
 const i32 count=signed_word(save.get(0xf16c));
 if(!g.trophy_owner&&(count<=0||count>16||save.get(0xf16c+u32(count)*4)!=39))return true;
 handled=true;if(!advance_title_return_music(b))return false;
 auto ascii=b.ascii.view();const u32 fade=b.application.get(0x1d0);
 if(b.world.find(fade).data){
  if(!signal_animation(b.world,ascii.get(0x191e8),1,false)||!signal_animation(b.world,ascii.get(0x191ec),1,false)||!menu.screen_transition_signal(fade,1))return false;
  ascii.put(0x191ec,0);title.put(0xe000,title.get(0xe000)|0x40u);
 }
 b.application.put(0x1d0,0);g.fade_handle=0;
 if(!signal_animation(b.world,ascii.get(0x191ec),1,false))return false;ascii.put(0x191ec,0);
 if(g.trophy_owner){if(!notice.data)return false;if(notice.get(0x118)&&!host.final_notice_destroy())return false;}
 else {save.put(0xf16c,u32(count-1));const u32 id=save.get(0xf170+u32(count-1)*4);if(!host.final_notice_create(id))return false;g.return_mode=0;}
 // Both original early returns leave the Title clock untouched.
 result=1;return true;
}
}
