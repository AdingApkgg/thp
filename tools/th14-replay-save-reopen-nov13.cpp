#include "GameSession.hpp"
#include <cstdlib>
using namespace th11;
namespace {
std::vector<u8> saved,decoded;
void require(bool ok){if(!ok)std::abort();}
u32 word32(const u8* p){u32 x;std::memcpy(&x,p,4);return x;}
}
#define API(n) extern "C" __attribute__((export_name(#n)))
API(run) u32 run(i32 selection,i32 difficulty,i32 practice){
 auto s=std::make_unique<GameSession>(0);
 ShtResource sht;AnmResource anm;
 s->state.character=selection/2;s->state.subtype=selection%2;s->state.difficulty=difficulty;
 s->state.practice=practice;s->state.stage=practice?5u:difficulty==4?7u:1u;
 require(s->recording.begin(selection/2,selection%2,difficulty,practice,0));
 s->battle=std::make_unique<GameBattle>(s->resources,s->animations,s->economy,s->spell_records,s->compositor,s->clear_records,true);
 auto& b=*s->battle;
 b.player=std::make_unique<PlayerFrame>(sht,anm,anm,s->animations,s->economy,b,9,7);
 b.player->motion.state.x=-1234;b.player->motion.state.y=51199;
 require(s->record_stage_entry(true));
 const u32 first=s->state.stage;
 const auto input=[](u32 n){return u32(n%3==0?0x11:n%3==1?0x20:0);};
 const auto tick=[&](u32 count){for(u32 n=0;n<count;++n){u32 h=input(n),p=n?input(n-1):0;require(s->recording.tick(h,h&~p,p&~h,n<30?59.f:60.f));}};
 tick(33);
 std::vector<u8> a,c;
 require(s->save_replay("ORACLE",a,true,1));
 require(s->save_replay("ORACLE",c,true,1));require(a==c);
 require(s->recording.stages[first].frames==33&&!s->recording.stages[first].terminal);
 const bool two=!practice&&difficulty<4;
 if(two){
  require(s->recording.finish_stage());s->state.stage=2;
  b.player->motion.state.x=3456;b.player->motion.state.y=50001;
  require(s->record_stage_entry(false));tick(17);
 }
 require(s->save_replay("ORACLE",saved,true,1));
 const auto liveFrames=s->recording.stages[s->state.stage].frames;
 require(liveFrames==(two?17u:33u)&&!s->recording.stages[s->state.stage].terminal);
 Replay replay;require(replay.open(saved.data(),u32(saved.size())));
 require(replay.stage_count()==(two?2u:1u)&&replay.character()==u32(selection/2)&&replay.subtype()==u32(selection%2)&&replay.difficulty()==u32(difficulty));
 for(u32 ordinal=0;ordinal<(two?2u:1u);++ordinal){
  const u32 stage=ordinal?2:first,count=ordinal?17:33;
  require(replay.select(stage));const auto* header=replay.header(stage);
  require(header&&word32(header+0xd8)==(ordinal?0u:1u));
  require(i32(word32(header+12))==(ordinal?3456:-1234)&&i32(word32(header+16))==(ordinal?50001:51199));
  for(u32 n=0;n<count;++n){
   const auto v=replay.tick();const u32 h=input(n),p=n?input(n-1):0;
   require(!v.end_marker&&v.held==h&&v.pressed==(h&~p)&&v.released==(p&~h));
  }
  // Only the selected last stage gains a sentinel in the save snapshot.
  if(!two||ordinal)require(replay.tick().end_marker);
 }
 decoded=replay.decoded();b.player.reset();return u32(saved.size());
}
API(file_data) const u8* file_data(){return saved.data();}
API(decoded_data) const u8* decoded_data(){return decoded.data();}
API(decoded_size) u32 decoded_size(){return u32(decoded.size());}
