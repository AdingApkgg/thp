#pragma once
#include "MusicArchiveInitialize.hpp"
#include "OwnedMusicControllerMainHost.hpp"
namespace th143 {
//Composition adapter:472560 ->4729f0 and485360 use owned game bodies.
//The supplied host continues to own all physical file/buffer/thread services.
bool initialize_owned_music_archive(AnmView audio,u32 bytes,OwnedMusicControllerMainHost&,u32& result);
}
