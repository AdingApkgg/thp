#include "../../cpp/game/BulletTh14.hpp"
#include "../../cpp/game/BulletManager.hpp"
#include "../../cpp/game/EnemyManager.hpp"
#include "../../cpp/game/EnemyCommands.hpp"
#include <cstdlib>
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static EnemyState enemy;static EnemyEnvironment environment;static EnemyGlobals globals(enemy,environment);
alignas(4) static u8 code[128];static u8 packed[0x3800];static BulletState bullet;
struct World:BulletEnvironment{
 EnemySpawn value{};u32 calls=0;const char* name=nullptr;
 bool th14_spawn_enemy(const char* n,const EnemySpawn& v)override{name=n;value=v;++calls;return true;}
};static World world;
API(allocate) void* allocate(u32 n){return std::malloc(n);}
API(release) void release(void* p){std::free(p);}
API(setter) i32 setter(const u8* bytes,u32 length){
 enemy={};std::memset(enemy.th14_emitters,0xa5,sizeof enemy.th14_emitters);std::memcpy(code,bytes,length);
 auto* instruction=reinterpret_cast<EclInstruction*>(code);const u32 emitter=instruction->argument(),at=instruction->argument(1);enemy.th14_emitter_cursors[emitter]=13;
 EclContext c;c.instruction=instruction;const auto result=enemy_th14_emitter_command(enemy,c,globals);
 if(!result){auto& t=enemy.th14_emitters[emitter].transforms[at];if(t.script!=u32(uintptr_t(code+28)))return -3;t.script=28;}
 std::memcpy(packed,enemy.th14_emitters,sizeof packed);return result;
}
API(output) const u8* output(){return packed;}
API(cursor) i32 cursor(u32 n){return enemy.th14_emitter_cursors[n];}
API(begin) i32 begin(u32 index,u32 active,u32 concurrent,u32 n){
 bullet={};world.value={};world.calls=0;world.name=nullptr;std::memcpy(code,"Child",6);
 bullet.position={-12.25f+n*4,70.5f-n*3,n*.125f};bullet.transform_index=i32(index);bullet.active_transforms=active;
 auto& t=bullet.th14_transforms[index];t.a=n*.25f;t.b=-2.5f+n*.125f;t.c=999;t.d=-.125f;t.p=i32(0x80000000u+n);t.q=-999+i32(n);t.r=0x7fffffff-i32(n);t.s=i32(n*991);t.opcode=0x1000000;t.concurrent=i32(concurrent);t.script=u32(uintptr_t(code));
 return bullet_th14_start_transforms(bullet,world);
}
API(state) u32 state(u32 n){return n?bullet.active_transforms:u32(bullet.transform_index);}
API(calls) u32 calls(){return world.calls;}
API(name) const char* name(){return world.name;}
API(descriptor) const EnemySpawn* descriptor(){return &world.value;}
struct ConsumerWorld:BulletWorld,EnemyFrameWorld{
 EnemyManager* enemies=nullptr;
 bool th14_spawn_enemy(const char* name,const EnemySpawn& value)override{return enemies->spawn(name,value)!=nullptr;}
 bool shot_damage(EnemyState&,i32& damage)override{damage=0;return true;}
 bool player_collision(EnemyState&,float,i32& result)override{result=0;return true;}
 void clear_shot_targets(Enemy*)override{}
};
static u32 consumed[25];
API(consume) i32 consume(u32 index,u32 active,u32 concurrent,u32 n){
 EclProgram program;auto file=std::make_unique<EclResource>();file->bytes.resize(48);
 file->subroutines.push_back({"Child",0,48});auto* first=reinterpret_cast<EclInstruction*>(file->bytes.data()+16);first->opcode=642;first->length=16;first->difficulty=255;
 auto* next=reinterpret_cast<EclInstruction*>(file->bytes.data()+32);*next=*first;next->time=10000;program.definitions.push_back({file.get(),0});program.files.push_back(std::move(file));
 EnemyEnvironment env;EnemyCommandEnvironment commands;ConsumerWorld consumer;AnmManager animations;EnemyAnimations enemy_animations(animations);commands.animations=&enemy_animations;
 EnemyManager enemies(program,env,commands,consumer);consumer.enemies=&enemies;AnmResource resource;BulletManager bullets(resource,animations,consumer);
 begin(index,active,concurrent,n);bullet.transform_index=i32(index);bullet.active_transforms=active;
 // Use the producer's long-lived instruction bytes, then copy that same
 // descriptor through the actual BulletManager bridge and EnemyManager factory.
 alignas(4) u8 writer[36]{};auto* instruction=reinterpret_cast<EclInstruction*>(writer);instruction->opcode=640;instruction->length=36;const u32 arguments[]={0,index,8};std::memcpy(writer+16,arguments,12);std::memcpy(writer+28,"Child",6);
 EclContext c;c.instruction=instruction;if(enemy_th14_emitter_command(enemy,c,globals))return -2;bullet.th14_transforms[index].script=enemy.th14_emitters[0].transforms[index].script;
 const auto result=bullet_th14_start_transforms(bullet,bullets);std::memset(consumed,0,sizeof consumed);consumed[0]=enemies.count;consumed[1]=enemies.total_created;
 if(enemies.first){const auto& child=*enemies.first->value;const auto& e=child.state;consumed[2]=u32(e.instance_id);consumed[3]=float_bits(e.current.position.x);consumed[4]=float_bits(e.current.position.y);consumed[5]=float_bits(e.current.position.z);consumed[6]=u32(e.health);std::memcpy(consumed+7,e.integers,48);consumed[19]=u32(e.score);consumed[20]=u32(e.drops.primary);consumed[21]=e.parent_instance_id;consumed[22]=u32(e.lifetime.current);consumed[23]=float_bits(child.script.root.time);consumed[24]=child.script.root.instruction==next;}
 return result;
}
API(consumer_word) u32 consumer_word(u32 n){return consumed[n];}
