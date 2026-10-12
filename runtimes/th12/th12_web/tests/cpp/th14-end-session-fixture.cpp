#include "../../cpp/game/GameSession.hpp"
#include "render-fixture.hpp"
#include <cstdlib>
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static GameResources source;
static GameSession session;
static test::RecordingGraphics graphics;
static AnmRenderer renderer(graphics);
struct Effects:StageResourceEffects {
    i32 pages=0,releases=0;u32 last_png_hash=0;
    bool prepare_manual_image(AnmResource& file,u32 texture,const u8* bytes,u32 size)override{
        if(texture!=1||file.textures.size()!=2||size<24||std::memcmp(bytes,"\x89PNG\r\n\x1a\n",8))return false;
        if(bytes[16]!=0||bytes[17]!=0||bytes[18]!=4||bytes[19]!=0||bytes[20]!=0||bytes[21]!=0||bytes[22]!=4||bytes[23]!=0)return false;
        ++pages;last_png_hash=anm_bytes_hash(bytes,size);return true;
    }
    void release_animation(AnmResource&)override{++releases;}
};
static Effects effects;
API(allocate) void* allocate(u32 n){return std::malloc(n);}
API(open_archive) i32 open_archive(const u8* p,u32 n){return source.open_archive(p,n);}
API(begin) i32 begin(){effects.pages=effects.releases=0;session.resources.effects=&effects;session.interactive=true;if(!session.begin(source,1,0,0,1))return 0;session.economy.lives=-1;session.battle->game_over_requested=true;return 1;}
API(begin_natural) i32 begin_natural(){effects.pages=effects.releases=0;session.resources.effects=&effects;session.interactive=true;return session.begin(source,1,0,0,1);}
API(begin_selection) i32 begin_selection(i32 character,i32 subtype){effects.pages=effects.releases=0;session.resources.effects=&effects;session.interactive=true;return session.begin(source,1,character,subtype,1);}
API(force_loss) void force_loss(){session.economy.lives=-1;session.battle->player->state.life_state=2;session.battle->player->state.state_timer.set(30,&session.animations.rate);session.battle->game_over_requested=true;}
API(tick) i32 tick(u32 held){return session.update({held});}
API(draw) i32 draw(){graphics.submissions.clear();graphics.snapshots.clear();graphics.data.clear();return session.draw(renderer);}
// Diagnostic archive firing coverage. Controlled stock and invulnerability
// do not validate natural gameplay, death, replay or score equivalence.
API(diagnostic_power) i32 diagnostic_power(i32 power){
 if(session.economy.power==power)return 1;session.economy.power=power;
 return session.battle&&session.battle->power_changed();
}
API(diagnostic_shot_tick) i32 diagnostic_shot_tick(u32 held){if(session.battle&&session.battle->player)session.battle->player->state.invincibility.set(120,&session.animations.rate);return session.update({held});}
API(shot_callbacks) u32 shot_callbacks(u32 selection,u32 kind){u32 mask=0;for(const auto& group:session.resources.core.shots[selection].groups)for(const auto& s:group.shots){const u32 n=kind==0?u32(s.spawn):kind==1?u32(s.update):s.extra_callback;if(n<32)mask|=1u<<n;}return mask;}
API(shot_observation) u32 shot_observation(u32 kind){
 if(!session.battle||!session.battle->player)return 0;auto& manager=session.battle->player->shots;u32 count=0;
 for(u32 j=0;j<256;++j){const auto& s=manager.at(j);if(kind==2){const auto* a=manager.th14_bomb_area(j);if((a->flags&1)&&a->moving)++count;}
  else if(s.spec&&s.state){if(kind==0&&u32(s.spec->spawn)==4)++count;if(kind==1&&s.spec->extra_callback==4&&s.state==2)++count;
   if(kind==3&&u32(s.spec->spawn)==3&&s.state==1)++count;
   if(kind==4&&u32(s.spec->spawn)==3&&s.hit_last_frame)++count;}}
 if(kind>=6&&kind<=8)for(u32 j=0;j<256;++j){const auto& s=manager.at(j);if(s.state&&s.spec&&u32(s.spec->spawn)==6&&((s.th14_shot_flags>>2)&15)==kind-6)++count;}
 if(kind==9||kind==10)for(auto* n=session.battle->enemies.first;n;n=n->next){const auto& e=n->value->state;if(kind==9&&e.th14_attached_knives>0)++count;if(kind==10&&e.th14_knife_slowdown>0)++count;}
 if(kind==11||kind==12)return u32(kind==11?manager.player.th14_cached_power:manager.player.th14_attached_count);
 if(kind==13)for(u32 j=0;j<256;++j){const auto* a=manager.th14_bomb_area(j);if((a->flags&3)==3&&a->callback==1&&a->period==2&&a->radius>0)++count;}
 if(kind>=14&&kind<=17)for(u32 j=0;j<256;++j){const auto& s=manager.at(j);if(!s.state||!s.spec)continue;
  if(kind==14&&u32(s.spec->update)==1&&s.target&&s.th14_target_id)++count;
  if(kind==15&&u32(s.spec->update)==8&&signed_bits(s.spec->native_tail[0])>=0&&s.timer.current>=signed_bits(s.spec->native_tail[0])&&s.movement.angle==-1.5707963705062866f)++count;
  if(kind==16&&s.spec->type==2&&s.state==1)++count;
  if(kind==17)++count;}
 if(kind==5)for(const auto& e:session.battle->events)if(e.kind==BattleEventKind::SoundPan&&e.value==20)++count;
 return count;
}
API(error) const char* error(){return session.error.c_str();}
API(reimu_observation) u32 reimu_observation(u32 kind){
 if(!session.battle||!session.battle->bomb)return 0;const auto& bomb=*session.battle->bomb;const auto& motion=session.battle->player->motion.state;
 if(kind==0)return u32(bomb.th14_reimu_allocated);if(kind==1)return u32(bomb.state.elapsed.current);
 if(kind==2)return float_bits(motion.position.x);if(kind==3)return float_bits(motion.th14_bomb_shift.x);
 if(kind==4)return session.battle->player->th14_scale.flags;
 if(kind>=5&&kind<37){const u32 i=(kind-5)/8,n=(kind-5)%8;const auto* a=session.battle->player->shots.th14_bomb_area(bomb.th14_reimu_areas[i]);if(!a)return 0;
  const u32 v[]={a->flags,u32(a->period),float_bits(a->position.x),float_bits(a->position.y),float_bits(a->angle),u32(a->timer.current),u32(a->damage),a->callback};return v[n];}
 return 0;
}
API(shot_detail) i32 shot_detail(u32 index,u32 kind){
 if(!session.battle||!session.battle->player||index>=256)return -1;
 auto& manager=session.battle->player->shots;const auto& s=manager.at(index);const auto& p=manager.player;
 if(!s.spec)return -1;const auto* vm=session.animations.find(s.animation);
 const i32 values[]={s.state,s.spec->type,s.spec->option,i32(manager.laser_active[s.spec->option]),p.power/p.power_step,p.option_count,manager.schedule.timer.current,i32(p.focused),p.th14_dialogue_blocked,p.th14_enemy_manager,i32(u32(s.spec->spawn)),i32(s.animation),bool(vm),vm?vm->pending_interrupt:-999,i32(s.th14_shot_flags)};
 return kind<15?values[kind]:-1;
}
API(value) i32 value(u32 n){
    if(n>=36&&n<=39&&session.battle&&session.battle->bomb){const auto& bomb=*session.battle->bomb;
        if(n==36)return bomb.state.active;if(n==37)return bomb.last_error;
        if(n==38)return bomb.create_script;return bomb.create_opcode;}
    if(n>=33&&n<=35&&session.battle){auto& hud=session.battle->hud;
        if(n==35){const auto* vm=hud.icon_th14(0);return vm?i32(vm->color>>24):-1;}
        i32 count=0;
        if(n==34){for(u32 i=0;i<16;++i)if(hud.icon_th14(i))++count;}
        else for(auto* vm=session.animations.layer_first(24);vm;vm=vm->draw_next)
            for(u32 i=0;i<16;++i)if(vm==hud.icon_th14(i))++count;
        return count;
    }
    if(n==0)return i32(session.state.phase);if(n==7)return effects.pages;if(n==8)return effects.releases;if(n==9)return effects.last_png_hash;
    if(n==12)return session.state.frame;if(n==13)return session.state.stage;
    if(n==32)return session.recording.stages[session.state.stage].frames;
    if(n==14)return session.economy.lives;if(n==15)return session.economy.life_fragments;if(n==16)return session.economy.th14_bombs;if(n==17)return session.economy.th14_bomb_fragments;if(n==18)return session.economy.power;if(n==19)return session.economy.score_units;
    if(session.battle){auto& b=*session.battle;if(n==20)return b.hud.score.continues;if(n==21)return u32(b.player.get());if(n==22)return u32(session.battle.get());if(n==23)return b.frame;if(n==24)return b.enemies.total_created;if(n==25)return b.bullets.active_count;if(n==26)return b.player->state.life_state;if(n==27)return session.animations.script_rng.seed;if(n==28)return b.enemies.timer.current;if(n==29)return b.enemies.count;if(n==30)return b.player->motion.state.option_count;if(n==31)return b.game_over_requested;}
    if(!session.pause_menu)return -1;const auto& m=*session.pause_menu;
    if(n==40)return m.name_cursor.selected;if(n==41)return m.name_length;
    if(n==1)return m.state;if(n==2)return m.cursor.count;if(n==3)return m.cursor.selected;if(n==4)return m.manual_substate;if(n==5)return m.manual_cursor.selected;if(n==6)return bool(m.manual_resource);
    const auto* vm=session.animations.find(m.menu_animation);if(n==10)return vm?vm->script_index:-1;if(n==11)return vm?vm->layer:-1;return -1;
}
