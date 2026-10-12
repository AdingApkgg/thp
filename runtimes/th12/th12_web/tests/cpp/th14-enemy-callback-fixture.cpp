#include "../../cpp/game/EnemyCommands.hpp"
#include "../../cpp/game/AnmVm.hpp"
#include "../../cpp/game/EnemyCallbacks.hpp"
#include "../../cpp/game/EnemyScript.hpp"
#include "../../cpp/game/BulletState.hpp"
#include "../../cpp/game/BulletTh14.hpp"
#include <cstdlib>
using namespace th11;
static EnemyState enemy;static BulletState bullets[8];
extern "C" {
__attribute__((export_name("allocate"))) void* allocate(u32 n){return std::malloc(n);}
__attribute__((export_name("release"))) void release(void* p){std::free(p);}
__attribute__((export_name("run"))) void run(const u32* p,u32 count){
    enemy.current.position={float_bits(p[0]),float_bits(p[1]),0};enemy.floats[3]=float_bits(p[2]);enemy.integers[0]=i32(p[3]);enemy.floats[0]=float_bits(p[4]);enemy.floats[1]=float_bits(p[5]);
    for(u32 j=0;j<count;++j){auto& b=bullets[j];b.th14_script_state=i32(p[6+j*3]);b.state=4;b.position={float_bits(p[7+j*3]),float_bits(p[8+j*3]),0};b.th14_active_next=j+1<count?&bullets[j+1]:nullptr;}
    enemy_th14_closest_bullet(enemy,count?bullets:nullptr);
}
static AnmVm screen;
static bool damage_present;static u32 damage_calls[16];static u32 damage_count;static i32 damage_returns[2];
static u32 scale_request;
static Vec3 freeze_player;static u32 freeze_count;static std::vector<u32> freeze_sounds;
struct FreezeEnvironment:BulletEnvironment{bool sound(i32 id,float x,bool positional)override{freeze_sounds.push_back(u32(id));freeze_sounds.push_back(float_bits(x));return false;}};
static FreezeEnvironment freeze_environment;
struct World:EnemyCallbackWorld{
 EnemyLink* callback_enemies()override{return nullptr;}
 bool callback_spawn(const EnemyState&,Vec3)override{return false;}
 bool callback_move_player(Vec3)override{return false;}
 bool callback_indicator(i16,bool)override{return false;}
 AnmVm* callback_animation(u32& id)override{if(damage_present)return &screen;id=0;return nullptr;}
 bool callback_damage(Vec3,Vec2,i32&)override{return false;}
 bool callback_collision(Vec3,float,float,float)override{return false;}
 AnmVm* callback_th14_visual()override{return &screen;}
 bool callback_th14_player_scale(float v)override{scale_request=float_bits(v);return true;}
 bool callback_th14_damage(const EnemyState&,Vec3 p,const Vec2* size,float radius,float angle,i32& out)override{
  const u32 words[]={float_bits(p.x),float_bits(p.y),float_bits(p.z),u32(size!=nullptr),size?float_bits(size->x):0,size?float_bits(size->y):0,float_bits(radius),float_bits(angle)};
  std::memcpy(damage_calls+damage_count*8,words,sizeof(words));out=damage_returns[damage_count++];return true;
 }
};
extern "C" {
__attribute__((export_name("freeze_begin"))) void freeze_begin(const u32* p,u32 count){
 freeze_player={float_bits(p[0]),float_bits(p[1]),0};enemy.floats[0]=float_bits(p[2]);enemy.floats[1]=float_bits(p[3]);freeze_count=count;
 for(u32 j=0;j<count;++j){auto& b=bullets[j];const u32* r=p+4+j*7;b={};b.th14_script_state=signed_bits(r[0]);b.reserved_4c0=signed_bits(r[1]);b.transform_index=signed_bits(r[2]);b.active_transforms=r[3];b.state=i16(r[4]);b.position={float_bits(r[5]),float_bits(r[6]),0};b.th14_active_next=j+1<count?&bullets[j+1]:nullptr;}
}
__attribute__((export_name("freeze_tick"))) void freeze_tick(){freeze_sounds.clear();enemy_th14_freeze_bullets(enemy,freeze_count?bullets:nullptr,freeze_player,freeze_environment);}
__attribute__((export_name("freeze_word"))) u32 freeze_word(u32 j,u32 n){const auto& b=bullets[j];const u32 values[]={u32(b.th14_script_state),u32(b.reserved_4c0),u32(b.transform_index),b.active_transforms,u32(u16(b.state)),float_bits(b.position.x),float_bits(b.position.y)};return values[n];}
static Rng acceleration_random;
__attribute__((export_name("acceleration_case"))) void acceleration_case(u32 seed,u32 calls,u32 count){
 acceleration_random.seed=u16(seed);acceleration_random.calls=calls;
 for(u32 j=0;j<count;++j){auto& b=bullets[j];b={};b.th14_active_next=j+1<count?&bullets[j+1]:nullptr;
  u32 words[11];for(u32 n=0;n<11;++n)words[n]=0x12340000+j*0x100+n;std::memcpy(&b.th14_transforms[1],words,sizeof words);
  b.transform_index=7;b.active_transforms=0x100;b.state=4;
 }enemy_th14_random_acceleration(count?bullets:nullptr,acceleration_random);
}
__attribute__((export_name("acceleration_word"))) u32 acceleration_word(u32 j,u32 n){u32 word;std::memcpy(&word,reinterpret_cast<const u8*>(&bullets[j].th14_transforms[1])+n*4,4);return word;}
__attribute__((export_name("acceleration_rng"))) u32 acceleration_rng(u32 n){return n?acceleration_random.calls:acceleration_random.seed;}
__attribute__((export_name("freeze_sound_count"))) u32 freeze_sound_count(){return u32(freeze_sounds.size());}
__attribute__((export_name("freeze_sound_word"))) u32 freeze_sound_word(u32 n){return freeze_sounds[n];}
__attribute__((export_name("tag_case"))) i32 tag_case(i32 index,i32 tag,u32 active,i32 concurrent){auto& b=bullets[0];b={};b.th14_script_state=0x12345678;b.transform_index=index;b.active_transforms=active;auto& t=b.th14_transforms[index];t.opcode=0x8000;t.p=tag;t.concurrent=concurrent;return bullet_th14_start_transforms(b,freeze_environment);}
__attribute__((export_name("scale_case"))) i32 scale_case(i32 index,u32 value){
 enemy.floats[0]=float_bits(value);World world;EnemyEnvironment env;EnemyCommandEnvironment commands;EnemyCallbacks callbacks(env,commands,world);commands.callbacks=&callbacks;EnemyScriptServices services(enemy,env,commands);
 alignas(4) u8 bytes[20]{};auto* ins=reinterpret_cast<EclInstruction*>(bytes);ins->opcode=637;ins->length=20;std::memcpy(bytes+16,&index,4);EclContext c;c.instruction=ins;return services.command(c);
}
__attribute__((export_name("scale_request_value"))) u32 scale_request_value(){return scale_request;}
__attribute__((export_name("damage_case"))) u32 damage_case(const u32* p,i32 present,i32 first,i32 second,i32 initial){
 screen.initialize();damage_present=present;damage_count=0;damage_returns[0]=first;damage_returns[1]=second;
 enemy.current.position={float_bits(p[0]),float_bits(p[1]),float_bits(p[2])};screen.scale={float_bits(p[3]),float_bits(p[4])};screen.rotation.z=float_bits(p[5]);enemy.animations[1]=37;
 World world;EnemyEnvironment env;EnemyCommandEnvironment commands;EnemyCallbacks callbacks(env,commands,world);i32 out=initial;if(!callbacks.damage_th14(enemy,out))return 0xdeadbeef;return u32(out);
}
__attribute__((export_name("damage_word"))) u32 damage_word(u32 index){return index<16?damage_calls[index]:index==16?damage_count:enemy.animations[1];}
__attribute__((export_name("damage_setter"))) i32 damage_setter(u32 prior,i32 index){
 enemy.damage_callback=EnemyDamage(prior);EnemyEnvironment env;EnemyCommandEnvironment commands;EnemyScriptServices services(enemy,env,commands);
 alignas(4) u8 bytes[20]{};auto* ins=reinterpret_cast<EclInstruction*>(bytes);ins->opcode=633;ins->length=20;std::memcpy(bytes+16,&index,4);EclContext c;c.instruction=ins;return services.command(c);
}
__attribute__((export_name("damage_setter_value"))) u32 damage_setter_value(){return u32(enemy.damage_callback);}
__attribute__((export_name("command_case"))) i32 command_case(i32 input,i32 prior){
 screen.initialize();screen.pending_interrupt=prior;enemy.integers[0]=input;
 World world;EnemyEnvironment env;EnemyCommandEnvironment commands;EnemyCallbacks callbacks(env,commands,world);commands.callbacks=&callbacks;
 EnemyScriptServices services(enemy,env,commands);alignas(4) u8 bytes[20]{};auto* ins=reinterpret_cast<EclInstruction*>(bytes);ins->opcode=637;ins->length=20;const i32 index=2;std::memcpy(bytes+16,&index,4);EclContext c;c.instruction=ins;return services.command(c);
}
__attribute__((export_name("command_visual"))) u32 command_visual(){return u32(screen.pending_interrupt);}
}
__attribute__((export_name("value"))) u32 value(u32 n){return n==0?u32(enemy.integers[0]):float_bits(enemy.floats[n-1]);}
__attribute__((export_name("visual_case"))) u32 visual_case(i32 input,i32 prior){AnmVm vm;vm.initialize();vm.pending_interrupt=prior;enemy.integers[0]=input;enemy_th14_visual_interrupt(enemy,vm);return u32(vm.pending_interrupt);}
}
