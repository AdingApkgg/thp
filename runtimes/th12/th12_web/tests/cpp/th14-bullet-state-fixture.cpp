#include "../../cpp/game/BulletManager.hpp"
#include "../../cpp/game/BulletTh14.hpp"
#include "../../cpp/game/AnmOpcodes.hpp"
#include "../../cpp/game/EclContext.hpp"
#include "../../cpp/game/EnemyManager.hpp"
#include <memory>
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
struct World final:BulletWorld {
 std::vector<std::array<u32,21>> spawned;
 i32 collision(const BulletState&)override{return 0;}
 bool th14_spawn_enemy(const char* name,const EnemySpawn& value)override{if(std::strcmp(name,"Child"))return false;std::array<u32,21> data;std::memcpy(data.data(),&value,84);spawned.push_back(data);return true;}
};
static World world;static AnmEnvironment animations;static AnmResource resource;static std::unique_ptr<BulletManager> manager;
static BulletState* bullet;static AnmSprite sprite;static i32 initial_type;
API(begin) i32 begin(i32 type,i32 color,i32 mode,float rate){
    initial_type=type;world.spawned.clear();animations.rate=rate;animations.visual_rng={1234,0,0};resource={};resource.scripts.resize(294);
    const AnmInstruction code[]={{i16(anm_canonical_opcode(2)),8,0,0},{-1,8,0,0}};
    for(auto& script:resource.scripts){script.bytes.resize(sizeof code);std::memcpy(script.bytes.data(),code,sizeof code);}
    manager=std::make_unique<BulletManager>(resource,animations,world,7);
    for(u32 n=0;n<BulletManager::capacity;++n){manager->at(n).th14_wait_timer.previous=0;manager->at(n).th14_freeze_timer.previous=0;}
    Th14BulletEmitter e{};e.sprite=type;e.color=color;e.position={-12.25f,70.5f,0};e.angle=1.25f;e.spread=.375f;e.speed=2.75f;e.slow_speed=1.125f;e.count=3;e.layers=2;e.aim=1;e.flags=0x23;e.transform_sound=38;
    const Vec3 positions[]={{-12.25f,70.5f,0},{185,440,0},{-210,50,0},{200,300,0},{20,-90,0},{25,453,0},{0,200,0}};e.position=positions[type%7];
    if(mode==1||mode==2){e.transforms[0].opcode=2;e.transforms[0].p=mode==1?1:0;}
    if(mode==2||mode==3){auto& t=e.transforms[mode==2?1:0];t.opcode=1;t.concurrent=1;}
    if(mode==4||mode==5){if(mode==5)e.transforms[0].opcode=1;auto& t=e.transforms[mode==5?1:0];t.a=-.01f;t.b=-99999.f;t.p=60;t.opcode=4;t.concurrent=mode==5;}
    if(mode>=6){
        const auto entry=[&](i32 index,u32 op,float a,float b,i32 duration,i32 concurrent=0){auto& t=e.transforms[index];t.opcode=op;t.a=a;t.b=b;t.p=duration;t.concurrent=concurrent;};
        if(mode==6)entry(0,8,-.03f,.013f,30);
        if(mode==7){entry(0,1,0,0,0);entry(1,4,-.01f,-99999.f,20,1);entry(2,8,-.03f,.013f,30,1);}
        if(mode==8){entry(0,4,-.01f,-99999.f,1);entry(1,8,-.03f,.013f,7);}
        if(mode==9){entry(0,8,-.03f,.013f,1);entry(1,4,-.01f,-99999.f,7);}
        if(mode==10){e.transforms[0].opcode=0x80;e.transforms[0].p=9;}
        if(mode==11){e.transforms[0].opcode=1;e.transforms[1].opcode=0x80;e.transforms[1].p=9;}
        if(mode==12){e.transforms[0].opcode=0x10000;e.transforms[0].p=2;entry(1,8,99,99,60);entry(2,8,-.03f,.013f,30);}
        if(mode==13){e.transforms[0].opcode=0x2000000;e.transforms[0].p=3;}
        if(mode>=14&&mode<24){const i32 variant=(mode-14)%5,durations[]={-1,0,1,7,7};entry(0,mode<19?0x80000000u:0x4000000u,0,0,durations[variant]);entry(1,8,-.03f,.013f,30,variant==4);}
        if(mode==24)entry(0,0x200000,5,-99999,30);
        if(mode==25){entry(0,1,0,0,0);entry(1,4,-.01f,-99999,20,1);entry(2,0x200000,5,.4f,30,1);entry(3,8,-.03f,.013f,40,1);}
        if(mode==26){entry(0,0x80000000,0,0,7);entry(1,0x200000,5,990,30);}
        if(mode==27){entry(0,0x200000,5,-99999,1);entry(1,8,-.03f,.013f,7);}
        if(mode>=28){
            const auto bounce=[&](i32 index,i32 flags,i32 limit=2,i32 concurrent=0){entry(index,0x40,-99999,256,limit,concurrent);e.transforms[index].q=flags;e.transforms[index].c=320;};
            if(mode==28)bounce(0,15);
            if(mode==29)bounce(0,47);
            if(mode==30){bounce(0,15);entry(1,8,-.03f,.013f,30,1);}
            if(mode==31){bounce(0,47,0);entry(1,0x200000,5,-99999,7);}
            if(mode==32){entry(0,0x4000000,0,0,7);bounce(1,31,1);entry(2,8,-.03f,.013f,30);}
        }
        if(mode>=33&&mode<37){const i32 index=mode>=35;if(index)entry(0,0x80000000,0,0,7);entry(index,0x200,0,0,(type+19)%43);e.transforms[index].q=color|(mode%2==0?0x8000:0);}
        if(mode>=37&&mode<48){
            const auto step=[&](i32 index,i32 kind,i32 concurrent=0,i32 duration=7,i32 limit=2){entry(index,0x10,.4f,3,duration,concurrent);auto& t=e.transforms[index];t.q=limit;t.r=kind;t.s=19;};
            if(mode<44)step(0,mode-37);
            if(mode==44){entry(0,0x800000,0,0,0);step(1,2);}
            if(mode==45){entry(0,0x800000,0,0,0);step(1,3);}
            if(mode==46){step(0,1,0,1,1);entry(1,0x200000,5,-99999,7);}
            if(mode==47){step(0,0);entry(1,4,-.01f,-99999,20,1);entry(2,8,-.03f,.013f,30,1);entry(3,0x40,-99999,256,2,1);e.transforms[3].q=15;}
        }
        if(mode>=48&&mode<83){const i32 durations[]={-1,0,1};entry(0,0x400000,2.5f,1,mode<80?7:durations[mode-80]);e.transforms[0].q=mode<80?mode-48:0;entry(1,8,-.03f,.013f,30,mode%2==0);}
        if(mode>=83){const auto wrap=[&](i32 index,i32 limit=2,i32 flags=15,i32 concurrent=0){entry(index,0x1000,0,0,limit,concurrent);e.transforms[index].q=flags;};
            const auto hold=[&](i32 index,i32 count=7,i32 early=0){entry(index,0x100,0,0,count);e.transforms[index].q=early;};
            if(mode==88)hold(0);if(mode==89)hold(0,7,1);if(mode==90){hold(0,19,1);entry(1,4,-.01f,-99999.f,15);}if(mode==91)hold(0,0);if(mode==92){entry(0,0x80000000,0,0,7);hold(1,19,1);}if(mode==93){hold(0,19,1);wrap(1,2,15);}
            if(mode==83)wrap(0);if(mode==84)wrap(0,0);if(mode==85){wrap(0,2,5);entry(1,4,-.01f,-99999.f,15,1);}if(mode==86){entry(0,0x80000000,0,0,7);wrap(1);}if(mode==87){entry(0,0x400000,2.5f,1,7);wrap(1,2,15,1);}
        }
    }
    if(mode>=94){const auto entry=[&](i32 index,u32 op,float a,float b,i32 duration,i32 concurrent=0){auto& t=e.transforms[index];t.opcode=op;t.a=a;t.b=b;t.p=duration;t.concurrent=concurrent;};
        if(mode==94)entry(0,0x40000,.4f,2.5f,0);if(mode==95)entry(0,0x40000,999,-999,0);
        if(mode==96)entry(0,0x80000,.4f,1,7);if(mode==97){entry(0,0x80000,.4f,1,7);entry(1,8,-.03f,.013f,30,1);}
    }
    if(mode>=98){const auto entry=[&](i32 index,u32 op,float a,float b,i32 duration,i32 concurrent=0){auto& t=e.transforms[index];t.opcode=op;t.a=a;t.b=b;t.p=duration;t.concurrent=concurrent;};
        if(mode<130){entry(0,0x20000,22.5f,-40,7);e.transforms[0].q=(mode-98)|(type%2?0x100:0);}
        if(mode==130)entry(0,0x20000,22.5f,-40,0);if(mode==131){entry(0,0x20000,22.5f,-40,1);e.transforms[0].q=0x100;}
        if(mode==132){entry(0,0x20000,22.5f,-40,7);entry(1,8,-.03f,.013f,30,1);}if(mode==133){entry(0,0x80000000,0,0,7);entry(1,0x20000,22.5f,-40,7);}
    }
    if(mode>=134){const i32 index=mode!=134;
        if(mode==135){e.transforms[0].opcode=0x80000000;e.transforms[0].p=7;}
        if(mode==136){auto& t=e.transforms[0];t.opcode=4;t.a=-.01f;t.b=-99999;t.p=7;}
        if(mode==137){auto& t=e.transforms[0];t.opcode=0x20000;t.a=22.5f;t.b=-40;t.p=7;}
        auto& t=e.transforms[index];t.opcode=0x1000000;t.concurrent=mode==136;t.a=.125f;t.b=-2.5f;t.c=3.25f;t.d=-999;t.p=-99;t.q=250;t.r=-1000;t.s=31415;t.script=u32(uintptr_t("Child"));
    }
    const auto result=manager->spawn_th14(e,1,0,0);bullet=&manager->at(BulletManager::capacity-1);return result;
}
API(tick) i32 tick(u32 frame){
    if(!frame)bullet->collision_delay=27+initial_type;
    if(frame)bullet->lifetime.tick();sprite.width=20;sprite.height=12;bullet->vm.sprite=&sprite;bullet->vm.integers[0]=frame>=6;
    return manager->update_th14(*bullet);
}
API(value) u32 value(u32 n){
    const auto& b=*bullet;const u32 values[]={b.flags,u32(b.collision_delay),float_bits(b.position.x),float_bits(b.position.y),float_bits(b.position.z),float_bits(b.velocity.x),float_bits(b.velocity.y),float_bits(b.velocity.z),float_bits(b.speed),float_bits(b.angle),float_bits(b.hitbox.x),float_bits(b.hitbox.y),u32(b.offscreen_grace),u32(b.cancel_effect),b.active_transforms,b.emitter_flags,u32(b.transform_index),u32(b.draw_group),u32(u16(b.sprite))|(u32(u16(b.color))<<16),u32(b.lifetime.previous),u32(b.lifetime.current),float_bits(b.lifetime.fractional),u32(b.auxiliary_timer.previous),u32(b.auxiliary_timer.current),float_bits(b.auxiliary_timer.fractional),u32(b.motion[0].timer.previous),u32(b.motion[0].timer.current),float_bits(b.motion[0].timer.fractional),u32(b.motion[1].timer.previous),u32(b.motion[1].timer.current),float_bits(b.motion[1].timer.fractional),float_bits(b.motion[1].a),float_bits(b.motion[1].b),float_bits(b.motion[1].vector.x),float_bits(b.motion[1].vector.y),float_bits(b.motion[1].vector.z),u32(b.motion[1].duration),u32(b.motion[2].timer.previous),u32(b.motion[2].timer.current),float_bits(b.motion[2].timer.fractional),float_bits(b.motion[2].a),float_bits(b.motion[2].b),float_bits(b.motion[2].vector.x),float_bits(b.motion[2].vector.y),float_bits(b.motion[2].vector.z),u32(b.motion[2].duration),u32(b.th14_wait_timer.previous),u32(b.th14_wait_timer.current),float_bits(b.th14_wait_timer.fractional),u32(b.th14_freeze_timer.previous),u32(b.th14_freeze_timer.current),float_bits(b.th14_freeze_timer.fractional),u32(b.motion[10].timer.previous),u32(b.motion[10].timer.current),float_bits(b.motion[10].timer.fractional),float_bits(b.motion[10].a),float_bits(b.motion[10].b),float_bits(b.motion[10].vector.x),float_bits(b.motion[10].vector.y),float_bits(b.motion[10].vector.z),u32(b.motion[10].duration),float_bits(b.motion[4].a),float_bits(b.motion[4].b),float_bits(b.motion[4].vector.x),float_bits(b.motion[4].vector.y),float_bits(b.motion[4].vector.z),u32(b.motion[4].count),u32(b.motion[4].limit),u32(b.motion[4].duration),u32(b.motion[3].timer.previous),u32(b.motion[3].timer.current),float_bits(b.motion[3].timer.fractional),float_bits(b.motion[3].a),float_bits(b.motion[3].b),u32(b.motion[3].duration),u32(b.motion[3].limit),u32(b.motion[3].count),u32(b.th14_step_mode),u32(b.th14_step_extra),float_bits(b.motion[9].a),float_bits(b.motion[9].b),float_bits(b.motion[9].vector.x),float_bits(b.motion[9].vector.y),float_bits(b.motion[9].vector.z),float_bits(b.th14_size_interpolation.start[0]),float_bits(b.th14_size_interpolation.end[0]),float_bits(b.th14_size_interpolation.initial_tangent[0]),float_bits(b.th14_size_interpolation.final_tangent[0]),float_bits(b.th14_size_current),u32(b.th14_size_interpolation.timer.previous),u32(b.th14_size_interpolation.timer.current),float_bits(b.th14_size_interpolation.timer.fractional),u32(b.th14_size_interpolation.duration),u32(b.th14_size_interpolation.mode),float_bits(b.th14_size),u32(b.motion[5].count),u32(b.motion[5].limit),u32(b.motion[5].duration),u32(b.motion[6].timer.previous),u32(b.motion[6].timer.current),float_bits(b.motion[6].timer.fractional),u32(b.motion[6].duration),u32(animations.visual_rng.seed),animations.visual_rng.calls,u32(b.state)};
    return values[n];
}
API(table) const void* table(){return th14_bullet_appearances;}
API(spawn_count) u32 spawn_count(){return world.spawned.size();}
API(spawn_word) u32 spawn_word(u32 n,u32 at){return world.spawned[n][at];}
