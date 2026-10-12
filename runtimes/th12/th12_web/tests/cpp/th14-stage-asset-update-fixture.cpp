#include "th14-stage-asset-anm-fixture.cpp"
#include "../../cpp/game/Stage.hpp"
#include <memory>
static AnmResource text;
static SceneCamera camera;
static u32 background_color;
static std::unique_ptr<Stage> stage;
static std::vector<u32> observed;
static void append_vm(const AnmVm& v){
    auto out=fields(v);
    if(v.geometry){
        if(v.th13_effect==8){
            const auto& r=*static_cast<const AnmTh14Ribbon*>(v.geometry);
            for(u32 i=0;i<602;++i){u32 value;std::memcpy(&value,static_cast<const u8*>(v.geometry)+i*4,4);out.push_back(value);}
            for(u32 value:{word(r.phase),u32(r.timer.previous),u32(r.timer.current),word(r.timer.fractional)})out.push_back(value);
        }else for(u32 i=0;i<u32(v.integers[0])*12u;++i){u32 value;std::memcpy(&value,static_cast<const u8*>(v.geometry)+i*4,4);out.push_back(value);}
    }
    observed.push_back(u32(out.size()));observed.insert(observed.end(),out.begin(),out.end());
}
static void capture(){
    const auto& s=stage->state;
    observed={s.frame_count,u32(s.script_timer.previous),u32(s.script_timer.current),word(s.script_timer.fractional),s.tint,u32(s.frame_effect),word(camera.position.x),word(camera.position.y),word(camera.position.z),word(camera.direction.x),word(camera.direction.y),word(camera.direction.z),word(camera.up.x),word(camera.up.y),word(camera.up.z)};
    for(i32 layer:s.script_animation_layers)observed.push_back(u32(layer));
    for(const auto& object:stage->resource.objects)observed.push_back(object.flags);
    for(const auto& v:stage->object_animations)append_vm(v);
    for(const auto& v:s.script_animations)append_vm(v);
    for(u32 i=0;i<4;++i)observed.push_back(rng(i));
}
API(stage_begin) u32 stage_begin(const u8* data,u32 size,u32 number){
    stage.reset();camera={};camera.up={};StageResource file;if(!file.open(data,size))return 0;
    manager.script_rng={12345,0,0};manager.visual_rng={54321,0,0};
    stage=std::make_unique<Stage>(manager,resource,text,background_color,u16((number&1)+3));
    if(!stage->initialize(file,i32(number),SceneCamera{},true))return 0;
    stage->active_camera=&camera;capture();return 1;
}
API(stage_tick) u32 stage_tick(){if(!stage->update())return 0;capture();return 1;}
API(words) u32 words(){return u32(observed.size());}
API(data) const u32* data(){return observed.data();}
API(last_error) const char* last_error(){return stage?stage->error.c_str():"no Stage";}
