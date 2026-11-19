#pragma once
#include "MusicStreamCore.hpp"
namespace th143 {
struct MusicFileOpenHost:MusicStreamHost {
    virtual bool log_music_open(u32 path)=0;
    virtual bool create_music_file(u32 path,u32& handle)=0;
    virtual bool music_last_error(u32& error)=0;
    virtual bool format_music_error(u32 error,u32& message)=0;
    virtual bool log_music_error(u32 message)=0;
    virtual bool free_music_error(u32 message)=0;
    virtual bool log_music_metadata(u32 metadata,u32 start,u32 length)=0;
};
bool open_music_file(AnmView stream,u32 bytes,u32 path,AnmView metadata,
                     u32 metadata_token,u32 file_base,MusicFileOpenHost&,u32& result); //486c10
bool reopen_music_file(AnmView stream,u32 bytes,AnmView metadata,u32 metadata_token,
                       u32 position,u32 file_base,MusicFileOpenHost&,u32& result); //486cd0
}
