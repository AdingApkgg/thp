#include "th14-replay-session-fixture.cpp"
static ReplayRecorder writer;static Replay written;static std::vector<u8> writer_bytes;
API(config_default) const u8* config_default(const u8* controller){static GameConfig cfg;cfg.reset(controller);return cfg.bytes.data();}
API(writer_begin) i32 writer_begin(i32 character,i32 subtype,i32 difficulty,i32 practice,u32 low,u32 high,const u8* cfg){
 if(!writer.begin(character,subtype,difficulty,practice,u64(high)<<32|low))return 0;
 std::memcpy(writer.header.data()+0x18,cfg,0x5c);return 1;
}
API(writer_stage) i32 writer_stage(u32 number,const u8* p,i32 initial){ReplayStageState entry;entry.read(p);return writer.start_stage(number,entry,initial);}
API(writer_tick) i32 writer_tick(u32 held,u32 pressed,u32 released,float fps){return writer.tick(held,pressed,released,fps);}
API(writer_finish) i32 writer_finish(i32 terminal){return writer.finish_stage(terminal);}
API(writer_save) i32 writer_save(const char* name,i32 score,i32 reached,i32 continues,float slowdown){
 return writer.save(name,score,reached,continues,slowdown,writer_bytes)&&written.open(writer_bytes.data(),u32(writer_bytes.size()));
}
API(writer_data) const u8* writer_data(){return writer_bytes.data();}
API(writer_size) u32 writer_size(){return u32(writer_bytes.size());}
API(writer_decoded) const u8* writer_decoded(){return written.decoded().data();}
API(writer_decoded_size) u32 writer_decoded_size(){return u32(written.decoded().size());}
API(session_start_word) u32 session_start_word(u32 n){const u32 v[]={u32(session.economy.point_value),u32(session.battle->player->state.minimum_point_value),u32(session.economy.max_point_value),u32(session.economy.power)};return v[n];}
API(session_save) i32 session_save(){return session.save_replay("SESSION",writer_bytes,true,0)&&written.open(writer_bytes.data(),u32(writer_bytes.size()));}
API(written_play) i32 written_play(){return session.begin_replay(source,writer_bytes.data(),u32(writer_bytes.size()));}
API(session_word) u32 session_word(u32 n){
 const auto& e=session.economy;const auto& p=session.battle->player->motion.state;
 u32 enemies=0;for(auto* node=session.battle->enemies.first;node;node=node->next)++enemies;
 const u32 values[]={u32(session.state.phase),session.state.frame,u32(e.score_units),u32(e.power),u32(e.point_value),u32(e.lives),u32(e.life_fragments),u32(e.th14_bombs),u32(e.th14_bomb_fragments),u32(e.graze),u32(p.x),u32(p.y),u32(p.weapon_mode),u32(p.focused),u32(session.battle->player->state.life_state),session.animations.visual_rng.seed,session.animations.visual_rng.calls,enemies,u32(session.battle->bullets.active_count),u32(e.th14_special_drop_count)};
 return n<sizeof values/sizeof *values?values[n]:0;
}
