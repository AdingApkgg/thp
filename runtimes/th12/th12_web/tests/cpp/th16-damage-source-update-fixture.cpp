#include "../../cpp/game/ShotTh16.hpp"
#include "../../cpp/game/EclContext.hpp"
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static Th16DamageSources sources;static float scale;
API(begin) i32 begin(u32 seed){sources={};scale=seed&128?1.f:std::array<float,4>{0,.5,1,1.5}[seed%4];
 for(u32 id:{1u,2u,256u}){auto& w=sources.records[id].words;w[0]=std::array<u32,5>{0,1,3,5,7}[(seed+id)%5];w[1]=float_bits(3.5f);w[2]=float_bits(seed&1?-.5f:.25f);w[3]=float_bits(std::array<float,3>{-7,.75,7}[(seed/8)%3]);w[4]=float_bits(seed&2?.25f:-.1f);w[7]=float_bits(2.25f+float(id)*.5f);w[8]=float_bits(300.5f);w[9]=float_bits(1.25f);w[13]=float_bits(seed&4?6.25f:0.f);w[14]=float_bits(-.75f);w[22]=float_bits(2.f);const i32 clock=std::array<i32,4>{0,1,3,9999999}[(seed/16)%4];w[24]=0;w[25]=u32(clock);w[26]=float_bits(float(clock)+.25f);w[27]=std::array<u32,3>{0,1,0xffffffff}[(seed/64)%3];w[28]=5;w[33]=7;}
 return sources.update(seed&128?nullptr:&scale);
}
API(area) u32 area(u32 id,u32 n){return sources.records[id].words[n];}
