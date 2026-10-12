#include "th14-replay-session-fixture.cpp"
API(campaign_begin) u32 campaign_begin(u32 selection,u32 difficulty){
    session.interactive=false;long_recording=false;recording_chunks=0;
    g_th14_bullet_unhandled=g_th14_bullet_unsupported_native=0;
    return session.begin(source,difficulty==4?7:1,selection/2,selection%2,difficulty);
}
API(campaign_clock) u32 campaign_clock(double now){return session.sample_spell_clock(now);}
API(campaign_save) u32 campaign_save(){return session.save_replay("CAMPAIGN",saved_replay,true);}
API(campaign_bytes) const u8* campaign_bytes(){return saved_replay.data();}
API(campaign_size) u32 campaign_size(){return saved_replay.size();}
API(campaign_replay) u32 campaign_replay(){return session.begin_replay(source,saved_replay.data(),saved_replay.size());}
API(campaign_record_frames) u32 campaign_record_frames(u32 stage){return session.recording.stages[stage].frames;}
API(campaign_decoded_frames) u32 campaign_decoded_frames(u32 stage){const auto* s=session.playback.stage(stage);return s?s->frames:0;}
API(campaign_state) u32 campaign_state(u32 field){
    if(field==0)return session.state.stage;
    if(field==1)return session.state.frame;
    if(field==2)return session.animations.visual_rng.seed;
    if(field==3)return session.animations.visual_rng.calls;
    if(!session.battle)return 0;const auto& b=*session.battle;
    const u32 values[]={b.frame,b.enemies.count,b.enemies.total_created,b.bullets.active_count,
        u32(b.spells.frame_count),b.spell_flags,u32(b.spell_timing.last_frames),u32(b.spell_timing.encoded),b.spell_timing.index,
        u32(session.economy.point_value),u32(session.economy.rank),u32(session.economy.th14_point_items),
        u32(session.economy.life_fragments),u32(session.economy.th14_bomb_fragments)};
    if(field==18)return b.stage_active;
    if(field==19)return b.completion.state.ending_active;
    return field>=4&&field<18?values[field-4]:0;
}
