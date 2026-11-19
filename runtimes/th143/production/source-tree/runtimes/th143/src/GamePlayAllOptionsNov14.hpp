#include "PlayerLantern.hpp"
#include "PlayerJizo.hpp"
#include "PlayerDecoy.hpp"
#include "PlayerMallet.hpp"
#include <functional>
#include "EnemyVisualPositionBinding.hpp"
#include "BulletEnemyTransform.hpp"
#include "EnemyAnimationCurveScratch.hpp"
#include "GameLaserKinds012Runtime.hpp"
#include "LaserRectangleCancel.hpp"
#include "LaserFullCancel.hpp"
#include "LaserReset.hpp"
#include "PlayerUmbrella.hpp"
#include "PlayerOrb.hpp"
#pragma once
#include "GamePlayAttack.hpp"
#include "PlayerCamera.hpp"
#include "SceneCancellationClear.hpp"
#include "AnmOverlay.hpp"
#include "SceneRectangleCancellation.hpp"
namespace th143 {
class GamePlayAllOptionsNov14Runtime final:private PlayerFrameHost,private PlayerShootingHost,
    private PlayerShotContactHost,private EnemyCombatServices,private BulletFactoryHost,
    private BulletManagerHost,private BulletContactHost,private ItemMotionHost,
    private PlayerEffectsHost,private PlayerEquipmentFrameHost,private PlayerCameraHost,
    private LaserManagerHost,private LaserRectangleCancelHost,private LaserResetHost,private PlayerAlternateHost,
    private SceneCancellationServices,private PlayerCloakHost,private PlayerOrbHost,private PlayerUmbrellaHost,private PlayerLanternHost,private PlayerJizoHost,private PlayerDecoyHost {
    GameOwnerRuntime& owners;GameEnemyStartup& enemies;GameEnemyRuntime& enemy;
    GameCheatRuntime& cheat;GameAuxRuntime& auxiliary;GameHudRuntime& hud;
    AnmResourceWorld& animations;SoundQueue& audio;std::array<u32,40>& game;Rng& random;GamePlayServices& services;
public:
    GameLaserKinds012Runtime lasers;
    AnmView option_ascii{nullptr};
    std::function<bool(i32)> option_pan;
    PlayerJizoDrawState jizo_draw;
    void bind_option_services(AnmView ascii,std::function<bool(i32)> pan){option_ascii=ascii;option_pan=pan;}

    GamePlayAllOptionsNov14Runtime(GameOwnerRuntime&,GameEnemyStartup&,GameEnemyRuntime&,GameCheatRuntime&,
        GameAuxRuntime&,GameHudRuntime&,AnmResourceWorld&,SoundQueue&,std::array<u32,40>&,Rng&,GamePlayServices&,GameOwnerServices&,GameRenderRuntime&,GameRenderDevice&);
    ~GamePlayAllOptionsNov14Runtime(){bind_enemy_visual_positions(enemies.scripts,{},{});bind_bullet_enemy_transform(static_cast<BulletFactoryHost&>(*this),{});bind_enemy_animation_scratch(enemies.scripts,nullptr,0);}
    PlayerFrameGlobals player_globals;
    PlayerShootingConfig shooting;
    PlayerShotContactGlobals shot_globals;
    EnemyContactGlobals enemy_globals;
    ItemPlayer item_player;
    PlayerEffectGlobals effects;
    ItemRewards rewards;
    PlayerBombGlobals bomb_input;
    std::array<u32,3> umbrella_neutral_velocity{}; // Explicit prototype OS/global binding, not a full-application proof.
    EnemyCombat combat;
    SceneCancellation cancellation;
    SceneCancellationClear clear_cancellation;
    SceneRectangleCancellation camera_rectangles;
    AnmOverlay* camera_overlay=nullptr;
    void bind_camera_overlay(AnmOverlay& o){camera_overlay=&o;}
    PlayerBombScene bomb;
    u32 fresh=0,root_flags=0,secondary_mode=0,secondary_time=0;
    bool failed=false;
    void bind(GameFrameRuntime&);
    bool before(u32 entry,u32 flags);
    bool after(u32 entry);
    bool launch(const u8* parameters,u32 bytes,u32 owner);
 bool scene_lasers_circle(const std::array<float,3>& p,float r,i32 kind,bool items){return cancel_lasers(p,r,kind,items);}
 bool scene_lasers_full(i32 kind,bool items){return cancel_all_lasers(kind,items);}
 bool scene_lasers_reset(){i32 result;return reset_lasers(GameOwnerRuntime::laser_self,*this,result);}
private:
    bool option_countdown(const std::array<float,3>&,const char*,double);
    bool lantern_resource(u32& out)override{return resource(2,out);}
    bool lantern_pan(i32 value)override{return option_pan&&option_pan(value);}
    bool lantern_countdown(const std::array<float,3>& p,double s)override{return option_countdown(p,"%.2f",s);}
    bool decoy_countdown(const std::array<float,3>& p,double s)override{return option_countdown(p,"%.2fs",s);}
    bool jizo_alternate_release()override{return bomb_alternate_release();}
    bool jizo_sound(u32 id,float x)override{return sound(i32(id),true,x);}
    bool jizo_remaining(const std::array<float,3>&,i32)override;
    std::vector<EnemyScripts::Actor*> cancel_bindings;
    AnmView option(u32);
    bool refresh_actors();
    void publish_audio();
    bool read(u32,void*,u32)override;
    bool write(u32,const void*,u32)override;
    bool timer_rate(u32 p,float& value)override{return animations.timer_rate(p,value);}
    u32 global_rate_token()const override{return animations.global_rate_token();}
    bool set_frame_rate(float value)override{animations.rate=value;return true;}
    bool bind_player_visual(PlayerState&,i32)override;
    bool bind_player(PlayerState&,i32)override;
    bool update_player_visual(PlayerState& p)override;
    bool animate_player(PlayerState& p)override{return update_player_visual(p);}
    bool create_focus(i32,u32&)override;
    AnmView visual(u32 h)override{return animations.find(h);}
    bool signal_visual(u32 h,i32 s)override{return signal_animation(animations,h,s,false,this);}
    bool option_callback(PlayerState&,u32,u32)override{return false;}
    bool effect(i32,const std::array<float,3>&)override;
    bool cancel_circle(const std::array<float,3>&,float,i32)override;
    bool cancel_lasers(const std::array<float,3>&,float,i32,bool)override;
    bool cancel_all_lasers(i32,bool)override;
    bool lives_changed(i32 n,u32 f)override{return services.gameplay_lives(n,f);}
    bool bombs_changed(u32 n,u32 f)override{return services.gameplay_bombs(n,f);}
    bool game_over(bool replay)override{return services.gameplay_game_over(replay);}
    bool retire_visual(u32 h)override{return animations.mark_retirement(h);}
    bool shoot(PlayerState&,PlayerFrameGlobals&)override;
    bool update_shots(PlayerState&)override;
    bool create_shot_visual(u32,i32,u32&)override;
    AnmView shot_visual(u32 h)override{return animations.find(h);}
    bool retire_shot_visual(u32 h)override{return animations.mark_retirement(h);}
    bool shot_vertices(AnmView,std::array<std::array<float,2>,4>&)override;
    bool shot_sound(i32 id,float x)override{return sound(id,true,x);}
    bool shot_callback(u32,bool,PlayerState&,u32,i32,i32&)override{return false;}
    AnmView impact_visual(u32 h)override{return animations.find(h);}
    bool impact_animation_callback(u32,AnmView,i32)override;
    bool specialized_impact(u32,PlayerState&,u32,const PlayerShotImpactQuery&,i32&)override{return false;}
    bool cheat_damage(const PlayerShotImpactQuery&,i32&)override{return false;}
    bool area_callback(u32,PlayerState&,u32,const PlayerShotImpactQuery&,i32&)override{return false;}
    bool actor_callback(u32,ActorState&,i32&)override;
    void frame_rate(float v)override{animations.rate=v;}
    bool sound(i32 id,float x)override{return sound(id,true,x);}
    bool resource(i32,u32&)override;
    bool visual_script(AnmView,i32)override;
    bool body_circle(const std::array<float,3>&,float,i32&)override;
    bool body_rectangle(const std::array<float,3>&,float,float,float,i32&)override;
    bool body_graze()override;
    bool sprite(u32 r,i32 i,u32& p,std::array<u32,17>& d)override{return animations.sprite(r,i,p,d);}
    bool fallback_sprite(u32& r,i32& i)override{return animations.fallback_sprite(r,i);}
    bool bullet_style(u32,i32&,i32&)override;
    bool script(u32 r,i32 i,u32& p,u16& f,bool& ready)override{return animations.script(r,i,p,f,ready);}
    bool script_bound()override{
        //473f01 records embedded script binds in the actual ANM manager.
        if(animations.pool){auto manager=animations.pool->view();manager.put(0xc0,manager.get(0xc0)+1);}
        return true;
    }
    Rng* script_rng()override{return &animations.animation_rng;}
    bool player_position(float&,float&)override;
    bool aim_position(float&,float&)override;
    bool launch_sound(i32 id,float x)override{return sound(id,true,x);}
    bool paused()const override{return (root_flags&2)!=0;}
    bool sprite_dimensions(u32,float&,float&)override;
    i32 collision(BulletView,bool)override;
    i32 animate(BulletView,u32)override;
    void retire(BulletView)override;
    bool cancellation_effect(BulletView)override;
    bool update(BulletView,u32,i32&)override;
    bool forced_contact(BulletView,u32)override;
    bool hit(PlayerState& p)override{return player_hit(p,*this,animations.global_rate_token());}
    bool graze(PlayerState&,const std::array<float,3>&)override;
    bool cancellation_visual(i32,const std::array<float,3>&,const std::array<float,3>&)override;
    bool bind(AnmView,u32,i32)override;
    bool animate(AnmView vm)override{return anm_step(vm,static_cast<AnmWorld&>(animations))!=-2;}
    bool collect(i32,const std::array<float,3>&)override;
    bool position_visual(u32,const std::array<float,3>&)override;
    bool retire_visual(u32 h,i32 signal)override{return signal_animation(animations,h,signal,false,this);}
    void homing_type(i32 type)override{rewards.homing(type);game[35]=rewards.chain;}
    bool sound(i32,bool,float)override;
    bool item(i32,const std::array<float,3>&,float,float)override;
    bool update_equipment_option(u32)override;
    bool draw_equipment_option(u32)override;
    bool equipment_option_busy(u32,bool&)override;
    bool equipment_option_count(u32,u32&)override;
    bool equipment_empty_sound(u32 id)override{return sound(i32(id),false,0);}
    bool cloak_option_view(u32 p,AnmView& out)override{out=option(p);return out.data;}
    bool cloak_option_busy(u32 p,bool& out)override{return equipment_option_busy(p,out);}
    bool cloak_alternate_release()override{return bomb_alternate_release();}
    bool cloak_sound(u32 id,float x)override{return sound(i32(id),true,x);}
    // Countdown text belongs to the draw pass, which this update bridge does
    // not yet dispatch. Reject it until an actual ASCII renderer is bound.
    bool cloak_countdown(const std::array<float,3>&,double)override{return false;}
    bool camera_enemy(bool&,bool&,std::array<float,3>&)override;
    bool orb_target(std::array<float,3>& p)override{bool present,exists;if(!camera_enemy(present,exists,p)||!present)return false;if(!exists)p={0,192,0};return true;}
    bool camera_rate(float value)override{animations.rate=value;return true;}
    bool camera_surface(u32&,AnmView&,std::array<float,2>&)override;
    bool camera_surface_view(u32,AnmView&,std::array<float,2>&)override;
    bool camera_request_capture()override{auxiliary.independent.signals|=2;return true;}
    bool camera_photo(i32,u32&)override;
    bool camera_bullets(AnmView,const std::array<float,3>&,float)override;
    bool camera_lasers(AnmView p,const std::array<float,3>& size,float angle)override{auto v=AnmView{owners.lasers.data()};for(u32 i=0;i<3;++i){v.put(0x5dc+i*4,p.get(i*4));v.put(0x5e8+i*4,word(size[i]));}i32 result;return cancel_lasers_rectangle(GameOwnerRuntime::laser_self,GameOwnerRuntime::laser_self+0x5dc,GameOwnerRuntime::laser_self+0x5e8,angle,*this,result);}
 bool laser_cancel_rectangle_virtual(u32 beam,u32 position,u32 size,float angle,i32& result)override{std::array<float,3> p,s;return read(position,p.data(),12)&&read(size,s.data(),12)&&lasers.rectangle(beam,p,s,angle,0,false,result);}
    bool bomb_option_busy(u32 p,bool& v)override{return equipment_option_busy(p,v);}
    bool bomb_alternate_release()override;
    bool bomb_sound(u32 id,float x)override{return sound(i32(id),true,x);}
    bool bomb_stop_sound(u32)override;
    bool bomb_sound_unpositioned(u32 id)override{return sound(i32(id),false,0);}
    bool bomb_bullets(AnmView p,float r)override{return cancel_circle({p.floating(0),p.floating(4),p.floating(8)},r,0);}
    bool bomb_lasers(AnmView p,float r)override{return cancel_lasers({p.floating(0),p.floating(4),p.floating(8)},r,0,false);}
    bool laser_read(u32 p,void* o,u32 n)override{return read(p,o,n);}
    bool laser_write(u32 p,const void* o,u32 n)override{return write(p,o,n);}
    bool laser_virtual(u32 p,u32 s,bool h,u32 a,i32& r)override{return lasers.invoke(p,s,h,a,r);}
    bool laser_release(u32 p)override{return lasers.release(p);}
    bool laser_cancel_read(u32 p,void* o,u32 n)override{return read(p,o,n);}
    bool laser_cancel_write(u32 p,const void* o,u32 n)override{return write(p,o,n);}
    bool laser_reset_write(u32 p,const void* in,u32 n)override{return write(p,in,n);}
 bool laser_full_read(u32 p,void* out,u32 n)override{return read(p,out,n);}
 bool laser_full_virtual(u32 b,i32 k,bool items,i32& result)override{return lasers.full(b,k,items,result);}
 bool laser_cancel_virtual(u32 b,u32 p,float r,i32 k,bool i,i32& out)override{std::array<float,3> position;return read(p,position.data(),12)&&lasers.circle(b,position,r,k,i,out);}
    bool alternate_read(u32 p,void* o,u32 n)override{return read(p,o,n);}
    bool alternate_write(u32 p,const void* o,u32 n)override{return write(p,o,n);}
    bool alternate_cheat_view(u32 p,AnmView& out)override{out=p==GameCheatRuntime::self?cheat.view():AnmView{nullptr};return out.data;}
    bool alternate_bullet_circle(u32,float,i32)override;
    bool alternate_beam_circle(u32 b,u32 p,float r,i32 k,bool i)override{i32 result;return laser_cancel_virtual(b,p,r,k,i,result);}
    bool begin_cancelled_actor(ActorState&,EclOwner&)override;
    bool end_cancelled_actor()override;
    bool death_sound(i32 id,float x)override{return sound(id,true,x);}
    bool death_resource(i32 i,u32& out)override{return resource(i,out);}
    bool death_script_name(u32,const char*&)override;
    bool death_callback(u32,ActorState&,EclOwner&)override{return false;}
    bool animation_signal_callback(u32,AnmView,i32)override;
};
}
