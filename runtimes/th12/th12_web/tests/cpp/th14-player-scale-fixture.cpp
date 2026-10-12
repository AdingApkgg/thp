#include "../../cpp/game/PlayerFrame.hpp"
#include <cstdlib>
using namespace th11;
static PlayerTh14Scale scale;static float rate=1,other=1;static u32 pointer;static u32 visual[3],regions[24];
#define API(name) extern "C" __attribute__((export_name(#name)))
API(allocate) void* allocate(u32 n){return std::malloc(n);}API(release) void release(void* p){std::free(p);}
static void load(const u32* p){scale={};scale.flags=p[0];auto& v=scale.interpolation;v.start[0]=float_bits(p[1]);v.end[0]=float_bits(p[2]);v.initial_tangent[0]=float_bits(p[3]);v.final_tangent[0]=float_bits(p[4]);v.timer.previous=i32(p[5]);v.timer.current=i32(p[6]);v.timer.fractional=float_bits(p[7]);pointer=p[8];v.timer.rate=pointer==1?&other:pointer==2?&rate:nullptr;v.timer.flags=p[9];v.duration=i32(p[10]);v.mode=InterpolationMode(p[11]);scale.factor=float_bits(p[12]);scale.recall=i32(p[13]);}
API(request) i32 request(const u32* p,u32 value){load(p);return scale.request(float_bits(value),&rate);}
API(update) void update(const u32* p,u32 speed,i32 frame){load(p);rate=float_bits(speed);const float s=scale.update(frame,&rate);visual[0]=visual[1]=float_bits(s);visual[2]=8;
 PlayerFrameState state;state.hit_half={1,2,5};state.pickup_size={30,35,5};state.focused_half={50,59,5};player_th14_scale_bounds(state,{12.25,-80.5,3.25},scale.factor);
 const PlayerBounds b[]={state.hit,state.pickup,state.focused_attract,state.unfocused_attract};
 for(u32 j=0;j<4;++j){const float values[]={b[j].minimum.x,b[j].minimum.y,b[j].minimum.z,b[j].maximum.x,b[j].maximum.y,b[j].maximum.z};for(u32 k=0;k<6;++k)regions[j*6+k]=float_bits(values[k]);}
}
API(value) u32 value(u32 index){auto& v=scale.interpolation;const u32 words[]={scale.flags,float_bits(v.start[0]),float_bits(v.end[0]),float_bits(v.initial_tangent[0]),float_bits(v.final_tangent[0]),u32(v.timer.previous),u32(v.timer.current),float_bits(v.timer.fractional),v.timer.rate==nullptr?0u:v.timer.rate==&other?1u:2u,v.timer.flags,u32(v.duration),u32(v.mode),float_bits(scale.factor),u32(scale.recall)};return words[index];}
API(visual_value) u32 visual_value(u32 i){return visual[i];}API(bounds_value) u32 bounds_value(u32 i){return regions[i];}
