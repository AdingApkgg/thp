#pragma once
#include "GameSaveRuntime.hpp"
#include "AnmResourceWorld.hpp"
namespace th143 {
//455e30/4560a0 with an existing file. File I/O owns the raw address; the
// runtime binds the decoded array to the shared game allocator independently.
class GameSavedFile {
public:
    GameSavedFile(SaveData& s,GameOwnerServices& a):save(s),storage(a){}
    bool initialize(const u8*,u32,u32 input_token,AnmResourceWorld&,Rng&,std::array<u32,4>& equipment,std::array<u32,4>& saved,SaveDataHost&);
    bool synchronize(AnmResourceWorld&);
    bool read(u32,void*,u32);
    u32 file_token=0,decoded_token=0;
private:SaveData& save;GameOwnerServices& storage;bool resource_file=false;
};
}
