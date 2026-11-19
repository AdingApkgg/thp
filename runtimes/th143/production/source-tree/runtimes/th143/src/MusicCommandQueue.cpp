#include "MusicCommandQueue.hpp"
namespace th143 {
bool MusicCommandQueue::enqueue(u32 kind,u32 parameter,const char* name){
    if(!name)return false;u32 size=0;while(size<256&&name[size])++size;if(size==256)return false;
    auto s=view();for(u32 i=0;i<count;++i){auto q=s.sub(i*stride);if(q.get(0))continue;
        q.put(0,kind);q.put(4,parameter);std::memcpy(q.data+12,name,size+1);q.put(8,0);break;
    }return true;
}
bool MusicCommandQueue::start(SaveData& save,u32 parameter,u32 track,u32 flags){
    if(track>=save.data.size()-0xef74)return false;
    if((flags&0x10)&&!enqueue(4,0,"dummy"))return false;
    if(!enqueue(2,parameter,"dummy"))return false;save.data[0xef74+track]=1;return true;
}
}
