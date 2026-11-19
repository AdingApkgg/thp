#pragma once
#include "GameOwnerRuntime.hpp"
#include "SaveData.hpp"
namespace th143 {
// Cold missing-save ownership: SaveData computes the records/RNG/header, then
// the shared game allocator assigns the retained file's guest address. This
// avoids SaveData's isolated-test address colliding with the live laser owner.
class GameSaveRuntime {
public:
    GameSaveRuntime(SaveData& s,GameOwnerServices& a):save(s),storage(a){}
    bool initialize_missing(Rng&,std::array<u32,4>&,std::array<u32,4>&,SaveDataHost&);
    bool read(u32,void*,u32);
    u32 file_token=0;
private:
    SaveData& save;GameOwnerServices& storage;
};
}
