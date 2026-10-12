#include "../../cpp/game/ShotSchedule.hpp"
#include "../../cpp/game/EclContext.hpp"
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static Th16ShotSchedule schedule;static float rate;
struct Requests:Th16FireFrames{std::vector<u32> events;bool fire(i32 frame,i32 long_frame)override{events.push_back(u32(frame));events.push_back(u32(long_frame));return true;}};static Requests requests;
API(begin) i32 begin(i32 state,u32 held,i32 regular,i32 long_frame,float speed,u32 same){
 schedule={};rate=speed;schedule.locked_id=123;schedule.locked=1;
 schedule.regular.set(regular,&rate);schedule.long_timer.set(long_frame,&rate);for(auto* t:{&schedule.regular,&schedule.long_timer}){if(same)t->previous=t->current;t->fractional+=.25f;}
 requests.events.clear();return schedule.update(state,held,&rate,requests);
}
API(value) u32 value(u32 n){const auto& a=schedule.regular;const auto& b=schedule.long_timer;const u32 words[]={u32(a.previous),u32(a.current),float_bits(a.fractional),u32(b.previous),u32(b.current),float_bits(b.fractional),schedule.locked_id,schedule.locked};return words[n];}
API(count) u32 count(){return requests.events.size()/2;}
API(event) u32 event(u32 n,u32 k){return requests.events[n*2+k];}
