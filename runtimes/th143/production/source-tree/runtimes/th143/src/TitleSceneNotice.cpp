#include "TitleSceneNotice.hpp"
#include "PendingNoticeQueue.hpp"
namespace th143 {
bool advance_title_scene_notice(AnmView title,AnmView save,AnmView notice,u32 owner,TitleSceneNoticeHost& h,bool& handled,u32& result){
 handled=false;result=1;if(title.get(0x1c)!=11||title.get(0x24)!=2||signed_word(title.get(0x2b8))<4)return true;
 if(owner){handled=true;if(!notice.data)return false;
  if(notice.get(0x118)){if(!h.title_notice_destroy())return false;if(signed_word(save.get(0xf16c))<=0&&!title.get(0x28)&&!h.title_notice_dialog(title))return false;}
 }else if(signed_word(save.get(0xf16c))>0){handled=true;u32 id;if(!pop_pending_notice(save,id)||!h.title_notice_create(id))return false;}
 if(!handled)return true;if(!h.title_notice_responses())return false;
 auto timer=title.sub(0x2b4);const u32 previous=timer.get(4),pointer=timer.get(12);timer.put(0,previous);float rate=1;if(pointer&&!h.timer_rate(pointer,rate))return false;
 const bool unit=!pointer||(rate>real(0x3f7d70a4)&&rate<real(0x3f8147ae));const float value=timer.floating(8)+(unit?1.f:rate);timer.put(4,unit?previous+1:value>=-2147483648.f&&value<2147483648.f?u32(i32(value)):0x80000000);timer.put(8,word(value));return true;
}
}
