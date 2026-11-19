#include "NoticeWorkers.hpp"
namespace th143 {
bool run_notice_worker(u32 entry,AnmView s,AnmView w,AnmView update,AnmView draw,NoticeWorkerHost& h,u32& result){
 if(entry==0x446b00||entry==0x446bb0){
  const bool congratulations=entry==0x446bb0;
  if(!h.notice_resource(congratulations?29:19,congratulations?"congra.anm":"notice.anm",result))return false;
  s.put(congratulations?0x128:0x124,result);
  if(!result)return h.notice_resource_error(result);
  if(congratulations)s.put(0x130,6);
  w.put(16,0);w.put(12,1);
  if(!congratulations){update.put(4,update.get(4)|2);draw.put(4,draw.get(4)|2);result=s.get(12);}
  return true;
 }
 if(entry!=0x446b60)return false;
 u32 bytes=s.get(0x1b4);
 if(!h.notice_read_file(reinterpret_cast<const char*>(s.data+0x134),bytes,result))return false;
 s.put(0x1b4,bytes);s.put(0x12c,result);s.put(0x130,3);w.put(16,0);w.put(12,1);return true;
}
}
