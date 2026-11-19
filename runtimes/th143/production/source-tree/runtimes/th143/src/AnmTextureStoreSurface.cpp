#include "AnmTextureStore.hpp"
namespace th143 {
struct AnmTextureStore::Transfer:AnmTextureTransferHost {
    AnmTextureStore& owner;ResourceLoaderHost& memory;
    Transfer(AnmTextureStore& owner,ResourceLoaderHost& memory):owner(owner),memory(memory){}
    bool read_texture_memory(u32 p,void* out,u32 n)override{return memory.read(p,out,n);}
    bool write_texture_memory(u32 p,const void* in,u32 n)override{return memory.write(p,in,n);}
    bool create_device_texture(const AnmDeviceTextureRequest& r,u32 output,i32& hr)override{
        AnmTextureLayout layout;if(!owner.device.select_texture_layout(r,layout,hr))return false;if(hr!=0)return true;const u32 bpp=anm_texture_pixel_bytes(layout.format);
        if(!bpp||!layout.width||!layout.height||std::uint64_t(layout.width)*layout.height*bpp>0x10000000)return false;
        u32 token,vtable;if(!memory.allocate_resource_storage(16,false,token)||!memory.allocate_resource_storage(0x60,false,vtable))return false;std::array<u8,0x60> table{};AnmView t{table.data()};t.put(8,0x7002d008);t.put(0x44,0x7002d000);t.put(0x48,0x7002d004);
        // Declared D3D9 surface bridge uses these logical service identities.
        // They are address metadata; portable calls still use typed texture services.
        t.put(0x30,0x7002c090);t.put(0x34,0x7002c094);t.put(0x38,0x7002c098);t.put(0x24,0x7002c09c);
        if(!memory.write(vtable,table.data(),table.size())||!memory.write(token,&vtable,4)||!memory.write(output,&token,4))return false;
        AnmStoredTexture texture;texture.requested=r;texture.pixels.format=layout.format;texture.pixels.width=layout.width;texture.pixels.height=layout.height;texture.pixels.data.assign(layout.width*layout.height*bpp,owner.initial_fill);auto result=owner.images.emplace(token,std::move(texture));if(!result.second)return false;return owner.device.texture_created(token,result.first->second.pixels);
    }
    bool texture_surface(u32 texture,u32 level,u32& surface,i32& hr)override{return owner.surface(texture,level,surface,hr);}
    bool upload_texture_surface(const AnmSurfaceUpload& r,i32& hr)override{
        hr=i32(0x8876086cu);auto found=owner.images.find(r.surface);if(found==owner.images.end())return true;const u32 bpp=anm_texture_pixel_bytes(r.format);if(!bpp||r.pitch%bpp||r.source_rect[3]<0||r.color_key)return false;
        const u32 width=r.pitch/bpp,height=u32(r.source_rect[3]);const std::uint64_t n=std::uint64_t(r.pitch)*height;if(n>0x10000000)return false;std::vector<u8> source;source.resize(u32(n));if(n&&!memory.read(r.source,source.data(),u32(n)))return false;
        if(!upload_anm_texture_region(found->second.pixels,r.destination,r.format,width,height,source.data(),u32(n),r.source_rect,r.filter,hr))return false;return hr<0||owner.device.texture_uploaded(r.surface,found->second.pixels);
    }
    bool release_texture_object(u32 token)override{return owner.release(token);}
};
bool AnmTextureStore::create(const AnmTextureRequest& r,ResourceLoaderHost& memory,float scale,u32 backbuffer,i32& result,u32& width,u32& height){Transfer transfer{*this,memory};if(!transfer_anm_texture(r,scale,backbuffer,transfer,result))return false;width=height=0;if(result<0)return true;u32 token;if(!memory.read(r.entry,&token,4))return false;auto p=images.find(token);if(p==images.end())return false;width=p->second.pixels.width;height=p->second.pixels.height;return true;}
bool AnmTextureStore::release(u32 token){auto p=images.find(token);if(p==images.end()||!p->second.references)return false;if(p->second.references>1){--p->second.references;return device.texture_reference_changed(token,p->second.references);}if(!device.texture_destroyed(token))return false;images.erase(p);return true;}
bool AnmTextureStore::surface(u32 texture,u32 level,u32& surface,i32& hr){surface=0;hr=i32(0x8876086cu);auto p=images.find(texture);if(p==images.end()||level)return true;++p->second.references;surface=texture;hr=0;return device.texture_reference_changed(texture,p->second.references);}
}
