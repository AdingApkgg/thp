#include "../../cpp/sdl/GraphicsDevice.hpp"
#include "../../cpp/sdl/FontDevice.hpp"
#include "../../cpp/game/GameSession.hpp"
#include "../../cpp/game/GameBattle.hpp"
#include "../../cpp/game/StageFiles.hpp"
#include "render-fixture.hpp"
#include <cstdlib>
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static GameResources source;
static std::unique_ptr<GameSession> session;
static th11::test::RecordingGraphics graphics;
static AnmRenderer renderer(graphics);
static std::vector<u8> tape;
static std::vector<u32> writes;
static u32 state[20],line_ids[4],program_start;
static std::string diagnostic;
static u32 bits(float v){u32 n;std::memcpy(&n,&v,4);return n;}
static u32 text_state[4*38];
static bool reject_text=false;
static th11::sdl::GraphicsDevice font_graphics;
static std::unique_ptr<th11::sdl::FontDevice> font_device;
static std::vector<std::vector<u8>> atlas_snapshots;
static bool capture_atlases=false;
struct SyncText final:StageResourceEffects,DialogueEffects {
 DialogueEffects* dialogue_text_device()override{return this;}
 bool dialogue_text(const DialogueText& r)override{
  if(reject_text)return false;
  u32 line=0;while(line<4&&line_ids[line]!=r.animation)++line;
  auto* vm=session->animations.find(r.animation);
  if(line==4||!vm){diagnostic="invalid synchronous text animation";return false;}
  const u32 a[]={line,r.color,u32(r.style),u32(r.offset),u32(r.font),vm->flags2&0x800,u32(r.bytes.size())};
  writes.insert(writes.end(),a,a+7);for(u8 b:r.bytes)writes.push_back(b);
  // Actual production FontDevice writes at the original priority27 boundary.
  if(!font_device->text(*vm,r)){diagnostic=font_device->error;return false;}
  if(capture_atlases){auto* image=font_graphics.pixels(font_graphics.texture(*vm->resource,vm->sprite->texture));if(!image){diagnostic="missing written atlas";return false;}atlas_snapshots.push_back(image->pixels);}
  return true;
 }
};static SyncText sync_text;
static void capture_text(){
 for(u32 i=0;i<4;++i){auto* out=text_state+i*38;auto* vm=session->animations.find(line_ids[i]);
  if(!vm){std::memset(out,0,38*sizeof(u32));continue;}
  const u32 a[]={u32(i32(vm->sprite_index)),vm->color,vm->secondary_color,vm->layer,u32(vm->timer.current),bits(vm->timer.fractional),
   bits(vm->script_position.x),bits(vm->script_position.y),bits(vm->script_position.z),bits(vm->scale.x),bits(vm->scale.y),u32(vm->pending_interrupt),
   bits(vm->floats[0]),bits(vm->floats[1]),bits(vm->texture_scale.x),bits(vm->texture_scale.y),vm->rectangle_columns|(u32(vm->rectangle_rows)<<8),vm->flags2&0xa00,vm->flags&1,
   vm->instruction?u32(reinterpret_cast<const u8*>(vm->instruction)-reinterpret_cast<const u8*>(vm->script_begin)):0xffffffff,
   vm->parent==session->animations.find(line_ids[0]),u32(i32(vm->script_index)),bits(vm->sprite_size.x),bits(vm->sprite_size.y),
   bits(vm->uv[0].x),bits(vm->uv[0].y),bits(vm->uv[1].x),bits(vm->uv[1].y),bits(vm->uv[2].x),bits(vm->uv[2].y),bits(vm->uv[3].x),bits(vm->uv[3].y),
   bits(vm->sprite_matrix.m[0]),bits(vm->sprite_matrix.m[5]),bits(vm->uv_matrix.m[0]),bits(vm->uv_matrix.m[5]),bits(vm->transform_matrix.m[0]),bits(vm->transform_matrix.m[5])};
  std::memcpy(out,a,sizeof a);
 }
}
API(allocate) void* allocate(u32 n){return std::malloc(n);}
API(open_archive) i32 open_archive(const u8* p,u32 n){return source.open_archive(p,n);}
API(error) const char* error(){return diagnostic.c_str();}
static bool failed(const char* fallback){diagnostic=session->error.empty()?fallback:session->error;return false;}
static void capture(){
 const auto& d=*session->battle->dialogue;const auto& s=d.state;
 const auto& message=session->resources.stage->messages[stage_dialogue_index(session->state.character,session->state.subtype)];
 const u32 a[]={s.flags,u32(s.release_signal),u32(s.next_line),u32(s.lines_initialized),u32(s.speaker),s.colors[0],s.colors[1],s.colors[2],bits(d.text_pair_194.x),bits(d.text_pair_194.y),bits(d.th14_text_width),u32(d.th14_text_layout),u32(s.elapsed.current),bits(s.elapsed.fractional),u32(s.time.current),bits(s.time.fractional),u32(s.wait.current),bits(s.wait.fractional),u32(s.instruction-(message.data()+program_start)),d.th14_text_background!=0};
 std::memcpy(state,a,sizeof a);
}
API(begin_session_message) i32 begin_session_message(u32 stage,u32 selection,u32 entry,u32 frames){
 if(session)font_graphics.unload(session->resources.core.text);session.reset();session=std::make_unique<GameSession>();session->resources.effects=&sync_text;reject_text=false;diagnostic.clear();tape.clear();writes.clear();
 capture_atlases=(stage==1&&selection==0)||(stage==4&&selection==3)||(stage==7&&selection==4);atlas_snapshots.clear();
 if(!font_device)return failed("font device uninitialized");
 if(!session->begin(source,stage,selection/2,selection%2,1))return failed("begin stage");
 // Save and decode the same controlled edge stream used by the original
 // oracle. This deliberately is not a natural player recording.
 for(u32 frame=0;frame<frames+1;++frame)if(!session->recording.tick(0,frame%60?0:0x80001,0))return failed("record controlled edges");
 if(!session->recording.finish_stage(true)||!session->recording.save("MSG",0,1,0,0,tape))return failed("save controlled replay");
 if(!session->begin_replay(source,tape.data(),tape.size(),stage))return failed("decode controlled replay");
 if(!font_graphics.preload(session->resources.core.text))return failed(font_graphics.error.c_str());
 if(!session->battle->start_dialogue(entry))return failed(session->battle->error.c_str());
 const auto& message=session->resources.stage->messages[stage_dialogue_index(selection/2,selection%2)];
 std::memcpy(&program_start,message.data()+4+entry*8,4);
 for(u32 i=0;i<4;++i)line_ids[i]=session->battle->dialogue->state.animations[3+i];
 capture();capture_text();return 1;
}
API(step_session_message) i32 step_session_message(){
 writes.clear();atlas_snapshots.clear();session->battle->dialogue_text_requests.clear();
 if(!session->update({})){failed("session update");return -2;}
 if(!session->battle||!session->battle->dialogue){diagnostic="session left dialogue owner";return -3;}
 if(!session->battle->dialogue_text_requests.empty()){diagnostic="synchronous consumer unexpectedly queued text";return -4;}
 graphics.data.clear();graphics.submissions.clear();graphics.snapshots.clear();graphics.target_events.clear();
 if(!session->draw(renderer)){failed("session draw");return -5;}
 capture();capture_text();return session->battle->dialogue->active?0:1;
}
API(message_state) const u32* message_state(){return state;}
API(message_writes) const u32* message_writes(){return writes.data();}
API(message_write_words) u32 message_write_words(){return writes.size();}
API(session_stage_frame) u32 session_stage_frame(){return session->battle->frame;}
API(session_phase) u32 session_phase(){return u32(session->state.phase);}

API(message_text_state) const u32* message_text_state(){return text_state;}
API(reject_next_text) void reject_next_text(){reject_text=true;}

API(font_initialize) i32 font_initialize(){if(!font_graphics.initialize())return 0;FontBitmapTh14 bitmap;Rng rng;rng.seed=0;bitmap.initialize(rng);font_device=std::make_unique<th11::sdl::FontDevice>(font_graphics);return font_device->initialize(&bitmap);}
API(font_error) const char* font_error(){return font_device?font_device->error.c_str():font_graphics.error.c_str();}
API(font_writes) u32 font_writes(){return font_device?font_device->writes:0;}
API(atlas_count) u32 atlas_count(){return atlas_snapshots.size();}
API(atlas_data) const u8* atlas_data(u32 index){return index<atlas_snapshots.size()?atlas_snapshots[index].data():nullptr;}
API(atlas_bytes) u32 atlas_bytes(u32 index){return index<atlas_snapshots.size()?atlas_snapshots[index].size():0;}
