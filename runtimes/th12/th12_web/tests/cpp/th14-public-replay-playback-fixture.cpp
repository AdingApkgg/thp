#include "th14-custom-replay-reference-fixture.cpp"
API(public_replay_begin) u32 public_replay_begin(const u8* data,u32 size){
    session.interactive=false;
    if(!session.begin_replay(source,data,size,0,false))return 0;
    session.battle->before_player_update=observe_reference;
    return 1;
}
API(public_replay_clock) u32 public_replay_clock(double now){return session.sample_spell_clock(now);}
API(public_replay_status) u32 public_replay_status(u32 field){
    const u32 values[]={session.state.stage,session.state.frame,session.battle?session.battle->frame:0,
        session.battle?u32(session.battle->game_over_requested):0,session.battle?u32(session.battle->stage_active):0,
        g_th14_bullet_unhandled,g_th14_bullet_unsupported_native};
    return field<7?values[field]:0;
}
