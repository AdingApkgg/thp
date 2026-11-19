#pragma once
#include "AnmState.hpp"
#include <array>
namespace th143 {
struct TitleReplayWorkerHost {
 virtual ~TitleReplayWorkerHost()=default;
 virtual bool replay_worker_allocate(u32 bytes,u32& token,AnmView&)=0;
 virtual bool replay_worker_load(u32 token,const u8* name,u32 bytes,u32& result)=0;
 virtual bool replay_worker_destroy(u32 token)=0;
 virtual bool replay_worker_free(u32 token)=0;
 virtual bool replay_worker_directory(u32 path)=0;
 virtual bool replay_worker_first(u32 pattern,std::array<u8,320>& data,u32& handle)=0;
 virtual bool replay_worker_next(u32 handle,std::array<u8,320>& data,u32& result)=0;
 virtual bool replay_worker_close(u32 handle)=0;
};
//464e60 (4650b0 trampoline): numbered1..25 then up to50user files. Even a
//cancelled numbered loop proceeds throughFindFirst and onefounduser entry.
//CompleteFindDataA/nonnull17callocation/terminatedfilename<=255 domain.
bool load_title_replay_list(AnmView title,TitleReplayWorkerHost&);
}
