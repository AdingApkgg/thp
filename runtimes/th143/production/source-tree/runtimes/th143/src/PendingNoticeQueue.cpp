#include "PendingNoticeQueue.hpp"
namespace th143 {
bool pop_pending_notice(AnmView save,u32& id){const u32 count=save.get(0xf16c)-1;save.put(0xf16c,count);const u32 at=0xf170+count*4u;if(at>SaveData::bytes-4)return false;id=save.get(at);return true;}
}
