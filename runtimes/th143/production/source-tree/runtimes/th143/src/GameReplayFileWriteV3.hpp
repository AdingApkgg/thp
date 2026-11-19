#pragma once
#include "GameReplayFileWrite.hpp"
namespace th143 {
// Full454c00 domain extended to the native naming menu's12-byte names.
bool write_game_replay_file_v3(GameManagerState&,u32 self,th11::Lzss&,const u8* filename,u32 filename_bytes,const u8* name,u32 name_bytes,GameReplayFileWriteHost&,u32& result);
}
