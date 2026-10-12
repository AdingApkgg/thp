#include "../../cpp/game/ScreenDeformation.hpp"
#include "../../cpp/game/EclContext.hpp"
#include "../../cpp/game/AnmOpcodes.hpp"
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static AnmManager manager;static AnmResource text;static EnemyState enemy;static std::unique_ptr<ScreenDeformation> effect;
API(begin) i32 begin(float x,float y,float z,float radius,float rate){
    effect.reset();manager.clear();manager.rate=rate;enemy={};enemy.current.position={x,y,z};enemy.deformation_target=128;enemy.deformation_radius=radius;enemy.deformation_color=0x008f8fff;enemy.deformation_phase_x=.25f;enemy.deformation_phase_y=-.5f;
    text.scripts.resize(60);const AnmInstruction code[]={{i16(anm_canonical_opcode(2)),8,0,0},{-1,8,0,0}};
    for(auto& s:text.scripts){s.bytes.resize(sizeof code);std::memcpy(s.bytes.data(),code,sizeof code);}
    effect=std::make_unique<ScreenDeformation>(manager);return effect->initialize(text)?0:-2;
}
API(tick) void tick(){effect->update(enemy,0);}
API(radius) float radius(){return enemy.deformation_radius;}
API(phase) float phase(u32 n){return n?enemy.deformation_phase_y:enemy.deformation_phase_x;}
API(value) float value(u32 j,u32 n){auto& v=effect->vertices[j];auto& p=effect->positions[j];const float a[]={v.position.x,v.position.y,v.position.z,v.reciprocal_w,v.uv.x,v.uv.y,p.x,p.y,p.z};return a[n];}
API(color) u32 color(u32 j){return effect->vertices[j].color;}
