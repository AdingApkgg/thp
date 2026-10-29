#define main legacy_fixture_main
#include "th14-initial-stage-decode-fixture.cpp"
#undef main
#include "../../cpp/game/GameSessionResources.hpp"
#include "../../cpp/sdl/StageDecodeTh14.hpp"
#include <emscripten.h>

namespace {
GameResources source;
GameSessionResources session;
StageResources baseline,other;
th11::sdl::StageDecodeTh14 decoder;
std::vector<th11::sdl::StageDecodeTh14::Token> tokens;
u32 selection_index=0,gpu_requests=0,cpu_cancels=0,gpu_cancels=0;
bool asynchronous=true,gpu_ready=true;
std::string names;
struct Effects final:StageResourceEffects {
    DecodeResult decode_stage_phase(GameResources& resources,StageResources& stage,Phase phase,u32 selection)override{
        return asynchronous?decoder.begin(resources,stage,phase,selection):StageResourceEffects::decode_stage_phase(resources,stage,phase,selection);
    }
    bool prepare_stage_phase(StageResources&,Phase)override{++gpu_requests;return true;}
    bool stage_phase_ready(Phase)const override{return gpu_ready;}
    void cancel_stage_decode(StageResources& stage)override{++cpu_cancels;decoder.cancel(stage);}
    void cancel_stage_phases(StageResources&,u32)override{++gpu_cancels;}
    void finish_stage_phases(StageResources& stage,u32)override{decoder.finish(stage);}
    const std::string& last_error()const override{return decoder.error();}
} effects;
}
extern "C" {
EMSCRIPTEN_KEEPALIVE int fixture_open(const u8* data,u32 size){session.effects=&effects;return source.open_archive(data,size);}
EMSCRIPTEN_KEEPALIVE int fixture_prepare(u32 stage,u32 selection,u32 sync){
    session.cancel_stage_loading();session.stage=std::make_unique<StageResources>();session.previous_stage.reset();
    baseline={};selection_index=selection;asynchronous=!sync;gpu_ready=true;gpu_requests=cpu_cancels=gpu_cancels=0;
    return source.load_stage(stage,baseline)&&session.begin_stage_loading(stage);
}
EMSCRIPTEN_KEEPALIVE int fixture_advance(u32 phase){
    return int(session.advance_stage_phase(source,StageResourceEffects::Phase(phase),phase==0?selection_index:0));
}
EMSCRIPTEN_KEEPALIVE const char* fixture_names(){
    names.clear();for(const auto& name:decoder.names()){if(!names.empty())names+='\n';names+=name;}return names.c_str();
}
EMSCRIPTEN_KEEPALIVE int fixture_dispatch(){
    if(!decoder.dispatchable())return -1;tokens.push_back(decoder.dispatch());return int(tokens.size()-1);
}
EMSCRIPTEN_KEEPALIVE int fixture_deliver(u32 id,u32 status){return id<tokens.size()&&decoder.complete(tokens[id],status!=0);}
EMSCRIPTEN_KEEPALIVE int fixture_publish(){return session.publish_stage_scene();}
EMSCRIPTEN_KEEPALIVE void fixture_finish(){session.finish_stage_parts();}
EMSCRIPTEN_KEEPALIVE void fixture_cancel(){session.cancel_stage_loading();}
EMSCRIPTEN_KEEPALIVE void fixture_suspend(){decoder.suspend();}
EMSCRIPTEN_KEEPALIVE void fixture_resume(){decoder.resume();}
EMSCRIPTEN_KEEPALIVE void fixture_gpu(u32 ready){gpu_ready=ready!=0;}
EMSCRIPTEN_KEEPALIVE u32 fixture_counts(u32 index){return index==0?gpu_requests:index==1?cpu_cancels:gpu_cancels;}
EMSCRIPTEN_KEEPALIVE int fixture_wrong_owner(){return int(decoder.begin(source,other,StageResourceEffects::Phase::Hud,0));}
EMSCRIPTEN_KEEPALIVE int fixture_compare(){
    const auto* incoming=session.loading_bundle();const auto& deferred=incoming?*incoming:*session.stage;
    bool same=scene(baseline.scene,deferred.scene)&&anm(baseline.background,deferred.background)&&
        anm(baseline.logo,deferred.logo)&&anm(baseline.enemies,deferred.enemies)&&
        ecl(baseline.timeline,deferred.timeline)&&baseline.messages[selection_index]==deferred.messages[selection_index]&&
        baseline.ecl_animation_names==deferred.ecl_animation_names&&baseline.boss_programs.size()==deferred.boss_programs.size();
    for(u32 slot=0;same&&slot<deferred.ecl_animations.size();++slot)same=anm(baseline.ecl_animations[slot],deferred.ecl_animations[slot]);
    for(u32 boss=0;same&&boss<deferred.boss_programs.size();++boss)same=ecl(baseline.boss_programs[boss],deferred.boss_programs[boss]);return same;
}
EMSCRIPTEN_KEEPALIVE const char* fixture_error(){return session.error.empty()?decoder.error().c_str():session.error.c_str();}
}
