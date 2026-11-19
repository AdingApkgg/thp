#pragma once
#include "TitleLoad.hpp"
namespace th143 {
struct TitleReplayCleanupHost {
    virtual ~TitleReplayCleanupHost()=default;
    virtual bool cleanup_title_replay(u32)=0;
};
//45f6a0 ->45f370. Replay-list objects can use the existing GameManager cleanup
// through the caller; an unbound nonempty replay list rejects before mutation.
bool destroy_title(TitleLoadBindings&,RootFactoryHost&,TitleReplayCleanupHost* replays=nullptr,u32 wait_budget=100000);
}
