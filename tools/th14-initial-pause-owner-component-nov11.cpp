#include "GameSession.hpp"
#include "StageCppWorkerTh14.hpp"
#include <fstream>
#include <iterator>
#include <cstdio>
#include <cstdlib>
#include <new>
using namespace th11;
static void* tracked=nullptr;static u32 allocations=0,frees=0;static bool recording=false;
void* operator new(std::size_t n){auto* p=std::malloc(n);if(!p)std::abort();if(recording&&n==sizeof(PauseMenu)){tracked=p;++allocations;}return p;}
void operator delete(void* p)noexcept{if(p&&p==tracked)++frees;std::free(p);}
void operator delete(void* p,std::size_t)noexcept{::operator delete(p);}
static void need(bool ok,const char* reason){if(!ok){std::fprintf(stderr,"%s\n",reason);std::abort();}}
static u32 output[52];
extern "C" __attribute__((export_name("data"))) const u32* data(){return output;}
extern "C" __attribute__((export_name("run"))) u32 run(){
 std::ifstream in("/stock/th14.dat",std::ios::binary);std::vector<u8> bytes((std::istreambuf_iterator<char>(in)),{});
 GameResources archive;need(archive.open_archive(bytes.data(),u32(bytes.size())),"stock archive");
 GameSession session(0,false);auto& r=session.resources;auto& a=session.animations;
 need(archive.open_anm("ascii.anm",r.core.ascii),"ascii");a.fallback_sprites=&r.core.ascii;
 need(archive.open_anm("front.anm",r.core.front),"front");need(archive.open_anm("text.anm",r.core.text),"text");
 need(a.prepare_resource(r.core.front,5),a.last_error_text().c_str());need(a.prepare_resource(r.core.text,0),a.last_error_text().c_str());
 r.stage=std::make_unique<StageResources>();r.stage_number=1;
 session.battle=std::make_unique<GameBattle>(r,a,session.economy,session.spell_records,session.compositor,session.clear_records,true);
 session.battle->initialize_initial_pools();session.state.phase=GameSessionPhase::loading;session.state.stage=1;
 const auto scriptSeed=a.script_rng.seed_value(),visualSeed=a.visual_rng.seed_value();const auto scriptCalls=a.script_rng.call_count(),visualCalls=a.visual_rng.call_count();
#ifdef TH14_PAUSE_OWNER_TEST_CANDIDATE
 {StageCppWorkerScopeTh14 scope(&session);recording=true;need(session.prepare_initial_pause(),session.error.c_str());recording=false;}
#endif
 output[40]=allocations;output[41]=a.script_rng.seed_value()==scriptSeed&&a.script_rng.call_count()==scriptCalls&&a.visual_rng.seed_value()==visualSeed&&a.visual_rng.call_count()==visualCalls;
 need(!session.pause_menu,"Initial owner must remain private/inactive");session.state.phase=GameSessionPhase::stage;
 const u32 continues[]={0,1,0,0},playback[]={0,0,1,0};
 for(u32 cycle=0;cycle<4;++cycle){
  session.state.replay=bool(playback[cycle]);session.battle->hud.score.continues=continues[cycle];
  recording=true;need(session.pause(),session.error.c_str());recording=false;
  auto* owner=session.pause_menu.get();if(cycle==0)owner->entered_name[0]='K';
  for(u32 tick=0;tick<32&&owner->state!=3;++tick)need(session.update({}),session.error.c_str());
  need(owner->state==3,"Pause choices must open");
  auto* row=output+cycle*10;row[0]=cycle;row[1]=allocations;row[2]=frees;row[3]=owner->cursor.disabled_count;row[4]=owner->entered_name[0]=='K';
  row[5]=owner->cursor.selected;row[6]=u32(owner->state);row[7]=owner->timer.current;
  GameSessionInput confirm;confirm.held=1;confirm.pressed=1;need(session.update(confirm),session.error.c_str());
  for(u32 tick=0;tick<32&&session.state.phase==GameSessionPhase::paused;++tick)need(session.update({}),session.error.c_str());
  need(session.state.phase==GameSessionPhase::stage&&!session.pause_menu,"Natural resume must return to stage");row[8]=frees;row[9]=allocations;
 }
#ifdef TH14_PAUSE_OWNER_TEST_CANDIDATE
 recording=true;need(session.open_result(false),session.error.c_str());recording=false;
 output[48]=allocations;output[49]=session.state.phase==GameSessionPhase::game_over&&session.pause_menu.get()==tracked;
 output[50]=session.pause_menu->entered_name[0]=='K';
#endif
 output[42]=frees;session.shutdown();output[43]=frees;output[44]=allocations;tracked=nullptr;
#ifdef TH14_PAUSE_OWNER_TEST_CANDIDATE
 {
  GameSession abandoned(0,false);auto& br=abandoned.resources;br.stage=std::make_unique<StageResources>();
  abandoned.battle=std::make_unique<GameBattle>(br,abandoned.animations,abandoned.economy,abandoned.spell_records,abandoned.compositor,abandoned.clear_records,true);
  abandoned.battle->initialize_initial_pools();abandoned.state.phase=GameSessionPhase::loading;
  {StageCppWorkerScopeTh14 scope(&abandoned);recording=true;need(abandoned.prepare_initial_pause(),abandoned.error.c_str());recording=false;}
  {StageCppWorkerScopeTh14 scope(&abandoned);output[51]=!abandoned.prepare_initial_pause()&&!abandoned.error.empty();}
  abandoned.shutdown();output[45]=allocations;output[46]=frees;tracked=nullptr;
 }
 {GameSession wrong_thread(0,false);output[47]=!wrong_thread.prepare_initial_pause()&&!wrong_thread.error.empty();}
#endif
 return 52;
}
