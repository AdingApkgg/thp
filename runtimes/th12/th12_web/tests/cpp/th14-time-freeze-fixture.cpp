#include "../../cpp/game/BulletManager.hpp"
#include "../../cpp/game/LaserManager.hpp"
#include "../../cpp/game/AnmOpcodes.hpp"
#include "../../cpp/game/EclContext.hpp"
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static std::vector<u32> events,result;static u32 grazes=0;
struct World:BulletWorld,LaserWorld {
 i32 hit(const BulletState& b,bool probe){events.insert(events.end(),{0,u32(probe),float_bits(b.position.x),float_bits(b.position.y),float_bits(b.hitbox.x),float_bits(b.hitbox.y)});return probe?2:0;}
 i32 collision(const BulletState& b)override{return hit(b,false);}i32 th14_probe_collision(const BulletState& b)override{return hit(b,true);}
 bool register_graze()override{return true;}bool reward_graze()override{++grazes;return true;}
 i32 warning_collision(Vec3 p,float angle,float width,float length)override{events.insert(events.end(),{1,1,float_bits(p.x),float_bits(p.y),float_bits(angle),float_bits(width),float_bits(length)});return 2;}
 bool th14_curve_graze(Vec3)override{++grazes;return true;}
}world;
static AnmEnvironment animations;static AnmResource resource;static std::unique_ptr<BulletManager> bullets;static std::unique_ptr<LaserManager> lasers;static BulletState* bullet;static LaserState* laser;static i32 kind;
API(begin) i32 begin(i32 k,u32 flags,i32 state,i32 timer,float rate){
 kind=k;animations.rate=world.rate=rate;events.clear();grazes=0;resource={};resource.scripts.resize(294);
 const AnmInstruction code[]={{i16(anm_canonical_opcode(2)),8,0,0},{-1,8,0,0}};
 for(auto& s:resource.scripts){s.bytes.resize(sizeof code);std::memcpy(s.bytes.data(),code,sizeof code);}
 if(!kind){
  bullets=std::make_unique<BulletManager>(resource,animations,world,7);Th14BulletEmitter e{};e.sprite=0;e.color=0;e.position={12.25f,70.5f,2};e.count=e.layers=1;e.aim=1;
  if(bullets->spawn_th14(e,0,0,0)<0)return -1;bullet=bullets->first_th14();auto& b=*bullet;
  b.flags=flags;b.state=state;b.position={12.25f,70.5f,2};b.velocity={1.25f,-.75f,.5f};b.hitbox={8,8};b.collision_delay=3;b.draw_group=2;b.offscreen_grace=10;b.cancel_effect=-1;
  b.lifetime.set(timer,&bullets->rate);b.lifetime.fractional=timer+.25f;b.auxiliary_timer.set(5,&bullets->rate);b.auxiliary_timer.fractional=5.5f;return 0;
 }
 lasers=std::make_unique<LaserManager>(resource,animations,world,7);
 if(kind==1){auto* p=new Th14LaserInfinite{};p->native_flags=8;laser=&p->base;}
 else if(kind==2){auto* p=new Th14LaserCurve{};p->native_flags=8;p->path.samples.resize(7);
  for(u32 j=0;j<7;++j){auto& s=p->path.samples[j];s.position={12.25f+j*.75f,70.5f-j*.125f,2};s.angle=.125f;s.speed=4;}laser=&p->base;}
 else {auto* p=new Th14LaserShell{};p->native_flags=8;laser=&p->base;}
 auto& b=*laser;b.initialize(&world.rate);b.type=kind;b.state=state;b.position={12.25f,70.5f,2};b.angle=.125f;b.length=64;b.width=24;
 b.lifetime.set(9,&world.rate);b.lifetime.previous=8;b.lifetime.fractional=9.25f;b.graze_timer.set(timer,&world.rate);b.graze_timer.fractional=timer+.25f;lasers->append(b);return 0;
}
API(tick) i32 tick(){events.clear();grazes=0;
 if(!kind){const bool ok=bullets->update();const auto& b=*bullet;result={b.flags,u32(b.collision_delay),float_bits(b.position.x),float_bits(b.position.y),float_bits(b.position.z),u32(b.lifetime.previous),u32(b.lifetime.current),float_bits(b.lifetime.fractional),u32(b.auxiliary_timer.previous),u32(b.auxiliary_timer.current),float_bits(b.auxiliary_timer.fractional),u32(b.state),bullets->active_count,u32(bool(bullets->group_first(2)))};return ok;}
 const bool ok=lasers->update();const auto& b=*laser;const u32 flags=kind==1?reinterpret_cast<Th14LaserInfinite*>(laser)->native_flags:kind==2?reinterpret_cast<Th14LaserCurve*>(laser)->native_flags:reinterpret_cast<Th14LaserShell*>(laser)->native_flags;
 result={flags,u32(b.state),u32(b.lifetime.previous),u32(b.lifetime.current),float_bits(b.lifetime.fractional),u32(b.graze_timer.previous),u32(b.graze_timer.current),float_bits(b.graze_timer.fractional)};return ok;
}
API(value) u32 value(u32 n){return result.at(n);}API(graze) u32 graze(){return grazes;}
API(event_words) u32 event_words(){return events.size();}API(event_value) u32 event_value(u32 n){return events.at(n);}
