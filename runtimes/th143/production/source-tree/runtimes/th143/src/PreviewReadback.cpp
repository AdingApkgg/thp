#include "PreviewReadback.hpp"
#include <cstdint>
namespace th143 {
bool readback_clear_preview(u8* pixels,u32 bytes,const PreviewReadbackParameters& p,PreviewReadbackHost& host,i32& result){
 result=-1;u32 surface=0;i32 status;
 if(!host.create_preview_surface(p.screen_width,p.screen_height,21,2,surface,status))return false;
 if(status)return true;
 if(!host.copy_preview_surface(p.source_surface,surface,status))return false;
 if(status)return !surface||host.release_preview_surface(surface);
 const u8* source=nullptr;u32 accessible=0,pitch=0;
 if(!host.lock_preview_surface(surface,source,accessible,pitch,status))return false;
 // The original ignores LockRect's HRESULT and consumes its output fields.
 const u32 rows=signed_word(p.height)>0?p.height:0,row_bytes=p.width*4;
 const std::uint64_t copied=std::uint64_t(rows)*row_bytes,last=rows&&row_bytes?std::uint64_t(rows-1)*pitch+row_bytes:0;
 if(!pixels||bytes<0x5e800||copied>bytes||last>accessible||(last&&!source))return false;
 for(u32 row=0;row<rows;++row)if(row_bytes)std::memcpy(pixels+row*row_bytes,source+row*pitch,row_bytes);
 if(!host.unlock_preview_surface(surface))return false;
 for(u32 i=0;i<0x17a00;++i)pixels[i*4+3]=255;
 if(surface&&!host.release_preview_surface(surface))return false;result=0;return true;
}
}
