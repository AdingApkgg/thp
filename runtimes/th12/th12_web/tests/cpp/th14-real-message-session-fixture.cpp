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
 session.reset();session=std::make_unique<GameSession>();diagnostic.clear();tape.clear();writes.clear();
 if(!session->begin(source,stage,selection/2,selection%2,1))return failed("begin stage");
 // Save and decode the same controlled edge stream used by the original
 // oracle. This deliberately is not a natural player recording.
 for(u32 frame=0;frame<frames+1;++frame)if(!session->recording.tick(0,frame%60?0:0x80001,0))return failed("record controlled edges");
 if(!session->recording.finish_stage(true)||!session->recording.save("MSG",0,1,0,0,tape))return failed("save controlled replay");
 if(!session->begin_replay(source,tape.data(),tape.size(),stage))return failed("decode controlled replay");
 if(!session->battle->start_dialogue(entry))return failed(session->battle->error.c_str());
 const auto& message=session->resources.stage->messages[stage_dialogue_index(selection/2,selection%2)];
 std::memcpy(&program_start,message.data()+4+entry*8,4);
 for(u32 i=0;i<4;++i)line_ids[i]=session->battle->dialogue->state.animations[3+i];
 capture();return 1;
}
API(step_session_message) i32 step_session_message(){
 writes.clear();session->battle->dialogue_text_requests.clear();
 if(!session->update({})){failed("session update");return -2;}
 if(!session->battle||!session->battle->dialogue){diagnostic="session left dialogue owner";return -3;}
 for(const auto& r:session->battle->dialogue_text_requests){u32 line=0;while(line<4&&line_ids[line]!=r.animation)++line;if(line==4){diagnostic="text request from a different dialogue";return -4;}const auto* vm=session->animations.find(r.animation);const u32 a[]={line,r.color,u32(r.style),u32(r.offset),u32(r.font),vm?vm->flags2&0x800:0,u32(r.bytes.size())};writes.insert(writes.end(),a,a+7);for(u8 b:r.bytes)writes.push_back(b);}
 graphics.data.clear();graphics.submissions.clear();graphics.snapshots.clear();graphics.target_events.clear();
 if(!session->draw(renderer)){failed("session draw");return -5;}
 capture();return session->battle->dialogue->active?0:1;
}
API(message_state) const u32* message_state(){return state;}
API(message_writes) const u32* message_writes(){return writes.data();}
API(message_write_words) u32 message_write_words(){return writes.size();}
API(session_stage_frame) u32 session_stage_frame(){return session->battle->frame;}
API(session_phase) u32 session_phase(){return u32(session->state.phase);}
