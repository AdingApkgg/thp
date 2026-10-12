#include "render-fixture.hpp"
#include "../../cpp/game/BulletManager.hpp"
#include "../../cpp/game/AnmOpcodes.hpp"
#include "../../cpp/game/EclContext.hpp"
#include <memory>
using namespace th11;using namespace th11::test;
#define API(name) extern "C" __attribute__((export_name(#name)))
struct World:BulletWorld{i32 collision(const BulletState&)override{return 0;}};
static World world;static AnmEnvironment animations;static RenderFixture fixture;static std::unique_ptr<BulletManager> manager;static BulletState* bullet;
API(begin) i32 begin(i32 rotate,i32 scaled,float angle,float scale){
 fixture.resource={};fixture.resource.scripts.resize(294);
 const AnmInstruction code[]={{i16(anm_canonical_opcode(2)),8,0,0},{-1,8,0,0}};
 for(auto& script:fixture.resource.scripts){script.bytes.resize(sizeof code);std::memcpy(script.bytes.data(),code,sizeof code);}
 manager=std::make_unique<BulletManager>(fixture.resource,animations,world,7);Th14BulletEmitter e{};e.count=e.layers=1;
 if(manager->spawn_th14(e,0,0,0)<0||!manager->update())return -2;
 bullet=manager->first_th14();if(!bullet)return -2;auto& vm=bullet->vm;
 bullet->position={-12.25f,70.5f,.25f};bullet->angle=angle;bullet->th14_size=scale;bullet->flags=scaled?0x40:0;
 vm.flags=0;vm.flags2=rotate?0x40:0;vm.script_position={3.25f,-9.5f,.125f};vm.rotation.z=-.625f;vm.scale={1.1f,-.625f};vm.extra_scale={.75f,1.25f};
 return manager->draw_group(bullet->draw_group,fixture.renderer)?0:-2;
}
API(word) u32 word(u32 n){const auto& v=bullet->vm;const u32 words[]={v.flags,float_bits(v.script_position.x),float_bits(v.script_position.y),float_bits(v.script_position.z),float_bits(v.rotation.z),float_bits(v.scale.x),float_bits(v.scale.y),float_bits(v.extra_scale.x),float_bits(v.extra_scale.y)};return words[n];}
