#include "EnemyScript.hpp"
#include "EnemyAnimations.hpp"
#include "ShotManager.hpp"
#include "AnmOpcodes.hpp"
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static std::unique_ptr<AnmManager> manager;
static AnmResource resource;
static u32 results[5];
API(run) i32 run(u32 mode,i32 duration,u32 start_z,u32 rate_bits){
    manager.reset();resource={};manager=std::make_unique<AnmManager>();
    std::memcpy(&manager->rate,&rate_bits,4);
    resource.scripts.resize(1);
    const AnmInstruction code[]={{i16(anm_canonical_opcode(2)),8,1,0},{-1,8,1,0}};
    const auto* bytes=reinterpret_cast<const u8*>(code);
    resource.scripts[0].bytes.assign(bytes,bytes+sizeof code);
    AnmVm* created=nullptr;
    manager->before_initial_update=[&](const AnmVm& input){
        // Controlled synthetic VM initialization before its first update.
        auto& vm=const_cast<AnmVm&>(input);
        created=&vm;vm.flags2&=~0x100u;
        auto& v=vm.position_interpolation;v={};
        v.start[0]=1;v.start[1]=2;std::memcpy(&v.start[2],&start_z,4);
        v.end[0]=3;v.end[1]=4;v.end[2]=83.97372436523438f;
        v.initial_tangent[2]=.125f;v.final_tangent[2]=-.25f;
        v.timer.set(0,&manager->rate);v.duration=duration;v.mode=InterpolationMode(mode);return true;
    };
    auto& stack=manager->th14_native_stack;stack.scratch=stack.spawn_scratch=float_bits(31.25f);
    EnemyAnimations animations(*manager);animations.resources[1]={&resource,1};
    EnemyState enemy{};EnemyEnvironment environment;EnemyCommandEnvironment world;world.animations=&animations;
    alignas(4)u8 instruction[24]{};auto* ins=reinterpret_cast<EclInstruction*>(instruction);
    ins->opcode=308;ins->length=sizeof instruction;const i32 args[]={1,0};std::memcpy(instruction+16,args,sizeof args);
    EclContext c;c.instruction=ins;EnemyScriptServices services(enemy,environment,world);
    if(services.command(c)||!created)return -1;
    results[0]=stack.spawn_scratch_known;results[1]=stack.spawn_scratch;results[2]=float_bits(created->script_position.z);
    ShotState shot{};ShotPlayer player{};Th14DamageArea area{};Th14BeamHit hit{};
    player.th14_native_stack=&stack;shot.movement.position={40,259.9700012207031f,0};shot.movement.angle=-1.5707963705062866f;
    shot.timer.previous=226;shot.timer.current=227;shot.hit_last_frame=1;area.size={320.96453857421875f,16};
    NativeStackTh14::CounterScope constructor_scope(&stack.enemy_spawn_depth);
    if(!shot_th14_beam_hit(shot,player,area,{64,-48,0},nullptr,16,0,hit))return -2;
    results[3]=float_bits(shot.th14_beam_length);results[4]=float_bits(area.size.x);return 0;
}
API(word) u32 word(u32 n){return n<5?results[n]:0;}
