// Offscreen observation adapter. Every tick calls the production Application;
// no title, RNG, animation, input or rendering state is replaced by reference data.
#include "Application.cpp"
#include "th14-native-title-live-observer.hpp"

extern "C" {
EMSCRIPTEN_KEEPALIVE int component_initialize() {
    return th11::sdl::app.initialize();
}
EMSCRIPTEN_KEEPALIVE int component_tick(unsigned held, unsigned pause) {
    return th11::sdl::app.tick(held, pause != 0);
}
EMSCRIPTEN_KEEPALIVE const unsigned* component_state() {
    auto& a = th11::sdl::app;
    auto& s = a.session;
    static unsigned data[20];
    data[0] = unsigned(s.state.phase); data[1] = s.state.stage;
    data[2] = s.state.frame;
    data[3] = s.title ? unsigned(s.title->screen) : ~0u;
    data[4] = s.title ? unsigned(s.title->cursor.selected) : ~0u;
    data[5] = s.title ? unsigned(s.title->substate) : ~0u;
    data[6] = s.battle ? s.battle->frame : 0;
    data[7] = unsigned(s.economy.lives); data[8] = unsigned(s.economy.power);
    data[9] = unsigned(s.economy.score_units);
    data[10] = s.battle ? unsigned(s.battle->hud.score.continues) : 0;
    data[11] = s.pause_menu ? unsigned(s.pause_menu->state) : ~0u;
    data[12] = s.pause_menu ? unsigned(s.pause_menu->cursor.selected) : ~0u;
    data[13] = unsigned(s.state.character); data[14] = unsigned(s.state.subtype);
    data[15] = unsigned(s.state.difficulty); data[16] = s.stage_load_host_flags;
    data[17] = s.title_idle; data[18] = unsigned(a.audio.current_music());
    data[19] = a.initialized;
    return data;
}
EMSCRIPTEN_KEEPALIVE const unsigned* component_reference_state() {
    auto& a = th11::sdl::app;
    auto& s = a.session;
    static unsigned words[12];
    words[0] = a.initial_ticks; words[1] = a.process_cookie;
    words[2] = s.title_idle;
    words[3] = s.animations.script_rng.seed;
    words[4] = s.animations.script_rng.calls;
    words[5] = s.animations.visual_rng.seed;
    words[6] = s.animations.visual_rng.calls;
    words[7] = unsigned(s.state.phase); words[8] = s.state.stage;
    words[9] = s.title ? unsigned(s.title->screen) : ~0u;
    words[10] = s.title ? unsigned(s.title->substate) : ~0u;
    words[11] = s.animations.active_count();
    return words;
}
EMSCRIPTEN_KEEPALIVE const unsigned char* component_pixels() {
    auto& g = th11::sdl::app.graphics;
    g.backend.read(g.screen);
    auto* pixels = g.pixels(g.screen);
    return pixels ? pixels->pixels.data() : nullptr;
}
EMSCRIPTEN_KEEPALIVE const unsigned* component_live_state() {
    std::vector<std::vector<th11::u32>> rows;
    th11::u32 expected = 0; bool complete = false;
    th14_title_observer::capture_live_rows(th11::sdl::app.session, rows, expected, complete);
    static std::vector<unsigned> words;
    words = {unsigned(complete), unsigned(rows.size()), expected, 303};
    for (const auto& row : rows) {
        if (row.size() != 303) { words[0] = 0; return words.data(); }
        words.insert(words.end(), row.begin(), row.end());
    }
    return words.data();
}
EMSCRIPTEN_KEEPALIVE void component_audio_close() {
    th11::sdl::app.audio.close();
}
}
