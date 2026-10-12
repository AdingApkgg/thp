#include "../../cpp/game/Ending.hpp"
#include "../../cpp/game/AnmOpcodes.hpp"
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static AnmManager manager;
static AnmResource resource,text;
static ScoreFile scores;
static Ending ending(manager,text,scores);
static std::array<u8,20> code;
static std::array<u32,15> result;
static std::array<u8,256> text_payload;
static std::array<u32,5> text_ids;
static std::vector<u8> text_code;
static std::array<u32,6> text_request_words;
static void append(i16 op,const void* args=nullptr,u32 count=0){
 auto& b=resource.scripts[1].bytes;const auto at=b.size();b.resize(at+8+count);const AnmInstruction h{op==-1?i16(-1):i16(anm_canonical_opcode(op)),u16(8+count),0,0};std::memcpy(b.data()+at,&h,8);if(count)std::memcpy(b.data()+at+8,args,count);
}
API(run) const u32* run(i32 op,i32 difficulty,u32 file,u32 slot,u32 program){
 manager.clear();resource={};resource.scripts.resize(2);
 if(program){const i32 layer=program==1?8:28;append(304,&layer,4);}
 if(program==2){const float p[]={3.25f,-7.5f,9.125f},r[]={.25f,-.5f,2.25f},s[]={2.5f,-3.25f};append(400,p,12);append(401,r,12);append(404,s,8);}
 append(2);append(-1);resource.scripts[0]=resource.scripts[1];
 auto* old=manager.create(resource,0,1,0);if(!old)return nullptr;const u32 id=old->id;
 ending.active=true;ending.flags=1;ending.difficulty=difficulty;ending.seen=0;ending.images.fill(0);ending.images[slot]=id;ending.slots.fill(nullptr);ending.slots[file]=&resource;
 ending.elapsed.set(0,&manager.rate);ending.time.set(0,&manager.rate);ending.wait.set(0,&manager.rate);
 code.fill(0);code[2]=u8(op);code[3]=12;const i32 args[]={i32(slot),i32(file),1};std::memcpy(code.data()+4,args,12);code[16]=255;code[17]=255;ending.instruction=code.data();ending.end=code.data()+code.size();
 if(!ending.update(0,0))return nullptr;const auto created=manager.find(id+1);
 result.fill(0);result[0]=u32(ending.instruction-code.data());result[1]=bool(old->flags2&32);result[2]=ending.images[slot]==id?100:ending.images[slot]==id+1?200:0;result[3]=created!=nullptr;
 if(created){const auto& v=*created;const u32 words[]={v.layer,v.flags2&0x60220,float_bits(v.position.x),float_bits(v.position.y),float_bits(v.position.z),float_bits(v.script_position.x),float_bits(v.script_position.y),float_bits(v.script_position.z),float_bits(v.rotation.z),float_bits(v.scale.x),float_bits(v.scale.y)};std::copy(std::begin(words),std::end(words),result.begin()+4);}
 return result.data();
}
API(file_id) i32 file_id(){auto* vm=manager.find(ending.images[0]);for(auto id:ending.images)if(auto* p=manager.find(id))vm=p;return vm?vm->file_index:-1;}
API(text_input) u8* text_input(){return text_payload.data();}
API(text_run) i32 text_run(u32 op,i32 line,u32 color,u32 size){
 manager.clear();resource={};resource.scripts.resize(2);append(2);append(-1);resource.scripts[0]=resource.scripts[1];
 for(u32 i=0;i<5;++i){auto* vm=manager.create(resource,0,0,0);if(!vm)return -1;text_ids[i]=ending.text_lines[i]=vm->id;}
 ending.active=true;ending.flags=1;ending.seen=0;ending.line=line;ending.color=color;ending.elapsed.set(0,&manager.rate);ending.time.set(0,&manager.rate);ending.wait.set(0,&manager.rate);
 const u32 n=op==3?size+1:0;text_code.assign(8+n,0);text_code[2]=u8(op);text_code[3]=u8(n);u8 key=0x77,step=7;
 for(u32 i=0;i<n;++i){text_code[4+i]=(i<size?text_payload[i]:0)^key;key=u8(key+step);step=u8(step+16);}
 text_code[4+n]=255;text_code[5+n]=255;ending.instruction=text_code.data();ending.end=text_code.data()+text_code.size();return ending.update(0,0)?0:-2;
}
API(text_state) u32 text_state(u32 n){if(n==0)return ending.line;if(n==1)return u32(ending.instruction-text_code.data());if(n==2)return ending.text_requests.size();return manager.find(text_ids[n-3])->pending_interrupt;}
API(text_request) const u32* text_request(u32 n){const auto& t=ending.text_requests[n];const auto found=std::find(text_ids.begin(),text_ids.end(),t.animation);text_request_words={u32(found-text_ids.begin()+100),t.color,u32(t.offset),u32(t.font),u32(t.style),u32(t.bytes.size())};return text_request_words.data();}
API(text_bytes) const char* text_bytes(u32 n){return ending.text_requests[n].bytes.data();}
API(music_run) const u8* music_run(u32 size,u32 initial){
 scores.settings.fill(u8(initial));ending.active=true;ending.flags=1;ending.elapsed.set(0,&manager.rate);ending.time.set(0,&manager.rate);ending.wait.set(0,&manager.rate);
 text_code.assign(size+9,0);text_code[2]=10;text_code[3]=u8(size+1);std::memcpy(text_code.data()+4,text_payload.data(),size);text_code[5+size]=255;text_code[6+size]=255;ending.instruction=text_code.data();ending.end=text_code.data()+text_code.size();return ending.update(0,0)?scores.settings.data():nullptr;
}
API(music_cue) i32 music_cue(){return ending.music_request;}
static std::array<u32,13> switch_result;
API(staff_run) const u32* staff_run(i32 time,i32 wait,i32 line,u32 flags,u32 schedule,float rate){
 manager.clear();manager.rate=rate;resource={};resource.scripts.resize(2);append(2);append(-1);resource.scripts[0]=resource.scripts[1];
 for(u32 i=0;i<5;++i){auto* vm=manager.create(resource,0,0,0);if(!vm)return nullptr;ending.text_lines[i]=vm->id;}
 ending.images.fill(100);ending.slots.fill(&resource);ending.active=true;ending.flags=flags;ending.line=line;ending.color=0x123456;ending.elapsed.set(0,&manager.rate);ending.time.set(time,&manager.rate);ending.wait.set(wait,&manager.rate);
 auto& staff=ending.messages["staff.msg"];staff.assign(20,0);staff[4]=8;staff[8]=u8(schedule);staff[10]=9;staff[11]=4;const u32 ink=0x654321;std::memcpy(staff.data()+12,&ink,4);staff[16]=255;staff[17]=255;
 text_code.assign(18,0);text_code[2]=12;text_code[3]=10;std::memcpy(text_code.data()+4,"staff.msg",10);text_code[14]=255;text_code[15]=255;ending.instruction=text_code.data();ending.end=text_code.data()+text_code.size();
 if(!ending.update(0,0))return nullptr;switch_result[0]=u32(ending.instruction-staff.data());switch_result[1]=ending.flags;switch_result[2]=ending.line;switch_result[3]=ending.color;
 u32 i=4;for(const Timer* t:{&ending.elapsed,&ending.time,&ending.wait}){switch_result[i++]=u32(t->previous);switch_result[i++]=u32(t->current);switch_result[i++]=float_bits(t->fractional);}return switch_result.data();
}
API(staff_handle) u32 staff_handle(u32 n){if(n<5)return ending.text_lines[n];if(n<9)return ending.slots[n-5]!=nullptr;return ending.images[n-9];}
