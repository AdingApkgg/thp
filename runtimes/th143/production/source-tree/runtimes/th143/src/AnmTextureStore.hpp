#pragma once
#include "AnmTextureTransfer.hpp"
#include "AnmTextureRegion.hpp"
#include <map>
namespace th143 {
struct AnmTextureLayout {u32 format=0,width=0,height=0;};
struct AnmTextureStoreDevice {
    virtual ~AnmTextureStoreDevice()=default;
    virtual bool select_texture_layout(const AnmDeviceTextureRequest&,AnmTextureLayout&,i32& hresult)=0;
    virtual bool texture_created(u32,const AnmTexturePixels&){return true;}
    virtual bool texture_uploaded(u32,const AnmTexturePixels&){return true;}
    virtual bool texture_reference_changed(u32,u32){return true;}
    virtual bool texture_destroyed(u32){return true;}
};
struct AnmStoredTexture {AnmTexturePixels pixels;AnmDeviceTextureRequest requested;u32 references=1;};
// Persistent CPU images share raw ResourceLoader ownership. Only physical
// format/size selection and optional GPU notifications are device services.
class AnmTextureStore {
public:
    explicit AnmTextureStore(AnmTextureStoreDevice& device,u8 initial_fill=0):device(device),initial_fill(initial_fill){}
    bool create(const AnmTextureRequest&,ResourceLoaderHost&,float scale,u32 backbuffer_format,i32& result,u32& physical_width,u32& physical_height);
    bool release(u32 token);
    bool surface(u32 texture,u32 level,u32& surface,i32& hresult);
    std::map<u32,AnmStoredTexture> images;
private:
    struct Transfer;
    AnmTextureStoreDevice& device;
    u8 initial_fill;
};
}
