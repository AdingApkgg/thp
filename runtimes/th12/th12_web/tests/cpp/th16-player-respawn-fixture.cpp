#include "../../cpp/game/PlayerTh16Life.hpp"
#include "../../cpp/game/PlayerFrame.hpp"
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static PlayerFrameState state;static PlayerMotionState motion;static PlayerOption options[12];static u32 events[2][7],count;
struct World:PlayerFrameWorld{
 bool record(u32 kind,const Vec3* p,float r,bool delayed,bool reward){if(!p||count>=2)return false;const u32 row[]={kind,float_bits(p->x),float_bits(p->y),float_bits(p->z),float_bits(r),u32(delayed),u32(reward)};std::memcpy(events[count++],row,sizeof row);return true;}
 bool cancel_bullets(const Vec3* p,float r,bool reward)override{return record(0,p,r,false,reward);}
 bool cancel_lasers(const Vec3* p,float r,bool delayed,bool reward)override{return record(1,p,r,delayed,reward);}
};
API(run_case) bool run_case(i32 age,float x,float z){state={};motion={};state.state_timer.current=age;state.death_position={11.5f,127.25f,-2.f};motion.position={x,80.5f,z};motion.warp=17;motion.warp_timer=19;count=0;for(u32 i=0;i<12;++i){options[i]={};options[i].snap=20+i;}World world;return player_th16_respawn_frame(state,motion,options,world);}
API(value) u32 value(u32 n){return n==0?u32(motion.y):n==1?float_bits(motion.position.x):n==2?float_bits(motion.position.y):n==3?float_bits(motion.position.z):n<16?u32(options[n-4].snap):n==16?motion.warp:motion.warp_timer;}
API(event_count) u32 event_count(){return count;}
API(event) u32 event(u32 n,u32 field){return events[n][field];}
