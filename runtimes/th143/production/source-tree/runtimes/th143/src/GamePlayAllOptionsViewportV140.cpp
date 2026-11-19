#include "AsciiQueue.hpp"
#include "AsciiFormat.hpp"
#include "EnemyVisualPositionBinding.hpp"
#include "BulletEnemyTransform.hpp"
#include "EnemyVisualScaleDecay.hpp"
#include "BulletSoundTransform.hpp"
#include "BulletSpawnTransform.hpp"
#include "PlayerRotatedCollision.hpp"
#include "BulletTransformCancel.hpp"
#include "BulletBoundaryBounceRuntime.hpp"
#include "EnemyBulletCircleActivate.hpp"
#include "EnemyBulletRectangleBounce.hpp"
#include "GamePlayAllOptionsNov14.hpp"
#include "AnmQuad.hpp"
#include "BulletDirectionChange.hpp"
#include "BulletCartesianAcceleration.hpp"
#include "BulletVelocityApproach.hpp"
#include "BulletAppearanceTransform.hpp"
#include <cmath>
#include "AnmRotatedQuad.hpp"
namespace th143 {
GamePlayAllOptionsNov14Runtime::GamePlayAllOptionsNov14Runtime(GameOwnerRuntime& o,GameEnemyStartup& e,GameEnemyRuntime& er,GameCheatRuntime& c,GameAuxRuntime& a,GameHudRuntime& h,AnmResourceWorld& w,SoundQueue& q,std::array<u32,40>& g,Rng& r,GamePlayServices& s,GameOwnerServices& allocation,GameRenderRuntime& renderer,GameRenderDevice& device)
    :owners(o),enemies(e),enemy(er),cheat(c),auxiliary(a),hud(h),animations(w),audio(q),game(g),random(r),services(s),lasers(o,w,allocation,q,renderer,device),combat({w,er.program,o.player,o.shots,shooting,shot_globals,*this,enemy_globals,o.items,r},*this),cancellation(w,o.bullets,o.items,r,*this),clear_cancellation(w,o.bullets,o.items,r,*this),camera_rectangles(w,o.bullets,o.items,r,*this),bomb(cancellation,static_cast<PlayerCameraHost&>(*this)){lasers.rectangle_contact=[this](const std::array<float,3>& p,float length,float width,float angle,bool forced,i32& result){result=player_rotated_rectangle_collision(owners.player,hud.view().get(0x198)!=0,p,length,width,angle,forced,static_cast<BulletContactHost&>(*this));return result!=-2;};lasers.graze_effect=[this](const std::array<float,3>& p){return graze(owners.player,p);};lasers.item_effect=[this](const std::array<float,3>& p,i32 kind){return cancellation.item(p,kind,auxiliary.special_view().get(0x7c));};}
void GamePlayAllOptionsNov14Runtime::bind(GameFrameRuntime& f){lasers.boss_position=[this](std::array<float,3>& p,bool& present){const u32 token=enemies.scripts.controls.bosses[0];present=token!=0;if(!present)return true;for(auto& a:enemies.scripts.storage)if(a->token==token){for(u32 i=0;i<3;++i)p[i]=a->state.fields.floating(0x44+i*4);return true;}return false;};bind_enemy_visual_positions(enemies.scripts,[this](u32 h){return animations.find(h);},[this]{return animations.rate;});bind_bullet_enemy_transform(static_cast<BulletFactoryHost&>(*this),[this](u32 name,const EnemySpawn& descriptor){
    std::string script;bool terminated=false;for(u32 i=0;i<256;++i){char c;if(!enemy.read(name+i,&c,1))return false;if(!c){terminated=true;break;}script.push_back(c);}if(!terminated)return false;
    if(!enemies.scripts.spawn_enemy(script.c_str(),descriptor))return false;enemies.publish();return animations.synchronize_resources();});bind_bullet_sound_transform(static_cast<BulletFactoryHost&>(*this),[this](i32 id,float x){return sound(id,true,x);});bind_bullet_spawn_transform(static_cast<BulletFactoryHost&>(*this),
 [this](const u8* parameters,u32 bytes){return launch(parameters,bytes,0);},
 [this](BulletView b,i32 kind){const auto offset=b.data-owners.bullets.data.data();return offset>=BulletPool::first&&offset<0x9bf6c0&&cancellation.single(BulletPool::token(u32(offset)),kind,auxiliary.special_view().get(0x7c));});
bind_enemy_animation_scratch(enemies.scripts,&lasers.contact_scratch,enemy.global_owner);bind_enemy_curve_scratch(enemies.scripts,&lasers.kind2_contact_z_scratch);bind_bullet_transform_cancel(static_cast<BulletFactoryHost&>(*this),[this](BulletView b,i32 kind){const auto offset=b.data-owners.bullets.data.data();return offset>=BulletPool::first&&offset<0x9bf6c0&&cancellation.single(BulletPool::token(u32(offset)),kind,auxiliary.special_view().get(0x7c));});auto transform_sound=[this](i32 id){return sound(id,false,0);};bind_bullet_boundary_bounce(static_cast<BulletFactoryHost&>(*this),owners.bullets,transform_sound);bind_bullet_transform_sound(static_cast<BulletFactoryHost&>(*this),transform_sound);bind_bullet_cartesian_services(static_cast<BulletFactoryHost&>(*this),[this](BulletView b,float& angle){float x,y;if(!aim_position(x,y))return false;x-=b.floating(0xbc0);y-=b.floating(0xbc4);if(!std::isfinite(x)||!std::isfinite(y))return false;angle=x==0.f&&y==0.f?real(0x3fc90fdb):float(std::atan2(double(y),double(x)));return true;},transform_sound);bind_bullet_velocity_approach_services(static_cast<BulletFactoryHost&>(*this),[this](BulletView b,float& angle){float x,y;if(!aim_position(x,y))return false;x-=b.floating(0xbc0);y-=b.floating(0xbc4);if(!std::isfinite(x)||!std::isfinite(y))return false;angle=x==0.f&&y==0.f?real(0x3fc90fdb):float(std::atan2(double(y),double(x)));return true;},transform_sound);bind_bullet_direction_change(static_cast<BulletFactoryHost&>(*this),{&random,[this](const std::array<float,3>& p,float& angle){float x,y;if(!aim_position(x,y))return false;x-=p[0];y-=p[1];if(!std::isfinite(x)||!std::isfinite(y))return false;angle=x==0.f&&y==0.f?real(0x3fc90fdb):float(std::atan2(double(y),double(x)));return true;},transform_sound});bind_bullet_appearance_transform(static_cast<BulletFactoryHost&>(*this),[this](BulletView b,u32 row){const auto offset=b.data-owners.bullets.data.data();if(offset<BulletPool::first||offset>=0x9bf6c0)return false;return change_bullet_appearance(b,row,BulletPool::token(u32(offset)),owners.bullets.get(0x9bf6cc),*this);});f.player_globals=&player_globals;f.player_host=this;f.bullet_host=this;f.item_player=&item_player;f.item_host=this;f.equipment_host=this;f.fresh=&fresh;f.enemies=&enemies.scripts;f.laser_host=this;f.special_flags=reinterpret_cast<const u32*>(auxiliary.special.data()+0x7c);enemies.scripts.combat=&combat;}
AnmView GamePlayAllOptionsNov14Runtime::option(u32 token){for(auto& s:owners.storage)if(token>=s.token&&token-s.token<s.bytes.size())return {s.bytes.data()+token-s.token};return {nullptr};}
bool GamePlayAllOptionsNov14Runtime::read(u32 p,void* out,u32 n){return owners.read(p,out,n)||enemy.read(p,out,n)||auxiliary.read(p,out,n);}
bool GamePlayAllOptionsNov14Runtime::write(u32 p,const void* in,u32 n){return owners.write(p,in,n)||auxiliary.write(p,in,n);}
bool GamePlayAllOptionsNov14Runtime::refresh_actors(){std::vector<SceneCancellation::Actor> actors;for(auto* a:enemies.scripts.live)actors.push_back({a->token,&a->state,&a->owner,a->death_callback});return cancellation.bind_actors(actors)&&camera_rectangles.bind_actors(actors);}
bool GamePlayAllOptionsNov14Runtime::before(u32 entry,u32 flags){
    root_flags=flags;animations.effect_resource=auxiliary.effects_view().get(0x10);fresh=owners.input.fresh();
    if(entry==0x450820)return refresh_actors();
    if(entry==0x44e3d0){
        // Shot vertices include the ANM viewport origin; clip in that same space.
        shooting.viewport_origin={animations.viewport.first_origin[0]-192,animations.viewport.first_origin[1]};
        auto& p=player_globals;p.input={owners.input.held(),enemy.view().get(0xd8)!=0,secondary_mode==1,signed_word(game[9]),animations.rate};p.message=hud.view().get(0x198)!=0;p.root_flags=flags;p.game_mode=owners.input.manager.view().get(0x10);p.lives=signed_word(game[27]);p.life_fragments=game[28];p.bombs=game[30];p.bomb_fragments=game[31];p.deaths=enemy.view().get(0x10);p.death_flag=enemy.view().get(0x18);
        for(u32 i=0;i<12;++i){p.sound_ids[i]=signed_word(audio.view().get(i*4));p.sound_parameters[i]=audio.view().get(0x30+i*4);}return refresh_actors();
    }
    if(entry==0x41edb0&&!(flags&0x407)){enemy.view().put(0x24,0);enemy.view().put(0x28,0);shot_globals.score=game[2];shot_globals.cheat_active=secondary_mode==1;enemy_globals.cheat_mode=secondary_mode;enemy_globals.hud_blocked=hud.view().get(0x198)!=0;enemy_globals.phase={auxiliary.special_view().get(0x7c),enemy.view().get(0x18),signed_word(hud.view().get(0x1a0)),signed_word(hud.view().get(0x1a4))};}
    if(entry==0x435fd0){const auto& p=owners.player;item_player.state=p.get(0x684);for(u32 i=0;i<3;++i)item_player.position[i]=p.floating(0x5e0+i*4);for(u32 i=0;i<4;++i){item_player.collect[i]=p.floating((i<2?0x18310:0x18314)+i*4);item_player.magnet[i]=p.floating((i<2?0x18340:0x18344)+i*4);item_player.focused_magnet[i]=p.floating((i<2?0x18328:0x1832c)+i*4);}item_player.speed=owners.shots.floating(8);item_player.keys=owners.input.held();item_player.attract_all=(secondary_mode==1&&signed_word(secondary_time)<60)||hud.view().get(0x198);rewards={game[23],game[2],game[35]};}
    return true;
}
bool GamePlayAllOptionsNov14Runtime::after(u32 entry){
    if(entry==0x44e3d0){const auto& p=player_globals;game[27]=u32(p.lives);game[28]=p.life_fragments;game[30]=p.bombs;game[31]=p.bomb_fragments;enemy.view().put(0x10,p.deaths);enemy.view().put(0x18,p.death_flag);for(u32 i=0;i<12;++i){audio.view().put(i*4,u32(p.sound_ids[i]));audio.view().put(0x30+i*4,p.sound_parameters[i]);}}
    if(entry==0x41edb0&&!(root_flags&0x407)){enemies.publish();enemy.view().put(0x28,enemy_globals.normal_damage);enemy.view().put(0x24,enemy_globals.bomb_damage);enemy.view().put(0x18,enemy_globals.phase.manager_phase);auxiliary.special_view().put(0x7c,enemy_globals.phase.special_flags);hud.view().put(0x1a0,u32(enemy_globals.phase.countdown_seconds));hud.view().put(0x1a4,u32(enemy_globals.phase.countdown_hundredths));game[2]=shot_globals.score;
        if(!(root_flags&0x407)){auto v=enemy.view();const u32 old=v.get(0xbc),rate=v.get(0xc4);float elapsed=1;if(rate&&!animations.timer_rate(rate,elapsed))return false;const bool unit=!rate||(elapsed>real(0x3f7d70a4)&&elapsed<real(0x3f8147ae));const float value=v.floating(0xc0)+(unit?1.f:elapsed);v.put(0xb8,old);v.put(0xbc,unit?old+1:value>=-2147483648.f&&value<2147483648.f?u32(i32(value)):0x80000000);v.put(0xc0,word(value));}}
    if(entry==0x435fd0){game[23]=rewards.count;game[2]=rewards.score;game[35]=rewards.chain;}
    return !failed;
}
bool GamePlayAllOptionsNov14Runtime::bind_player(PlayerState& p,i32 script){auto* r=animations.resource(p.get(0x10));if(!r||script<0||u32(script)>=r->templates.size())return false;AnmView vm{p.data.data()+0x14};anm_copy_template(vm,GameOwnerRuntime::player_self+0x14,{r->templates[u32(script)].data()},animations.global_rate_token());return true;}
bool GamePlayAllOptionsNov14Runtime::bind_player_visual(PlayerState& p,i32 script){if(!bind_player(p,script))return false;p.put(0x14+0x594,0);return update_player_visual(p);}
bool GamePlayAllOptionsNov14Runtime::update_player_visual(PlayerState& p){return anm_step({p.data.data()+0x14},static_cast<AnmWorld&>(animations))!=-2;}
bool GamePlayAllOptionsNov14Runtime::create_focus(i32 script,u32& handle){return animations.create_at(animations.effect_resource,script,14,{0,0,0},handle);}
bool GamePlayAllOptionsNov14Runtime::effect(i32 script,const std::array<float,3>& p){u32 handle;return animations.create_effect(script,p,handle);}
bool GamePlayAllOptionsNov14Runtime::cancel_circle(const std::array<float,3>& p,float r,i32 k){return cancellation.circle(p,r,k,false,auxiliary.special_view().get(0x7c));}
bool GamePlayAllOptionsNov14Runtime::cancel_lasers(const std::array<float,3>& p,float r,i32 kind,bool items){for(u32 i=0;i<3;++i)AnmView{owners.lasers.data()}.put(0x5dc+i*4,word(p[i]));i32 result;return cancel_lasers_circle(GameOwnerRuntime::laser_self,GameOwnerRuntime::laser_self+0x5dc,r,kind,items,*this,result);}
bool GamePlayAllOptionsNov14Runtime::cancel_all_lasers(i32 kind,bool items){i32 result;return cancel_lasers_full(GameOwnerRuntime::laser_self,kind,items,*this,result);}
bool GamePlayAllOptionsNov14Runtime::shoot(PlayerState& p,PlayerFrameGlobals& g){shooting.self=GameOwnerRuntime::player_self;shooting.keys=g.input.keys;shooting.alternate=game[14]!=0;shooting.equipment=signed_word(game[9]);shooting.power=signed_word(game[20]);shooting.power_step=i32(owners.power.step);return player_shoot(p,owners.shots,shooting,*this);}
bool GamePlayAllOptionsNov14Runtime::update_shots(PlayerState& p){return player_update_shots(p,owners.shots,shooting,*this);}
bool GamePlayAllOptionsNov14Runtime::create_shot_visual(u32 resource,i32 script,u32& handle){return animations.create_at(resource,script,-1,{0,0,0},handle);}
bool GamePlayAllOptionsNov14Runtime::shot_vertices(AnmView vm,std::array<std::array<float,2>,4>& out){const u32 mode=(vm.get(0x18)>>25)&31;if(mode>3)return false;AnmQuad quad;if(!(mode==1?anm_rotated_quad_position(vm,animations.viewport,animations,quad):anm_quad_position(vm,animations.viewport,animations,quad)))return false;for(u32 i=0;i<4;++i){AnmView v{quad.vertices[i].data()};out[i]={v.floating(0),v.floating(4)};}return true;}
bool GamePlayAllOptionsNov14Runtime::impact_animation_callback(u32 entry,AnmView vm,i32 signal){i32 result;return signal==1&&animations.callback(entry,vm,animations.rate,result);}
bool GamePlayAllOptionsNov14Runtime::resource(i32 file,u32& token){if(file<0||file>=6)return false;token=enemy.view().get(0xa0+file*4);return token!=0;}
bool GamePlayAllOptionsNov14Runtime::visual_script(AnmView vm,i32 script){return anm_bind_script(vm,vm.get(0x30),script,*this);}
bool GamePlayAllOptionsNov14Runtime::body_circle(const std::array<float,3>& p,float r,i32& result){result=player_circle_collision(owners.player,owners.shots.floating(4),hud.view().get(0x198)!=0,p[0],p[1],r,false,*this);return result!=-2;}
bool GamePlayAllOptionsNov14Runtime::body_rectangle(const std::array<float,3>& p,float l,float w,float a,i32& result){result=player_rotated_rectangle_collision(owners.player,hud.view().get(0x198)!=0,p,l,w,a,false,*this);return result!=-2;}
bool GamePlayAllOptionsNov14Runtime::body_graze(){auto& p=owners.player;return graze(p,{p.floating(0x5e0),p.floating(0x5e4),p.floating(0x5e8)});}
bool GamePlayAllOptionsNov14Runtime::bullet_style(u32 token,i32& type,i32& color){if(token<BulletPool::bullet(0)||token>=BulletPool::bullet(BulletPool::count))return false;const u32 value=owners.bullets.get(BulletPool::offset(token)+0x13ec);type=std::int16_t(value);color=std::int16_t(value>>16);return true;}
bool GamePlayAllOptionsNov14Runtime::player_position(float& x,float& y){x=owners.player.floating(0x5e0);y=owners.player.floating(0x5e4);return true;}
bool GamePlayAllOptionsNov14Runtime::aim_position(float& x,float& y){const auto& p=owners.player;const u32 at=p.get(0x1847c)&0x100?0x184b4:0x5e0;x=p.floating(at);y=p.floating(at+4);return true;}
bool GamePlayAllOptionsNov14Runtime::sprite_dimensions(u32 p,float& w,float& h){std::array<u32,17> d;if(!animations.read(p,d.data(),68))return false;w=real(d[14]);h=real(d[13]);return true;}
i32 GamePlayAllOptionsNov14Runtime::collision(BulletView b,bool forced){return bullet_contact(b,owners.player,owners.shots.floating(4),hud.view().get(0x198)!=0,forced,animations.rate,*this);}
i32 GamePlayAllOptionsNov14Runtime::animate(BulletView b,u32 slot){return anm_step({b.data+(slot?0x5f4:0x28)},*this);}
void GamePlayAllOptionsNov14Runtime::retire(BulletView b){const auto offset=b.data-owners.bullets.data.data();if(offset<BulletPool::first||offset>=0x9bf6c0||!owners.bullets.release(BulletPool::token(u32(offset)),animations.global_rate_token()))failed=true;}
bool GamePlayAllOptionsNov14Runtime::cancellation_effect(BulletView b){const auto at=b.data-owners.bullets.data.data();return at>=BulletPool::first&&cancellation.single(BulletPool::token(u32(at)),1,auxiliary.special_view().get(0x7c));}
bool GamePlayAllOptionsNov14Runtime::update(BulletView b,u32,i32& result){result=bullet_step(b,animations.rate,*this);return result!=-2&&!failed;}
bool GamePlayAllOptionsNov14Runtime::forced_contact(BulletView b,u32){return collision(b,true)!=-2&&!failed;}
bool GamePlayAllOptionsNov14Runtime::graze(PlayerState& p,const std::array<float,3>& position){effects={game[6],owners.items.get(0xde21d8),random};const bool result=player_graze(p,position,effects,*this);game[6]=effects.graze;owners.items.put(0xde21d8,effects.item_graze_counter);random=effects.gameplay_rng;return result;}
bool GamePlayAllOptionsNov14Runtime::cancellation_visual(i32 script,const std::array<float,3>& p,const std::array<float,3>& target){return animations.cancel_bullet(owners.bullets.get(0x9bf6cc),script,p,target);}
bool GamePlayAllOptionsNov14Runtime::bind(AnmView vm,u32 self,i32 type){auto* r=animations.resource(owners.bullets.get(0x9bf6cc));const i32 script=type==13?103:type==14?104:-1;if(!r||script<0||u32(script)>=r->templates.size())return false;anm_copy_template(vm,self,{r->templates[u32(script)].data()},animations.global_rate_token());return true;}
bool GamePlayAllOptionsNov14Runtime::collect(i32 type,const std::array<float,3>& p){return rewards.collect_delayed(type,p,owners.scores,animations.global_rate_token())&&sound(37,true,p[0]);}
bool GamePlayAllOptionsNov14Runtime::position_visual(u32 h,const std::array<float,3>& p){auto vm=animations.find(h);if(!vm.data)return true;for(u32 i=0;i<3;++i)vm.put(0x59c+i*4,word(p[i]));return true;}
void GamePlayAllOptionsNov14Runtime::publish_audio(){auto q=audio.view();for(u32 i=0;i<12;++i){player_globals.sound_ids[i]=signed_word(q.get(i*4));player_globals.sound_parameters[i]=q.get(0x30+i*4);}}
bool GamePlayAllOptionsNov14Runtime::sound(i32 id,bool spatial,float x){if(!services.gameplay_sound(u32(id),spatial,x)||!audio.request(u32(id),spatial,x))return false;publish_audio();return true;}
bool GamePlayAllOptionsNov14Runtime::item(i32 type,const std::array<float,3>& p,float a,float speed){owners.items.put(0xde21d8,effects.item_graze_counter);u32 result;return owners.items.spawn_delayed(type,p,a,speed,animations.global_rate_token(),result);}
bool GamePlayAllOptionsNov14Runtime::update_equipment_option(u32 token){
    auto vm=option(token);if(!vm.data)return false;
    const u32 table=vm.get(0);
    if(table==0x4c6d08||table==0x4c6d5c){
        PlayerCloakGlobals g{owners.input.held(),fresh,game[9]};
        return update_player_cloak(vm,table==0x4c6d5c,owners.equipment.view(),owners.player,cheat.view(),g,animations,*this);
    }
    if(table==0x4c6cd0||table==0x4c6d40){PlayerUmbrellaGlobals g;g.fresh=fresh;g.held=owners.input.held();g.primary=game[8];g.secondary=game[9];g.neutral_velocity=umbrella_neutral_velocity;return update_player_umbrella(vm,table==0x4c6d40,owners.equipment.view(),&owners.player,cheat.view(),g,animations,static_cast<PlayerUmbrellaHost&>(*this));}
    if(table==0x4c6c98){PlayerOrbGlobals g;g.fresh=fresh;g.held=owners.input.held();g.secondary=game[9];return update_player_orb(vm,owners.equipment.view(),&owners.player,cheat.view(),g,animations,static_cast<PlayerOrbHost&>(*this));}
    if(table==0x4c6cec){PlayerCameraGlobals g;g.fresh=fresh;g.held=owners.input.held();g.released=owners.input.released();g.secondary=game[9];g.screen_width=animations.width;g.viewport_scale=animations.viewport.scale;return update_player_camera(vm,owners.equipment.view(),&owners.player,cheat.view(),g,animations,*this);}
    PlayerBombGlobals other{fresh,game[9]};
    if(table==0x4c6cb4)return update_player_lantern(vm,owners.equipment.view(),&owners.player,cheat.view(),other,audio,animations,*this);
    if(table==0x4c6c60||table==0x4c6d24)return update_player_jizo(vm,table==0x4c6d24,owners.equipment.view(),&owners.player,cheat.view(),animations,*this);
    if(table==0x4c6c44)return update_player_decoy(vm,owners.equipment.view(),&owners.player,cheat.view(),other,animations,*this);
    if(table==0x4c6c28)return update_player_mallet(vm,owners.equipment.view(),&owners.player,cheat.view(),other,animations,static_cast<PlayerLanternHost&>(*this));
    if(table!=0x4c6c7c)return services.gameplay_other_option(token,false);
    bomb_input={fresh,game[9]};return bomb.update(vm,owners.equipment.view(),&owners.player,cheat.view(),bomb_input,auxiliary.special_view().get(0x7c),animations);
}
bool GamePlayAllOptionsNov14Runtime::draw_equipment_option(u32 token){
    auto vm=option(token);if(!vm.data)return false;const u32 table=vm.get(0);
    if(table==0x4c6cb4)return draw_player_lantern(vm,&owners.player,option_ascii,*this);
    if(table==0x4c6c60||table==0x4c6d24)return draw_player_jizo(vm,table==0x4c6d24,&owners.player,option_ascii,jizo_draw,*this);
    if(table==0x4c6c44)return draw_player_decoy(vm,option_ascii,*this);
    return table==0x4c6c28||table==0x4c6cd0||table==0x4c6d40||table==0x4c6c98||table==0x4c6c7c||table==0x4c6cec||services.gameplay_other_option(token,true);
}
bool GamePlayAllOptionsNov14Runtime::option_countdown(const std::array<float,3>& p,const char* format,double value){std::string text;return format_ascii_value(format,value,text)&&queue_ascii_text(option_ascii,p,text,animations.viewport);}
bool GamePlayAllOptionsNov14Runtime::jizo_remaining(const std::array<float,3>& p,i32 count){return queue_ascii_text(option_ascii,p,"&   "+std::to_string(count),animations.viewport);}

bool GamePlayAllOptionsNov14Runtime::equipment_option_busy(u32 token,bool& out){auto vm=option(token);if(!vm.data)return false;out=vm.get(0x1c)!=0;return true;}
bool GamePlayAllOptionsNov14Runtime::equipment_option_count(u32 token,u32& out){auto vm=option(token);if(!vm.data)return false;out=vm.get(0x18);return true;}
bool GamePlayAllOptionsNov14Runtime::bomb_alternate_release(){PlayerAlternateGlobals g{game[9],GameOwnerRuntime::player_self,GameOwnerRuntime::laser_self,cheat.global_owner};return release_player_alternate(g,animations,*this);}
bool GamePlayAllOptionsNov14Runtime::bomb_stop_sound(u32 id){auto q=audio.view();for(u32 i=0;i<12;++i){const i32 sound=signed_word(q.get(i*4));if(sound<0||u32(sound)==id){if(sound<0)q.put(i*4,id);q.put(0x30+i*4,0xffffffff);break;}}return true;}
bool GamePlayAllOptionsNov14Runtime::alternate_bullet_circle(u32 position,float radius,i32 kind){std::array<float,3> p;if(!read(position,p.data(),12))return false;return cancel_circle(p,radius,kind);}
bool GamePlayAllOptionsNov14Runtime::begin_cancelled_actor(ActorState& state,EclOwner& owner){for(auto& a:enemies.scripts.storage)if(&a->state==&state&&&a->owner==&owner){cancel_bindings.push_back(enemies.scripts.active);enemies.scripts.active=a.get();return true;}return false;}
bool GamePlayAllOptionsNov14Runtime::end_cancelled_actor(){if(cancel_bindings.empty())return false;enemies.scripts.active=cancel_bindings.back();cancel_bindings.pop_back();return true;}
bool GamePlayAllOptionsNov14Runtime::death_script_name(u32 p,const char*& name){for(const auto& file:enemy.program.files){const auto base=std::uintptr_t(file->bytes.data());if(p>=base&&std::uint64_t(p)<base+file->bytes.size()){const u32 at=u32(p-base);if(!std::memchr(file->bytes.data()+at,0,file->bytes.size()-at))return false;name=reinterpret_cast<const char*>(file->bytes.data()+at);return true;}}return false;}
bool GamePlayAllOptionsNov14Runtime::animation_signal_callback(u32 entry,AnmView vm,i32){i32 result;return animations.callback(entry,vm,animations.rate,result);}
bool GamePlayAllOptionsNov14Runtime::launch(const u8* p,u32 n,u32 forbidden){if(n<0x380)return false;owners.bullets.put(0x60,forbidden);BulletLaunchResult result;const bool okay=bullet_launch(owners.bullets,p,random,*this,result);owners.bullets.put(0x60,0);return okay&&!failed;}
}

namespace th143 {
bool GamePlayAllOptionsNov14Runtime::camera_enemy(bool& present,bool& exists,std::array<float,3>& p){present=enemy.global_owner!=0;exists=false;p={0,0,0};if(!present)return true;const u32 token=enemy.view().get(0x5c);if(!token)return true;for(const auto& a:enemies.scripts.storage)if(a->token==token){exists=true;for(u32 i=0;i<3;++i)p[i]=a->state.fields.floating(0x44+i*4);return true;}return false;}
bool GamePlayAllOptionsNov14Runtime::camera_surface(u32& token,AnmView& vm,std::array<float,2>& size){token=auxiliary.independent.animations[1];return camera_surface_view(token,vm,size);}
bool GamePlayAllOptionsNov14Runtime::camera_surface_view(u32 token,AnmView& vm,std::array<float,2>& size){
 vm={nullptr};for(auto& s:auxiliary.storage)if(token>=s.token&&std::uint64_t(token)+AnmView::bytes<=std::uint64_t(s.token)+s.bytes.size()){vm={s.bytes.data()+token-s.token};break;}if(!vm.data)return false;
 std::array<u32,18> sprite;if(!animations.read(vm.get(0x2c),sprite.data(),72))return false;size={real(sprite[8]),real(sprite[7])};return true;
}
bool GamePlayAllOptionsNov14Runtime::camera_photo(i32 script,u32& handle){return camera_overlay&&camera_overlay->create(animations,auxiliary.independent.resource,script,nullptr,0,-1,4,handle);}
bool GamePlayAllOptionsNov14Runtime::camera_bullets(AnmView p,const std::array<float,3>& size,float angle){return refresh_actors()&&camera_rectangles.rectangle({p.floating(0),p.floating(4),p.floating(8)},size,angle,0,auxiliary.special_view().get(0x7c));}

}

namespace th143 {bool GamePlayAllOptionsNov14Runtime::actor_callback(u32 entry,ActorState& actor,i32& result){if(entry==0x42a0b0){struct Scale:EnemyVisualScaleDecayHost{AnmResourceWorld& w;explicit Scale(AnmResourceWorld& a):w(a){}AnmView enemy_scale_animation(u32 h)override{return w.find(h);}} scale{animations};return decay_enemy_visual_scale({actor.fields.data.data()},animations.rate,scale,result);}if(entry==0x429da0)return enemy_bullet_circle_activate({actor.fields.data.data()},owners.bullets,[this](i32 id){return sound(id,false,0.f);},result);if(entry!=0x429ab0)return false;return enemy_bullet_rectangle_bounce({actor.fields.data.data()},owners.bullets,[this](i32 id){return sound(id,false,0.f);},result);}}
