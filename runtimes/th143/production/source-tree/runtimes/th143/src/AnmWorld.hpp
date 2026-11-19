#pragma once
#include "AnmManager.hpp"
#include "AnmTemplate.hpp"
#include "AnmEffect7.hpp"
#include "AnmTransform.hpp"
#include "AnmPool.hpp"
#include <memory>
#include <vector>

namespace th143 {
// Resource-backed animation ownership. Tokens represent guest addresses;
// external allocations are retained after retirement for deterministic audit.
class AnmWorld : public AnmVmHost, public AnmEffect7Host, public AnmStorageHost,public AnmTransformHost,public AnmPoolHost {
public:
    using State=std::array<u8,AnmView::bytes>;
    struct StateStorage {
        std::unique_ptr<State> owned;
        u8* alias=nullptr;
        StateStorage():owned(std::make_unique<State>()){}
        explicit StateStorage(u8* p):alias(p){}
        u8* data(){return alias?alias:owned->data();}
    };
    struct Region {u32 token;std::vector<u8> bytes;};
    struct Resource {
        u32 token,table,count,file,template_token;
        std::vector<u32> scripts;
        std::vector<State> templates;
    };
    struct Extra {u32 token;std::array<u8,0x193c> data;};
    std::vector<Region> regions;
    std::vector<Resource> resources;
    std::vector<std::unique_ptr<StateStorage>> states;
    std::vector<u32> state_tokens;
    std::vector<u32> allocations;
    std::map<u32,u32> state_indices;
    std::unique_ptr<AnmPool> pool;
    std::vector<std::unique_ptr<Extra>> extras;
    std::vector<Region> geometry_buffers;
    AnmViewport viewport;
    AnmInstances instances;
    AnmManager manager;
    Rng animation_rng{12345};
    std::vector<u32> releases;
    float rate=1.f;
    u32 effect_resource=0,error=0;

    bool enable_pool(AnmPoolGlobals&,AnmPoolHost&);
    bool acquire_state(u32& token,AnmView&);
    AnmView state(u32 token);
    bool register_pool_callback(u32 entry,i32 priority,bool draw,u32 owner)override;
    bool set_pool_vertex_format(u32)override;
    bool allocate_pool_fallback(u32& token,AnmView&)override;

    Resource* resource(u32 token);
    bool build(u32 token);
    bool create(u32 resource,i32 script,i32 layer,u32& handle,bool prepend=true);
    bool create_effect(i32 script,const std::array<float,3>& position,u32& handle);
    bool create_at(u32 resource,i32 script,i32 layer,const std::array<float,3>& position,u32& handle);
    bool cancel_bullet(u32 resource,i32 script,const std::array<float,3>& position,const std::array<float,3>& target);
    bool begin_frame(float elapsed);
    bool update();
    bool flag(u32 handle,bool enabled);
    bool mark_retirement(u32 handle);

    bool read(u32,void*,u32) override;
    bool write(u32,const void*,u32) override;
    bool timer_rate(u32,float&) override;
    u32 global_rate_token() const override {return 0x4e40b0;}
    bool sprite(u32,i32,u32&,std::array<u32,17>&) override;
    bool fallback_sprite(u32&,i32&) override;
    bool script(u32,i32,u32&,u16&,bool&) override;
    Rng* script_rng() override {return &animation_rng;}
    Rng& rng() override {return animation_rng;}
    bool translation(std::array<float,3>& v) override {v={0,0,0};return true;}
    bool parent_slowdown(u32,float&) override;
    bool effect(AnmView,i32) override;
    bool child(AnmView parent,i32 script,u32 flags) override;
    bool detached_child(AnmView parent,i32 script) override;
    AnmView parameter_child(AnmView parent,i32 script,bool detached) override;
    bool allocate_geometry(u32,u32&) override;
    bool update_geometry(AnmView) override;
    AnmView transform_parent(u32) override;
    bool callback(u32,AnmView,float,i32&) override;
    AnmView find(u32 handle) override {return instances.registry.find(handle);}
    bool create(i32 script,u32& handle) override {return create(effect_resource,script,-1,handle,false);}
    bool slowdown(AnmView,float&) override;
    bool release_buffer(u32 token) override;
    bool release_instance(u32 token) override;
    bool prepare_instance_release(u32 token,AnmView)override;
private:
    AnmPoolHost* pool_services=nullptr;
    u32 external_count=0,last_child_token=0;
    bool propagate(u32 handle,u32 at,u32 mask,bool enabled);
};
}
