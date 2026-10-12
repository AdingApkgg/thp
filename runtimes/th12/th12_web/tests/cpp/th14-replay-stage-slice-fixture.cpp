#include "../../cpp/game/Replay.hpp"
#include "../../cpp/game/Lzss.hpp"
#include "../../cpp/game/ResourceCrypt.hpp"
#include <cstdlib>
#include <cstring>
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static std::vector<u8> sliced;
API(allocate) void* allocate(u32 n){return std::malloc(n);}
API(release) void release(void* p){std::free(p);}
API(slice_stage) u32 slice_stage(const u8* p,u32 size,u32 stage){
 Replay replay;if(!replay.open(p,size))return 0;
 const auto* entry=replay.stage(stage);if(!entry)return 0;
 const auto& original=replay.decoded();std::vector<u8> decoded(original.begin(),original.begin()+kReplayFileHeader);
 const auto put=[](u8* p,u32 x){std::memcpy(p,&x,4);};
 put(decoded.data()+0x78,1);
 decoded.insert(decoded.end(),original.begin()+entry->offset,original.begin()+entry->offset+kReplayStageHeader+entry->payload_size);
 Lzss codec;const auto packed=codec.encode(decoded.data(),u32(decoded.size()));const u32 n=u32(packed.size());if(!n)return 0;
 std::vector<u8> first(n),second(n);
 if(!resource_crypt(packed.data(),first.data(),n,{0x7d,0x3a,0x100,n},true)||!resource_crypt(first.data(),second.data(),n,{0x5c,0xe1,0x400,n},true))return 0;
 sliced.assign(p,p+0x24);put(sliced.data()+12,0x24+n);put(sliced.data()+28,n);put(sliced.data()+32,u32(decoded.size()));sliced.insert(sliced.end(),second.begin(),second.end());
 Replay check;if(!check.open(sliced.data(),u32(sliced.size()))||check.stage_count()!=1)return 0;
 const auto* copy=check.stage(stage);return copy&&copy->frames==entry->frames&&copy->payload_size==entry->payload_size&&std::memcmp(check.header(stage),replay.header(stage),kReplayStageHeader+entry->payload_size)==0;
}
API(slice_data) const u8* slice_data(){return sliced.data();}
API(slice_size) u32 slice_size(){return u32(sliced.size());}
