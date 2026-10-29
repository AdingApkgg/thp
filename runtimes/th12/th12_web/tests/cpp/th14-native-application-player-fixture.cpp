// Read-only Player-boundary diagnostics around the real Application tick.
// This file is never part of the browser release.
#define component_tick component_tick_without_player_observer
#include "th14-native-initial-loading-fixture.cpp"
#undef component_tick

namespace th14_application_player_observer {
using namespace th11;
struct Records {
    u32 count=0,width=34,overflow=0,unexpected_existing_hook=0;
    u32 rows[32768][34]{};
};
static Records records;
static GameBattle* attached=nullptr;
static u32 app_tick=0;
static void capture(const GameBattle& b) {
    if(records.count>=32768){records.overflow=1;return;}
    const auto& p=*b.player;const auto& e=b.economy;
    const auto& s=th11::sdl::app.session;
    u32 live=0;for(u32 n=0;n<256;++n)if(p.shots.at(n).state)++live;
    const i32 words[]={b.control_frame(),i32(p.input.movement.held),i32(p.input.movement.pressed),
        p.motion.state.x,p.motion.state.y,p.state.life_state,p.state.state_timer.current,
        p.state.transition_timer.current,p.state.th14_shooting_age.current,p.state.invincibility.current,
        p.shots.schedule.timer.current,p.motion.state.weapon_mode,
        e.score_units,e.graze,e.point_value,e.power,e.lives,e.life_fragments,e.th14_bombs,e.th14_bomb_fragments,e.rank,
        i32(b.animations.script_rng.seed),i32(b.animations.script_rng.calls),
        i32(b.animations.visual_rng.seed),i32(b.animations.visual_rng.calls),i32(b.enemies.count),i32(live),
        s.state.character,s.state.subtype,s.state.difficulty,i32(s.state.stage),i32(p.th14_scale.flags)};
    auto* row=records.rows[records.count++];for(u32 n=0;n<32;++n)row[n]=u32(words[n]);
    row[32]=app_tick;row[33]=b.animations.th14_native_stack.scratch;
}
}
extern "C" {
EMSCRIPTEN_KEEPALIVE int component_tick(unsigned held,unsigned pause) {
    using namespace th14_application_player_observer;
    auto* b=th11::sdl::app.session.battle.get();
    if(b&&b!=attached){
        if(b->before_player_update){records.unexpected_existing_hook=1;return 0;}
        b->before_player_update=capture;attached=b;
    }
    ++app_tick;
    return component_tick_without_player_observer(held,pause);
}
EMSCRIPTEN_KEEPALIVE const unsigned* component_player_observations() {
    return &th14_application_player_observer::records.count;
}
}
