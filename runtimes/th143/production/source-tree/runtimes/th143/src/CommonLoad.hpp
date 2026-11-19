#pragma once
#include "GameCommonRuntime.hpp"
#include "GameAuxRuntime.hpp"
#include "GameSaveRuntime.hpp"
#include "GameSavedFile.hpp"
#include "TrophyCatalog.hpp"
namespace th143 {
struct CommonLoadHost:SaveDataHost {
    virtual bool read_common_file(const char* name,bool external,std::vector<u8>&,bool& found)=0;
    virtual bool common_archive_exists(const char* name,bool&)=0;
};
struct CommonLoadBindings {
    GameCommonRuntime& common;GameFrameRuntime& frames;GameAsciiRuntime& ascii;
    GameAuxRuntime& auxiliary;TrophyCatalog& trophies;SaveData& save;GameSaveRuntime& save_runtime;
    AnmResourceWorld& resources;GameOwnerServices& storage;
    AnmView application,audio;Rng& gameplay;
    std::array<u32,4>& equipment;std::array<u32,4>& saved_equipment;
    u32 save_owner=0,last_entry=0;
    GameSavedFile* loaded_save=nullptr;
};
//4430b0 and442f00, cold resources and missing/existing Save. Physical audio/active audio worker
// initialization is explicitly unsupported until those services are bound.
bool load_common(CommonLoadBindings&,CommonLoadHost&,i32& result);
}
