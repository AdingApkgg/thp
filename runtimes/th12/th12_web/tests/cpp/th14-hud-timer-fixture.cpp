#include "../../cpp/game/Hud.hpp"
#include "../../cpp/game/AnmOpcodes.hpp"
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static AnmManager manager;static AnmResource front,text;static GameEconomy economy;
static EnemyCommandEnvironment enemies;static StageCompletionState completion;static EnemyState boss;
struct Sounds final:HudEffects{std::vector<i32> calls;bool hud_sound(i32 n)override{calls.push_back(n);return true;}};
static Sounds effects;static std::unique_ptr<Hud> hud;
API(run) u32 run(i32 seconds,i32 previous,i32 resources){
 hud.reset();manager.clear();front={};text={};enemies={};completion={};boss={};effects.calls.clear();
 front.scripts.resize(256);text.scripts.resize(4);text.sprites.resize(256);text.textures.resize(1);text.textures[0].width=text.textures[0].height=256;
 const AnmInstruction code[]={{i16(anm_canonical_opcode(2)),8,0,0},{-1,8,0,0}};
 for(auto* file:{&front,&text})for(auto& s:file->scripts){s.bytes.resize(sizeof code);std::memcpy(s.bytes.data(),code,sizeof code);}
 for(auto& s:text.scripts)reinterpret_cast<AnmInstruction*>(s.bytes.data())->opcode=i16(anm_canonical_opcode(3));
 hud=std::make_unique<Hud>(manager,front,text,economy,enemies,completion,effects);
 for(u32 i=0;i<2;++i){auto* ptr=manager.create(text,2+i,2,u32(-1));if(!ptr)return 0;hud->digit_handles[i]=ptr->id;auto& vm=*ptr;vm.pending_interrupt=0;vm.sprite_index=-1;if(!(resources&(1<<i)))vm.resource=nullptr;}
 boss.health=boss.max_health=1;enemies.bosses[0]=&boss;auto* name=manager.create(front,153,5,u32(-1));if(!name)return 0;hud->boss_name=name->id;hud->previous_seconds=previous;
 HudInput input;input.seconds=seconds;input.player_position={0,400,0};return hud->timer_th14(input)?1:0;
}
API(value) u32 value(u32 k){if(k<2)return u32(hud->digit_th14(k)->pending_interrupt);if(k<4)return u32(hud->digit_th14(k-2)->sprite_index);if(k==4)return u32(hud->previous_seconds);return effects.calls.size();}
API(sound) u32 sound(u32 k){return u32(effects.calls[k]);}
API(control_run) u32 control_run(i32 seconds,i32 previous,i32 mode,u32 flags,float y,i32 gate,i32 resources){
 if(!run(0,0,resources))return 0;effects.calls.clear();completion.hud_flags=0x80+mode*512;enemies.manager_flags=gate==2?1:0;enemies.bosses[0]=gate==1?nullptr:&boss;
 for(u32 n=0;n<2;++n){auto* vm=hud->digit_th14(n);vm->pending_interrupt=17;vm->sprite_index=-1;vm->flags&=~2u;vm->age.set(0,&manager.rate);}
 hud->previous_seconds=previous;HudInput input;input.seconds=seconds;input.spell_flags=flags;input.spell=flags&1;input.player_position={0,y,0};input.dialogue=gate==3;return hud->timer_th14(input)?1:0;
}
API(control_value) u32 control_value(u32 k){if(k<2)return hud->digit_th14(k)->pending_interrupt;if(k==2)return hud->previous_seconds;if(k==3)return completion.hud_flags;if(k<6)return hud->digit_th14(k-4)->flags&2;if(k<8)return hud->digit_th14(k-6)->age.current;return hud->digit_th14(k-8)->sprite_index;}
static std::unique_ptr<AsciiText> queued;
API(text_run) u32 text_run(i32 gate,i32 seconds,i32 hundredths,float x,float y,u32 color){
 if(!run(0,0,3))return u32(-1);queued=std::make_unique<AsciiText>(text);
 enemies.bosses[0]=gate==1||gate==2?nullptr:&boss;enemies.manager_flags=gate==3?1:0;
 hud->digit_th14(0)->script_position={x,y,0};hud->digit_th14(0)->color=color;
 HudInput input;input.seconds=seconds;input.hundredths=hundredths;input.dialogue=gate==4;
 if(!hud->timer_text_th14(*queued,input))return u32(-1);return queued->requests.size();
}
API(text_byte) u32 text_byte(u32 n,u32 k){const auto& s=queued->requests[n].text;return k<s.size()?u8(s[k]):0;}
API(text_word) u32 text_word(u32 n,u32 k){const auto& r=queued->requests[n];switch(k){case 0:return float_bits(r.position.x);case 1:return float_bits(r.position.y);case 2:return float_bits(r.position.z);case 3:return r.style.color;case 4:return float_bits(r.style.scale.x);case 5:return float_bits(r.style.scale.y);case 6:return r.style.font;default:return r.style.pass;}}
