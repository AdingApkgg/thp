#include "th14-stage-asset-anm-fixture.cpp"
#include "../../cpp/game/Stage.hpp"
#include <memory>
static AnmResource text;
static SceneCamera camera;
static u32 background_color;
static std::unique_ptr<Stage> stage;
API(stage_begin) u32 stage_begin(u32 flags,u32 fade){
    stage.reset(); camera={}; camera.up={};
    StageResource file; StageInstruction stop; stop.time=0;stop.opcode=0;stop.length=8;stop.offset=0;file.instructions.push_back(stop);
    stage=std::make_unique<Stage>(manager,resource,text,background_color,3);
    if(!stage->initialize(file,1,SceneCamera{},false))return 0;
    stage->active_camera=&camera;stage->state.draw_flags=flags;stage->state.fade_timer.set(i32(fade),&manager.rate);
    manager.script_rng={12345,0,0};manager.visual_rng={54321,0,0};
    for(auto& v:stage->state.script_animations)if(!v.copy_script(resource,0,3,&manager.rate))return 0;
    return 1;
}
API(stage_tick) u32 stage_tick(){return stage->update();}
API(stage_field) u32 stage_field(u32 i){
    const auto& s=stage->state;const u32 out[]={s.frame_count,u32(s.script_timer.previous),u32(s.script_timer.current),word(s.script_timer.fractional),s.tint,u32(s.frame_effect),word(camera.position.x),word(camera.position.y),word(camera.position.z),word(camera.direction.x),word(camera.direction.y),word(camera.direction.z),word(camera.up.x),word(camera.up.y),word(camera.up.z)};return out[i];
}
API(slot_field) u32 slot_field(u32 slot,u32 i){return fields(stage->state.script_animations[slot])[i];}
