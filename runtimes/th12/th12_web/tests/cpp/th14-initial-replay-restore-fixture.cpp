#include "Replay.hpp"
#include "Rng.hpp"
#include "GameEconomy.hpp"
#include <cstring>
using namespace th11;
extern "C" {
__attribute__((export_name("probe_restore"))) const u32* probe_restore(const u8* header,u32 first,u32 old_script,u32 old_game,u32 calls){
 static u32 output[26];ReplayStageState entry;entry.read(header);
 Rng script{u16(old_script),0xa5a5,calls},game{u16(old_game),0x5a5a,calls};GameEconomy economy;
 entry.restore(economy,game,first!=0,&script);
 std::memcpy(output,&script,8);std::memcpy(output+2,&game,8);
 const i32 values[]={economy.score_units,economy.difficulty,economy.rank,economy.graze,economy.th14_point_items,
  economy.point_value,economy.max_point_value,economy.power,economy.max_power,economy.power_step,economy.lives,
  economy.life_fragments,economy.th14_life_awards,economy.th14_bombs,economy.th14_bomb_fragments,economy.th14_combo.total,
  economy.th14_reserved_54,economy.th14_combo.count,economy.th14_combo.timer};
 std::memcpy(output+4,values,sizeof(values));std::memcpy(output+23,&economy.th14_combo.position,12);return output;
}
__attribute__((export_name("probe_header"))) u8* probe_header(){static u8 header[0xdc];return header;}
}
