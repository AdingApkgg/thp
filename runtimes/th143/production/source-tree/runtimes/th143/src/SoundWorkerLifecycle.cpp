#include "SoundWorkerLifecycle.hpp"
namespace th143 {
bool run_sound_worker_lifecycle(AnmView audio,u32 bytes,SoundWorkerOperation op,u32 window,SoundWorkerLifecycleHost& host,u32& result){
    if(!audio.data||bytes<0x57b0)return false;
    if(op==SoundWorkerOperation::Construct){if(!host.zero_sound_owner(audio,0x57b0))return false;audio.put(0x579c,window);u32 handle=0;if(!host.create_sound_device_worker(0x471ed0,0x53b1e0,audio,handle))return false;audio.put(0x578c,handle);result=0;return true;}
    if(op==SoundWorkerOperation::Abort){audio.put(0x5798,2);result=0;return true;}
    if(op==SoundWorkerOperation::DeviceWorker){u32 ignored=0;if(!host.initialize_worker_sound_device(audio.get(0x579c),audio,ignored))return false;for(u32 waits=0;audio.get(0x5798)==0;++waits){if(waits==1000000||!host.sleep_sound_worker(1))return false;}audio.put(0x57a0,1);result=0;return true;}
    if(op!=SoundWorkerOperation::Drain)return false;const u32 first=audio.get(0x578c);if(!first){result=0;return true;}if(!audio.get(0x5798))audio.put(0x5798,1);
    u32 status=0;if(!host.wait_sound_worker(first,100,status))return false;
    for(u32 waits=0;status==0x102;++waits){if(waits==1000000||!host.sleep_sound_worker(1)||!host.wait_sound_worker(audio.get(0x578c),100,status))return false;}
    if(!host.wait_sound_worker(audio.get(0x5790),100,status))return false;
    for(u32 waits=0;status==0x102;++waits){if(waits==1000000||!host.sleep_sound_worker(1)||!host.wait_sound_worker(audio.get(0x5790),100,status))return false;}
    if(!host.close_sound_worker(audio.get(0x578c))||!host.close_sound_worker(audio.get(0x5790)))return false;audio.put(0x578c,0);audio.put(0x5790,0);result=0;return true;
}
}
