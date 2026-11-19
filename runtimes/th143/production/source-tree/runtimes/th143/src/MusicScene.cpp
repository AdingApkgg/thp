#include "MusicScene.hpp"
#include <string>
namespace th143 {
bool MusicScene::load(MusicCommandQueue& queue,const char* name){
    if(!name)return false;u32 n=0;while(n<252&&name[n])++n;if(n==252)return false;
    return queue.enqueue(1,0,(std::string(name,n)+".wav").c_str());
}
bool MusicScene::pump_silent(MusicCommandQueue& queue,bool wrapper,bool bgm,bool playback){
    if(!wrapper)return true;if(bgm||playback)return false;
    auto s=queue.view();
    for(u32 budget=0;budget<MusicCommandQueue::count;++budget){
        const u32 kind=s.get(0);if(!kind)return true;if(kind!=1&&kind!=2)return false;
        if(kind==1){
            const u32 index=s.get(4);if(index>=path_count)return false;
            u32 n=0;while(n<path_bytes&&s.data[12+n])++n;if(n==path_bytes)return false;
            std::memcpy(paths.data()+index*path_bytes,s.data+12,n+1);
        }
        // Native shifts through the first empty entry. The physical sentinel
        // after the 31 searchable slots is declared zero in this cold branch.
        for(u32 i=0;i<MusicCommandQueue::count&&s.get(i*MusicCommandQueue::stride);++i){
            if(i+1==MusicCommandQueue::count)std::memset(s.data+i*MusicCommandQueue::stride,0,MusicCommandQueue::stride);
            else std::memmove(s.data+i*MusicCommandQueue::stride,s.data+(i+1)*MusicCommandQueue::stride,MusicCommandQueue::stride);
        }
        if(kind!=1)return true;
    }
    return true;
}
}
