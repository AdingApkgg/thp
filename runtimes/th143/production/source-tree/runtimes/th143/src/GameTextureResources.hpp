#pragma once
#include "AnmResourceWorld.hpp"
#include "AnmTextureStore.hpp"
namespace th143 {
// Application resource services over the production persistent texture store.
// Files/allocator notifications belong to the caller; texture pixels, surface
// references and native transfer/resize rules remain in AnmTextureStore.
class GameTextureResources final:public AnmResourceServices {
public:
    GameTextureResources(AnmResourceServices& files,AnmTextureStoreDevice& device,u8 initial_fill=0):textures(device,initial_fill),files(files){}
    AnmTextureStore textures;float scale=1.f;u32 backbuffer_format=21;
    bool read_animation_file(const std::string& name,bool external,std::vector<u8>& out)override{return files.read_animation_file(name,external,out);}
    bool create_animation_texture(const AnmTextureRequest&,ResourceLoaderHost&,i32&,u32&,u32&)override;
    bool release_animation_texture(u32 token)override{return textures.release(token);}
    void animation_storage_allocated(u32 p,u32 n,bool array)override{files.animation_storage_allocated(p,n,array);}
private:AnmResourceServices& files;
};
}
