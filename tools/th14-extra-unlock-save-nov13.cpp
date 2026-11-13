// External save precondition for Extra menu tests; never changes a live game.
#include "ScoreFile.hpp"
#include <vector>
using namespace th11;
static std::vector<u8> bytes;
#define API(n) extern "C" __attribute__((export_name(#n)))
API(make_extra_test_save) u32 make_extra_test_save(){
 ScoreFile score;Rng rng;rng.set_seed(12345);score.initialize(rng);
 SpellRecords spells;ClearRecords clears;score.read_records(spells,clears);
 for(u32 selection=0;selection<6;++selection){clears.clears[selection][1]=1;clears.no_continue_clears[selection][1]=1;}
 score.write_records(spells,clears);if(!score.save(bytes))return 0;
 ScoreFile reopened;if(!reopened.open(bytes.data(),u32(bytes.size())))return 0;
 SpellRecords read_spells;ClearRecords read_clears;reopened.read_records(read_spells,read_clears);
 for(u32 selection=0;selection<6;++selection)if(read_clears.no_continue_clears[selection][1]!=1)return 0;
 return u32(bytes.size());
}
API(extra_test_save_data) const u8* extra_test_save_data(){return bytes.data();}
