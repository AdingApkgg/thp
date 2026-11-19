#include "GameLaserKind1Runtime.hpp"
#pragma once
#include "GameLaserKind0SharedRuntime.hpp"
#include "LaserKind2Initialize.hpp"
#include "LaserKind2Update.hpp"
#include "LaserKind2Contact.hpp"
#include "LaserKind2Draw.hpp"
#include "LaserKind2RectangleCancel.hpp"
#include "LaserKind2Cleanup.hpp"
#include "AnmExternalGeometry.hpp"
#include "LaserKind2CircleCancel.hpp"
#include "LaserKind2FullCancel.hpp"
namespace th143 {
// Live typed kind0/kind2 binding; the enemy animation call-site stack word
// is bound by GamePlayCampaignCurveRuntime. Full-scene verification is separate.
class GameLaserKinds012Runtime final:public LaserEmitterSink,private LaserFactoryHost,private LaserKind2Host,private LaserKind2UpdateHost,private LaserKind2ContactHost,private LaserKind2DrawHost,private LaserKind2RectangleCancelHost,private LaserKind2CleanupHost,private AnmRenderMemory {
 GameOwnerRuntime& owners;AnmResourceWorld& world;GameOwnerServices& allocator;SoundQueue& audio;GameRenderRuntime& render;GameRenderDevice& device;
 GameLaserKind0SharedRuntime kind0;GameLaserKind1Runtime kind1;
 std::array<u8,0x354> parameters{};
 std::vector<u8> mask;
 u32 mask_token=0;
public:
 GameLaserKinds012Runtime(GameOwnerRuntime&,AnmResourceWorld&,GameOwnerServices&,SoundQueue&,GameRenderRuntime&,GameRenderDevice&);
 std::function<bool(const std::array<float,3>&,float,float,float,bool,i32&)> rectangle_contact;
 std::function<bool(const std::array<float,3>&)> graze_effect;
 std::function<bool(const std::array<float,3>&,i32)> item_effect;
 std::array<u32,2>& contact_scratch;
 u32 kind2_contact_z_scratch=0;
 std::array<u32,12> diagnostic{};
 std::function<bool(std::array<float,3>&,bool&)> boss_position;
 bool launch_laser(u32,const u8*,u32)override;
 bool invoke(u32,u32,bool,u32,i32&);
 bool draw(u32,u32);
 bool rectangle(u32,const std::array<float,3>&,const std::array<float,3>&,float,i32,bool,i32&);
 bool circle(u32,const std::array<float,3>&,float,i32,bool,i32&);
 bool full(u32,i32,bool,i32&);
 bool release(u32);
private:
 AnmView beam(u32);
 bool allocate(u32,u32&,u8*&);
 bool read(u32,void*,u32)override;
 bool write(u32,const void*,u32)override;
 bool timer_rate(u32 p,float& out)override{return world.timer_rate(p,out);}
 u32 global_rate_token()const override{return world.global_rate_token();}
 bool sprite(u32 r,i32 i,u32& p,std::array<u32,17>& out)override{return world.sprite(r,i,p,out);}
 bool script(u32 r,i32 i,u32& p,u16& f,bool& ready)override{return world.script(r,i,p,f,ready);}
 bool fallback_sprite(u32& r,i32& i)override{return world.fallback_sprite(r,i);}
 bool script_bound()override;
 Rng* script_rng()override{return &world.animation_rng;}
 bool translation(std::array<float,3>& out)override{return world.translation(out);}
 bool parent_slowdown(u32 p,float& out)override{return static_cast<AnmWorld&>(world).parent_slowdown(p,out);}
 bool bullet_style(u32,i32&,i32&)override;
 AnmView laser_animation_template(u32,i32)override;
 bool laser_launch_sound(i32 id,float x)override{return audio.request(u32(id),true,x);}
 bool laser_curve_allocate(u32 n,bool,u32& p,u8*& out)override{return allocate(n,p,out);}
 bool laser_factory_read(u32 p,void* out,u32 n)override{return read(p,out,n);}
 bool laser_factory_write(u32 p,const void* in,u32 n)override{return write(p,in,n);}
 bool laser_factory_allocate(u32 n,u32& p,u8*& out)override{return n==0x14f0&&allocate(n,p,out);}
 bool laser_factory_initialize(u32,u32,u32)override;
 bool laser_point_read(u32 p,void* out,u32 n)override{return read(p,out,n);}
 bool laser_point_write(u32 p,const void* in,u32 n)override{return write(p,in,n);}
 bool laser_node_read(u32 p,void* out,u32 n)override{return read(p,out,n);}
 bool laser_node_write(u32 p,const void* in,u32 n)override{return write(p,in,n);}
 bool laser_node_allocate(u32 n,u32& p,u8*& out)override{return n==0x3c&&allocate(n,p,out);}
 bool laser_kind2_update_contact(u32,bool)override;
 bool laser_kind2_update_animation(u32,AnmView)override;
 bool laser_contact_read(u32 p,void* out,u32 n)override{return read(p,out,n);}
 bool laser_player_rectangle(const std::array<float,3>& p,float l,float w,float a,bool f,i32& r)override{return rectangle_contact&&rectangle_contact(p,l,w,a,f,r);}
 bool laser_player_position(std::array<float,3>&)override;
 bool laser_player_cancel(u32,const std::array<float,3>&,const std::array<float,3>&,float,i32,bool)override;
 bool laser_player_graze(const std::array<float,3>& p)override{return graze_effect&&graze_effect(p);}
 bool laser_rectangle_item(const std::array<float,3>& p,i32 k)override{return item_effect&&item_effect(p,k);}
 bool laser_rectangle_visual(i32,const std::array<float,3>&)override;
 bool laser_rectangle_spawn(const u8* p,u32 n)override{return launch_laser(2,p,n);}
 bool laser_rectangle_mask_allocate(u32,u32&,u8*&)override;
 bool laser_rectangle_mask_release(u32)override;
 bool laser_draw_external(u32,AnmView,u32,u32)override;
 bool laser_draw_secondary(u32 p,AnmView v)override{return render.draw_player_visual(p,v);}
 bool read_render_memory(u32 p,void* out,u32 n)override{return read(p,out,n)||device.read_game_render_memory(p,out,n);}
 bool write_render_memory(u32 p,const void* in,u32 n)override{return write(p,in,n)||device.write_game_render_memory(p,in,n);}
 bool laser_cleanup_read(u32 p,void* out,u32 n)override{return read(p,out,n);}
 bool laser_cleanup_release(u32 p,bool array)override{return world.release_enemy_storage(p,array);}
};
}
