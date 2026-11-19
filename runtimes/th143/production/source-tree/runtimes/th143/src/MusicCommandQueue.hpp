#pragma once
#include "SaveData.hpp"
namespace th143 {
// 4737b0 CPU command storage. Device playback and main-thread processing of
// commands are separate; a full queue silently drops the new command.
struct MusicCommandQueue {
    static constexpr u32 count=31,stride=0x10c,bytes=count*stride;
    std::array<u8,bytes> data{};
    AnmView view(){return {data.data()};}
    bool enqueue(u32 kind,u32 parameter,const char* name);
    bool start(SaveData&,u32 parameter,u32 track,u32 scene_flags); //4446e0
};
}
