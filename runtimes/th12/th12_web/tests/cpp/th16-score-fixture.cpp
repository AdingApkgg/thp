#include "../../cpp/game/ScoreFile.hpp"
#include <cstring>
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static ScoreFile scores;
API(initialize_character) const u8* initialize_character(){ScoreFile::th16_initialize_character(scores.th16_characters[0]);return scores.th16_characters[0].data();}
API(insert) i32 insert(u32 difficulty,u32 score,i32 stage,i32 continues,float ratio,u32 season){
 auto& bank=scores.th16_characters[0];ScoreFile::th16_initialize_character(bank);for(u32 n=0;n<60;++n)bank[0x10+n*32+15]=u8(n+8);
 const float percent=ratio*100.f;const float slowdown=100.f-percent;
 return scores.th16_insert_score(0,difficulty,score,stage,continues,0x123456789abcdef0ull,slowdown,season);
}
API(rows) const u8* rows(){return scores.th16_characters[0].data()+0x10;}
