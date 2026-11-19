#pragma once
#include "GameOwnerRuntime.hpp"
#include "AnmResourceWorld.hpp"
namespace th143 {
struct GameAuxServices {
    virtual ~GameAuxServices()=default;
    virtual bool auxiliary_surface(u32 texture,u32 level,u32& surface)=0;
    virtual bool release_auxiliary_surface(u32)=0;
    virtual bool release_auxiliary_storage(u32,bool array)=0;
};
// Actual41ae60/418880 owners and4112e0 independent screenshot storage.
// Special418920's enabled effects and screenshot capture/rendering are
// separate bodies; these factories never claim to have executed them.
class GameAuxRuntime final:private SchedulerHost,private ResourceCleanupMemory {
public:
    static constexpr u32 effects_self=0x6b008000,special_self=0x6b009000;
    GameAuxRuntime(Scheduler& s,AnmResourceWorld& w,GameOwnerServices& a,GameAuxServices& f):scheduler(s),animations(w),services(a),external(f){}
    alignas(4) std::array<u8,0x30> effects{};
    alignas(4) std::array<u8,0xc0> special{};
    u32 effects_owner=0,special_owner=0;
    IndependentGraphics independent;
    u32 descriptor=0,width=0,height=0,bytes_per_pixel=0;
    struct Storage{u32 token;std::vector<u8> bytes;};
    std::vector<Storage> storage;
    bool failed=false;
    AnmView effects_view(){return {effects.data()};}
    AnmView special_view(){return {special.data()};}
    bool create_effects(u32& result);
    bool create_special(u32& result);
    bool activate_special();
    bool create_independent(u32 display_width,i32& result);
    bool destroy_effects();
    bool destroy_special();
    bool destroy_independent();
    bool read(u32,void*,u32);
    bool write(u32,const void*,u32);
private:
    Scheduler& scheduler;AnmResourceWorld& animations;GameOwnerServices& services;GameAuxServices& external;
    bool effects_reserved=false,special_reserved=false;
    AnmView mapped(u32,u32);
    bool allocate(u32,u32&,AnmView&);
    bool callback(u32 entry,u32 owner,i32 priority,bool draw,bool enabled,u32& token);
    bool remove_pair(AnmView);
    bool bind(AnmView,u32 self,i32 script);
    std::array<u32,2> heads()const{return {animations.instances.registry.primary_head,animations.instances.registry.secondary_head};}
    bool invoke(u32 entry,u32,u32& result)override{if(entry!=0x41af20&&entry!=0x41af30)return false;result=1;return true;}
    bool release_callback(u32 p)override{return services.release_game_storage(p);}
    bool read_enemy_memory(u32 p,void* out,u32 n)override{return read(p,out,n);}
    bool write_enemy_memory(u32 p,const void* in,u32 n)override{return write(p,in,n);}
    bool release_enemy_storage(u32,bool array)override;
    bool find_enemy_visual(u32 handle,u32& token)override{return animations.find_enemy_visual(handle,token);}
    bool release_graphics_object(u32 p)override{return p==independent.surface?external.release_auxiliary_surface(p):animations.release_graphics_object(p);}
};
}
