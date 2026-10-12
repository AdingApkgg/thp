#include "../../cpp/game/EnemyManager.hpp"
#include "../../cpp/game/LaserManager.hpp"
#include <cstdlib>
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static Enemy enemies[3];
static EnemyEnvironment environment;
static EnemyGlobals globals(enemies[0].state,environment);
static AnmManager animations;
static EnemyAnimations binding(animations);
static AnmResource effects;
static u32 sounds[6],sound_count;
static u32 first_creation;
struct World:EnemyFrameWorld{
    bool sound(i32 id,float x)override{sounds[sound_count++]=u32(id);sounds[sound_count++]=float_bits(x);return true;}
    bool drop_items(EnemyState& e)override{
        if(e.drops.primary)return false;
        for(u32 n=0;n<13;++n)if(e.drops.counts[n])return false;
        environment.rng().signed_unit();return true;
    }
    void clear_shot_targets(Enemy*)override{}
};
static World world;
static EnemyCommandEnvironment commands;
static EclProgram program;
static EnemyManager manager(program,environment,commands,world);
API(allocate) void* allocate(u32 n){return std::malloc(n);}
API(release) void release(void* p){std::free(p);}
API(metadata) void metadata(i32 file,i32 script,i32 override,i32 id){
    auto& e=enemies[0].state;e={};e.bound_animation_file=file;e.animation_script=script;e.death_animation=override;e.death_animation_file=7;e.instance_id=id;enemy_th14_death_metadata(e);
}
API(meta_value) u32 meta_value(u32 n){auto& e=enemies[0].state;return u32(n==0?e.death_sound:n==1?e.death_animation:e.death_animation_file);}
API(run) i32 run(float rate,const u32* input){
    animations.clear();first_creation=anm_creation_count();sound_count=0;environment.rate=rate;environment.random={12345,0,0};environment.shared_random=nullptr;
    effects.scripts.resize(44);alignas(4) const u8 code[]={2,0,8,0,0,0,0,0,255,255,8,0,0,0,0,0};
    for(auto& script:effects.scripts)script.bytes.assign(code,code+sizeof code);
    binding.resources[1]={&effects,8};commands.animations=&binding;manager.last_error=0;
    manager.timer.set(10,&environment.rate);manager.timer.previous=9;manager.timer.fractional=10.5f;
    for(u32 j=0;j<3;++j){auto& e=enemies[j].state;e={};e.flags=input[j*3];e.current.position={float_bits(input[j*3+1]),float_bits(input[j*3+2]),0};
        e.death_sound=i32(j)+3;e.death_animation=43;e.death_animation_file=1;
        e.manager_link={&enemies[j],j<2?&enemies[j+1].state.manager_link:nullptr,j?&enemies[j-1].state.manager_link:nullptr};
        e.drops.primary=1000+j*100;for(u32 k=0;k<13;++k)e.drops.counts[k]=i32(1001+j*100+k);
        e.drops.spread={float_bits(1014+j*100),float_bits(1015+j*100)};
    }
    manager.first=&enemies[0].state.manager_link;manager.last=&enemies[2].state.manager_link;
    EclInstruction cmd{};cmd.opcode=525;EclContext context;context.instruction=&cmd;return manager.command(enemies[0].state,context,globals);
}
API(value) u32 value(u32 j,u32 n){auto& e=enemies[j].state;if(!n)return e.flags;if(n==1)return u32(e.drops.primary);if(n<15)return u32(e.drops.counts[n-2]);return float_bits(n==15?e.drops.spread.x:e.drops.spread.y);}
API(timer_value) u32 timer_value(u32 n){return n==0?u32(manager.timer.previous):n==1?u32(manager.timer.current):float_bits(manager.timer.fractional);}
API(sound_size) u32 sound_size(){return sound_count;}
API(sound_value) u32 sound_value(u32 n){return sounds[n];}
API(sound_case) i32 sound_case(i32 id,float x){
    sound_count=0;auto& e=enemies[0].state;e.current.position.x=x;
    alignas(4) u8 bytes[20]{};auto* cmd=reinterpret_cast<EclInstruction*>(bytes);cmd->opcode=516;cmd->length=20;std::memcpy(bytes+16,&id,4);
    EclContext c;c.instruction=cmd;return manager.command(e,c,globals);
}
API(inactive_spell_case) i32 inactive_spell_case(u32 health_flags,u32 spell_flags){
    auto& e=enemies[0].state;e.health_flags=health_flags;world.spell_flags=spell_flags;
    EclInstruction cmd{};cmd.opcode=523;EclContext c;c.instruction=&cmd;return manager.command(e,c,globals);
}
API(inactive_spell_value) u32 inactive_spell_value(u32 n){return n?world.spell_flags:enemies[0].state.health_flags;}
API(empty_laser_gate) i32 empty_laser_gate(u32 populated){
    LaserWorld w;AnmEnvironment a;AnmResource r;LaserManager l(r,a,w,7);
    if(populated){auto* line=new LaserLine{};l.append(line->base);}
    commands.lasers=&l;EclInstruction cmd{};cmd.opcode=545;EclContext c;c.instruction=&cmd;
    const i32 result=manager.command(enemies[0].state,c,globals);commands.lasers=nullptr;return result;
}
API(rng_value) u32 rng_value(u32 n){return n?environment.random.calls:environment.random.seed;}
API(effect_size) u32 effect_size(){return anm_creation_count()-first_creation;}
API(effect_value) u32 effect_value(u32 j,u32 n){auto* pointer=animations.find(u32(anm_creation_value(first_creation+j,5)));if(!pointer)return 0xffffffff;auto& vm=*pointer;
    switch(n){case 0:return u32(vm.script_index);case 1:return float_bits(vm.position.x);case 2:return float_bits(vm.position.y);case 3:return float_bits(vm.position.z);case 4:return float_bits(vm.rotation.z);case 5:return vm.layer;case 6:return vm.flags2&0x60200;case 7:return u32(vm.file_index);}return 0;
}
