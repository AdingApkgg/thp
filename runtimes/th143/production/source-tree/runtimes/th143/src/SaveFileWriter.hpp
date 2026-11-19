#pragma once
#include "GameSavedFile.hpp"
namespace th143 {
struct SaveFileServices {
    virtual ~SaveFileServices()=default;
    virtual bool save_directory(bool restore)=0;
    virtual bool open_save_file(i32& result,u32& handle)=0;
    virtual bool write_save_file_bytes(u32 handle,const u8*,u32,u32& written)=0;
    virtual bool close_save_file(u32 handle)=0;
    virtual bool save_file_error()=0;
};
//4562e0 serialization/I/O is shared by common teardown and title loading.
bool write_save_file(SaveData&,const std::array<u32,4>& saved_equipment,AnmResourceWorld&,SaveFileServices&,GameSavedFile* loaded=nullptr);
}
