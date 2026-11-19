#pragma once
#include "TitleReturnActivation.hpp"
namespace th143 {
struct TitleFinalNoticeHost {
 virtual bool final_notice_create(u32 id)=0;
 virtual bool final_notice_destroy()=0;
};
// Original 45f6e0 state-zero overlay branch, before normal activation.
bool advance_title_final_notice_v141(TitleActivationBindings&,AnmMenuWorld&,AnmView notice,TitleFinalNoticeHost&,bool& handled,u32& result);
}
