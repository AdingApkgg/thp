#include "EnemyTargetAngle.hpp"
#include "EnemyBossIntegerVariables.hpp"
#include "EnemyOffsetPositionTween.hpp"
#include "EnemyAnimationParameters.hpp"
#include "EnemyBossPositionVariables.hpp"
#include "EnemyVisibilityBounds.hpp"
#include "EnemyVisualPositionBinding.hpp"
#include "EnemyReservedInteger.hpp"
#include "EnemyLastActorIdentity.hpp"
#include "EmitterCursorDecrement.hpp"
#include "EnemyPositionMerge.hpp"
#include "EnemyActorIdentity.hpp"
#include "EnemyHermiteRouting.hpp"
#include "EnemyPlayerDistance.hpp"
#include "EnemyScriptFloatCells.hpp"
#include "EnemyRandomInteger.hpp"
#include "EnemyDifficultyInteger.hpp"
#include "EnemyDifficultyFloat.hpp"
namespace th143 {u32 campaign_difficulty_index();}
#include "EnemyAnimationRefresh.hpp"
#include "EnemyDeathVisualConfig.hpp"
#include "EnemyAnimationCurveScratchDirect.hpp"
#include "LaserEmitterLaunch.hpp"
#include "EnemyClockVariables.hpp"
#include "EnemyPositionClampDisable.hpp"
#include "EnemyEllipseTween.hpp"
#include "EnemyEllipseCommands.hpp"
#include "LaserEmitterSetup.hpp"
#include "EnemyHealthVariable.hpp"
#include "EnemyDamageFactor.hpp"
#include "EnemyVelocityAngle.hpp"
#include "EnemyAnimationOffset.hpp"
#include "EnemyAimVariables.hpp"
#include "EnemyMotionVariables.hpp"
#include "EnemyAngleTween.hpp"
#include "EnemySpeedTween.hpp"
#include "EnemyFlag27.hpp"
#include "EnemyHitSound.hpp"
#include "EclVariableTweenRuntime.hpp"
#include "EnemySpecialFlag.hpp"
// Alternate link composition; all interpreter bodies come from EnemyScripts.cpp.
#include "EnemyScriptsDay1.hpp"
#include "EnemySpawnDefaults.hpp"
#include <cmath>
#include <algorithm>

namespace th143 {
i32 campaign_alpha_command(AnmView,Vm&,VmHost&);
i32 campaign_laser_command(Emitters&,Vm&,VmHost&);
namespace {
u32 truncate(float v) { return v >= -2147483648.f && v < 2147483648.f ? u32(i32(v)) : 0x80000000; }
u32 pointer(const void* p) { return u32(reinterpret_cast<std::uintptr_t>(p)); }
i32 nested_failure_opcode = 0;
u32 day1_spawn_failure[4]{};
u32 campaign_actor_tick_failure[16]{};
}
extern "C" __attribute__((export_name("day1_spawn_failure"))) u32 day1_spawn_failure_word(u32 i){return i<4?day1_spawn_failure[i]:0;}
extern "C" __attribute__((export_name("campaign_actor_tick_diagnostic"))) u32 campaign_actor_tick_diagnostic(u32 i){return i<16?campaign_actor_tick_failure[i]:0;}
bool EnemyScripts::integer(i32 id, i32& value) {
    if(id>=-9943&&id<=-9940){const u32 token=controls.bosses[0];AnmView boss{nullptr};if(token){for(auto& a:storage)if(a->token==token){boss={a->state.fields.data.data()};break;}if(!boss.data)return false;}return enemy_boss_integer_variable(boss,id,value);}
    if(enemy_reserved_integer(id,value))return true;
    if(enemy_last_actor_identity(last_id,id,value))return true;
    if(id==-10000){auto* random=services.gameplay_rng();return random&&enemy_random_integer(*random,id,value);}
    if(active&&enemy_actor_identity(active->state.id,id,value))return true;
    if(active&&enemy_clock_variable({active->state.fields.data.data()},id,value))return true;
    if(active&&enemy_health_variable({active->state.fields.data.data()},id,value))return true;
    if (id != -9905) return false;
    value = (services.game_flags() >> 1) & 1; return true;
}
bool EnemyScripts::floating(i32 id,float& value){
    if(id==-9963||id==-9962){const u32 token=controls.bosses[0];AnmView boss{nullptr};if(token){for(auto& a:storage)if(a->token==token){boss={a->state.fields.data.data()};break;}if(!boss.data)return false;}return enemy_boss_position_variable(boss,id,value);}
    if(id==-9999){auto* random=services.gameplay_rng();if(!random)return false;value=random->unit();return true;}
    if(id==-9987){auto* random=services.gameplay_rng();if(!random)return false;value=random->signed_unit();return true;}
    if(id==-9998){auto* random=services.gameplay_rng();if(!random)return false;value=random->signed_unit()*real(0x40490fdb);return true;}
    if(enemy_aim_variable(services,id,value))return true;
    if(!active)return false;
    if(enemy_script_float_value({active->state.fields.data.data()},id,value))return true;
    if(id==-9944){float x,y;return services.aim_position(x,y)&&enemy_player_distance({active->state.fields.data.data()},id,x,y,value);}
    if(enemy_velocity_angle({active->state.fields.data.data()},id,value))return true;
    if(enemy_motion_variable({active->state.fields.data.data()},id,value))return true;
    switch(id){case -9997:value=active->state.fields.floating(0x44);return true;case -9996:value=active->state.fields.floating(0x48);return true;case -9981:case -9980:case -9979:case -9978:value=active->state.fields.floating(0x33c+u32(id+9981)*4);return true;default:break;}
    if(id!=-9989)return false;
    float x,y;if(!services.aim_position(x,y))return false;
    x-=active->state.fields.floating(0x44);y-=active->state.fields.floating(0x48);
    if(!std::isfinite(x)||!std::isfinite(y))return false;
    value=x==0.f&&y==0.f?real(0x3fc90fdb):float(std::atan2(double(y),double(x)));return true;
}
bool EnemyScripts::timer(ActorState& s, u32 at, float elapsed, bool decrement) {
    const u32 current = s.get(at + 4), token = s.get(at + 12);
    if (token && token != rate_token) return false;
    const bool unit = !token || (elapsed > real(0x3f7d70a4) && elapsed < real(0x3f8147ae));
    s.put(at, current);
    if (decrement) {
        const float fraction = s.fields.floating(at + 8) - (unit ? 1.f : elapsed);
        s.put(at + 4, truncate(fraction)); s.put(at + 8, word(fraction));
    } else if (unit) {
        s.put(at + 4, current + 1); s.put(at + 8, word(s.fields.floating(at + 8) + 1.f));
    } else {
        const float fraction = s.fields.floating(at + 8) + elapsed;
        s.put(at + 4, truncate(fraction)); s.put(at + 8, word(fraction));
    }
    return true;
}
bool EnemyScripts::position(ActorState& s, bool before,float elapsed) {
    // Native41f3b0: scalar angle/speed interpolation and mode0 movement.
    if (before) {
        for (u32 i = 0; i != 17; ++i) s.put(i * 4, s.get(0x44 + i * 4));
        struct Rates:AnmTimerHost{float rate;u32 token;Rates(float r,u32 t):rate(r),token(t){}bool timer_rate(u32 t,float& v)override{if(t!=token)return false;v=rate;return true;}u32 global_rate_token()const override{return token;}} rates(elapsed,rate_token);
        if(!enemy_direct_movement(s,rates.rate,rates))return false;
    }
    // 400/41fa10 composes absolute and relative parts; the immediate setter
    // clears the movement delta by composing before refreshing the delta.
    for (u32 i = 0; i != 3; ++i) {
        const float value = s.fields.floating(0xcc + i * 4) + s.fields.floating(0x88 + i * 4);
        s.put(0x78 + i * 4, word(value - s.fields.floating(0x44 + i * 4)));
        const float integrated=s.fields.floating(0x44+i*4)+s.fields.floating(0x78+i*4);
        s.put(0x44 + i * 4, word(i<2?enemy_position_quantize(integrated):integrated));
    }
    if(s.get(0x4100)&0x20000){for(u32 i=0;i<2;++i){const float center=s.fields.floating(0x4004+i*4),half=s.fields.floating(0x400c+i*4)*.5f,value=s.fields.floating(0x44+i*4);if(center-half>value)s.put(0x44+i*4,word(center-half));else if(value>center+half)s.put(0x44+i*4,word(center+half));}for(u32 i=0;i<3;++i)s.put(0x88+i*4,word(s.fields.floating(0x44+i*4)-s.fields.floating(0xcc+i*4)));}
    if (before) {
        if(!change_visual(s))return false;
        EnemyVisual visual;
        if (services.visual(s.get(0x124), visual)) {
            s.put(0x3ffc, word(std::fabs(visual.height * visual.scale_y)));
            s.put(0x4000, word(std::fabs(visual.width * visual.scale_x)));
        } else s.put(0x124, 0);
        const float x = s.fields.floating(0x44), y = s.fields.floating(0x48);
        const float hx = s.fields.floating(0x3ffc) * .5f, hy = s.fields.floating(0x4000) * .5f;
        if (x + hx >= -192.f && x - hx <= 192.f && y + hy >= 0.f && y - hy <= 448.f) s.put(0x4100, s.get(0x4100) | 0x10000);
    }
    return true;
}
bool EnemyScripts::change_visual(ActorState& s){
    if(!(s.get(0x4100)&0x100000))return true;
    const float dx=s.fields.floating(0x78);const i32 direction=dx<real(0xbcf5c28f)?-1:dx>real(0x3cf5c28f)?1:0;
    const i32 previous=signed_word(s.get(0x314));if(previous==direction)return true;
    const i32 offset=previous==1?(direction==0?4:1):previous==-1?(direction==0?3:2):direction==-1?1:2;
    EnemyVisual visual;if(!services.change_visual(s.get(0x124),signed_word(s.get(0x310))+offset,signed_word(s.get(0x31c))+7,visual))return false;
    s.put(0x124,visual.handle);s.put(0x314,u32(direction));
    auto node=std::make_unique<AnmNode>();node->id=visual.handle;node->flags=visual.flags;node->secondary_flags=visual.flags2;node->active=true;
    AnmNode* p=node.get();visual_nodes[visual.handle]=std::move(node);
    if((visual.handle&8191)==8191)animations.primary.push_back(p);else animations.pool[visual.handle&8191]=p;return true;
}
bool EnemyScripts::spawn_enemy(const char* name, const EnemySpawn& spawn) {
    auto failure=[&](u32 stage){day1_spawn_failure[0]=stage;day1_spawn_failure[1]=u32(error_opcode);day1_spawn_failure[2]=u32(storage.size());day1_spawn_failure[3]=active?active->state.id:0;return false;};
    if (failed || storage.size() >= 99999 || !program.find(name)) return failure(1);
    u32 token;if(!allocate_enemy_actor_address(*this,next_id,token))return failure(2);
    auto owned = std::make_unique<Actor>(enemy_scene_vm_host(*this), token, name); Actor& actor = *owned;
    if(!services.prepare_actor(actor.owner)){failed=true;return failure(3);}
    actor.state.initialize(next_id, last_id, token, rate_token);
    actor.owner.root.instruction = program.find(name);
    actor.owner.root.difficulty = actor.state.bind_spawn(spawn, difficulty, rate_token);
    storage.push_back(std::move(owned));
    Actor* previous = active;
    if (!tick(actor, combat?combat->current_rate():1.f)) { nested_failure_opcode=error_opcode; failure(4); active = previous; failed = true; return false; }
    active = previous;
    auto& s = actor.state;
    finish_enemy_spawn_defaults({s.fields.data.data()},s.id);
    if (!live.empty()) {
        Actor* tail = live.back(); tail->state.put(0x390, actor.token + 0x157c);
        s.put(0x394, tail->token + 0x157c);
    }
    live.push_back(&actor); return true;
}
bool EnemyScripts::position_visuals(ActorState& s){return position_enemy_visuals(*this,s);}
bool EnemyScripts::tick(Actor& actor, float elapsed,i32* result) {
    i32 ignored=0;if(!result)result=&ignored;*result=0;
    active = &actor; auto& s = actor.state;auto tick_failure=[&](u32 stage){if(campaign_actor_tick_failure[0])return false;const u32 words[]={stage,s.id,s.get(0x4100),s.get(0x4104),s.get(0x388),word(elapsed),s.get(0x41d8),s.get(0x41bc),s.get(0x407c),s.get(0x41e0),s.get(0x41e4),s.get(0x4030),u32(actor.owner.root.error_opcode),u32(actor.owner.root.failed),s.get(0x4018),s.get(0x4020)};std::memcpy(campaign_actor_tick_failure,words,sizeof(words));return false;};
    if(combat)elapsed=combat->current_rate();
    s.put(0x388, word(elapsed));
    const float slowdown = s.fields.floating(0x384);
    const bool slowed=slowdown > 0.f || (s.get(0x4100) & 0x2000);
    if (slowed) {
        elapsed -= slowdown * elapsed;
        if (elapsed > 1.f) elapsed = 1.f;
        if (elapsed < 0.f) elapsed = 0.f;
        if (s.get(0x4100) & 0x2000) elapsed = 1.f;
        if(combat&&!combat->slowdown(s,slowdown))return tick_failure(1);
        if(!combat)s.put(0x4104,s.get(0x4104)|2);
    }else if(combat&&(s.get(0x4104)&2)){
        if(!combat->slowdown(s,0.f))return tick_failure(2);
        s.put(0x4104,s.get(0x4104)&~2u);
    }
    struct RestoreRate {EnemyActorRuntime* runtime;ActorState& state;float previous;bool slowed;
        ~RestoreRate(){if(runtime){if(slowed)state.put(0x4104,state.get(0x4104)|2);runtime->exchange_rate(state.fields.floating(0x388));}}
    } restore{combat,s,combat?combat->exchange_rate(elapsed):0.f,slowed};
    if (s.get(0x4100) & 0x40000) {enemy_animation_stack_entry(*this);return true;}
    s.put(0x4100, s.get(0x4100) | 0x40000);
    if (!position(s, true,elapsed)) return tick_failure(3);
    if(update_enemy_visibility_bounds({s.fields.data.data()})==-1){*result=-1;return true;}
    const i32 script_status = actor.owner.update(elapsed);
    // ECL547 changes actor388/current global rate during this update.
    // Post-script callbacks and timers consume that new rate.
    elapsed=combat?combat->current_rate():s.fields.floating(0x388);
    if (script_status != 0) {
        error_opcode = nested_failure_opcode ? nested_failure_opcode : actor.owner.active->error_opcode;
        if(!combat||script_status==-2)return tick_failure(4);
        *result=-1;return true;
    }
    if(combat){
        if(!combat->update_actor(s,actor.owner,actor.death_callback,elapsed,*result))return tick_failure(5);
        if(*result)return true;
    }else{
    // Empty-shot update profile. Damage, death, phase transitions and actor
    // callbacks are intentionally not fabricated by this script composition.
    if (s.get(0x41d8) || s.get(0x41bc) || s.get(0x407c) || s.get(0x41e0) || s.get(0x41e4) || (s.get(0x4030) & 2)) return tick_failure(6);
    // 420400/428c90, with no incoming shot damage: refresh the phase-relative
    // health cache and stop at an unimplemented health/time transition.
    s.put(0x4100, s.get(0x4100) & ~0x200000u);
    s.put(0x4020, s.get(0x4018)); s.put(0x4028, 0);
    for (u32 slot = 0; slot != 8; ++slot) {
        const u32 at = 0x4118 + slot*20;
        if (signed_word(s.get(at)) < 0) continue;
        s.put(0x4020, s.get(0x4018)-s.get(at)); s.put(0x4028, s.get(at));
        if (signed_word(s.get(0x4018)) <= signed_word(s.get(at))) return tick_failure(7);
        break;
    }
    for (u32 slot = 0; slot != 8; ++slot) {
        const u32 at = 0x4118 + slot*20;
        if (signed_word(s.get(at)) >= 0 && signed_word(s.get(at+4)) > 0) {
            if (signed_word(s.get(0x360)) >= signed_word(s.get(at+4))) return tick_failure(8);
            break;
        }
    }
    }
    if (!position_visuals(s)) return tick_failure(9);
    if (signed_word(s.get(0x409c)) > 0 && !timer(s, 0x4098, elapsed, true)) return tick_failure(10);
    if (signed_word(s.get(0x40b0)) > 0 && !timer(s, 0x40ac, elapsed, true)) return tick_failure(11);
    return timer(s, 0x370, elapsed) && timer(s, 0x35c, elapsed);
}
bool EnemyScripts::update(float elapsed) {
    if (failed) return false;
    ++frame;
    if(combat)combat->begin_frame();
    for (auto at = live.begin(); at != live.end();) {
        Actor* actor = *at; auto next = std::next(at);
        i32 result=0;
        if(combat&&(actor->state.get(0x4100)&0x2000000))result=-1;
        else if (!tick(*actor, elapsed,&result)) { failed = true; return false; }
        if(result){
            if(!retire(*actor)){failed=true;return false;}
            live.erase(at);
        }else actor->state.put(0x4100, actor->state.get(0x4100) & ~0x40000u);
        at = next;
    }
    active = nullptr; return true;
}
bool EnemyScripts::retire(Actor& actor){
    if(!combat)return false;
    auto at=std::find(live.begin(),live.end(),&actor);if(at==live.end())return false;
    auto next=std::next(at);Actor* previous=at==live.begin()?nullptr:*std::prev(at);
    if(!begin_enemy_actor_retirement(*this,actor)||!combat->retire_actor(actor.state,actor.owner))return false;
    if(next!=live.end())(*next)->state.put(0x394,previous?previous->token+0x157c:0);
    if(previous)previous->state.put(0x390,next==live.end()?0:(*next)->token+0x157c);
    actor.state.put(0x390,0);actor.state.put(0x394,0);
    if(actor.state.get(0x4100)&0x800000){const u32 slot=actor.state.get(0x4110);if(slot>=controls.bosses.size())return false;controls.bosses[slot]=0;}
    actor.retired=true;return finish_enemy_actor_retirement(*this,actor);
}
bool EnemyScripts::animation_command(Vm& vm) {
    auto& s = active->state; const u32 op = vm.instruction->opcode;
    const i32 slot = op==318?0:vm.integer_argument(0, active->owner), argument = op==318?signed_word(s.get(0x310)):op == 319 ? 0 : vm.integer_argument(1, active->owner);
    if (slot < 0 || slot >= 24 || vm.failed) return false;
    const u32 at = 0x124 + u32(slot)*4, previous = s.get(at);
    if (op == 319) {
        EnemyVisual found;
        if (!services.visual(previous, found)) { s.put(at, 0); return true; }
        return services.rotate_visual(previous, vm.float_argument(1, active->owner));
    }
    if (previous && !services.retire_visual(previous)) return false;
    s.put(at, 0);
    if (op == 303 && argument < 0) return true;
    EnemyVisual visual;
    if (!services.create_visual(signed_word(s.get(0x304)), op==316?signed_word(s.get(0x310))+(argument>=0?argument+5:0):argument, signed_word(s.get(0x31c))+7, visual)) return false;
    s.put(at, visual.handle);
    auto node = std::make_unique<AnmNode>(); node->id = visual.handle; node->flags = visual.flags; node->secondary_flags = visual.flags2; node->active = true;
    AnmNode* p = node.get(); visual_nodes[visual.handle] = std::move(node);
    if ((visual.handle & 8191) == 8191) animations.primary.push_back(p);
    else animations.pool[visual.handle & 8191] = p;
    if (!slot) {
        if(op!=318){s.put(0x3ffc, word(visual.height * visual.scale_y)); s.put(0x4000, word(visual.width * visual.scale_x));}
        if(op!=316){s.put(0x30c, u32(argument)); s.put(0x308, s.get(0x304));}
        if (op == 306) { s.put(0x4100, s.get(0x4100) | 0x100000); s.put(0x310, u32(argument)); s.put(0x314, 0); }
        if(op==318){s.put(0x4100,s.get(0x4100)&~0x100000u);s.put(0x314,0);}
    }
    if (op!=318&&(s.get(0x4100) & 0x20)) {
        animations.flag2(visual.handle, false);
        if(!services.flag_visual(visual.handle,false))return false;
    }
    return !vm.failed;
}
i32 EnemyScripts::command(Vm& vm) {
    if (!active) return -2;
    auto& actor = *active; auto& s = actor.state; const u32 op = vm.instruction->opcode;
    error_opcode = i32(op); services.command(s.id, vm);
    if(op==623){struct Target:EnemyTargetAngleHost{EnemyScriptServices& services;explicit Target(EnemyScriptServices& s):services(s){}bool target_angle_position(float& x,float& y)override{return services.aim_position(x,y);}}target(services);return enemy_target_angle_command(vm,actor.owner,target);}
    if(op==436||op==437){struct Rates:AnmTimerHost{u32 token;explicit Rates(u32 p):token(p){}bool timer_rate(u32,float&)override{return false;}u32 global_rate_token()const override{return token;}}rates(rate_token);return enemy_offset_position_tween_command(s,vm,actor.owner,rates);}
    if(op==322||op==552)return enemy_animation_parameter_command({s.fields.data.data()},vm,actor.owner);
    if (op == 502 || op == 503) {
        const i32 result=actor_visual_command(vm,actor.owner,s,animations);
        if(result)return result;
        if(op==502?(s.get(0x4100)&0x20)!=0:(s.get(0x4100)&0x20)==0)
            for(u32 slot=0;slot<24;++slot)if(!services.flag_visual(s.get(0x124+slot*4),op==503))return -2;
        return 0;
    }
    if(op>=626&&op<=628)return emitter_placement_command(s.fields,vm,actor.owner);
    if(op==613||op==543||op==800||op==801||op==637||op==555)return dispatch_enemy_scene_command(*this,vm);
    if (op >= 600 && op <= 614) return s.fields.command(vm, actor.owner, &emitters);
    if (op == 300 || op == 301 || op == 304 || op == 305 || (op >= 309 && op <= 312) || op == 321) {
        const SpawnLimits limits{i32(live.size()), 99999, 0};
        return enemy_spawn_command(vm, actor.owner, s.fields, s.id, limits, *this);
    }
    if (op == 302 || op == 500 || op == 501 || op == 506 || op == 507 || op == 508 || op == 510 || op == 511 || op == 512 || op == 515)
        return actor_control_command(vm, actor.owner, s, controls, actor.token, rate_token);
    if (op == 303 || op == 306 || op == 316 || op == 318 || op == 319) return animation_command(vm) ? 0 : -2;
    switch (op) {
    case 535:return enemy_difficulty_integer(vm,actor.owner,campaign_difficulty_index());
    case 536:return enemy_difficulty_float(vm,actor.owner,campaign_difficulty_index());
    case 313:{
        struct Refresh:EnemyAnimationRefreshHost {
            EnemyScripts& owner;std::array<u8,0x88> image{};
            explicit Refresh(EnemyScripts& scripts):owner(scripts){}
            bool refresh_retire(u32,u32& handle)override {
                if(handle&&!owner.services.retire_visual(handle))return false;
                handle=0;return true;
            }
            bool refresh_create(i32 selector,i32 script,i32 layer,u32& handle)override {
                EnemyVisual visual;if(!owner.services.create_visual(selector,script,layer,visual))return false;
                handle=visual.handle;
                auto node=std::make_unique<AnmNode>();node->id=handle;node->flags=visual.flags;node->secondary_flags=visual.flags2;node->active=true;
                AnmNode* p=node.get();owner.visual_nodes[handle]=std::move(node);
                if((handle&8191)==8191)owner.animations.primary.push_back(p);else owner.animations.pool[handle&8191]=p;
                return true;
            }
            bool refresh_find(u32,u32& handle,AnmView& result)override {
                EnemyVisual visual;if(!owner.services.visual(handle,visual)){handle=0;result={nullptr};return true;}
                result={image.data()};result.put(0x80,word(visual.width));result.put(0x84,word(visual.height));
                result.put(0x60,word(visual.scale_x));result.put(0x64,word(visual.scale_y));return true;
            }
            bool refresh_clear_flag2(u32,u32& handle)override {
                owner.animations.flag2(handle,false);return owner.services.flag_visual(handle,false);
            }
        } visuals(*this);
        return enemy_animation_refresh({s.fields.data.data()},vm,actor.owner,visuals);
    }
    case 320:return enemy_animation_offset({s.fields.data.data()},vm,actor.owner);
    case 323:return enemy_death_visual_config({s.fields.data.data()},vm,actor.owner);
    case 425:case 426:return enemy_hermite_routing({s.fields.data.data()},vm,actor.owner,rate_token);
    case 421:case 423:return enemy_ellipse_tween({s.fields.data.data()},vm,actor.owner,rate_token);
    case 420:case 422:return enemy_ellipse_command({s.fields.data.data()},vm,actor.owner);
    case 317:case 640:case 712:return dispatch_enemy_scene_command(*this,vm);
    case 702:case 703:case 711:return campaign_laser_command(s.fields,vm,actor.owner);
    case 700:case 701:return laser_emitter_setup(s.fields,vm,actor.owner);
    case 1004:signal_flags|=1;++signal_count;break;
    case 412:case 413:{
        Rng* rng=services.gameplay_rng();float x,y;if(!rng||!services.aim_position(x,y))return -2;
        struct Rates:AnmTimerHost{u32 token;Rates(u32 t):token(t){}bool timer_rate(u32,float&)override{return false;}u32 global_rate_token()const override{return token;}} rates(rate_token);
        return enemy_random_movement(s,op==413,vm.integer_argument(0,actor.owner),vm.integer_argument(1,actor.owner),vm.float_argument(2,actor.owner),x,*rng,rates)&&!vm.failed?0:-2;
    }
    case 91:case 92:return campaign_tweens_command(vm,enemy_scene_vm_host(*this));
    case 331:case 332:case 329:case 330:case 335:case 336:case 328:return campaign_alpha_command({s.fields.data.data()},vm,actor.owner);
    case 440:case 441:case 442:case 443:{struct Rates:AnmTimerHost{u32 token;Rates(u32 p):token(p){}bool timer_rate(u32,float&)override{return false;}u32 global_rate_token()const override{return token;}}rates(rate_token);return enemy_angle_command(s.fields,vm,actor.owner,rates);}
    case 444:case 445:case 446:case 447:{struct Rates:AnmTimerHost{u32 token;Rates(u32 p):token(p){}bool timer_rate(u32,float&)override{return false;}u32 global_rate_token()const override{return token;}}rates(rate_token);return enemy_speed_command(s.fields,vm,actor.owner,rates);}
    case 544:return enemy_flag27_command(s.fields,vm,actor.owner);
    case 553:return enemy_hit_sound_command(s.fields,vm,actor.owner);
    case 565:return enemy_damage_factor_command(s.fields,vm,actor.owner);
    case 568:return enemy_special_flag_command(s.fields,vm,actor.owner);
    case 525:return dispatch_enemy_manager_sweep(*this)?0:-2;
    case 526:{const float radius=vm.float_argument(0,actor.owner);s.put(0x4114,word(radius*radius));return vm.failed?-2:0;}
    case 1006:case 524:case 1005:case 307:case 315:case 517:case 615:case 616:case 522:case 523:case 545:case 547:return dispatch_enemy_scene_command(*this,vm);
    case 641:{const i32 index=vm.integer_argument(0,actor.owner);return !vm.failed&&decrement_emitter_cursor({s.fields.data.data()},index)?0:-2;}
    // Actual4253a0 stores the inline NUL-terminated name at instruction+20.
    case 556:{if(vm.instruction->length<21)return -2;const auto* name=reinterpret_cast<const u8*>(vm.instruction)+20;if(!std::memchr(name,0,vm.instruction->length-20))return -2;s.put(0x41d4,pointer(name));return 0;}
    case 564:{const float value=vm.float_argument(0,actor.owner);if(vm.failed)return -2;s.put(0x120,word(value));return 0;}
    case 632:{static constexpr u32 entries[]={0,0x429ab0,0x429da0,0x429ec0,0x429f90,0x42a0b0,0x42a120,0x42a330,0x42a350,0x4295a0,0x429690,0x4297e0,0x4297f0,0x429800,0x429990};const i32 i=vm.integer_argument(0,actor.owner);if(vm.failed||i<0||i>=15)return -2;s.put(0x41dc,0);s.put(0x41d8,entries[i]);return 0;}
    case 427:merge_enemy_position({s.fields.data.data()},{0,0,0});return 0;
    case 505:return disable_enemy_position_clamp({s.fields.data.data()})?0:-2;
    case 504:s.put(0x4100,s.get(0x4100)|0x20000);for(u32 i=0;i<4;++i)s.put(0x4004+i*4,word(vm.float_argument(i,actor.owner)));return vm.failed?-2:0;
    case 404:case 406:return set_enemy_polar(s,op==406,vm.float_argument(0,actor.owner),vm.float_argument(1,actor.owner))&&!vm.failed?0:-2;
    case 405:case 407:{const float angle=vm.float_argument(2,actor.owner),speed=vm.float_argument(3,actor.owner);const i32 duration=vm.integer_argument(0,actor.owner),mode=duration>0?vm.integer_argument(1,actor.owner):0;struct Rates:AnmTimerHost{u32 token;Rates(u32 t):token(t){}bool timer_rate(u32,float&)override{return false;}u32 global_rate_token()const override{return token;}} rates(rate_token);return start_enemy_polar_tween(s,op==407,duration,mode,angle,speed,rates)&&!vm.failed?0:-2;}
    case 401:case 403:{
        const float x=vm.float_argument(2,actor.owner),y=vm.float_argument(3,actor.owner);const i32 duration=vm.integer_argument(0,actor.owner);const i32 mode=duration>0?vm.integer_argument(1,actor.owner):0;
        struct Rates:AnmTimerHost{EnemyScriptServices& services;u32 token;Rates(EnemyScriptServices& s,u32 p):services(s),token(p){}bool timer_rate(u32,float&)override{return false;}u32 global_rate_token()const override{return token;}} rates(services,rate_token);
        return !vm.failed&&start_enemy_position_tween(s,op==403,duration,mode,x,y,rates)?0:-2;
    }
    case 400:case 402: {
        const u32 base=op==400?0x88:0xcc;
        for (u32 i = 0; i != 2; ++i) {
            const float value = vm.float_argument(i, actor.owner);
            if (double(value) > -999999.) s.put(base + i*4, word(value));
        }
        s.put(base+0x40, s.get(base+0x40) & ~15u);
        for (u32 i = 0; i != 3; ++i) s.put(0x44 + i*4, word(s.fields.floating(0xcc + i*4) + s.fields.floating(0x88 + i*4)));
        return position(s, false) ? 0 : -2;
    }
    case 513:
        if (!(s.get(0x36c) & 1)) { s.put(0x368, rate_token); s.put(0x36c, s.get(0x36c) | 1); }
        s.put(0x35c, 0xffffffff); s.put(0x360, 0); s.put(0x364, 0); break;
    case 514: {
        const u32 slot = u32(vm.integer_argument(0, actor.owner)), health = u32(vm.integer_argument(1, actor.owner)), time = u32(vm.integer_argument(2, actor.owner));
        if (slot >= 8 || (services.game_flags() & 0x60) == 0x40) return -2;
        const u32 at = 0x4118 + slot*20, name = pointer(reinterpret_cast<const u8*>(vm.instruction)+32);
        s.put(at, health);
        if (signed_word(health) >= 0) { s.put(at+4, time); s.put(at+8, name); s.put(at+12, name); s.put(at+16, 0); }
        break;
    }
    case 516: return services.sound(vm.integer_argument(0, actor.owner), s.fields.floating(0x44)) ? 0 : -2;
    case 518:
        if (!services.root_special() && !services.message_select(vm.integer_argument(0, actor.owner))) return -2;
        break;
    case 519: if (services.message_active()) return -2; break;
    case 521: {
        const u32 slot = u32(vm.integer_argument(0, actor.owner)); if (slot >= 8) return -2;
        s.put(0x4124+slot*20, pointer(reinterpret_cast<const u8*>(vm.instruction)+24)); break;
    }
    case 540: return services.hud_value(vm.integer_argument(0, actor.owner)) ? 0 : -2;
    default: return -2;
    }
    return vm.failed ? -2 : 0;
}
}
