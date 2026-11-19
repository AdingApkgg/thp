#pragma once
#include "PendingNoticeQueue.hpp"
namespace th143 {
struct NoticeResultsHost:AnmTimerHost {
 virtual bool results_create_notice(u32 id,u32& owner)=0;
 virtual bool results_destroy_notice(u32 owner)=0;
};
// Notice branches of44aae0 within actual447db0 wrapper. Every handled branch
// advances both menu clocks, including creation and destruction early returns.
bool results_notice_gate(AnmView menu,AnmView save,AnmView notice,u32& owner,NoticeResultsHost&,bool& handled);
}
