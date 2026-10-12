#include "../../cpp/game/ShotTh16.hpp"
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static Th16DamageSources sources;
API(run_case) u32 run_case(i32 cursor,u32 mode,u32 tf,float radius,float growth,i32 duration,i32 damage,u32 seed){
 sources={};sources.cursor=cursor;for(u32 i=0;i<256;++i){auto& words=sources.records[i+1].words;for(u32 j=0;j<37;++j)words[j]=0x12340000u+(i*37+j)*17+seed;const bool active=mode==0?false:mode==1?i==u32((cursor+1)%256):mode==2?true:mode==3?i!=17:mode==4?i!=0:bool((i+seed)%2);words[0]=0x40000084u|u32(active);words[28]=tf;words[27]=5;}
 return sources.circle({-12.25f,80.5f,1.25f},radius,growth,duration,damage);
}
API(cursor) i32 cursor(){return sources.cursor;}
API(pool) const Th16DamageSource* pool(){return &sources.records[1];}
