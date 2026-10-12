#include "../../cpp/game/ScoreFile.hpp"
#include <cstdlib>
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static ScoreFile::Th14Character character;
static ScoreFile::Th14Settings settings;
static Rng gameplay;
static ScoreFile file;
static std::vector<u8> saved;
static SpellRecords inspection;
static ClearRecords inspected_clears;
API(initialize_character) const u8* initialize_character(){ScoreFile::th14_initialize_character(character);return character.data();}
API(initialize_settings) const u8* initialize_settings(u32 seed,u32 calls){
    gameplay.seed=u16(seed);gameplay.calls=calls;ScoreFile::th14_initialize_settings(settings,gameplay);return settings.data();
}
API(final_seed) u32 final_seed(){return gameplay.seed;}
API(final_calls) u32 final_calls(){return gameplay.calls;}
API(insert) i32 insert(u32 difficulty,u32 score,i32 stage,i32 continues,float ratio){
    ScoreFile::th14_initialize_character(character);for(u32 n=0;n<60;++n)character[0x10+n*28+15]=u8(n+8);
    const float percent=ratio*100.f,slowdown=100.f-percent;
    return ScoreFile::th14_insert_score(character,difficulty,score,stage,continues,0x123456789abcdef0ull,slowdown);
}
API(rows) const u8* rows(){return character.data()+0x10;}
API(allocate) void* allocate(u32 n){return std::malloc(n);}
API(release) void release(void* p){std::free(p);}
API(initialize_file) void initialize_file(u32 seed,u32 calls){gameplay.seed=u16(seed);gameplay.calls=calls;file.initialize(gameplay);}
API(open_file) u32 open_file(const u8* p,u32 n){return file.open(p,n);}
API(save_file) const u8* save_file(){return file.save(saved)?saved.data():nullptr;}
API(saved_size) u32 saved_size(){return u32(saved.size());}
API(file_character) const u8* file_character(u32 index){return index<7?file.characters[index].data():nullptr;}
API(file_settings) const u8* file_settings(){return file.settings.data();}
API(commit_name) u32 commit_name(u32 selection,u32 difficulty,u32 rank,const char* name){
    auto* row=file.characters[selection].data()+0x10+(difficulty*10+rank)*28;
    for(u32 n=0;n<28;++n)row[n]=u8(n);
    std::memcpy(file.settings.data()+12,"0123456789",10);
    return file.score_name(selection,difficulty,rank,name);
}
API(sync_file) void sync_file(){SpellRecords spells;ClearRecords clears;file.read_records(spells,clears);file.write_records(spells,clears);}
API(inspect_file) const char* inspect_file(){file.read_records(inspection,inspected_clears);return inspection.entries[5][119].name.data();}
API(inspect_value) i32 inspect_value(u32 index){
    const auto& r=inspection.entries[5][119];
    const i32 values[]={r.captures,r.practice_captures,r.attempts,r.practice_attempts,inspected_clears.clears[5][1],inspected_clears.stages[5][39][0],inspected_clears.stages[5][39][1]};
    return index<7?values[index]:-1;
}
