#pragma once
#include "AnmWorld.hpp"
#include "ResourceLoader.hpp"
#include "ResourcePump.hpp"

namespace th143 {
struct AnmResourceServices {
    virtual ~AnmResourceServices()=default;
    virtual bool read_animation_file(const std::string&,bool external,std::vector<u8>&)=0;
    virtual bool create_animation_texture(const AnmTextureRequest&,ResourceLoaderHost&,i32& status,u32& width,u32& height)=0;
    virtual bool release_animation_texture(u32 token)=0;
    virtual void animation_storage_allocated(u32 token,u32 bytes,bool array){}
};
// Raw loader storage and the persistent interpreter share one memory/RNG host.
// Resource templates are copied internally after portable finalization; no
// decoded table or original VM state is supplied by the caller.
class AnmResourceWorld:public AnmWorld,public ResourceLoaderHost,public ResourcePumpMemory {
public:
    explicit AnmResourceWorld(AnmResourceServices&,u32 heap_base=0x74000000);
    bool request(u32 file,const std::string&,u32& resource);
    bool pump(i32& result);
    bool ready(bool&);
    bool unload(u32 file);
    bool synchronize_resources();

    bool read(u32,void*,u32)override;
    bool write(u32,const void*,u32)override;
    bool timer_rate(u32 p,float& v)override{return AnmWorld::timer_rate(p,v);}
    u32 global_rate_token()const override{return AnmWorld::global_rate_token();}
    Rng* script_rng()override{return &animation_rng;}
    bool translation(std::array<float,3>& v)override{return AnmWorld::translation(v);}
    bool sprite(u32,i32,u32&,std::array<u32,17>&)override;
    bool script(u32,i32,u32&,u16&,bool&)override;
    bool fallback_sprite(u32&,i32&)override;
    bool allocate_resource_storage(u32,bool,u32&)override;
    bool release_resource_storage(u32)override;
    bool read_resource_file(const std::string&,bool,u32&,u32&)override;
    bool create_resource_texture(const AnmTextureRequest& r,i32& status,u32& w,u32& h)override{return services.create_animation_texture(r,*this,status,w,h);}
    bool build_resource_template(u32,u32,u32)override;
    u32 resource_viewport_width()const override{return width;}
    u32 resource_viewport_height()const override{return height;}
    bool read_enemy_memory(u32 p,void* out,u32 n)override{return read(p,out,n);}
    bool write_enemy_memory(u32 p,const void* in,u32 n)override{return write(p,in,n);}
    bool release_enemy_storage(u32,bool)override;
    bool release_graphics_object(u32 p)override{return services.release_animation_texture(p);}
    bool find_enemy_visual(u32,u32&)override;
    bool complete_resource_chunk(u32,u32&)override;

    using AnmWorld::create;
    bool create(u32,i32,i32,u32&,bool prepend=true);
    bool create(i32 script,u32& handle)override{return create(effect_resource,script,-1,handle,false);}
    bool create_at(u32,i32,i32,const std::array<float,3>&,u32&);
    bool create_effect(i32,const std::array<float,3>&,u32&);
    bool child(AnmView,i32,u32)override;
    bool detached_child(AnmView,i32)override;
    bool update();
    bool effect(AnmView,i32)override;
    bool callback(u32,AnmView,float,i32&)override;
    bool allocate_geometry(u32,u32&)override;
    bool update_geometry(AnmView)override;
    u32 width=640,height=480;
    std::vector<u32> resource_allocations;
private:
    AnmResourceServices& services;
    u32 heap;
    std::vector<u32> requested;
    AnmView storage(u32,u32);
    bool materialize(u32);
};
}
