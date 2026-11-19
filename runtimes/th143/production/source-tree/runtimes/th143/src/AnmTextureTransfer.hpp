#pragma once
#include "ResourceLoader.hpp"
#include <array>
namespace th143 {
struct AnmDeviceTextureRequest {bool direct=false;u32 width=0,height=0,levels=1,usage=0,format=0,pool=1;};
struct AnmSurfaceUpload {u32 surface=0,source=0,format=0,pitch=0,filter=1,color_key=0;std::array<i32,4> destination{},source_rect{};};
struct AnmTextureTransferHost {
    virtual ~AnmTextureTransferHost()=default;
    virtual bool read_texture_memory(u32,void*,u32)=0;
    virtual bool write_texture_memory(u32,const void*,u32)=0;
    // Device calls return transport success separately from their HRESULT.
    // Create writes its output token to the declared guest output address.
    virtual bool create_device_texture(const AnmDeviceTextureRequest&,u32 output,i32& hresult)=0;
    virtual bool texture_surface(u32 texture,u32 level,u32& surface,i32& hresult)=0;
    virtual bool upload_texture_surface(const AnmSurfaceUpload&,i32& hresult)=0;
    virtual bool release_texture_object(u32)=0;
};
// 481c40/481e10/481e60. Reconstruct source/destination rectangles, scaling,
// D3DX filter selection, texture flags/bpp and original return/error behavior.
bool transfer_anm_texture(const AnmTextureRequest&,float scale,u32 backbuffer_format,AnmTextureTransferHost&,i32& result);
}
