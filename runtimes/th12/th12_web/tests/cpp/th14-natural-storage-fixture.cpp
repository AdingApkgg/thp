#include "th14-natural-ending-fixture.cpp"
static std::vector<u8> natural_score_bytes;
API(natural_storage_stat) i32 natural_storage_stat(u32 field){
 const auto* t=session.title.get();
 switch(field){
 case 0:return t?t->substate:-1;
 case 1:return t?t->name_cursor.selected:-1;
 case 2:return t?t->replay_save_requested:0;
 case 3:return session.clear_records.clears[4][0];
 case 4:return session.clear_records.no_continue_clears[4][0];
 case 5:return t?t->result_score:-1;
 case 6:return t?t->cursor.selected:-1;
 default:return -1;
 }
}
API(natural_storage_save) u32 natural_storage_save(){return session.save_scores(natural_score_bytes);}
API(natural_storage_bytes) const u8* natural_storage_bytes(){return natural_score_bytes.data();}
API(natural_storage_size) u32 natural_storage_size(){return natural_score_bytes.size();}
API(natural_storage_character) const u8* natural_storage_character(u32 n){return n<7?session.scores.characters[n].data():nullptr;}
API(natural_storage_settings) const u8* natural_storage_settings(){return session.scores.settings.data();}
API(natural_storage_reload) u32 natural_storage_reload(const u8* p,u32 n){return session.load_scores(p,n);}
API(natural_storage_replay) u32 natural_storage_replay(){return session.title&&session.save_replay(session.title->entered_name.data(),saved_replay,true);}
