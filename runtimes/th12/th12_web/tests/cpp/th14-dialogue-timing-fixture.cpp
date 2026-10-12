#include "../../cpp/game/Dialogue.hpp"
#include "../../cpp/game/AnmOpcodes.hpp"
#include "../../cpp/game/GameInput.hpp"
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static GameInput input;
static AnmManager manager;static AnmResource resource;static std::vector<u8> message;static u32 state[12],sounds;
struct Effects:DialogueEffects{bool dialogue_sound(i32)override{++sounds;return true;}};static Effects effects;static std::unique_ptr<Dialogue> current;
static u32 bits(float v){u32 b;std::memcpy(&b,&v,4);return b;}
static void capture(const Dialogue& d,const u8* code=nullptr){if(!code)code=message.data()+12;const auto& s=d.state;const u32 words[]={s.flags,u32(s.release_signal),u32(s.next_line),u32(s.lines_initialized),u32(s.elapsed.current),bits(s.elapsed.fractional),u32(s.time.current),bits(s.time.fractional),u32(s.wait.current),bits(s.wait.fractional),u32(s.instruction-code),sounds};std::memcpy(state,words,sizeof state);}
API(begin_timing) i32 begin_timing(u32 flags,float rate,i32 duration,i32 profile){input={};if(profile==4||profile==6)for(u32 n=0;n<29;++n)input.update(profile==4?0x200:1);current.reset();manager.clear();manager.rate=rate;resource={};resource.scripts.resize(2);const AnmInstruction stop[]={{i16(anm_canonical_opcode(2)),8,0,0},{-1,8,0,0}};for(auto& script:resource.scripts){script.bytes.resize(sizeof stop);std::memcpy(script.bytes.data(),stop,sizeof stop);}message.resize(12);const u32 table[]={1,12,0};std::memcpy(message.data(),table,12);
 auto add=[](u16 time,u8 op,i32 size,i32 payload){message.push_back(u8(time));message.push_back(u8(time>>8));message.push_back(op);message.push_back(u8(size));if(size){const auto* p=reinterpret_cast<const u8*>(&payload);message.insert(message.end(),p,p+size);}};
 add(0,30,0,0);add(0,11,4,duration);add(8,12,0,0);add(10,11,4,duration+2);add(14,26,0,0);add(18,0,0,0);current=std::make_unique<Dialogue>(manager,resource,resource,resource,resource,resource,effects);if(!current->begin(message,0))return 0;current->state.flags=flags;current->state.release_signal=3;current->state.next_line=current->state.lines_initialized=1;sounds=0;capture(*current);return 1;}
API(step) i32 step(u32 held,u32 pressed,i32 skip,i32 fire){const auto result=current->update(held,pressed,u32(skip),u32(fire));if(result==0)current->state.elapsed.tick();capture(*current);return result;}
API(data) const u32* data(){return state;}

API(sample_step) i32 sample_step(u32 held,u32 pressed){input.update(held);return step(held,pressed,input.held_frames[9],input.held_frames[0]);}
