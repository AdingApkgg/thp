#include "SaveFileWriter.hpp"
namespace th143 {
bool write_save_file(SaveData& save,const std::array<u32,4>& equipment,AnmResourceWorld& resources,SaveFileServices& host,GameSavedFile* loaded){
    std::vector<u8> output;if(!save.serialize(equipment,output)||output.size()<24||(loaded&&!loaded->synchronize(resources))||!host.save_directory(false))return false;
    i32 status;u32 handle;if(!host.open_save_file(status,handle))return false;
    if(status)return host.save_file_error()&&host.save_directory(true);
    if(handle!=0xffffffff){
        u32 written;if(!host.write_save_file_bytes(handle,output.data(),24,written))return false;
        // Original keeps the handle after an early close, attempts the second
        // write, and closes it again at the end even after either short write.
        if(written!=24&&!host.close_save_file(handle))return false;
        const u32 bytes=u32(output.size())-24;if(!host.write_save_file_bytes(handle,output.data()+24,bytes,written))return false;
        if(written!=bytes&&!host.close_save_file(handle))return false;
        if(!host.close_save_file(handle))return false;
    }return host.save_directory(true);
}
}
