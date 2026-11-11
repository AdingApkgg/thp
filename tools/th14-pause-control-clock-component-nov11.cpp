#include "GameSession.hpp"
#include <fstream>
#include <iterator>
#include <cstdio>
#include <cstdlib>
using namespace th11;
static void need(bool ok,const char* reason){if(!ok){std::fprintf(stderr,"%s\n",reason);std::abort();}}
static u32 rows[10*6];
extern "C" __attribute__((export_name("data"))) const u32* data(){return rows;}
extern "C" __attribute__((export_name("run"))) u32 run(){
 std::ifstream in("/stock/th14.dat",std::ios::binary);std::vector<u8> bytes((std::istreambuf_iterator<char>(in)),{});
 GameResources archive;need(archive.open_archive(bytes.data(),u32(bytes.size())),"stock archive");
 struct Case{i32 clock;u32 frame;float rate;u32 ticks;};
 const Case cases[]={{29,100,1,0},{30,0,1,0},{31,29,1,0},{0,100,1,0},{30,30,1,0},
 {0,40,.5f,40},{0,20,2,20},{0,100,0,100},{0,30,1,30},{-1,100,1,0}};
 for(u32 n=0;n<10;++n){
  GameSession session(0,false);auto& r=session.resources;auto& a=session.animations;
  need(archive.open_anm("ascii.anm",r.core.ascii),"ascii");a.fallback_sprites=&r.core.ascii;
  need(archive.open_anm("front.anm",r.core.front),"front");need(archive.open_anm("text.anm",r.core.text),"text");
  need(a.prepare_resource(r.core.front,5),a.last_error_text().c_str());need(a.prepare_resource(r.core.text,0),a.last_error_text().c_str());
  r.stage=std::make_unique<StageResources>();r.stage_number=1;
  session.battle=std::make_unique<GameBattle>(r,a,session.economy,session.spell_records,session.compositor,session.clear_records,true);
  session.state.phase=GameSessionPhase::stage;session.state.stage=1;session.state.frame=cases[n].frame;
  a.rate=cases[n].rate;auto& clock=session.battle->th14_control_clock;clock.set(cases[n].clock,&a.rate);
  for(u32 i=0;i<cases[n].ticks;++i)clock.tick();
  const i32 actual=clock.current;GameSessionInput input;input.pause=true;
  const bool ok=session.update(input);need(ok,session.error.c_str());
  u32* row=rows+n*6;row[0]=n;row[1]=u32(actual);row[2]=cases[n].frame;row[3]=u32(session.state.phase==GameSessionPhase::paused);row[4]=u32(bool(session.pause_menu));row[5]=u32(ok);
 }
 return 10;
}
