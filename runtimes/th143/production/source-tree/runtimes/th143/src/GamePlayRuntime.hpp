#pragma once
#include "GameEnemyStartup.hpp"
#include "GameAuxRuntime.hpp"
#include "GameCheatRuntime.hpp"
#include "GameHudRuntime.hpp"
#include "EnemyCombat.hpp"
#include "PlayerBombScene.hpp"
#include "PlayerAlternate.hpp"
#include "PlayerCloak.hpp"
#include "PlayerRotatedCollision.hpp"
#include "PlayerEffects.hpp"
#include "ItemRewards.hpp"
#include "SoundQueue.hpp"
#include "LaserCancel.hpp"
#include "BulletFactory.hpp"
#include "BulletContact.hpp"
namespace th143 {
struct GamePlayServices {
    virtual ~GamePlayServices()=default;
    virtual bool gameplay_game_over(bool replay)=0;
    virtual bool gameplay_lives(i32,u32)=0;
    virtual bool gameplay_bombs(u32,u32)=0;
    virtual bool gameplay_sound(u32,bool,float){return true;}
    virtual bool gameplay_other_option(u32,bool){return false;}
    virtual bool gameplay_laser(u32,u32,bool,u32,i32&){return false;}
    virtual bool gameplay_laser_circle(u32,u32,float,i32,bool,i32&){return false;}
};
// Live shared-owner gameplay services. No actor, shot, emitter or pool states
// are supplied by the reference. Unsupported specialized callbacks reject.
class GamePlayRuntime final:private PlayerFrameHost,private PlayerShootingHost,
    private PlayerShotContactHost,private EnemyCombatServices,private BulletFactoryHost,
    private BulletManagerHost,private BulletContactHost,private ItemMotionHost,
    private PlayerEffectsHost,private PlayerEquipmentFrameHost,private PlayerBombHost,
    private LaserManagerHost,private LaserCancelHost,private PlayerAlternateHost,
    private SceneCancellationServices,private PlayerCloakHost {
    GameOwnerRuntime& owners;GameEnemyStartup& enemies;GameEnemyRuntime& enemy;
    GameCheatRuntime& cheat;GameAuxRuntime& auxiliary;GameHudRuntime& hud;
    AnmResourceWorld& animations;SoundQueue& audio;std::array<u32,40>& game;Rng& random;GamePlayServices& services;
public:
    GamePlayRuntime(GameOwnerRuntime&,GameEnemyStartup&,GameEnemyRuntime&,GameCheatRuntime&,
        GameAuxRuntime&,GameHudRuntime&,AnmResourceWorld&,SoundQueue&,std::array<u32,40>&,Rng&,GamePlayServices&);
    PlayerFrameGlobals player_globals;
    PlayerShootingConfig shooting;
    PlayerShotContactGlobals shot_globals;
    EnemyContactGlobals enemy_globals;
    ItemPlayer item_player;
    PlayerEffectGlobals effects;
    ItemRewards rewards;
    PlayerBombGlobals bomb_input;
    EnemyCombat combat;
    SceneCancellation cancellation;
    PlayerBombScene bomb;
    u32 fresh=0,root_flags=0,secondary_mode=0,secondary_time=0;
    bool failed=false;
    void bind(GameFrameRuntime&);
    bool before(u32 entry,u32 flags);
    bool after(u32 entry);
    bool launch(const u8* parameters,u32 bytes,u32 owner);
private:
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
    bool bomb_option_busy(u32 p,bool& v)override{return equipment_option_busy(p,v);}
    bool bomb_alternate_release()override;
    bool bomb_sound(u32 id,float x)override{return sound(i32(id),true,x);}
    bool bomb_stop_sound(u32)override;
    bool bomb_bullets(AnmView,float)override{return false;}
    bool bomb_lasers(AnmView p,float r)override{return cancel_lasers({p.floating(0),p.floating(4),p.floating(8)},r,0,false);}
    bool laser_read(u32 p,void* o,u32 n)override{return read(p,o,n);}
    bool laser_write(u32 p,const void* o,u32 n)override{return write(p,o,n);}
    bool laser_virtual(u32 p,u32 s,bool h,u32 a,i32& r)override{return services.gameplay_laser(p,s,h,a,r);}
    bool laser_release(u32)override{return false;}
    bool laser_cancel_read(u32 p,void* o,u32 n)override{return read(p,o,n);}
    bool laser_cancel_write(u32 p,const void* o,u32 n)override{return write(p,o,n);}
    bool laser_cancel_virtual(u32 b,u32 p,float r,i32 k,bool i,i32& out)override{return services.gameplay_laser_circle(b,p,r,k,i,out);}
    bool alternate_read(u32 p,void* o,u32 n)override{return read(p,o,n);}
    bool alternate_write(u32 p,const void* o,u32 n)override{return write(p,o,n);}
    bool alternate_cheat_view(u32 p,AnmView& out)override{out=p==GameCheatRuntime::self?cheat.view():AnmView{nullptr};return out.data;}
    bool alternate_bullet_circle(u32,float,i32)override;
    bool alternate_beam_circle(u32 b,u32 p,float r,i32 k,bool i)override{i32 result;return services.gameplay_laser_circle(b,p,r,k,i,result);}
    bool begin_cancelled_actor(ActorState&,EclOwner&)override;
    bool end_cancelled_actor()override;
    bool death_sound(i32 id,float x)override{return sound(id,true,x);}
    bool death_resource(i32 i,u32& out)override{return resource(i,out);}
    bool death_script_name(u32,const char*&)override;
    bool death_callback(u32,ActorState&,EclOwner&)override{return false;}
    bool animation_signal_callback(u32,AnmView,i32)override;
};
}
