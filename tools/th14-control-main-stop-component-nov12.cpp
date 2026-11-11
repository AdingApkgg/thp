#include "GameSession.hpp"
#include <fstream>
#include <iterator>
#include <memory>
using namespace th11;
#define API(n) extern "C" __attribute__((export_name(#n)))
static GameResources source;
static std::unique_ptr<GameSession> session;
static u32 words[14],player_calls,copy_calls,player_anm_instructions;
extern "C" int __real__ZN4th115AnmVm6updateERNS_14AnmEnvironmentE(AnmVm*,AnmEnvironment*);
extern "C" int __wrap__ZN4th115AnmVm6updateERNS_14AnmEnvironmentE(AnmVm* vm,AnmEnvironment* env){
 if(session)for(u32 i=0;i<4;++i)if(vm==&session->compositor.copies[i]){++copy_calls;break;}
 return __real__ZN4th115AnmVm6updateERNS_14AnmEnvironmentE(vm,env);
}
API(open_stock) u32 open_stock(){
 std::ifstream in("/stock/th14.dat",std::ios::binary);
 std::vector<u8> bytes((std::istreambuf_iterator<char>(in)),{});
 return source.open_archive(bytes.data(),u32(bytes.size()));
}
API(begin_case) u32 begin_case(float rate,u32 flags,u32 enabled,u32 demo){
 session.reset();session=std::make_unique<GameSession>(0,false);auto& s=*session;
 s.interactive=true;s.animations.th14_native_stack.configure(0x12345678);
 if(demo){
  std::vector<u8> replay;
  if(!source.read("demo0.rpy",replay)||!s.begin_replay(source,replay.data(),u32(replay.size()),0,true))return 0;
 }else if(!s.begin(source,1,0,1,1,false,false,false))return 0;
 if(!s.battle||s.state.phase!=GameSessionPhase::stage)return 0;
 s.state.frame=200;s.animations.rate=rate;
 s.battle->th14_control_clock.set(200,&s.animations.rate);
 auto* c=s.animations.th14_control.get();if(!c)return 0;c->flags=flags;c->callbacks_enabled=enabled;
 i32 zero=0;std::memcpy(s.scores.characters[s.state.character*2+s.state.subtype].data()+ScoreFile::play_time_offset,&zero,4);
 player_calls=copy_calls=player_anm_instructions=0;
 s.battle->before_player_update=[](const GameBattle&){++player_calls;};
 s.animations.before_initial_update=[](const AnmVm& vm){if(vm.file_index==9)++player_anm_instructions;return true;};
 return 1;
}
API(tick_case) u32 tick_case(){
 auto& s=*session;const bool ok=s.update({});
 words[0]=u32(ok);words[1]=u32(s.state.phase);
 if(s.battle){
  const auto& t=s.battle->th14_control_clock;words[2]=u32(t.previous);words[3]=u32(t.current);std::memcpy(words+4,&t.fractional,4);words[5]=t.flags;
  words[6]=s.animations.th14_control.callback_flags();
  std::memcpy(words+7,s.scores.characters[s.state.character*2+s.state.subtype].data()+ScoreFile::play_time_offset,4);
  words[8]=player_calls;words[9]=copy_calls;words[10]=player_anm_instructions;
  words[11]=s.playback.frame();words[12]=s.battle->frame;words[13]=s.state.frame;
 }else for(u32 i=2;i<14;++i)words[i]=0;
 return ok;
}
API(data) const u32* data(){return words;}
API(error) const char* error(){return session?session->error.c_str():"no session";}
API(close_session) void close_session(){session.reset();}
