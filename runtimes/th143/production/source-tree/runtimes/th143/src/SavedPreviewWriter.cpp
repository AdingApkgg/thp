#include "SavedPreviewWriter.hpp"
#include <cstdint>
namespace th143 {
bool write_saved_preview(const std::string& name,const u8* pixels,u32 bytes,const SavedPreviewWriteParameters& p,th11::Lzss& codec,SavedPreviewWriteHost& host){
 if(!(p.flags&4))return true;
 const u32 count=p.width*p.height*p.bytes_per_pixel;if(count>bytes||(count&&!pixels)||count>0x20000000)return false;
 if(!host.preview_directory(0)||!host.preview_make_directory()||!host.preview_directory(1))return false;
 auto header=p.stack_bytes;AnmView h{header.data()};h.put(0,0x33545342);header[4]=1;
 auto half=[&](u32 at,u32 value){const u16 v=u16(value);std::memcpy(header.data()+at,&v,2);};
 half(6,p.day);half(8,p.within_day);half(10,0x100);half(12,p.width);half(14,p.height);h.put(16,count);
 std::uint64_t filetime;if(!host.preview_filetime(filetime))return false;
 const std::uint64_t seconds=(filetime-116444736000000000ull)/10000000ull;
 const std::uint64_t time=seconds>0x793406fffull?~std::uint64_t(0):seconds;std::memcpy(header.data()+20,&time,8);
 u32 handle;if(!host.preview_open(name,handle))return false;
 auto write=[&](const u8* data,u32 n){if(handle==0xffffffff)return true;u32 written;if(!host.preview_write(handle,data,n,written))return false;return written==n||host.preview_close(handle);};
 if(!write(header.data(),0x24)||!write(header.data()+0x24,0x50))return false;
 u32 allocation;if(!host.preview_allocate_payload(count*2,allocation)||!allocation)return false;
 const auto payload=codec.encode(pixels,count);
 if(!write(payload.data(),u32(payload.size())))return false;
 if(handle!=0xffffffff&&!host.preview_close(handle))return false;
 if(!host.preview_release_payload(allocation))return false;
 return host.preview_directory(2);
}
}
