// The comparison helpers cover actual parsed STD/ANM/ECL fields and bytes.
#define main legacy_fixture_main
#include "th14-initial-stage-decode-fixture.cpp"
#undef main
#include "../../cpp/game/StageFiles.hpp"
#include <emscripten.h>

namespace {
GameResources resources;
StageResources baseline,deferred;
u32 stage_number=0,selection_index=0;
std::string names;
}
extern "C" {
EMSCRIPTEN_KEEPALIVE int fixture_open(const u8* data,u32 size){return resources.open_archive(data,size);}
EMSCRIPTEN_KEEPALIVE int fixture_prepare(u32 stage,u32 selection){
    stage_number=stage;selection_index=selection;baseline={};deferred={};
    return resources.load_stage(stage,baseline);
}
EMSCRIPTEN_KEEPALIVE const char* fixture_names(u32 step){
    names.clear();char name[64];
    auto add=[&](const char* format){std::snprintf(name,sizeof name,format,stage_number);if(!names.empty())names+='\n';names+=name;};
    if(step==0){add(stage_files.scene);add(stage_files.background);}
    else if(step==1){
        add(stage_files.logo);stage_dialogue_name(name,sizeof name,stage_number,selection_index);names+='\n';names+=name;
    }else if(step==2){
        add(stage_files.timeline);
        for(const char* format:{stage_files.boss,stage_files.midboss}){
            std::snprintf(name,sizeof name,format,stage_number);
            if(resources.has(name)){names+='\n';names+=name;}
        }
        if(resources.has("default.ecl"))names+="\ndefault.ecl";
    }else if(step<7){names=deferred.ecl_animation_names[step-3];}
    else if(step==7){add(stage_files.enemies);}
    return names.c_str();
}
EMSCRIPTEN_KEEPALIVE int fixture_step(u32 step){
    if(step==0)return resources.load_stage_scene(stage_number,deferred);
    if(step==1)return resources.load_stage_hud(stage_number,deferred,selection_index);
    if(step==2)return resources.load_stage_timeline_plan(stage_number,deferred);
    if(step<7)return resources.load_stage_animation(deferred,step-3);
    if(step==7)return resources.complete_stage_timeline(stage_number,deferred);
    return 0;
}
EMSCRIPTEN_KEEPALIVE int fixture_compare(){
    bool same=scene(baseline.scene,deferred.scene)&&anm(baseline.background,deferred.background)&&
        anm(baseline.logo,deferred.logo)&&anm(baseline.enemies,deferred.enemies)&&
        ecl(baseline.timeline,deferred.timeline)&&baseline.messages[selection_index]==deferred.messages[selection_index]&&
        baseline.ecl_animation_names==deferred.ecl_animation_names&&baseline.boss_programs.size()==deferred.boss_programs.size();
    for(u32 slot=0;same&&slot<deferred.ecl_animations.size();++slot)same=anm(baseline.ecl_animations[slot],deferred.ecl_animations[slot]);
    for(u32 boss=0;same&&boss<deferred.boss_programs.size();++boss)same=ecl(baseline.boss_programs[boss],deferred.boss_programs[boss]);
    return same;
}
EMSCRIPTEN_KEEPALIVE int fixture_read(const char* name){std::vector<u8> output;return resources.read(name,output);}
EMSCRIPTEN_KEEPALIVE int fixture_anm(const char* name){AnmResource output;return resources.open_anm(name,output);}
EMSCRIPTEN_KEEPALIVE int fixture_std(const char* name){StageResource output;return resources.open_std(name,output);}
EMSCRIPTEN_KEEPALIVE int fixture_ecl(const char* name){EclProgram output;return resources.load_ecl(name,output);}
EMSCRIPTEN_KEEPALIVE const char* fixture_error(){return resources.error().c_str();}
}
