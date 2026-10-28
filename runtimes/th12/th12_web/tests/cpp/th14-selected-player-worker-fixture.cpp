// The production owner API and parsed resources, with no game-state writes.
#define main legacy_fixture_main
#include "th14-initial-stage-decode-fixture.cpp"
#undef main
#include "../../cpp/game/GameSessionResources.hpp"
#include <emscripten.h>
namespace {
struct Effects:StageResourceEffects {
    bool deferred=true;
    bool core_ready()const override{return false;}
    bool defer_initial_stage_decode()const override{return deferred;}
} effects;
GameResources source;
GameSessionResources session;
AnmResource expected;
u32 selected=0;
}
extern "C" {
EMSCRIPTEN_KEEPALIVE int fixture_open(const u8* bytes,u32 size){
    session.effects=&effects;return source.open_archive(bytes,size)&&session.load_core(source);
}
EMSCRIPTEN_KEEPALIVE const char* fixture_name(u32 selection){return selection<6?player_file_name(selection/2,selection%2):"";}
EMSCRIPTEN_KEEPALIVE int fixture_select(u32 selection){
    if(selection>=6)return 0;selected=selection;effects.deferred=true;
    return source.open_anm(player_file_name(selection/2,selection%2),expected)&&session.select_player(selection/2,selection%2);
}
EMSCRIPTEN_KEEPALIVE int fixture_load(u32 selection){return session.load_selected_player(selection/2,selection%2);}
EMSCRIPTEN_KEEPALIVE void fixture_cancel(){session.cancel_selected_player();}
EMSCRIPTEN_KEEPALIVE int fixture_empty(){const auto& file=session.core.players[selected/2];return file.textures.empty()&&file.sprites.empty()&&file.scripts.empty()&&!file.templates;}
EMSCRIPTEN_KEEPALIVE int fixture_compare(){return anm(expected,session.core.players[selected/2]);}
EMSCRIPTEN_KEEPALIVE int fixture_sync(u32 selection){
    if(selection>=6)return 0;effects.deferred=false;
    return source.open_anm(player_file_name(selection/2,selection%2),expected)&&session.select_player(selection/2,selection%2)&&anm(expected,session.core.players[selection/2]);
}
EMSCRIPTEN_KEEPALIVE const char* fixture_error(){return session.error.c_str();}
}
