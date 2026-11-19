// Read-only observations after each actual player callback, grouped by the
// actual replay-manager factory generation. No simulation state is changed.
static std::vector<std::array<u32,17>> campaign_replay_repeat_trace;
static void campaign_replay_player_sample(){
 if(!title_root_globals.root||title_root_state.view().get(0x94)!=1||!(owners->created&4))return;auto m=owners->input.manager.view();if(signed_word(m.get(0x50))<0)return;const auto& p=owners->player;u32 shots=0;for(u32 i=0;i<256;++i)shots+=p.get(0xde18+i*0xa4+0x10)&1;
 campaign_replay_repeat_trace.push_back({campaign_replay_playback_factories,m.get(0x50),title_root_state.view().get(0x14),owners->input.held(),owners->input.fresh(),owners->input.released(),AnmView{owners->input.input.keyboard.data()}.get(0x18c),p.get(0x5e0),p.get(0x5e4),p.get(0x684),p.get(0x680),p.get(0x18464),shots,title_root_game.random.seed,title_root_game.random.calls,title_root_game.game_state[2],title_root_game.game_state[4]});
}
API(campaign_replay_repeat_trace_count)u32 campaign_replay_repeat_trace_count(){return campaign_replay_repeat_trace.size();}
API(campaign_replay_repeat_trace_data)const u32* campaign_replay_repeat_trace_data(u32 i){return i<campaign_replay_repeat_trace.size()?campaign_replay_repeat_trace[i].data():nullptr;}
