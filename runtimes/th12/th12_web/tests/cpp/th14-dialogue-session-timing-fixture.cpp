#include "th14-dialogue-timing-fixture.cpp"
#include "../../cpp/game/GameSession.hpp"
#include "../../cpp/game/GameBattle.hpp"
#include <cstdlib>
static GameResources source;static std::unique_ptr<GameSession> session;static std::vector<u8> replay_bytes;static std::string diagnostic;
API(allocate) void* allocate(u32 n){return std::malloc(n);}
API(open_archive) i32 open_archive(const u8* p,u32 n){return source.open_archive(p,n);}
API(session_begin) i32 session_begin(i32 replay,i32 preheld,i32 fire,u32 flags){
 begin_timing(flags,1,60,0);session=std::make_unique<GameSession>();diagnostic.clear();replay_bytes.clear();
 auto fail=[](){diagnostic=session->error;return 0;};
 if(!session->begin(source,1,0,0,0))return fail();
 const u32 held=fire?1:0x200;
 if(replay){for(u32 n=0;n<320;++n)if(!session->recording.tick(held,n==0?held:0,0))return fail();
  if(!session->recording.finish_stage(true)||!session->recording.save("DIALOGUE",0,1,0,0,replay_bytes))return fail();
  if(!session->begin_replay(source,replay_bytes.data(),u32(replay_bytes.size())))return fail();}
 for(i32 n=0;n<preheld;++n){GameSessionInput in;in.held=held;if(!session->update(in))return fail();}
 session->resources.stage->messages[0]=message;
 if(!session->battle->start_dialogue(0)){diagnostic=session->battle->error;return 0;}
 auto& d=*session->battle->dialogue;d.state.flags=flags;d.state.release_signal=3;d.state.next_line=d.state.lines_initialized=1;
 capture(d,session->resources.stage->messages[0].data()+12);return 1;
}
API(session_step) i32 session_step(u32 held){GameSessionInput in;in.held=held;if(!session->update(in)){diagnostic=session->error;return -2;}const auto& d=*session->battle->dialogue;capture(d,session->resources.stage->messages[0].data()+12);return d.active?0:1;}
API(duration) u32 duration(u32 fire){return fire?session->battle->th14_dialogue_fire_frames:session->battle->th14_dialogue_skip_frames;}
API(error) const char* error(){return diagnostic.c_str();}
