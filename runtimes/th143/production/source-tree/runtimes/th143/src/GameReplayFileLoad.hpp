#pragma once
#include "GameManagerState.hpp"
#include "../../th12/th12_web/cpp/game/Lzss.hpp"
namespace th143 {
struct GameReplayFileHost {
 virtual ~GameReplayFileHost()=default;
 virtual bool replay_game_flags(u32&)=0;
 virtual bool replay_directory(u32 path)=0;
 virtual bool replay_exists(const u8* path,u32 bytes,bool& exists)=0;
 virtual bool replay_open(const u8* path,u32 bytes,u32& status)=0;
 virtual bool replay_read(u32 bytes,u32& token)=0;
 virtual bool replay_close()=0;
 virtual bool replay_archive(const u8* name,u32 bytes,u32& token,u32& file_bytes)=0;
 virtual bool replay_allocate(u32 bytes,u32& token)=0;
 virtual bool replay_region(u32 token,u32 bytes,AnmView&)=0;
 virtual bool replay_free(u32 token)=0;
};
//Full455280. External files validate36-byte t143/version1header; archiveflag80
//uses contiguous raw bytes. Both decrypt5c/e1/400 then7d/3a/100 and LZSS.
//Completefile/nonnullallocation/decodedlength>=b0/terminatedname<=255 domain.
//Decoder is supplied so its dictionary can retain the native shared lifetime.
bool load_game_replay_file(GameManagerState&,th11::Lzss& decoder,const u8* name,u32 available,GameReplayFileHost&,u32& result);
}
