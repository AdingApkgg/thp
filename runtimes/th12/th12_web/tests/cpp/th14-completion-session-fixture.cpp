#include "th14-session-fixture.cpp"
API(finish_stage) u32 finish_stage(i32 continues){
    if(!session.battle)return 0;
    session.battle->hud.score.continues=continues;
    return session.battle->dialogue_stage_complete();
}
API(ending_value) i32 ending_value(u32 kind){
    if(kind==0)return session.ending?session.ending->index:-1;
    if(kind==1)return session.ending?session.ending->seen:-1;
    if(kind==2)return session.title?i32(session.title->screen):-1;
    if(kind==3)return session.ending?session.ending->active:0;
    if(kind==4)return session.scores.characters[session.state.character*2+session.state.subtype][0x7dc+session.state.difficulty*4];
    if(kind>=5&&kind<=7&&session.battle){
        for(const auto& fade:session.battle->fades.effects)if(fade.type==5)
            return kind==5?i32(fade.priority):kind==6?fade.duration:fade.type;
        return -1;
    }
    return 0;
}
