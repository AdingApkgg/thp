#include "EnemyScript.hpp"
#include "EnemyAnimations.hpp"
#include "ShotManager.hpp"
#include "AnmOpcodes.hpp"
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static std::unique_ptr<AnmManager> manager;
static AnmResource resource;
static u32 results[5];

template<class V> void configure_interpolation(V& v,u32 dimensions,u32 mode,i32 duration){
    v={};
    const i32 values[4][3]={{11,17,23},{31,47,59},{2,3,5},{7,11,13}};
    for(u32 n=0;n<dimensions;++n){v.start[n]=values[0][n];v.end[n]=values[1][n];v.initial_tangent[n]=values[2][n];v.final_tangent[n]=values[3][n];}
    v.timer.set(0,&manager->rate);v.duration=duration;v.mode=InterpolationMode(mode);
}
static i32 run_case(u32 mask,u32 vector_mode,u32 rgb_mode,u32 vec2_mode,i32 duration,u32 rate_bits,u32 high_precision){
    manager.reset();resource={};manager=std::make_unique<AnmManager>();
    std::memcpy(&manager->rate,&rate_bits,4);
    manager->texture_high_precision=high_precision!=0;
    resource.scripts.resize(1);
    const AnmInstruction code[]={{i16(anm_canonical_opcode(2)),8,1,0},{-1,8,1,0}};
    const auto* bytes=reinterpret_cast<const u8*>(code);
    resource.scripts[0].bytes.assign(bytes,bytes+sizeof code);
    AnmVm* created=nullptr;
    manager->before_initial_update=[&](const AnmVm& input){
        auto& vm=const_cast<AnmVm&>(input);created=&vm;vm.flags2&=~0x100u;
        for(u32 field=0;field<11;++field){if(!(mask&(1u<<field)))continue;
        const u32 mode=(field==1||field==7)?rgb_mode:(field>=3&&field<=5)?vec2_mode:vector_mode;
        switch(field){
        case 0:configure_interpolation(vm.position_interpolation,3,mode,duration);break;
        case 1:configure_interpolation(vm.color_interpolation,3,mode,duration);break;
        case 2:configure_interpolation(vm.alpha_interpolation,1,mode,duration);break;
        case 3:configure_interpolation(vm.scale_interpolation,2,mode,duration);break;
        case 4:configure_interpolation(vm.extra_scale_interpolation,2,mode,duration);break;
        case 5:configure_interpolation(vm.texture_scale_interpolation,2,mode,duration);break;
        case 6:configure_interpolation(vm.rotation_interpolation,3,mode,duration);break;
        case 7:configure_interpolation(vm.color2_interpolation,3,mode,duration);break;
        case 8:configure_interpolation(vm.alpha2_interpolation,1,mode,duration);break;
        case 9:configure_interpolation(vm.scroll_x_interpolation,1,mode,duration);break;
        case 10:configure_interpolation(vm.scroll_y_interpolation,1,mode,duration);break;
        default:return false;
        }
        }
        return true;
    };
    auto& stack=manager->th14_native_stack;
    stack.scratch=stack.spawn_scratch=float_bits(31.25f);
    EnemyAnimations animations(*manager);animations.resources[1]={&resource,1};
    EnemyState enemy{};EnemyEnvironment environment;EnemyCommandEnvironment world;world.animations=&animations;
    alignas(4)u8 instruction[24]{};auto* ins=reinterpret_cast<EclInstruction*>(instruction);
    ins->opcode=308;ins->length=sizeof instruction;const i32 args[]={1,0};std::memcpy(instruction+16,args,sizeof args);
    EclContext c;c.instruction=ins;EnemyScriptServices services(enemy,environment,world);
    if(services.command(c)||!created)return -1;
    results[0]=stack.spawn_scratch_known;results[1]=stack.spawn_scratch;
    ShotState shot{};ShotPlayer player{};Th14DamageArea area{};Th14BeamHit hit{};
    player.th14_native_stack=&stack;shot.movement.position={40,259.9700012207031f,0};shot.movement.angle=-1.5707963705062866f;
    shot.timer.previous=226;shot.timer.current=227;shot.hit_last_frame=1;area.size={320.96453857421875f,16};
    NativeStackTh14::CounterScope constructor_scope(&stack.enemy_spawn_depth);
    results[2]=stack.beam_fallback_scratch();
    if(!shot_th14_beam_hit(shot,player,area,{64,-48,0},nullptr,16,0,hit))return -2;
    results[3]=float_bits(shot.th14_beam_length);results[4]=float_bits(area.size.x);return 0;
}
API(run) i32 run(u32 field,u32 mode,i32 duration,u32 rate_bits,u32 high_precision){
    return field<11?run_case(1u<<field,mode,mode,mode,duration,rate_bits,high_precision):-3;
}
API(run_mask) i32 run_mask(u32 mask,u32 vector_mode,u32 rgb_mode,u32 vec2_mode,i32 duration,u32 rate_bits,u32 high_precision){
    return run_case(mask,vector_mode,rgb_mode,vec2_mode,duration,rate_bits,high_precision);
}
API(word) u32 word(u32 n){return n<5?results[n]:0;}
