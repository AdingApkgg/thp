#pragma once
#include "TitlePreviewWorker.hpp"

namespace th143 {
//464b20 with the native worker's local values retained across Sleep yields.
// A caller resumes the task only when its declared OS scheduler wakes it.
struct TitlePreviewTask {
    u32 phase=0,day=0,encoded=0,token=0,bytes=0;
    //1: yielded at Sleep;0: returned; -1: external service/state failure.
    i32 resume(GameTitleRuntime&,AnmResourceWorld&,AnmView application,
               TitlePreviewWorkerHost&,u32 budget=100000);
};
}
