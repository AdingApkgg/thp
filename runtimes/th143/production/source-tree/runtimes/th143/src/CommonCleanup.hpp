#pragma once
#include "CommonLoad.hpp"
#include "SaveFileWriter.hpp"
namespace th143 {
struct CommonCleanupHost:SaveFileServices {
    virtual ~CommonCleanupHost()=default;
    virtual bool wait_common_worker(u32 handle,u32 milliseconds,u32& result)=0;
    virtual bool sleep_common_worker(u32 milliseconds)=0;
    virtual bool close_common_worker(u32 handle)=0;
    virtual bool common_save_directory(bool restore)=0;
    virtual bool open_common_save(i32& result,u32& handle)=0;
    virtual bool write_common_save(u32 handle,const u8*,u32,u32& written)=0;
    virtual bool close_common_save(u32 handle)=0;
    virtual bool common_save_error()=0;
    bool save_directory(bool restore)override{return common_save_directory(restore);}
    bool open_save_file(i32& result,u32& handle)override{return open_common_save(result,handle);}
    bool write_save_file_bytes(u32 handle,const u8* data,u32 bytes,u32& written)override{return write_common_save(handle,data,bytes,written);}
    bool close_save_file(u32 handle)override{return close_common_save(handle);}
    bool save_file_error()override{return common_save_error();}
};
//443520 ->443280. The serializer uses the existing independently verified
// SaveData codec; its library scratch allocation layout is not guest ownership.
bool destroy_common(CommonLoadBindings&,CommonCleanupHost&,u32 wait_budget=100000);
}
