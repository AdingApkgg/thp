#include "../../cpp/game/Hud.hpp"
#include "render-fixture.hpp"
#include <cstdlib>
#include <cmath>
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static AnmManager manager;static AnmResource front,ascii,logo;static GameEconomy economy;static EnemyCommandEnvironment enemies;
static StageCompletionState completion;struct Effects:HudEffects{std::vector<i32> sounds;bool hud_sound(i32 n)override{sounds.push_back(n);return true;}};
static Effects effects;static std::unique_ptr<Hud> hud;static EnemyState boss[2];static HudInput input;
static test::RecordingGraphics graphics;static AnmRenderer renderer(graphics);
API(allocate) void* allocate(u32 n){return std::malloc(n);}
API(open) u32 open(u32 which,const u8* bytes,u32 size){return (which?ascii:front).open(bytes,size);}
API(begin) u32 begin(){hud.reset();manager.clear();manager.fallback_sprites=&ascii;manager.rate=1;enemies={};completion={};economy={};economy.difficulty=1;effects.sounds.clear();
 enemies.th14_run_flags=32; // This controlled resource test uses Spell Practice (no stage logo).
 if(!manager.prepare_resource(front,5)||!manager.prepare_resource(ascii,2))return 0;hud=std::make_unique<Hud>(manager,front,ascii,economy,enemies,completion,effects);input={};input.stage=1;input.section=5;input.player_position={0,400,0};input.seconds=-1;
 for(u32 n=0;n<2;++n){boss[n]={};boss[n].health=boss[n].max_health=1000;boss[n].current.position={float(n*80),80,0};for(u32 i=0;i<4;++i)enemies.th14_health_segments[n][i]={float(i)*.2f,i32(i)};}
 return hud->start_stage(logo,input,false,false,0,0);
}
API(configure) void configure(u32 present,u32 flags,i32 health,float y,u32 spell){for(u32 n=0;n<2;++n){enemies.bosses[n]=(present&(1u<<n))?&boss[n]:nullptr;boss[n].health=health;boss[n].flags=flags;}input.player_position.y=y;input.spell_flags=spell;input.spell=spell&1;input.seconds=present?60:-1;}
API(tick) u32 tick(){return hud->update(input)&&hud->finish_update(input)&&manager.update(false);}
API(digit_age) u32 digit_age(u32 n){auto* vm=hud->digit_th14(n);return vm?vm->age.current:u32(-1);}
API(digit_layer) u32 digit_layer(u32 n){auto* vm=hud->digit_th14(n);return vm?vm->layer:u32(-1);}
API(render) u32 render(){graphics.data.clear();graphics.submissions.clear();graphics.snapshots.clear();renderer.viewport={0,0,640,480,0,1};
 for(const auto& row:hud->th14_boss)for(auto id:row.handles)if(auto* vm=manager.find(id))if(renderer.draw(*vm)==-2)return 0;
 for(u32 n=0;n<2;++n)if(auto* vm=hud->digit_th14(n))if(renderer.draw(*vm)==-2)return 0;renderer.flush();return graphics.submissions.size();}
API(render_finite) u32 render_finite(){for(const auto& s:graphics.submissions)for(u32 i=0;i<s.size/s.stride;++i){const auto* p=reinterpret_cast<const float*>(graphics.data.data()+s.start+i*s.stride);for(u32 axis=0;axis<3;++axis)if(!std::isfinite(p[axis]))return 0;}return 1;}
API(ring_count) u32 ring_count(){u32 n=0;for(const auto& row:hud->th14_boss)for(auto id:row.handles)if(manager.find(id))++n;return n;}
API(state) u32 state(u32 n){return n<2?hud->th14_boss[n].active:n<4?hud->th14_boss[n-2].hidden:n<6?float_bits(hud->th14_boss[n-4].displayed):effects.sounds.size();}
API(sound) u32 sound(u32 n){return effects.sounds[n];}
