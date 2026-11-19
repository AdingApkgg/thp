#include "TitleReplayWorker.hpp"
#include <cstdio>
namespace th143 {
bool load_title_replay_list(AnmView t,TitleReplayWorkerHost& h){
 if(!t.data)return false;auto load=[&](u32 slot,const u8* name,u32 n){u32 token;AnmView object;if(!h.replay_worker_allocate(0x17c,token,object)||!token||!object.data)return false;std::memset(object.data,0,0x17c);object.put(0x10,2);u32 status;if(!h.replay_worker_load(token,name,n,status))return false;if(status){if(!h.replay_worker_destroy(token)||!h.replay_worker_free(token))return false;token=0;}t.put(0x5b54+slot*4,token);return true;};
 for(u32 i=1;i<=25;++i){char name[64];const i32 n=std::snprintf(name,sizeof name,"th143_%.2d.rpy",i);if(n<0||u32(n)>=sizeof name||!load(i-1,reinterpret_cast<const u8*>(name),u32(n)+1))return false;if(t.get(0xe000)&4)break;}
 if(!h.replay_worker_directory(0x5390cd)||!h.replay_worker_directory(0x4c7be4))return false;std::array<u8,320> data{};u32 handle;if(!h.replay_worker_first(0x4c7bec,data,handle))return false;
 if(handle!=0xffffffff)for(u32 slot=25;slot<75;++slot){if(!h.replay_worker_directory(0x53a0cd))return false;u32 n=0;while(n<256&&data[44+n])++n;if(n>=256||!load(slot,data.data()+44,n+1)||!h.replay_worker_directory(0x5390cd)||!h.replay_worker_directory(0x4c7be4))return false;if(t.get(0xe000)&4)break;u32 found;if(!h.replay_worker_next(handle,data,found))return false;if(!found)break;}
 if(!h.replay_worker_close(handle)||!h.replay_worker_directory(0x53a0cd))return false;t.put(0xe000,(t.get(0xe000)&~4u)|8);return true;
}
}
