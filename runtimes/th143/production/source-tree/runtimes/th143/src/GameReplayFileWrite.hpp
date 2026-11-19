#pragma once
#include "GameManagerScene.hpp"
#include "../../th12/th12_web/cpp/game/Lzss.hpp"
namespace th143 {
struct GameReplayFileWriteHost:GameManagerSceneHost {
 virtual bool replay_output_directory(u32 path)=0;
 virtual bool replay_output_open(const u8* path,u32 bytes)=0;
 virtual bool replay_output_handle(u32& handle)=0;
 virtual bool replay_output_write(u32 handle,const u8*,u32 bytes,u32& written)=0;
 virtual bool replay_output_close(u32 handle)=0;
 virtual bool replay_output_localtime(u32 time_address,std::array<i32,9>&)=0;
};
// Full454c00 for live recording owners: nonnull header/checkpoint, finite
// timing ratio, <=8-byte name and <=248-byte filename, complete host memory.
// Opaque codec/USER workspace layouts are not observable parts of this API.
bool write_game_replay_file(GameManagerState&,u32 self,th11::Lzss&,const u8* filename,u32 filename_bytes,const u8* name,u32 name_bytes,GameReplayFileWriteHost&,u32& result);
}
