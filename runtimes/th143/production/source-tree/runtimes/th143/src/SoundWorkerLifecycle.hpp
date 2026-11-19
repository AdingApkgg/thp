#pragma once
#include "SoundReload.hpp"
namespace th143 {
struct SoundWorkerLifecycleHost:SoundReloadHost {
    virtual bool zero_sound_owner(AnmView audio,u32 bytes)=0;
    virtual bool create_sound_device_worker(u32 entry,u32 parameter,AnmView audio,u32& handle)=0;
    virtual bool initialize_worker_sound_device(u32 window,AnmView audio,u32& result)=0;
};
enum class SoundWorkerOperation:u32 {Construct,DeviceWorker,Abort,Drain};
//471dc0/471ed0/471e10/471e20 at global53b1e0. DeviceWorker's incidental EAX is
//not a portable return value; other operations explicitly return zero.
bool run_sound_worker_lifecycle(AnmView audio,u32 bytes,SoundWorkerOperation,u32 window,
                                SoundWorkerLifecycleHost&,u32& result);
}
