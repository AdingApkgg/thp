#include "../../cpp/game/GameSession.hpp"
#include "../../cpp/game/GameBattle.hpp"
#include "../../cpp/game/AnmOpcodes.hpp"
#include <cstring>
using namespace th11;
#define API(n) extern "C" __attribute__((export_name(#n)))
static std::unique_ptr<GameSession> session;
API(run) u32 run(i32 continues,u32 replay){
    session=std::make_unique<GameSession>(0);
    auto& text=session->resources.core.text;auto& front=session->resources.core.front;
    text.scripts.resize(53);front.scripts.resize(153);
    auto stop=[](AnmResource& f,u32 i){AnmInstruction h{i16(anm_canonical_opcode(2)),8,0,0};f.scripts[i].bytes.resize(8);std::memcpy(f.scripts[i].bytes.data(),&h,8);};
    stop(text,52);for(u32 i=0;i<153;++i)stop(front,i);
    session->resources.stage=std::make_unique<StageResources>();
    session->state.phase=GameSessionPhase::stage;session->state.stage=1;session->state.frame=100;session->state.replay=replay!=0;
    session->battle=std::make_unique<GameBattle>(session->resources,session->animations,session->economy,session->spell_records,session->compositor,session->clear_records);
    session->battle->hud.score.continues=continues;
    if(!session->pause())return 0;
    session->pause_menu->timer.set(10,&session->animations.rate);
    return session->pause_menu->update(0,0);
}
API(value) i32 value(u32 field){
    const auto& menu=*session->pause_menu;
    switch(field){case 0:return menu.continues;case 1:return menu.state;case 2:return menu.cursor.selected;case 3:return menu.cursor.count;case 4:return menu.cursor.wrap;case 5:return menu.cursor.disabled_count;default:return -1;}
}
API(disabled) i32 disabled(u32 index){return session->pause_menu->cursor.disabled[index];}
