#include "../../cpp/game/ScoreFile.hpp"
#include <cstdlib>
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static ScoreFile file;
static Rng rng;
static std::vector<u8> saved;
API(initialize) void initialize(u32 seed,u32 calls){rng.seed=u16(seed);rng.calls=calls;file.initialize(rng);}
API(seed) u32 seed(){return rng.seed;}
API(calls) u32 calls(){return rng.calls;}
API(data) u8* data(u32 n){return n<7?file.characters[n].data():file.settings.data();}
API(insert) i32 insert(u32 selection,u32 difficulty,i32 score,i32 stage,i32 continues){return file.insert_score(selection,difficulty,score,stage,continues,0x123456789abcdef0ull,33.125f);}
API(name) u32 name(u32 selection,u32 difficulty,u32 rank,const char* text){return file.score_name(selection,difficulty,rank,text);}
API(sync) void sync(){SpellRecords spells;ClearRecords clears;file.read_records(spells,clears);file.write_records(spells,clears);}
API(save) const u8* save(){return file.save(saved)?saved.data():nullptr;}
API(size) u32 size(){return u32(saved.size());}
API(open) u32 open(const u8* data,u32 size){return file.open(data,size);}
API(allocate) void* allocate(u32 size){return std::malloc(size);}
API(release) void release(void* p){std::free(p);}
