#include "../../cpp/game/ShotSchedule.hpp"
#include "../../cpp/game/SeasonTh16.hpp"
#include <cstdlib>
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static ShtResource main_sht,season_sht;
struct Requests:Th16ShotRequests{std::vector<u32> events;bool spawn(u32 packed,i32 frame)override{events.push_back(packed);events.push_back(u32(frame));return true;}};static Requests requests;
API(allocate) void* allocate(u32 n){return std::malloc(n);}
API(open) i32 open(const u8* p,u32 n,u32 sub){return (sub?season_sht:main_sht).open(p,n);}
API(begin) i32 begin(i32 power,i32 points,i32 focus,i32 frame,i32 long_frame){requests.events.clear();Th16SeasonState energy;energy.count=points;return shot_th16_select(main_sht,season_sht,power,100,focus!=0,energy,frame,long_frame,requests);}
API(count) u32 count(){return requests.events.size()/2;}
API(event) u32 event(u32 n,u32 k){return requests.events[n*2+k];}
