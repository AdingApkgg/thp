#include "GameSession.hpp"
#include <fstream>
#include <iterator>
#include <memory>
#include <cstdlib>
using namespace th11;
#define API(n) extern "C" __attribute__((export_name(#n)))
static GameResources source;
static std::unique_ptr<GameSession> session;
static u32 row[12], player_calls;
API(open_stock) u32 open_stock(){
 std::ifstream in("/stock/th14.dat",std::ios::binary);
 std::vector<u8> bytes((std::istreambuf_iterator<char>(in)),{});
 return source.open_archive(bytes.data(),u32(bytes.size()));
}
API(begin) u32 begin(i32 clock,u32 frame,float rate,u32 enabled){
 session.reset();session=std::make_unique<GameSession>(0,false);
 auto& s=*session;s.interactive=true;
 s.animations.th14_native_stack.configure(0x12345678);
 std::vector<u8> replay;
 if(!source.read("demo0.rpy",replay)||!s.begin_replay(source,replay.data(),u32(replay.size()),0,true))return 0;
 if(!s.battle||s.state.phase!=GameSessionPhase::stage)return 0;
 s.state.frame=frame;s.animations.rate=rate;
 s.battle->th14_control_clock.set(clock,&s.animations.rate);
 auto* c=s.animations.th14_control.get();if(!c)return 0;
 c->flags=0;c->callbacks_enabled=enabled;
 player_calls=0;s.battle->before_player_update=[](const GameBattle&){++player_calls;};
 return 1;
}
API(tick) u32 tick(u32 raw){
 auto& s=*session;
 const u32 before=s.battle?u32(s.battle->fades.effects.size()):0;
 GameSessionInput input;input.held=(raw&~0x80100u)|((raw&0x80000u)?256u:0u);input.pause=(raw&256u)!=0;
 const bool ok=s.update(input);
 row[0]=u32(ok);row[1]=u32(s.state.phase);row[2]=s.state.frame;row[3]=player_calls;
 if(s.battle){
  const auto& t=s.battle->th14_control_clock;row[4]=u32(t.previous);row[5]=u32(t.current);
  std::memcpy(row+6,&t.fractional,4);row[7]=t.flags;
  row[8]=u32(s.battle->fades.effects.size())-before;
  for(const auto& f:s.battle->fades.effects)if(f.type==5){row[9]=u32(f.duration);row[10]=f.color;row[11]=f.priority;}
 }else for(u32 i=4;i<12;++i)row[i]=0;
 return ok;
}
API(data) const u32* data(){return row;}
API(error) const char* error(){return session?session->error.c_str():"no session";}
API(close_session) void close_session(){session.reset();}
