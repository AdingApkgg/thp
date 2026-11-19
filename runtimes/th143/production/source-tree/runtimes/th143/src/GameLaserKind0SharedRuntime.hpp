#pragma once
#include "GameOwnerRuntime.hpp"
#include "LaserKind0RectangleCancel.hpp"
#include "LaserKind0CircleCancel.hpp"
#include "LaserKind0FullCancel.hpp"
#include "GameRenderRuntime.hpp"
#include "LaserEmitterLaunch.hpp"
#include "LaserFactory.hpp"
#include "LaserKind0OrdinaryUpdate.hpp"
#include "LaserKind0Contact.hpp"
#include "LaserKind0ContactShared.hpp"
#include "LaserKind0Draw.hpp"
#include "SoundQueue.hpp"
#include <functional>
namespace th143 {
// Typed kind0 binding over the live owner heap and ANM/resource/render world.
// Cancellation subclasses and nonempty transform programs remain explicit gaps.
class GameLaserKind0SharedRuntime final:public LaserEmitterSink,private LaserFactoryHost,private LaserKind0OrdinaryHost,private LaserKind0ContactHost,private LaserKind0DrawHost,private LaserKind0RectangleCancelHost {
public:
 GameLaserKind0SharedRuntime(GameOwnerRuntime& o,AnmResourceWorld& w,GameOwnerServices& a,SoundQueue& q,GameRenderRuntime& r):owners(o),world(w),allocator(a),audio(q),render(r){}
 std::function<bool(const std::array<float,3>&,float,float,float,bool,i32&)> rectangle_contact;
 std::function<bool(const std::array<float,3>&)> graze_effect;
 std::array<u32,2> contact_scratch{};
 std::function<bool(const std::array<float,3>&,i32)> item_effect;
 bool launch_laser(u32 kind,const u8*,u32 bytes)override;
 bool invoke(u32 token,u32 slot,bool has_argument,u32 argument,i32& result);
 bool draw(u32 entry,u32 token);
 bool rectangle(u32,const std::array<float,3>&,const std::array<float,3>&,float,i32,bool,i32&);
 bool circle(u32,const std::array<float,3>&,float,i32,bool,i32&);
 bool full(u32,i32,bool,i32&);
 bool release(u32 token);
private:
 GameOwnerRuntime& owners;AnmResourceWorld& world;GameOwnerServices& allocator;SoundQueue& audio;GameRenderRuntime& render;
 std::array<u8,0x354> parameters{};
 AnmView beam(u32);
 bool read(u32,void*,u32)override;
 bool write(u32,const void*,u32)override;
 bool timer_rate(u32 p,float& out)override{return world.timer_rate(p,out);}
 u32 global_rate_token()const override{return world.global_rate_token();}
 bool sprite(u32 r,i32 i,u32& p,std::array<u32,17>& out)override{return world.sprite(r,i,p,out);}
 bool script(u32 r,i32 i,u32& p,u16& file,bool& ready)override{return world.script(r,i,p,file,ready);}
 bool fallback_sprite(u32& r,i32& i)override{return world.fallback_sprite(r,i);}
 bool script_bound()override;
 Rng* script_rng()override{return &world.animation_rng;}
 bool translation(std::array<float,3>& out)override{return world.translation(out);}
 bool parent_slowdown(u32 p,float& out)override{return static_cast<AnmWorld&>(world).parent_slowdown(p,out);}
 bool bullet_style(u32,i32&,i32&)override;
 AnmView laser_animation_template(u32,i32)override;
 bool laser_launch_sound(i32 id,float x)override{return audio.request(u32(id),true,x);}
 bool laser_factory_read(u32 p,void* out,u32 n)override{return read(p,out,n);}
 bool laser_factory_write(u32 p,const void* in,u32 n)override{return write(p,in,n);}
 bool laser_factory_allocate(u32,u32&,u8*&)override;
 bool laser_factory_initialize(u32,u32,u32)override;
 bool laser_kind0_contact(u32 token,u32 argument)override;
 bool laser_player_rectangle(const std::array<float,3>& p,float length,float width,float angle,bool forced,i32& result)override{return rectangle_contact&&rectangle_contact(p,length,width,angle,forced,result);}
 bool laser_player_position(std::array<float,3>&)override;
 bool laser_player_cancel(u32,const std::array<float,3>&,const std::array<float,3>&,float,i32,bool)override;
 bool laser_rectangle_item(const std::array<float,3>& p,i32 kind)override{return item_effect&&item_effect(p,kind);}
 bool laser_rectangle_visual(i32,const std::array<float,3>&)override;
 bool laser_rectangle_spawn(const u8* p,u32 n)override{return launch_laser(0,p,n);}
 bool laser_player_graze(const std::array<float,3>& p)override{return graze_effect&&graze_effect(p);}
 bool laser_draw_animation(u32 token,AnmView v)override{return render.draw_player_visual(token,v);}
};
}
