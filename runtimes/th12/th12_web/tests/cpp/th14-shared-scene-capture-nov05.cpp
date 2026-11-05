// Asset-free test of the real SceneCamera layout/read job and a live Wasm
// publisher. Synthetic words only; no original game state is imported.
#include "SceneCameraReadJobTh14.hpp"
#include <array>
#include <cstring>
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
#define IMPORT(name) __attribute__((import_module("camera"),import_name(#name)))
extern "C" IMPORT(now_ms) double now_ms();
extern "C" IMPORT(read) u32 camera_read(u32,u32,u32,u32,u32);
namespace {
SceneCamera source;
SceneCameraReadJobTh14 copy;
const auto layout=[](){std::array<u32,75> words{};for(u32 i=0;i<75;++i)words[i]=SceneCameraReadJobTh14::source_offset(i);return words;}();
void store(u32 index,u32 value){
    *reinterpret_cast<volatile u32*>(reinterpret_cast<u8*>(&source)+layout[index])=value;
}
}
API(source_pointer) const SceneCamera* source_pointer(){return &source;}
API(layout_pointer) const u32* layout_pointer(){return layout.data();}
API(reset_copy) u32 reset_copy(){return copy.reset();}
API(fill) void fill(u32 base){for(u32 index=0;index<75;++index)store(index,base|index);}
API(source_word) u32 source_word(u32 index){u32 word=0;if(index<75)std::memcpy(&word,reinterpret_cast<const u8*>(&source)+layout[index],4);return word;}
API(snapshot_word) u32 snapshot_word(u32 index){u32 word=0;if(index<75)std::memcpy(&word,reinterpret_cast<const u8*>(&copy.snapshot())+layout[index],4);return word;}
API(copied_words) u32 copied_words(){return copy.copied_words();}
API(default_copy) u32 default_copy(u32 until,u32 fail){
    return u32(copy.advance(source,[&](u32 index){return index<until?prototype::Work::Ready:
        fail?prototype::Work::Failed:prototype::Work::Waiting;}));
}
API(worker_copy) u32 worker_copy(){
    return u32(copy.advance(source,[](u32){return prototype::Work::Ready;},[](u32 index,u32 offset,u32& value){
        const auto status=camera_read(u32(reinterpret_cast<uintptr_t>(&source)),u32(reinterpret_cast<uintptr_t>(layout.data())),
            index,offset,u32(reinterpret_cast<uintptr_t>(&value)));
        return status==0?prototype::Work::Waiting:status==1?prototype::Work::Ready:prototype::Work::Failed;
    }));
}
API(publish_for_ms) u32 publish_for_ms(double duration){
    const auto start=now_ms();u32 generation=0;
    while(now_ms()-start<duration){
        ++generation;for(u32 index=0;index<75;++index)store(index,(generation<<8)|index);
    }
    // After this call returns every source word is distinguishable from a
    // value read during the blocking C++ call. The worker has no handshake
    // telling the publisher where or when to stop between these stores.
    for(u32 index=0;index<75;++index)store(index,0xdead0000u|index);
    return generation;
}
