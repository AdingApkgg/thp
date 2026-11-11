#include "GameSession.hpp"
#include "ReplayRngRestoreTh14.hpp"
#include <fstream>
#include <iterator>
#include <cstdio>
#include <cstdlib>
using namespace th11;
static void need(bool ok,const char* why){if(!ok){std::fprintf(stderr,"%s\n",why);std::abort();}}
struct FakeInitial {
 bool ready=false,terminal=false,in_main=false;u32 joins=0;
 ReplayRngRestoreResultTh14 poll()const{return terminal?ReplayRngRestoreResultTh14::Ready:ReplayRngRestoreResultTh14::Waiting;}
 bool control_ready()const{return ready;}
 bool pending(AnmResource*&,u16&)const{return false;}
 void join(){need(in_main,"Post-overlay handoff must not reap a successful worker");++joins;}
 std::string error_after_join()const{return {};}
};
struct PreparedEffects:StageResourceEffects {
 bool* complete;
 explicit PreparedEffects(bool* p):complete(p){}
 bool stage_ready()const override{return *complete;}
};
struct Host;
static Host* active=nullptr;
static void overlay(AnmVm&);
static void normal(AnmVm&);
struct Host {
 FakeInitial reader;FakeInitial* initial_cpp_resources=&reader;
 bool initial_statistics_reset=false,initial_decode_complete=false,initial_upload_waiting=true;
 PreparedEffects effects{&initial_decode_complete};GameSession session{0};
 std::string error;std::vector<int> boot_uploads{1};u32 boot_upload_index=1;StageResources* boot_stage_owner=nullptr;
 u32 mode,overlay_calls=0,normal_calls=0,pump_calls=0;bool title_entry_advanced=false;
 struct {struct {void reset(){}}effects;int current_music(){return -1;}}audio;
 struct {float fps=60;}frame_statistics;
 explicit Host(GameResources& archive,u32 selected):mode(selected){
  session.resources.effects=&effects;active=this;
  need(session.begin(archive,1,0,1,1),session.error.c_str());
  need(session.state.phase==GameSessionPhase::loading&&!session.battle,"Declared ready service must hold activation");
  boot_stage_owner=session.resources.stage.get();
  auto* over=session.animations.create(session.resources.core.front,129,5,0,true);need(over,"actual overlay ANM");over->before_update=overlay;over->interrupt(3);
  auto* plain=session.animations.create(session.resources.core.ascii,17,2,0xffffffffu,false);need(plain,"actual normal ANM");plain->before_update=normal;
  if(mode==0)reader.ready=true;
 }
 bool pump_cpp_initial_upload_chunk(){++pump_calls;return true;}
 void cancel_boot_worker(bool=false){}
 void reset_entry_frame_statistics(){}
 bool play_stage_music(u32,bool){return true;}
 bool audio_events(){return true;}
 bool text_events(){return true;}
#ifdef TH14_OVERLAY_TEST_CANDIDATE
     bool poll_cpp_initial_completion(bool reap_terminal=true){
        if(!initial_cpp_resources)return true;
        const auto status=initial_cpp_resources->poll();
#if defined(TH14_CPP_STAGE_DECODE)
        if(!initial_cpp_resources->control_ready()){
            if(status==ReplayRngRestoreResultTh14::Waiting)return true;
            initial_cpp_resources->join();
            error="TH14 initial worker returned without Control enable: "+initial_cpp_resources->error_after_join();return false;
        }
        if(status!=ReplayRngRestoreResultTh14::Waiting){
            if(status!=ReplayRngRestoreResultTh14::Ready){initial_cpp_resources->join();error="TH14 initial worker failed after data publication";return false;}
            // Reaping remains a Main resource-poll job. The Control11 data
            // handoff after Overlay8 must not add a thread wait to this pass.
            if(reap_terminal)initial_cpp_resources->join();
        }
#else
        if(status==ReplayRngRestoreResultTh14::Waiting)return true;
        initial_cpp_resources->join();
#endif
        // Callback return publishes its final offers, but does not ACK any
        // unuploaded template. Drain every retained slot before Main activates.
        // This guard retains the existing incomplete-native-tail boundary.
#if defined(TH14_CPP_STAGE_DECODE)
        AnmResource* pending_resource=nullptr;u16 pending_file=0;
        if(initial_cpp_resources->pending(pending_resource,pending_file)){
            error="TH14 Control enabled before final file completion";return false;
        }
#else
        if(status==ReplayRngRestoreResultTh14::Ready){
            AnmResource* pending_resource=nullptr;u16 pending_file=0;
            if(initial_cpp_resources->pending(pending_resource,pending_file))return true;
        }
        if(status!=ReplayRngRestoreResultTh14::Ready){
            error="TH14 initial C++ resource worker: "+initial_cpp_resources->error_after_join();return false;
        }
#endif
        // Control enable publishes completed loading data. Retain the actor
        // until its independent return/reap boundary; activation needs no join.
        initial_statistics_reset=true;
        initial_decode_complete=true;initial_upload_waiting=false;return true;
    }
     bool pump_cpp_initial_upload(){
        if(!initial_cpp_resources)return true;
        if(!pump_cpp_initial_upload_chunk())return false;
        return poll_cpp_initial_completion();
    }
#else
     bool pump_cpp_initial_upload(){
        if(!initial_cpp_resources)return true;
        if(!pump_cpp_initial_upload_chunk())return false;
        const auto status=initial_cpp_resources->poll();
#if defined(TH14_CPP_STAGE_DECODE)
        if(!initial_cpp_resources->control_ready()){
            if(status==ReplayRngRestoreResultTh14::Waiting)return true;
            initial_cpp_resources->join();
            error="TH14 initial worker returned without Control enable: "+initial_cpp_resources->error_after_join();return false;
        }
        if(status!=ReplayRngRestoreResultTh14::Waiting){
            initial_cpp_resources->join();
            if(status!=ReplayRngRestoreResultTh14::Ready){error="TH14 initial worker failed after data publication";return false;}
        }
#else
        if(status==ReplayRngRestoreResultTh14::Waiting)return true;
        initial_cpp_resources->join();
#endif
        // Callback return publishes its final offers, but does not ACK any
        // unuploaded template. Drain every retained slot before Main activates.
        // This guard retains the existing incomplete-native-tail boundary.
#if defined(TH14_CPP_STAGE_DECODE)
        AnmResource* pending_resource=nullptr;u16 pending_file=0;
        if(initial_cpp_resources->pending(pending_resource,pending_file)){
            error="TH14 Control enabled before final file completion";return false;
        }
#else
        if(status==ReplayRngRestoreResultTh14::Ready){
            AnmResource* pending_resource=nullptr;u16 pending_file=0;
            if(initial_cpp_resources->pending(pending_resource,pending_file))return true;
        }
        if(status!=ReplayRngRestoreResultTh14::Ready){
            error="TH14 initial C++ resource worker: "+initial_cpp_resources->error_after_join();return false;
        }
#endif
        // Control enable publishes completed loading data. Retain the actor
        // until its independent return/reap boundary; activation needs no join.
        initial_statistics_reset=true;
        initial_decode_complete=true;initial_upload_waiting=false;return true;
    }
#endif
 bool step(){
  if(!boot_stage_owner)return session.update({});
  reader.in_main=true;const bool pumped=pump_cpp_initial_upload();reader.in_main=false;if(!pumped)return false;
  const u32 held=0;const bool pause_key=false;
#ifdef TH14_OVERLAY_TEST_CANDIDATE
             bool initial_stage_overlay_updated=false;
#if defined(TH14_CPP_INITIAL_LOADING) && defined(TH14_CPP_STAGE_DECODE)
            if(!title_entry_advanced&&boot_stage_owner&&initial_cpp_resources){
                // Overlay8 may overlap the worker's Control11 enable store.
                // Read completion again at this callback boundary, without
                // running Main's resource pump or an ANM update twice.
                if(!session.animations.update(true)){error=session.animations.last_error_text();return false;}
                initial_stage_overlay_updated=true;
                if(!poll_cpp_initial_completion(false))return false;
            }
#endif
            bool initial_stage_entry_advanced=false;
            if(boot_stage_owner&&boot_upload_index==boot_uploads.size()&&!initial_upload_waiting){
                // The worker clears Control+80 bit4 after its final upload.
                // Control11 then attaches the world before Player/ANM in the
                // next pass; do not create HUD after that pass's ANM update.
#if defined(TH14_CPP_INITIAL_LOADING) && defined(TH14_CPP_STAGE_DECODE)
                cancel_boot_worker(true);
#else
                cancel_boot_worker();
#endif
                // Control11 finishes the shared loading family after overlay8.
                boot_uploads.clear();boot_upload_index=0;boot_stage_owner=nullptr;
                if(!session.finish_loading(true)){error=session.error;return false;}
                reset_entry_frame_statistics();audio.effects.reset();
                if(!play_stage_music(session.state.stage,true))return false;
                const GameSessionInput input{held,0,0,pause_key,bool(held&0x100),bool(held&0x2),frame_statistics.fps};
                const bool updated=initial_stage_overlay_updated?session.update_after_initial_overlay(input):session.update(input);
                if(!updated){error=session.error;return false;}
                session.battle->th14_current_music=audio.current_music();
                if(!audio_events()||!text_events())return false;
                initial_stage_entry_advanced=true;
                std::printf("[loading14] initial worker ready; control callbacks attached\n");
            }
            if(!title_entry_advanced&&!initial_stage_entry_advanced&&
               ((!initial_stage_overlay_updated&&!session.animations.update(true))||!session.animations.update(false))){error="TH14 loading ANM update failed";return false;}

#else
             bool initial_stage_entry_advanced=false;
            if(boot_stage_owner&&boot_upload_index==boot_uploads.size()&&!initial_upload_waiting){
                // The worker clears Control+80 bit4 after its final upload.
                // Control11 then attaches the world before Player/ANM in the
                // next pass; do not create HUD after that pass's ANM update.
#if defined(TH14_CPP_INITIAL_LOADING) && defined(TH14_CPP_STAGE_DECODE)
                cancel_boot_worker(true);
#else
                cancel_boot_worker();
#endif
                // Control11 finishes the shared loading family after overlay8.
                boot_uploads.clear();boot_upload_index=0;boot_stage_owner=nullptr;
                if(!session.finish_loading(true)){error=session.error;return false;}
                reset_entry_frame_statistics();audio.effects.reset();
                if(!play_stage_music(session.state.stage,true))return false;
                const GameSessionInput input{held,0,0,pause_key,bool(held&0x100),bool(held&0x2),frame_statistics.fps};
                if(!session.update(input)){error=session.error;return false;}
                session.battle->th14_current_music=audio.current_music();
                if(!audio_events()||!text_events())return false;
                initial_stage_entry_advanced=true;
                std::printf("[loading14] initial worker ready; control callbacks attached\n");
            }
            if(!title_entry_advanced&&!initial_stage_entry_advanced&&(!session.animations.update(true)||!session.animations.update(false))){error="TH14 loading ANM update failed";return false;}

#endif
  return true;
 }
};
static void overlay(AnmVm&){++active->overlay_calls;if(active->mode==1||active->mode==4){active->reader.ready=true;if(active->mode==4)active->reader.terminal=true;}}
static void normal(AnmVm&){++active->normal_calls;if(active->mode==2)active->reader.ready=true;}
static u32 output[5*13];
extern "C" __attribute__((export_name("data"))) const u32* data(){return output;}
extern "C" __attribute__((export_name("run"))) u32 run(){
 std::ifstream in("/stock/th14.dat",std::ios::binary);std::vector<u8> bytes((std::istreambuf_iterator<char>(in)),{});GameResources archive;
 need(archive.open_archive(bytes.data(),u32(bytes.size())),"stock archive");
 for(u32 mode=0;mode<5;++mode){
  Host host(archive,mode);u32* row=output+mode*13;row[0]=mode;
  for(u32 pass=0;pass<2;++pass){
   need(host.step(),host.error.empty()?host.session.error.c_str():host.error.c_str());
   row[1+pass]=host.session.battle?u32(host.session.battle->control_frame()):0;
   row[3+pass]=host.overlay_calls;row[5+pass]=host.normal_calls;row[7+pass]=host.pump_calls;
  }
  row[9]=u32(host.session.state.phase);row[10]=host.session.state.frame;row[11]=u32(host.initial_cpp_resources->poll()==ReplayRngRestoreResultTh14::Waiting);
  row[12]=host.reader.joins;host.session.shutdown();active=nullptr;
 }
 return 65;
}

extern "C" __attribute__((export_name("session_bytes"))) u32 session_bytes(){return sizeof(GameSession);}
