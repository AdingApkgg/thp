#pragma once
#include "SavedPreview.hpp"
#include "TitlePreviewWorker.hpp"
namespace th143 {
struct SavedPreviewFileServices {
    virtual ~SavedPreviewFileServices()=default;
    virtual bool saved_preview_directory(bool restore)=0;
    virtual bool saved_preview_exists(const std::string&,bool& found)=0;
    virtual bool read_saved_preview_bytes(const std::string&,std::vector<u8>&)=0;
};
// BST3 arrays live in the same retained resource memory as the preview worker.
class GameSavedPreviewFiles:public SavedPreviewHost {
public:
    GameSavedPreviewFiles(AnmResourceWorld& world,SavedPreviewFileServices& files):world(world),files(files){}
    bool saved_preview_directory(bool restore)override{return files.saved_preview_directory(restore);}
    bool saved_preview_exists(const std::string& name,bool& found)override{return files.saved_preview_exists(name,found);}
    bool read_saved_preview_file(const std::string&,u32& token,u32& bytes)override;
    bool allocate_saved_preview_array(u32 n,u32& token)override{return world.allocate_resource_storage(n,true,token);}
    bool read_saved_preview_memory(u32 p,void* out,u32 n)override{return world.read(p,out,n);}
    bool write_saved_preview_memory(u32 p,const void* in,u32 n)override{return world.write(p,in,n);}
    bool release_saved_preview_array(u32 p)override{return world.release_enemy_storage(p,true);}
private:AnmResourceWorld& world;SavedPreviewFileServices& files;
};
class GameTitleSavedPreviewWorker final:public TitlePreviewWorkerHost {
public:
    GameTitleSavedPreviewWorker(TitlePreviewWorkerHost& next,SavedPreviewHost& files,th11::Lzss& codec):next(next),files(files),codec(codec){}
    bool read_scene_preview(const std::string& name,std::vector<u8>& bytes,bool& found)override{return next.read_scene_preview(name,bytes,found);}
    bool read_saved_preview(const std::string& name,u32& token)override{return load_saved_preview(name,codec,files,token);}
    bool sleep_scene_preview(u32 ms)override{return next.sleep_scene_preview(ms);}
private:TitlePreviewWorkerHost& next;SavedPreviewHost& files;th11::Lzss& codec;
};
}
