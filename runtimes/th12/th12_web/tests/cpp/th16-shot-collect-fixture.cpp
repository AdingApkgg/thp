#include "../../cpp/game/ShotTh16.hpp"
#include "../../cpp/game/EclContext.hpp"
#include <vector>
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static Th16DamageSources sources;static i32 damage;static bool bomb;static Vec3 last;static Vec2 size{12,18};
struct Delivery final:Th16DamageDelivery {
 u32 seed=0;std::vector<std::array<u32,3>> events;
 bool bomb(const Th16DamageQuery&,i32& damage)override{damage=std::array<i32,3>{0,5,-9}[(seed/16)%3];if(seed&256)events.push_back({1,u32(damage),0});else damage=0;return true;}
 bool overlaps(const Th16DamageSource& a,const Th16DamageQuery& q)override{const auto& w=a.words;if((w[0]&2)&&!q.size){float x,y,r;std::memcpy(&x,&w[7],4);std::memcpy(&y,&w[8],4);std::memcpy(&r,&w[1],4);x-=q.position.x;y-=q.position.y;r+=q.radius;return x*x+y*y<=r*r;}events.push_back({2,w[34],u32(bool(w[0]&2))*2+u32(q.size!=nullptr)});return seed&128;}
 bool hit(u32 id,Th16DamageSource& a,const Th16DamageQuery&,i32& hit)override{events.push_back({3,id,a.words[35]});a.words[29]=u32(signed_bits(a.words[29])/2);hit=wrapping_add(signed_bits(a.words[29]),7);return true;}
 bool score(i32 points)override{events.push_back({4,u32(points),0});return true;}
} delivery;
API(begin) i32 begin(u32 seed,i32 cap,u32 advanced){
 sources={};delivery.seed=seed;delivery.events.clear();
 for(u32 id:{1u,2u,256u}){auto& w=sources.records[id].words;w[0]=std::array<u32,5>{0,1,3,5,7}[(seed+id)%5];w[1]=float_bits(5.5f);w[3]=float_bits(-.75f);w[5]=float_bits(4.25f);w[6]=float_bits(7.5f);w[7]=float_bits(2.25f+float(id)*.5f);w[8]=float_bits(300.5f);w[9]=float_bits(1.25f);const i32 clock=std::array<i32,4>{0,1,6,-3}[seed%4];w[25]=u32(clock);w[24]=u32(seed&2?clock:-10);w[32]=u32(std::array<i32,3>{1,2,-1}[(seed/8+id)%3]);w[29]=u32(std::array<i32,3>{13,-9,INT32_MAX}[(seed/32+id)%3]);w[30]=u32(std::array<i32,3>{0,8,INT32_MAX}[(seed/64+id)%3]);w[31]=u32(std::array<i32,3>{10,9999999,10000000}[(seed/128+id)%3]);w[33]=seed&64?7:0;w[34]=id;w[35]=123;w[36]=seed&16?1:0;}
 Th16DamageQuery query;query.position={2.25,300.5,1.25};query.size=seed&1?&size:nullptr;query.radius=3;query.angle=.5f;query.advanced=advanced;query.probe=seed&8;query.stamp=seed&4?7:0;query.cap=cap;
 damage=999;bomb=true;last={99,88,77};return shot_th16_collect(sources,query,delivery,damage,bomb,&last);
}
API(value) u32 value(u32 n){const u32 words[]={u32(damage),u32(bomb),float_bits(last.x),float_bits(last.y),float_bits(last.z)};return words[n];}
API(area) u32 area(u32 id,u32 n){return sources.records[id].words[n];}
API(count) u32 count(){return delivery.events.size();}
API(event) u32 event(u32 n,u32 k){return delivery.events[n][k];}
