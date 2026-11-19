#pragma once
#include "GameTitleRuntime.hpp"
#include "GameCommonRuntime.hpp"
#include "GameCheatRuntime.hpp"
#include "SaveFileWriter.hpp"
#include "TitleMessages.hpp"
namespace th143 {
struct TitleLoadHost:SaveFileServices {
    virtual bool read_title_file(const char* name,std::vector<u8>&)=0;
    virtual bool title_file_padding(u32 token,u32 declared_bytes,std::vector<u8>&)=0;
    virtual bool sleep_title_worker(u32 milliseconds)=0;
    virtual bool title_resource_error()=0;
};
struct TitleLoadBindings {
    GameTitleRuntime& title;GameCommonRuntime& common;GameFrameRuntime& frames;
    GameCheatRuntime& cheat;AnmResourceWorld& resources;GameOwnerServices& storage;
    SaveData& save;AnmView application;CommonApplicationGlobals& globals;
    std::array<u32,4>& equipment;std::array<u32,4>& saved_equipment;
    u32& alternate;u32& global_538de4;
    GameSavedFile* loaded_save=nullptr;u32 last_entry=0;
};
//45f010 followed by45ef60's loading wait/sig retirement/update activation.
bool load_title(TitleLoadBindings&,TitleLoadHost&,i32& result,u32 wait_budget=100000);
}
