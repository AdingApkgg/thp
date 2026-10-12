#include "../../cpp/game/ShtResource.hpp"
#include "../../cpp/game/SoundEffects.hpp"
#include <cstdlib>
using namespace th11;
static ShtResource sht;
static u8 record[0x58],header[0xe0];
#define API(name) extern "C" __attribute__((export_name(#name)))
API(allocate) void* allocate(u32 n){return std::malloc(n);}
API(release) void release(void* p){std::free(p);}
API(open_sht) i32 open_sht(const void* p,u32 n){return sht.open(static_cast<const u8*>(p),n);}
API(group_count) u32 group_count(){return sht.groups.size();}
API(shot_count) u32 shot_count(u32 g){return sht.groups[g].shots.size();}
API(shot_data) const u8* shot_data(u32 g,u32 n){const auto& s=sht.groups[g].shots[n];std::memcpy(record,&s,0x1c);std::memcpy(record+0x1c,&s.native_at_1c,4);std::memcpy(record+0x20,reinterpret_cast<const u8*>(&s)+0x1c,0x18);std::memcpy(record+0x38,s.native_tail.data(),0x20);return record;}
API(header_data) const u8* header_data(){std::memcpy(header,&sht.header,0x28);std::memcpy(header+0x28,sht.header.native_extra.data(),0x18);std::memcpy(header+0x40,sht.header.option_offsets.data(),0xa0);return header;}
API(voice_count) u32 voice_count(){return sound_voice_count;}
API(sample_count) u32 sample_count(){return sound_sample_count;}
API(sample_name) const char* sample_name(u32 n){return sound_samples[n];}
API(voice_value) i32 voice_value(u32 n,u32 f){const auto& v=sound_definitions[n];return f==0?v.sample:f==1?v.volume:v.metadata;}
