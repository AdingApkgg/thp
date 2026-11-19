#include "NoticeResultsGate.hpp"
namespace th143 {
namespace {
bool tick(AnmView t,NoticeResultsHost& h){const u32 old=t.get(4),token=t.get(12);float rate=1;if(token&&!h.timer_rate(token,rate))return false;t.put(0,old);const bool unit=!token||(rate>real(0x3f7d70a4)&&rate<real(0x3f8147ae));const float value=t.floating(8)+(unit?1.f:rate);t.put(8,word(value));t.put(4,unit?old+1:value>=-2147483648.f&&value<2147483648.f?u32(i32(value)):0x80000000);return true;}
}
bool results_notice_gate(AnmView m,AnmView save,AnmView notice,u32& owner,NoticeResultsHost& h,bool& handled){
 handled=false;if(m.get(0x3e4)!=3||m.get(0x3ec)!=1)return true;
 if(owner){if(!notice.data)return false;handled=true;if(notice.get(0x118)){if(!h.results_destroy_notice(owner))return false;owner=0;}}
 else if(signed_word(save.get(0xf16c))>0){handled=true;u32 id;if(!pop_pending_notice(save,id)||!h.results_create_notice(id,owner))return false;}
 return !handled||(tick(m.sub(0x10),h)&&tick(m.sub(0x24),h));
}
}
