#pragma once
#include "ShotFiles.hpp"
#include "GameResources.hpp"
#include <memory>

namespace th11 {
#if PORT_TITLE == 14
class AnmManager;
struct DialogueEffects;
#endif

struct CoreResources {
    AnmResource ascii;
    AnmResource bullet;
    AnmResource enemy;
#if PORT_TITLE == 14 || PORT_TITLE == 16
    AnmResource effect;
#endif
    AnmResource front;
    AnmResource text;
    AnmResource title;
    AnmResource title_variant;
    // The counts are the shot table's (ShotFiles.hpp): three players with two loadouts on
    // TH12, four with one on TH13, and the ANM files follow the players.
    AnmResource players[player_file_count];
    ShtResource shots[shot_file_count];
#if PORT_TITLE == 16
    AnmResource season_players[5];
    ShtResource season_shots[5];
#endif
    EclProgram defaults;
};

// Resource ownership for the live session. It intentionally contains
// no frame state, input or rendering callbacks, so failed loading cannot leave
// a half-created gameplay world behind.
struct StageResourceEffects {
    virtual ~StageResourceEffects()=default;
    virtual bool prepare(StageResources&){return true;}
#if PORT_TITLE == 14
    virtual bool core_ready()const{return true;}
    virtual bool stage_ready()const{return true;}
    virtual bool defer_ending_loading()const{return false;}
    virtual bool begin_ending_loading(){return true;}
    virtual void finish_ending_loading(){}
    // Retail writes text inside priority27 dialogue processing, before normal
    // ANM at29 can hide it. Headless consumers may retain queued requests.
    virtual DialogueEffects* dialogue_text_device(){return nullptr;}
#endif
    virtual void release(StageResources&){}
    virtual bool prepare_animation(AnmResource&){return true;}
    virtual bool prepare_manual_image(AnmResource&,u32,const u8*,u32){return true;}
    virtual void release_animation(AnmResource&){}
    virtual bool read_replay(const std::string&,std::vector<u8>&){return false;}
    // Why the last prepare/prepare_animation failed. The caller reports this in
    // its own error text so a graphics failure is not flattened into a generic
    // "stage graphics preparation".
    virtual const std::string& last_error() const {static const std::string none;return none;}
#if PORT_TITLE == 14
    enum class Phase:u32 {Hud,Scene,Timeline};
    virtual bool prepare_stage_phase(StageResources& stage,Phase phase){
        if(phase==Phase::Hud)return prepare_animation(stage.logo);
        if(phase==Phase::Scene)return prepare_animation(stage.background);
        if(!prepare_animation(stage.enemies))return false;
        for(u32 i=0;i<stage.ecl_animations.size();++i)
            if(!stage.ecl_animation_names[i].empty()&&!prepare_animation(stage.ecl_animations[i]))return false;
        return true;
    }
    virtual bool stage_phase_ready(Phase)const{return true;}
    virtual void cancel_stage_phases(StageResources& stage,u32){release(stage);}
    virtual void finish_stage_phases(StageResources&,u32){}
#endif
};
class GameSessionResources {
public:
    CoreResources core;
    // Stable addresses are required by live ANM VMs during the native
    // overlap between outgoing and incoming stage backgrounds.
    std::unique_ptr<StageResources> stage=std::make_unique<StageResources>();
    std::unique_ptr<StageResources> previous_stage;
    StageResourceEffects* effects=nullptr;
#if PORT_TITLE == 14
    AnmManager* animation_manager=nullptr;
#endif
    u32 stage_number=0;
    std::string error;

    bool load_core(GameResources& source);
#if PORT_TITLE == 14
    bool prepare_core();
    bool load_core_job(u32 index);
    bool prepare_stage();
    enum class PhaseResult:u32 {Waiting,Ready,Failed};
    bool begin_stage_loading(u32 number);
    PhaseResult advance_stage_phase(GameResources&,StageResourceEffects::Phase,u32 dialogue_selection);
    bool publish_stage_scene();
    void finish_stage_parts();
    // Call after Battle/ANM retirement, before replacing resource ownership.
    void cancel_stage_loading();
    StageResources* loading_bundle()const noexcept{return incoming_stage;}
#endif
    bool load_stage(GameResources& source,u32 number);
    void retire_previous();
private:
    GameResources* core_source=nullptr;
#if PORT_TITLE == 14
    bool core_deferred=false;
    u16 core_loaded_jobs=0;
    std::unique_ptr<StageResources> pending_stage;
    StageResources* incoming_stage=nullptr;
    u32 pending_number=0,decoded_phases=0,requested_phases=0,ready_phases=0;
#endif
};

}
