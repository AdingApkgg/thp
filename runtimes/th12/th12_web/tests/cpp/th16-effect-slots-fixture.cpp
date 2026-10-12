#include "../../cpp/game/EffectTh16Slots.hpp"
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static Th16EffectSlots slots;static u32 events[1024],count;
struct Lookup:Th16EffectLookup{bool alive(u32 id)override{events[count++]=id;return id%4==1;}};
API(begin_case) void begin_case(i32 cursor,u32 mode,u32 seed){
 slots={};slots.cursor=cursor;for(u32 i=0;i<1024;++i){seed=seed*1664525u+1013904223u;slots.ids[i]=mode==0?0:mode==1?1:mode==2?2:mode==3&&i==17?0:mode==4&&i==17?1:mode==3||mode==4?2:seed%7;}
}
API(step) i32 step(u32 id){count=0;Lookup lookup;const i32 slot=slots.choose(lookup);if(slot>=0)slots.ids[u32(slot)]=id;return slot;}
API(cursor) i32 cursor(){return slots.cursor;}
API(value) u32 value(u32 n){return slots.ids[n];}
API(event_count) u32 event_count(){return count;}
API(event) u32 event(u32 n){return events[n];}
