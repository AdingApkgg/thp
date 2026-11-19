#pragma once
#include "AnmState.hpp"
#include "../../th12/th12_web/cpp/game/Lzss.hpp"
#include <array>
#include <string>
namespace th143 {
struct SavedPreviewWriteParameters {u32 flags=0,width=288,height=336,bytes_per_pixel=4,day=0,within_day=0;std::array<u8,0x74> stack_bytes{};};
struct SavedPreviewWriteHost {
 virtual ~SavedPreviewWriteHost()=default;
 virtual bool preview_directory(u32 phase)=0;
 virtual bool preview_make_directory()=0;
 virtual bool preview_filetime(std::uint64_t&)=0;
 virtual bool preview_open(const std::string&,u32& handle)=0;
 virtual bool preview_write(u32 handle,const u8*,u32 bytes,u32& written)=0;
 virtual bool preview_close(u32 handle)=0;
 virtual bool preview_allocate_payload(u32 bytes,u32& token)=0;
 virtual bool preview_release_payload(u32 token)=0;
};
//411920 with actual LZSS; initial stack bytes and file/GPU/OS services are explicit.
bool write_saved_preview(const std::string&,const u8* pixels,u32 bytes,const SavedPreviewWriteParameters&,th11::Lzss&,SavedPreviewWriteHost&);
}
