#pragma once

#include "GameSessionResources.hpp"
#include "AnmManager.hpp"
#include "AnmRenderer.hpp"
#include "GameEconomy.hpp"
#include "GameBattle.hpp"
#include "SceneCompositor.hpp"
#include "ReplayRecorder.hpp"
#include "GameInput.hpp"
#include "ScoreFile.hpp"
#include "GameConfig.hpp"
#include "TitleMenu.hpp"
#include "PauseMenu.hpp"
#include "Ending.hpp"
#include "FontBitmapTh14.hpp"
#include <string>
#include <memory>

namespace th11 {

// High-level lifetime and frame boundary shared by the native and WebAssembly
// front ends.  Managers that implement bullets, enemies and players are
// attached at the battle boundary; this class owns the deterministic timing
// and resource transition so both front ends observe the same order.
enum class GameSessionPhase : u8 { title, stage, paused, game_over, finished, ending
#if PORT_TITLE == 14
    ,loading
#endif
};

struct GameSessionInput {
    u32 held=0;
    u32 pressed=0;
    u32 released=0;
    bool pause=false;
    bool confirm=false;
    bool cancel=false;
    float recording_fps=60;
#if PORT_TITLE == 14
    u32 dialogue_skip_frames=0,dialogue_fire_frames=0;
#endif
};

struct GameSessionState {
    GameSessionPhase phase=GameSessionPhase::title;
    u32 frame=0;
    u32 stage=0;
    i32 character=0;
    i32 subtype=0;
    i32 difficulty=1;
    bool focus=false;
    bool replay=false;
    bool demo=false;
    bool practice=false;
#if PORT_TITLE == 14
    i32 spell_practice_id=-1;
#endif
};

class GameSession final {
public:
#if PORT_TITLE == 14
    explicit GameSession(u32 initial_ticks=0);
#else
    GameSession();
#endif
    GameSessionResources resources;
    AnmManager animations;
#if PORT_TITLE==14
    FontBitmapTh14 font_bitmap;
#endif
    SceneCompositor compositor{animations};
    GameEconomy economy;
    SpellRecords spell_records;
    ClearRecords clear_records;
    ScoreFile scores;
    GameConfig config;
    Replay playback;
    ReplayRecorder recording;
    GameInput game_input;
    u64 recording_timestamp=0;
    std::unique_ptr<GameBattle> battle;
    std::unique_ptr<TitleMenu> title;
    std::unique_ptr<PauseMenu> pause_menu;
#if PORT_TITLE == 14
    // Only the existing help controller is used; no pause/game-over entry.
    std::unique_ptr<PauseMenu> title_manual;
#endif
    std::unique_ptr<Ending> ending;
    std::unique_ptr<AsciiText> title_ascii;
    ScreenFades title_fades;
    TitleSelection menu_selection;
    bool interactive=false;
    GameSessionState state;
    std::string error;

    bool begin(GameResources& source, u32 stage=1, i32 character=0,
               i32 subtype=0, i32 difficulty=1, bool demo=false, bool replay=false,bool practice=false);
    bool open_title(GameResources&,bool first=false,TitleScreen screen=TitleScreen::Main);
    bool begin_replay(GameResources&,const u8*,u32,u32 stage=0,bool demo=false);
    bool save_replay(const char* name,std::vector<u8>& output,bool terminal=true,float slowdown=0);
    bool load_scores(const u8*,u32);
    bool save_scores(std::vector<u8>&);
    const GameConfig& persistent_config()const noexcept{
#if PORT_TITLE == 14
        if(replay_user_config)return *replay_user_config;
#endif
        return config;
    }
    bool update(const GameSessionInput& input);
#if PORT_TITLE == 14
    // Retail Supervisor samples41c800 after rendering while SpellManager lives.
    bool sample_spell_clock(double now);
#endif
    bool pause();
    bool resume();
    bool return_to_title();
    bool start_stage(GameResources& source, u32 stage);
#if PORT_TITLE == 14
    bool finish_loading();
#endif
    bool draw(AnmRenderer& renderer,AsciiText* overlay=nullptr);
    bool ready() const noexcept { return error.empty() && state.stage!=0
#if PORT_TITLE == 14
        &&state.phase!=GameSessionPhase::loading
#endif
        ; }
    bool battle_callbacks_attached() const noexcept { return battle_attached; }
    const char* phase_name() const noexcept;
private:
    bool battle_attached=false;
#if PORT_TITLE == 14
    bool demo_title_pending=false;
    bool pending_core_title=false,pending_core_first=false;
    TitleScreen pending_core_screen=TitleScreen::Main;
    bool activate_title(GameResources&,bool,TitleScreen);
    bool activate_stage();
    std::unique_ptr<GameConfig> replay_user_config;
#endif
    u32 last_held=0;
    bool last_pause=false;
    bool recording_active=false;
    u32 recording_seed=0;
    bool record_stage_entry(bool initial);
    bool open_result(bool completed);
    bool restart_run(bool continuation);
#if PORT_TITLE == 14
    bool continue_run_th14();
#endif
    bool open_ending();
    bool open_results();
    bool completed_run=false;
    i32 completed_score=0,completed_continues=0;
    u32 initial_stage=1;
    i32 next_continues=0;
    float paused_rate=1;
    GameInput menu_input;
    u32 title_idle=0,demo_index=0;
    i32 last_replay_file=0;
    GameResources* source=nullptr;
    bool fail(const char* message) { error=message?message:"session error"; return false; }
    void reset_state() noexcept;
};

}
