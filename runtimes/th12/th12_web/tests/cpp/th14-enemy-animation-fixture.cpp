#include "../../cpp/game/EnemyScript.hpp"
#include "../../cpp/game/EnemyAnimations.hpp"
#include "../../cpp/game/AnmOpcodes.hpp"
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static AnmManager manager;
static AnmResource resource;
static EnemyAnimations animations(manager);
static EnemyState enemy;
static EnemyEnvironment environment;
static EnemyCommandEnvironment world;
static AnmVm *old_vm,*created;
static u32 old_id,slot;
alignas(4) static u8 instruction[64];
static void append(u32 index,i16 op,const void* args=nullptr,u32 bytes=0){
    auto& b=resource.scripts[index].bytes;const auto at=b.size();b.resize(at+8+bytes);
    const AnmInstruction h{op==-1?i16(-1):i16(anm_canonical_opcode(op)),u16(8+bytes),0,0};
    std::memcpy(b.data()+at,&h,8);if(bytes)std::memcpy(b.data()+at+8,args,bytes);
}
API(run) i32 run(u32 op,u32 selected,u32 hidden,i32 facing,u32 program,i32 script){
    manager.clear();resource={};resource.scripts.resize(18);append(0,2);append(0,-1);
    for(u32 index=1;index<18;++index){
        if(program){const i32 layer=program==1?8:28;append(index,304,&layer,4);}
        if(program==2){const float p[]={3.25f,-7.5f,9.125f},scale[]={2.5f,-3.25f};append(index,400,p,12);append(index,404,scale,8);}
        append(index,2);append(index,-1);
    }
    old_vm=manager.create(resource,0,1,0);if(!old_vm)return -3;old_id=old_vm->id;slot=selected;
    enemy={};enemy.animation_handle(slot)=old_id;enemy.animation_file=1;enemy.bound_animation_file=8;
    enemy.animation_script=9;enemy.base_animation=10;enemy.direction=-1;enemy.facing=facing;enemy.flags=hidden*32|(op==318?0x100000u:0);enemy.visual_size={31,37};
    if(op==307)enemy.current.position={12.25f,-14.5f,4.75f};
    animations.resources[1]={&resource,1};world={};world.animations=&animations;
    std::memset(instruction,0,sizeof instruction);auto* cmd=reinterpret_cast<EclInstruction*>(instruction);
    cmd->opcode=u16(op);cmd->length=24;const i32 args[]={op==307||op==308?1:i32(slot),script};std::memcpy(instruction+16,args,8);
    EclContext context;context.instruction=cmd;EnemyScriptServices services(enemy,environment,world);
    const i32 result=services.command(context);created=manager.find(old_id+1);return result;
}
API(state) u32 state(u32 i){
    const u32 values[]={enemy.flags,u32(enemy.animation_file),u32(enemy.bound_animation_file),u32(enemy.animation_script),u32(enemy.base_animation),u32(enemy.direction),float_bits(enemy.visual_size.x),float_bits(enemy.visual_size.y)};
    return values[i];
}
API(vm_word) u32 vm_word(u32 i){
    if(!created)return 0;const auto& v=*created;
    const u32 values[]={v.layer,v.flags2&0x60220,v.flags&2,float_bits(v.position.x),float_bits(v.position.y),float_bits(v.position.z),
        float_bits(v.script_position.x),float_bits(v.script_position.y),float_bits(v.script_position.z),float_bits(v.scale.x),float_bits(v.scale.y)};
    return values[i];
}
API(meta) u32 meta(u32 i){
    if(i==0)return (old_vm->flags2&32)!=0;
    if(i==1){const auto id=enemy.animation_handle(slot);return id==old_id?100:id==old_id+1?200:0;}
    if(i==2)return created!=nullptr;
    if(i==3)return created&&created->registry.next==&old_vm->registry;
    return 0;
}
API(reject_legacy) i32 reject_legacy(){
    auto* cmd=reinterpret_cast<EclInstruction*>(instruction);cmd->opcode=550;cmd->length=24;
    EclContext context;context.instruction=cmd;EnemyScriptServices services(enemy,environment,world);
    const auto result=services.command(context);return result==-2&&services.error.opcode==550?0:-1;
}
API(offset_case) i32 offset_case(u32 slot,u32 x,u32 y){
 enemy={};for(u32 n=0;n<16;++n)enemy.animation_offsets[n]={float(n)*-.25f,float(n)*.5f,99.f};world={};world.animations=&animations;
 std::memset(instruction,0,sizeof instruction);auto* ins=reinterpret_cast<EclInstruction*>(instruction);ins->opcode=320;ins->length=28;const u32 args[]={slot,x,y};std::memcpy(instruction+16,args,12);EclContext c;c.instruction=ins;EnemyScriptServices services(enemy,environment,world);return services.command(c);
}
API(offset_word) u32 offset_word(u32 n){u32 v;std::memcpy(&v,reinterpret_cast<const u8*>(enemy.animation_offsets)+n*4,4);return v;}
static AnmVm* position_vms[16];
API(position_case) i32 position_case(u32 world_space,u32 rotation,u32 velocity,i32 parent){
    manager.clear();resource={};resource.scripts.resize(1);append(0,2);append(0,-1);enemy={};
    enemy.flags=world_space*0x4000000;enemy.current.position={12.25f,-14.5f,4.75f};enemy.animation_angle=.875f;
    const Vec3 velocities[]={{2,3,0},{0,0,0},{-3,-4,0}};enemy.current.velocity=velocities[velocity];
    for(u32 n=0;n<16;++n){
        auto* vm=manager.create(resource,0,1,0);if(!vm)return -1;position_vms[n]=vm;enemy.animation_handle(n)=vm->id;
        enemy.animation_offsets[n]={n*.25f,n*-.5f,n*.75f};enemy.animation_parents[n]=n==7?parent:-1;
        vm->flags=3;vm->flags2=rotation*0x40;vm->position={100.f+n,200.f+n,300.f+n};
        vm->script_position={1.25f+n,2.5f+n,3.75f+n};vm->rotation.z=-.625f;
    }
    return animations.update_positions(enemy)?0:-2;
}
API(position_value) u32 position_value(u32 n,u32 i){
    if(n==16)return float_bits(enemy.animation_angle);const auto& vm=*position_vms[n];
    const u32 values[]={float_bits(vm.position.x),float_bits(vm.position.y),float_bits(vm.position.z),float_bits(vm.rotation.z),vm.flags&4};return values[i];
}
API(direction_case) i32 direction_case(i32 prior,float vx,i32 facing){
    manager.clear();resource={};resource.scripts.resize(5);for(u32 i=0;i<5;++i){append(i,2);append(i,-1);}
    old_vm=manager.create(resource,0,1,0);if(!old_vm)return -1;old_id=old_vm->id;slot=0;created=nullptr;
    old_vm->script_position={3.25f,-7.5f,9.125f};enemy={};enemy.animations[0]=old_id;
    enemy.flags=0x100000;enemy.direction=prior;enemy.facing=facing;enemy.current.velocity.x=vx;
    const auto ok=animations.update_direction(enemy);created=manager.find(old_id+1);return ok?0:-2;
}
API(direction_value) u32 direction_value(u32 n){
    if(n==0)return u32(enemy.direction);if(n==1)return created?u32(created->script_index):0xffffffffu;
    if(n==2)return created&&created->registry.previous==&old_vm->registry;
    return 0;
}
API(logo_case) i32 logo_case(i32 mode,u32 flags,u32 program){
    manager.clear();resource={};resource.scripts.resize(1);
    if(program){const i32 layer=program==1?8:28;append(0,304,&layer,4);}
    if(program==2){const float p[]={3.25f,-7.5f,9.125f},scale[]={2.5f,-3.25f};append(0,400,p,12);append(0,404,scale,8);}
    append(0,2);append(0,-1);
    old_vm=manager.create(resource,0,6,0);if(!old_vm)return -3;old_id=old_vm->id;slot=0;created=nullptr;
    animations.stage_logo_resource={&resource,6};world={};world.animations=&animations;world.th14_runtime_mode=mode;world.th14_run_flags=flags;
    auto* cmd=reinterpret_cast<EclInstruction*>(instruction);*cmd={};cmd->opcode=554;cmd->length=16;
    EclContext context;context.instruction=cmd;EnemyScriptServices services(enemy,environment,world);
    const auto result=services.command(context);created=manager.find(old_id+1);return result;
}
API(logo_appended) u32 logo_appended(){return created&&created->registry.previous==&old_vm->registry;}
static u32 rotation_result[3];
API(rotation_case) i32 rotation_case(i32 selected,u32 present,float angle){
    manager.clear();resource={};resource.scripts.resize(1);append(0,2);append(0,-1);enemy={};
    auto* vm=manager.create(resource,0,1,0);if(!vm)return -3;
    vm->flags=0x202;vm->rotation.z=.75f;const u32 handle=present?vm->id:0x123456;
    if(selected>=0&&selected<16)enemy.animation_handle(u32(selected))=handle;
    *reinterpret_cast<EclInstruction*>(instruction)={};auto* cmd=reinterpret_cast<EclInstruction*>(instruction);cmd->opcode=319;cmd->length=24;
    std::memcpy(instruction+16,&selected,4);std::memcpy(instruction+20,&angle,4);
    world={};world.animations=&animations;EclContext c;c.instruction=cmd;EnemyScriptServices services(enemy,environment,world);
    const i32 result=services.command(c);const bool alive=selected<0||selected>=16||enemy.animation_handle(u32(selected))!=0;
    rotation_result[0]=vm->flags;rotation_result[1]=float_bits(vm->rotation.z);rotation_result[2]=alive?100:0;return result;
}
API(rotation_value) u32 rotation_value(u32 n){return rotation_result[n];}
API(angled_case) i32 angled_case(i32 file,u32 program,float x,float y,float z,u32 angle){
 manager.clear();resource={};resource.scripts.resize(2);append(0,2);append(0,-1);
 if(program){const i32 layer=program==1?8:28;append(1,304,&layer,4);}
 if(program==2){const float p[]={3.25f,-7.5f,9.125f},r[]={.25f,-.5f,2.25f},scale[]={2.5f,-3.25f};append(1,400,p,12);append(1,401,r,12);append(1,404,scale,8);}
 append(1,2);append(1,-1);old_vm=manager.create(resource,0,u16(file),0);if(!old_vm)return -3;old_id=old_vm->id;
 enemy={};enemy.current.position={x,y,z};animations.resources[file]={&resource,u16(file)};world={};world.animations=&animations;
 *reinterpret_cast<EclInstruction*>(instruction)={};auto* cmd=reinterpret_cast<EclInstruction*>(instruction);cmd->opcode=315;cmd->length=28;
 const u32 args[]={u32(file),1,angle};std::memcpy(instruction+16,args,12);EclContext c;c.instruction=cmd;EnemyScriptServices services(enemy,environment,world);const i32 result=services.command(c);created=manager.find(old_id+1);return result;
}
API(offset_effect_case) i32 offset_effect_case(i32 file,u32 program,float x,float y,float z,u32 angle){
 manager.clear();resource={};resource.scripts.resize(2);append(0,2);append(0,-1);
 if(program){const i32 layer=program==1?8:28;append(1,304,&layer,4);}
 if(program==2){const float p[]={3.25f,-7.5f,9.125f},r[]={.25f,-.5f,2.25f},scale[]={2.5f,-3.25f};append(1,400,p,12);append(1,401,r,12);append(1,404,scale,8);}
 append(1,2);append(1,-1);old_vm=manager.create(resource,0,u16(file),0);if(!old_vm)return -3;old_id=old_vm->id;
 enemy={};enemy.current.position={x,y,z};animations.resources[file]={&resource,u16(file)};world={};world.animations=&animations;
 *reinterpret_cast<EclInstruction*>(instruction)={};auto* cmd=reinterpret_cast<EclInstruction*>(instruction);cmd->opcode=337;cmd->length=36;
 const u32 args[]={u32(file),1,float_bits(-23.25f),float_bits(11.5f),angle};std::memcpy(instruction+16,args,20);EclContext c;c.instruction=cmd;EnemyScriptServices services(enemy,environment,world);const i32 result=services.command(c);created=manager.find(old_id+1);return result;
}
API(angled_value) u32 angled_value(u32 n){if(!created)return 0xffffffff;if(n==11)return float_bits(created->rotation.z);if(n==2)return created->flags&6;return vm_word(n);}
static u32 scale_result[6];
API(scale_case) i32 scale_case(u32 op,i32 selected,u32 present,u32 x,u32 y){
 manager.clear();resource={};resource.scripts.resize(1);append(0,2);append(0,-1);enemy={};
 auto* vm=manager.create(resource,0,1,0);if(!vm)return -3;vm->flags=0x202;vm->scale={1.25f,-2.5f};vm->scale_velocity={3.75f,-4.25f};
 if(selected>=0&&selected<16)enemy.animation_handle(u32(selected))=present?vm->id:0x123456;
 *reinterpret_cast<EclInstruction*>(instruction)={};auto* cmd=reinterpret_cast<EclInstruction*>(instruction);cmd->opcode=u16(op);cmd->length=28;
 const u32 args[]={u32(selected),x,y};std::memcpy(instruction+16,args,12);world={};world.animations=&animations;EclContext c;c.instruction=cmd;EnemyScriptServices services(enemy,environment,world);
 const i32 result=services.command(c);const bool alive=selected<0||selected>=16||enemy.animation_handle(u32(selected))!=0;
 const u32 values[]={vm->flags,float_bits(vm->scale.x),float_bits(vm->scale.y),float_bits(vm->scale_velocity.x),float_bits(vm->scale_velocity.y),alive?100u:0u};std::memcpy(scale_result,values,sizeof values);return result;
}
API(scale_value) u32 scale_value(u32 n){return scale_result[n];}
API(scale_interp_case) i32 scale_interp_case(i32 mode,i32 duration,float rate,float x,float y){
 manager.clear();manager.rate=rate;resource={};resource.scripts.resize(1);append(0,0);reinterpret_cast<AnmInstruction*>(resource.scripts[0].bytes.data())->time=32767;enemy={};created=manager.create(resource,0,1,0);if(!created)return -3;
 created->flags=7;created->scale={1.25f,-2.5f};auto& v=created->scale_interpolation;v.initial_tangent[0]=.25f;v.initial_tangent[1]=-.5f;v.final_tangent[0]=.75f;v.final_tangent[1]=-1.25f;
 enemy.animations[0]=created->id;world={};world.animations=&animations;*reinterpret_cast<EclInstruction*>(instruction)={};auto* cmd=reinterpret_cast<EclInstruction*>(instruction);cmd->opcode=330;cmd->length=36;
 const u32 args[]={0,u32(duration),u32(mode),float_bits(x),float_bits(y)};std::memcpy(instruction+16,args,20);EclContext c;c.instruction=cmd;EnemyScriptServices services(enemy,environment,world);return services.command(c);
}
API(scale_interp_tick) i32 scale_interp_tick(){return created->update(manager);}
API(scale_interp_value) u32 scale_interp_value(u32 n){const auto& v=created->scale_interpolation;
 if(n==0)return float_bits(created->scale.x);if(n==1)return float_bits(created->scale.y);if(n==2)return created->flags&8;
 if(n<11){const float* fields[]={v.start,v.end,v.initial_tangent,v.final_tangent};return float_bits(fields[(n-3)/2][(n-3)%2]);}
 if(n==11)return u32(v.timer.previous);if(n==12)return u32(v.timer.current);if(n==13)return float_bits(v.timer.fractional);if(n==14)return u32(v.duration);return u32(v.mode);
}
static u32 color_result[5];
API(color_case) i32 color_case(u32 op,i32 selected,u32 present,i32 value){
 manager.clear();resource={};resource.scripts.resize(1);append(0,2);append(0,-1);enemy={};auto* vm=manager.create(resource,0,1,0);if(!vm)return -3;
 vm->flags=0x602;vm->color=0x75214365;vm->secondary_color=0xc987a9cb;vm->layer=7;
 if(selected>=0&&selected<16)enemy.animation_handle(u32(selected))=present?vm->id:0x123456;
 *reinterpret_cast<EclInstruction*>(instruction)={};auto* cmd=reinterpret_cast<EclInstruction*>(instruction);cmd->opcode=u16(op);cmd->length=32;
 const u32 args[]={u32(selected),u32(value),u32(wrapping_add(value,1)),u32(wrapping_sub(value,1))};std::memcpy(instruction+16,args,16);world={};world.animations=&animations;EclContext c;c.instruction=cmd;EnemyScriptServices services(enemy,environment,world);
 const i32 result=services.command(c);const bool alive=selected<0||selected>=16||enemy.animation_handle(u32(selected))!=0;
 const u32 values[]={vm->flags,vm->color,vm->secondary_color,vm->layer,alive?100u:0u};std::memcpy(color_result,values,sizeof values);return result;
}
API(color_value) u32 color_value(u32 n){return color_result[n];}
static u32 alpha_op;
API(alpha_interp_case) i32 alpha_interp_case(u32 op,i32 mode,i32 duration,float rate,u32 start,i32 target){
 manager.clear();manager.rate=rate;resource={};resource.scripts.resize(1);append(0,0);reinterpret_cast<AnmInstruction*>(resource.scripts[0].bytes.data())->time=32767;enemy={};created=manager.create(resource,0,1,0);if(!created)return -3;
 alpha_op=op;created->flags=7;created->th13_native_flags=0x60000;created->color=(start<<24)|0x214365;created->secondary_color=(start<<24)|0x87a9cb;auto& v=op==328?created->alpha_interpolation:created->alpha2_interpolation;v.initial_tangent[0]=23;v.final_tangent[0]=-47;
 enemy.animations[0]=created->id;world={};world.animations=&animations;*reinterpret_cast<EclInstruction*>(instruction)={};auto* cmd=reinterpret_cast<EclInstruction*>(instruction);cmd->opcode=u16(op);cmd->length=32;
 const u32 args[]={0,u32(duration),u32(mode),u32(target)};std::memcpy(instruction+16,args,16);EclContext c;c.instruction=cmd;EnemyScriptServices services(enemy,environment,world);return services.command(c);
}
API(alpha_interp_value) u32 alpha_interp_value(u32 n){const auto& v=alpha_op==328?created->alpha_interpolation:created->alpha2_interpolation;
 if(n==0)return created->color;if(n==1)return created->secondary_color;if(n==2)return (created->flags&8)|(created->th13_native_flags&0x60000);
 if(n==3)return u32(v.start[0]);if(n==4)return u32(v.end[0]);if(n==5)return u32(v.initial_tangent[0]);if(n==6)return u32(v.final_tangent[0]);
 if(n==7)return u32(v.timer.previous);if(n==8)return u32(v.timer.current);if(n==9)return float_bits(v.timer.fractional);if(n==10)return u32(v.duration);return u32(v.mode);
}
API(rgb_interp_case) i32 rgb_interp_case(i32 mode,i32 duration,float rate,i32 red,i32 green,i32 blue){
 manager.clear();manager.rate=rate;resource={};resource.scripts.resize(1);append(0,0);reinterpret_cast<AnmInstruction*>(resource.scripts[0].bytes.data())->time=32767;enemy={};created=manager.create(resource,0,1,0);if(!created)return -3;
 created->flags=7;created->color=0x75214365;created->secondary_color=0xc987a9cb;auto& v=created->color_interpolation;for(u32 n=0;n<3;++n){v.initial_tangent[n]=i32(23+n*17);v.final_tangent[n]=i32(74+n*17);}
 enemy.animations[0]=created->id;world={};world.animations=&animations;*reinterpret_cast<EclInstruction*>(instruction)={};auto* cmd=reinterpret_cast<EclInstruction*>(instruction);cmd->opcode=326;cmd->length=40;
 const u32 args[]={0,u32(duration),u32(mode),u32(red),u32(green),u32(blue)};std::memcpy(instruction+16,args,24);EclContext c;c.instruction=cmd;EnemyScriptServices services(enemy,environment,world);return services.command(c);
}
API(rgb_interp_value) u32 rgb_interp_value(u32 n){const auto& v=created->color_interpolation;
 if(n==0)return created->color;if(n==1)return created->secondary_color;if(n==2)return created->flags&8;
 if(n<15){const i32* fields[]={v.start,v.end,v.initial_tangent,v.final_tangent};return u32(fields[(n-3)/3][(n-3)%3]);}
 if(n==15)return u32(v.timer.previous);if(n==16)return u32(v.timer.current);if(n==17)return float_bits(v.timer.fractional);if(n==18)return u32(v.duration);return u32(v.mode);
}
