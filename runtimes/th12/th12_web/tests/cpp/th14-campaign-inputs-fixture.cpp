#include "th14-campaign-pools-fixture.cpp"
// Ordinary recorded keys exercise focused/unfocused fire, horizontal/vertical
// movement, collection-line crossings and bombs from the actual stock. Only
// combat_tick's existing diagnostic invulnerability is applied to game state.
static u32 pattern_keys=0,pattern_bombs=0,pattern_focus_frames=0,pattern_move_frames=0;
static u32 pattern_collection_frames=0;
API(campaign_pattern_tick) u32 campaign_pattern_tick(u32 frame){
    const u32 phase=frame%1440;
    u32 held=513;
    if(phase>=720){held|=8;++pattern_focus_frames;}
    const u32 local=phase%720;
    if(local<20||local>=60&&local<80)held|=64;
    else if(local<60)held|=128;
    if(local>=120&&local<210)held|=16;
    else if(local>=210&&local<300)held|=32;
    if(held&240)++pattern_move_frames;
    if(frame%1800==97)held|=2;
    pattern_keys|=held;
    const bool was_bomb=session.battle&&session.battle->bomb&&session.battle->bomb->state.active;
    const u32 ok=combat_tick(held);
    if(session.battle){
        if(session.battle->bomb&&session.battle->bomb->state.active&&!was_bomb)++pattern_bombs;
        if(session.battle->player&&session.battle->player->motion.state.position.y<=
            (session.state.character==1?148.f:128.f))++pattern_collection_frames;
    }
    return ok;
}
API(campaign_pattern_stat) u32 campaign_pattern_stat(u32 field){
    const u32 values[]={pattern_keys,pattern_bombs,pattern_focus_frames,pattern_move_frames,pattern_collection_frames};return values[field];
}
API(campaign_pattern_state) u32 campaign_pattern_state(u32 field){
    if(!session.battle||!session.battle->bomb)return 0;const auto& s=session.battle->bomb->state;
    const u32 values[]={u32(s.active),u32(s.elapsed.previous),u32(s.elapsed.current),float_bits(s.elapsed.fractional),
        u32(s.secondary.previous),u32(s.secondary.current),float_bits(s.secondary.fractional),u32(s.th14_mode),
        float_bits(s.position.x),float_bits(s.position.y),float_bits(s.position.z),float_bits(s.radius),float_bits(s.growth),u32(s.started_during_spell)};
    return values[field];
}
