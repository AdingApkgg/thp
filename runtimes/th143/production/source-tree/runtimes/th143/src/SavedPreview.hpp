#pragma once
#include "SaveData.hpp"
#include <string>
namespace th143 {
struct SavedPreviewHost {
    virtual ~SavedPreviewHost()=default;
    virtual bool saved_preview_directory(bool restore)=0;
    virtual bool saved_preview_exists(const std::string&,bool& found)=0;
    virtual bool read_saved_preview_file(const std::string&,u32& token,u32& bytes)=0;
    virtual bool allocate_saved_preview_array(u32 bytes,u32& token)=0;
    virtual bool read_saved_preview_memory(u32,void*,u32)=0;
    virtual bool write_saved_preview_memory(u32,const void*,u32)=0;
    virtual bool release_saved_preview_array(u32)=0;
};
//411820: BST3 version1/header copy and469df0 decompression. The codec's
// dictionary is shared with the caller, as in the original global codec.
bool load_saved_preview(const std::string&,th11::Lzss&,SavedPreviewHost&,u32& result);
}
