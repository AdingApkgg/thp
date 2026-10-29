// Read-only boundaries around the real Application's first replay activation.
// No gameplay, RNG, loader or callback method is replaced by this adapter.
#include "th14-native-initial-loading-fixture.cpp"
extern "C" {
EMSCRIPTEN_KEEPALIVE const unsigned* component_replay_construction_state(){
    auto& s=th11::sdl::app.session;static unsigned words[10];
    words[0]=unsigned(s.state.phase);words[1]=s.state.stage;
    words[2]=s.battle!=nullptr;
    words[3]=s.battle?s.battle->enemy_commands.th14_run_flags:0;
    words[4]=s.animations.script_rng.seed;words[5]=s.animations.script_rng.calls;
    words[6]=s.animations.visual_rng.seed;words[7]=s.animations.visual_rng.calls;
    words[8]=s.state.replay;words[9]=s.state.demo;
    return words;
}
}
