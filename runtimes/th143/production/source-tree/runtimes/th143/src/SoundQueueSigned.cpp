#include "SoundQueue.hpp"

namespace th143 {
bool SoundQueue::pause(SoundQueueHost& host){
    auto s=view();s.put(0,0xffffffff);
    for(u32 at=0x1a68;at<bytes;at+=24){
        s.put(at+20,0);if(const u32 token=s.get(at)){u32 status;if(!host.stop_buffer(token,status))return false;s.put(at+20,status&1);}
    }return true;
}
bool SoundQueue::enqueue(u32 sound,i32 priority){
    return enqueue_pan(sound,priority,0);
}
bool SoundQueue::request(u32 sound,bool spatial,float x){
    // Signed priority words from v1.00a table4e128a, stride20.
    static constexpr i32 priorities[88]={0,0,5,5,100,100,100,50,50,50,100,100,10,10,100,50,50,50,100,0,0,0,20,20,20,50,50,50,100,20,90,20,50,100,100,0,100,100,100,100,100,100,100,100,100,100,100,100,100,0,0,0,0,0,100,0,100,100,100,100,100,100,100,100,5,5,100,100,5,100,100,0,0,0,100,100,100,100,100,100,100,100,100,100,100,100,100,100};
    if(sound>=88&&sound!=0xffffffff)return false;u32 pan=0;
    if(spatial){const float scaled=(x*1000.f)/192.f;pan=scaled>=-2147483648.f&&scaled<2147483648.f?u32(i32(scaled)):0x80000000u;}
    return enqueue_pan(sound,sound==0xffffffff?0:priorities[sound],pan);
}
bool SoundQueue::enqueue_pan(u32 sound,i32 priority,u32 pan){
    if(sound>=88&&sound!=0xffffffff)return false;auto s=view();
    for(u32 i=0;i<12;++i){
        const i32 id=signed_word(s.get(i*4));
        if(id<0){s.put(i*4,sound);s.put(0x60+i*512,pan);s.put(0x30+i*4,1);s.put(sound==0xffffffff?0x1a54:0x1a6c+sound*24,u32(priority));return true;}
        if(u32(id)==sound){const i32 n=signed_word(s.get(0x30+i*4));if(n>=0&&n<60){s.put(0x60+(i*128+u32(n))*4,pan);s.put(0x30+i*4,u32(n)+1);}return true;}
    }return true;
}
}
