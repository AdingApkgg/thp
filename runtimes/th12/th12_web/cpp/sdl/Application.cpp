#include "GraphicsDevice.hpp"
#if PORT_TITLE == 14
#include "PauseCaptureTh14.hpp"
#include "ApplicationCaptureTh14.hpp"
#include "StageUploadsTh14.hpp"
#endif
#include "AudioDevice.hpp"
#include "FontDevice.hpp"
#include "../game/MusicCatalog.hpp"
#include "../game/GameSession.hpp"
#include "../game/FrameStatistics.hpp"
#include "../game/LoadingTh14.hpp"
#include "../game/AnmRenderer.hpp"
#include <SDL3/SDL.h>
#include <emscripten.h>
#include <emscripten/heap.h>
#include <malloc.h>
#include <emscripten/html5.h>
#include "../../../portable/sdl/FrameCadence.hpp"
#include "../../../portable/input/TouchController.hpp"
#include <algorithm>
#if defined(TH12_DELETE_GUARD)
// Diagnostic build only. The allocator reports a negative live-byte total just before the fault, with a free
// total of exactly the same magnitude, which is the signature of releasing more than was ever handed out. The
// damage shows up much later as an out-of-bounds access inside the allocator with no application frame in the
// stack, so every pointer handed out is recorded here and checked off when it comes back: one that returns twice,
// or was never handed out, is reported at the release that did it. The table is fixed size on purpose so that
// recording a pointer never allocates.
#include <cstdlib>
#include <cstdio>
#include <malloc.h>
#include <emscripten/heap.h>
extern "C" unsigned char __heap_base;
extern "C" void* __real_malloc(std::size_t);
extern "C" void* __real_calloc(std::size_t,std::size_t);
extern "C" void* __real_realloc(void*,std::size_t);
extern "C" void __real_free(void*);
namespace {
constexpr uint32_t kSlots=1u<<20;
uint32_t* live_table=nullptr;
uint32_t slot_of(void* p){return (uint32_t((reinterpret_cast<uintptr_t>(p)>>4)*2654435761u))&(kSlots-1);}
void track_add(void* p){
    if(!p)return;
    if(!live_table)live_table=static_cast<uint32_t*>(__real_calloc(kSlots,sizeof(uint32_t)));
    if(!live_table)return;
    uint32_t slot=slot_of(p);
    for(uint32_t n=0;n<kSlots;++n){uint32_t& e=live_table[slot];if(!e||e==uint32_t(reinterpret_cast<uintptr_t>(p))){e=uint32_t(reinterpret_cast<uintptr_t>(p));return;}slot=(slot+1)&(kSlots-1);}
}
// Returns 0 when the pointer was never handed out, 1 when it was live and is now cleared, 2 when the table is
// not ready yet and the check cannot be made.
int track_remove(void* p){
    if(!p)return 1;
    if(!live_table)return 2;
    uint32_t slot=slot_of(p);
    for(uint32_t n=0;n<kSlots;++n){uint32_t& e=live_table[slot];if(e==uint32_t(reinterpret_cast<uintptr_t>(p))){e=0;return 1;}if(!e)return 0;slot=(slot+1)&(kSlots-1);}
    return 0;
}
bool inside_heap(const void* p){
    const uintptr_t base=reinterpret_cast<uintptr_t>(&__heap_base);
    const uintptr_t end=base+emscripten_get_heap_size();
    const uintptr_t value=reinterpret_cast<uintptr_t>(p);
    return value>=base&&value<end;
}
void inspect(void* p,const char* kind){
    if(!p)return;
    if(!inside_heap(p)){std::fprintf(stderr,"ALLOC GUARD: %s of a non-heap pointer %p\n",kind,p);std::fflush(stderr);return;}
    const int state=track_remove(p);
    if(state==0){std::fprintf(stderr,"ALLOC GUARD: %s of a pointer that was never handed out: %p\n",kind,p);std::fflush(stderr);}
}
}
// The check lives in __wrap_free alone. Checking here as well would see every pointer a second time, after the
// wrapper had already cleared it, and report a double release for every ordinary delete.
void operator delete(void* p)noexcept{std::free(p);}
void operator delete[](void* p)noexcept{std::free(p);}
void operator delete(void* p,std::size_t)noexcept{std::free(p);}
void operator delete[](void* p,std::size_t)noexcept{std::free(p);}
void* operator new(std::size_t n){void* p=std::malloc(n?n:1);track_add(p);return p;}
void* operator new[](std::size_t n){return operator new(n);}
extern "C" void* __wrap_malloc(std::size_t n){void* p=__real_malloc(n);track_add(p);return p;}
extern "C" void* __wrap_calloc(std::size_t c,std::size_t n){void* p=__real_calloc(c,n);track_add(p);return p;}
extern "C" void* __wrap_realloc(void* p,std::size_t n){
    if(p)inspect(p,"realloc");
    void* q=__real_realloc(p,n);track_add(q);return q;
}
extern "C" void __wrap_free(void* p){
    if(p)inspect(p,"free");
    __real_free(p);
}
#endif
EM_JS(int, th11_browser_keyboard, (), { return typeof Module["resetBrowserKeyboard"] === "function"; });
#if PORT_TITLE == 14
// Browser has no Windows boot-time clock. Preserve native integer wrapping
// using this environment's actual monotonic millisecond input.
EM_JS(unsigned, th14_clock_ticks, (), { return performance.now() >>> 0; });
#endif
EM_JS(void, th11_reset_browser_keyboard, (), { Module["resetBrowserKeyboard"]?.(); });
EM_JS(void, th11_browser_frame, (int ok,double milliseconds,unsigned ticks), { Module["onGameFrame"]?.(ok,milliseconds,ticks); });
#include <vector>
#include <string>
#include <cstdlib>
#include <ctime>
#include <cstdio>
#include <sys/stat.h>
#include <dirent.h>

namespace th11::sdl {
namespace {
#if PORT_TITLE == 14
constexpr const char* score_path="/save/scoreth14.dat";
constexpr const char* config_path="/save/th14.cfg";
constexpr const char* replay_prefix="th14";
#else
constexpr const char* score_path="/save/scoreth11.dat";
constexpr const char* config_path="/save/th11.cfg";
constexpr const char* replay_prefix="th11";
#endif
struct Application:StageResourceEffects
#if PORT_TITLE == 14
    ,DialogueEffects
#endif
{
    GraphicsDevice graphics;
    AudioDevice audio;
    FontDevice fonts{graphics};
    GameResources resources;
#if PORT_TITLE == 14
    u32 initial_ticks=th14_clock_ticks();
    GameSession session{initial_ticks};
#else
    GameSession session;
#endif
    FrameStatistics frame_statistics;
    AsciiText frame_text{session.resources.core.ascii};
    AnmRenderer renderer;
    std::vector<u8> archive;
    std::vector<u8> saved_score_state,saved_config_state;
    bool initialized=false;
#if PORT_TITLE == 14
    LoadingTh14 boot_loading;
    struct ResourceUpload {AnmResource* resource;u16 file;};
    std::vector<ResourceUpload> boot_uploads;
    u32 boot_upload_index=0;
    StageResources* boot_stage_owner=nullptr;
    StageUploadsTh14 stage_uploads;
    bool core_loading_done=false;
#endif
    std::string error;
    // Lines whose plate had no sprite when they arrived, held until the plate's own walk binds one.
    std::vector<DialogueText> waiting_text;

    Application():renderer(graphics) {
        session.resources.effects=this;
#if PORT_TITLE == 14
        session.stage_load_clock=[](){return u64(SDL_GetTicksNS());};
#endif
    }
    void reset_frame_window(){frame_statistics.window_start=double(SDL_GetTicks())*.001;frame_statistics.frames=0;}
    bool read_file(const char* path,std::vector<u8>& data,u32 limit){
        SDL_IOStream* io=SDL_IOFromFile(path,"rb");if(!io)return false;const auto size=SDL_GetIOSize(io);
        if(size<0||u64(size)>limit){SDL_CloseIO(io);return false;}data.resize(size_t(size));
        const bool ok=SDL_ReadIO(io,data.data(),data.size())==data.size();SDL_CloseIO(io);return ok;
    }
    bool write_file(const std::string& path,const std::vector<u8>& data){
        const auto temporary=path+".tmp";SDL_IOStream* io=SDL_IOFromFile(temporary.c_str(),"wb");
        if(!io){error="Unable to create save file";return false;}
        const bool written=SDL_WriteIO(io,data.data(),data.size())==data.size();const bool closed=SDL_CloseIO(io);
        if(!written||!closed||std::rename(temporary.c_str(),path.c_str())!=0){error="Unable to finish save file";return false;}return true;
    }
    bool save_scores(){
        if(!initialized)return true;
        if(!session.title)session.scores.write_records(session.spell_records,session.clear_records);
        std::vector<u8> state;state.reserve(7*ScoreFile::character_size+ScoreFile::settings_size);
        for(const auto& character:session.scores.characters)state.insert(state.end(),character.begin(),character.end());
        state.insert(state.end(),session.scores.settings.begin(),session.scores.settings.end());
        if(state!=saved_score_state){std::vector<u8> data;if(!session.scores.save(data)){error="Unable to encode scores";return false;}
            if(!write_file(score_path,data))return false;saved_score_state=std::move(state);}
        const auto& cfg=session.persistent_config().bytes;std::vector<u8> config(cfg.begin(),cfg.end());
        if(config!=saved_config_state){if(!write_file(config_path,config))return false;saved_config_state=std::move(config);}
        return true;
    }
    bool save_replay(u32 slot,const char* name){
        if(slot>99||!name||std::strlen(name)>8)return false;std::vector<u8> data;
        if(!session.save_replay(name,data,true,frame_statistics.slowdown())){error="No active recording to save";return false;}
        const bool touch=session.recording.uses_touch();char path[80];std::snprintf(path,sizeof(path),"/save/replay/%s_%.2u.%s",replay_prefix,slot,touch?"rpyx":"rpy");
        if(!write_file(path,data))return false;
        std::snprintf(path,sizeof(path),"/save/replay/%s_%.2u.%s",replay_prefix,slot,touch?"rpy":"rpyx");std::remove(path);return true;
    }
    bool stage_music_held()const{return kPortTitle!=14&&session.state.stage==6&&session.battle&&session.battle->frame<300&&!session.state.demo;}
    bool music_follows_pause()const{
#if PORT_TITLE == 14
        if(session.state.spell_practice_id>=0){
            // Retail448ef0 pauses music even for a forced replay exit.
            const auto* menu=session.pause_menu.get();
            if(!menu||!menu->replay||(menu->state!=2&&!menu->forced_exit))return false;
        }
#endif
        return !stage_music_held();
    }
    bool play_stage_music(u32 stage,bool activation=false){
        if(session.state.demo)return true;
#if PORT_TITLE == 14
        // Retail43697f skips direct-entry music in spell practice. Its ECL
        // -3/-1 requests remain responsible for selecting a track.
        if(activation&&session.state.spell_practice_id>=0)return true;
#endif
        if(!audio.music(stage_music(stage))){error=audio.error;return false;}
        audio.pause_music(kPortTitle!=14&&stage==6);return true;
    }
    bool pause(){if(!session.pause())return false;
#if PORT_TITLE == 14
        audio.pause_sounds(true);
#endif
        if(music_follows_pause())audio.pause_music(true);return true;}
    bool resume(){if(!session.resume())return false;
#if PORT_TITLE == 14
        audio.pause_sounds(false);
#endif
        if(music_follows_pause())audio.pause_music(false);
#if PORT_TITLE == 14
        return audio_events();
#else
        return true;
#endif
    }
#if PORT_TITLE == 14
    bool game_over_audio(bool replay){
        audio.pause_sounds(true);
        if(replay){if(music_follows_pause())audio.pause_music(true);}
        else if(session.state.spell_practice_id<0){
            audio.save_music();audio.pause_music(false);
            if(!audio.music(17)){error=audio.error;return false;}
        }
        return true;
    }
#endif
    bool audio_events(bool result_entry=false){
        if(session.ending){auto& ending=*session.ending;for(const auto sound:ending.sounds)audio.effects.enqueue(sound);
            if(ending.music_request>=0){audio.pause_music(false);if(!audio.music(ending.music_request)){error=audio.error;return false;}}
            if(ending.music_fade>=0)audio.fade_music(ending.music_fade);
        }
#if PORT_TITLE != 14
        if(session.pause_menu){for(const auto sound:session.pause_menu->sounds)audio.effects.enqueue(sound);session.pause_menu->sounds.clear();}
#else
        const auto menu_sounds=[this](){if(session.pause_menu){for(const auto sound:session.pause_menu->sounds)audio.effects.enqueue(sound);session.pause_menu->sounds.clear();}};
#endif
        if(session.title){
            for(const auto sound:session.title->sounds)audio.effects.enqueue(sound);
            if(session.title->music_pause)audio.pause_music(true);
            if(session.title->music_fade>=0)audio.fade_music(session.title->music_fade);
            if(session.title->music_request>=0){audio.pause_music(false);if(!audio.music(session.title->music_request)){error=audio.error;return false;}}
            if(session.title->volume_changed){audio.music_volume=session.config.music_volume();audio.effects.master_volume=session.config.sound_volume();audio.refresh_volume();}
            session.title->sounds.clear();
        }
        if(!session.battle){
#if PORT_TITLE == 14
            menu_sounds();
#endif
            return true;}
        for(const auto& event:session.battle->events){
            switch(event.kind){
            case BattleEventKind::Sound:
                if(event.positional)audio.effects.positioned(event.value,event.position.x);else audio.effects.enqueue(event.value);
                break;
            case BattleEventKind::StopSound:audio.effects.stop(event.value);break;
#if PORT_TITLE == 14
            // Retail4373b0 clears only sounds queued before the Player death callback.
            case BattleEventKind::GameOver:
                if(!game_over_audio(event.value!=0))return false;
                menu_sounds();break;
            case BattleEventKind::PauseResume:
                audio.pause_sounds(false);
                if(event.value){
                    if(!audio.restore_music()){error="Continue battle music restoration failed";return false;}
                    audio.discard_saved_music();
                }else if(music_follows_pause())audio.pause_music(false);
                break;
#endif
            case BattleEventKind::SoundPan:audio.effects.pan(event.value,event.extra);break;
            case BattleEventKind::StageMusic:if(!play_stage_music(event.value))return false;break;
            case BattleEventKind::BossMusic:
                if(!audio.music(stage_music(event.value,true))){error=audio.error;return false;}break;
            case BattleEventKind::MusicResume:audio.pause_music(false);break;
            case BattleEventKind::MusicFade:audio.fade_music(i32(event.position.x*60.f));break;
            case BattleEventKind::MusicStop:if(!audio.music(-1)){error=audio.error;return false;}break;
            default:break;
            }
        }
        session.battle->events.clear();
#if PORT_TITLE == 14
        // A completed result enters after the battle callbacks, without a death marker.
        if(result_entry&&!game_over_audio(false))return false;
        menu_sounds();
#endif
        return true;
    }
#if PORT_TITLE == 14
    DialogueEffects* dialogue_text_device()override{return this;}
    bool dialogue_text(const DialogueText& request)override{
        renderer.flush();
        auto* vm=session.animations.find(request.animation);
        if(!vm){error="TH14 dialogue text animation missing";return false;}
        if(!fonts.text(*vm,request)){error=fonts.error;return false;}
        return true;
    }
#endif
    bool text_events(){
        if(session.ending){renderer.flush();for(const auto& request:session.ending->text_requests){auto* vm=session.animations.find(request.animation);if(vm&&!fonts.text(*vm,request)){error=fonts.error;return false;}}session.ending->text_requests.clear();}
        if(session.title){renderer.flush();for(const auto& request:session.title->text_requests){auto* vm=session.animations.find(request.animation);if(vm&&!fonts.text(*vm,request)){error=fonts.error;return false;}}session.title->text_requests.clear();}
        if(!session.battle)return true;
        renderer.flush();
        // A dialogue plate binds its own sprite with its own walk, and the generation's line arrives
        // before that: th16 and th17 write their first line into a plate standing at +0xac, due at
        // plate time 8, while th12's plate opens with its sprite command at time 0. A request whose
        // animation has no sprite yet is kept for the frame the plate reaches it, and dropped when
        // the animation is gone, so a line never outlives the plate that carries it.
        std::vector<DialogueText> pending;
        for(auto it=waiting_text.begin();it!=waiting_text.end();){
            if(!session.animations.find(it->animation)){it=waiting_text.erase(it);continue;}
            pending.push_back(*it);++it;
        }
        for(const auto& request:session.battle->dialogue_text_requests){
            // A new line for the same plate replaces the one still waiting.
            pending.erase(std::remove_if(pending.begin(),pending.end(),
                [&](const DialogueText& held){return held.animation==request.animation;}),pending.end());
            pending.push_back(request);
        }
        waiting_text.clear();
        for(const auto& request:pending){
            auto* vm=session.animations.find(request.animation);
            if(!vm)continue;
            if(!fonts.text(*vm,request)){
                if(fonts.waiting){waiting_text.push_back(request);continue;}
                error=fonts.error;return false;
            }
        }
        session.battle->dialogue_text_requests.clear();return true;
    }
    bool prepare(StageResources& stage)override{
        renderer.flush();
        graphics.error.clear();
#if PORT_TITLE == 14
        // First entry waits before battle construction; later entries keep
        // the existing world until the incoming resources are ready.
        {
            boot_uploads.clear();boot_upload_index=0;
            boot_stage_owner=&stage;
            boot_uploads={{&stage.background,u16((stage.stage_number&1)+3)},{&stage.logo,6},{&stage.enemies,9}};
            for(u32 i=0;i<stage.ecl_animations.size();++i)if(!stage.ecl_animation_names[i].empty())boot_uploads.push_back({&stage.ecl_animations[i],u16(10+i)});
            if(!boot_uploads.empty()){
                if(!boot_loading.begin(session.animations,session.resources.core.ascii)){graphics.error="TH14 stage loading animation creation failed";return false;}
                std::printf("[loading14] stage entry; %u resource uploads pending\n",u32(boot_uploads.size()));
                return true;
            }
        }
#endif
        for(auto* file:{&stage.background,&stage.logo,&stage.enemies})if(!graphics.preload(*file)){error=graphics.error;return false;}
#if PORT_TITLE == 14 || PORT_TITLE == 16
        for(auto& file:stage.ecl_animations)if(!graphics.preload(file)){error=graphics.error;return false;}
#endif
        return true;
    }
#if PORT_TITLE == 14
    bool core_ready()const override{return core_loading_done;}
    bool stage_ready()const override{return boot_uploads.empty();}
    bool prepare_stage_phase(StageResources& stage,StageResourceEffects::Phase phase)override{
        renderer.flush();graphics.error.clear();
        if(!stage_uploads.begin(stage,phase)){graphics.error="TH14 stage upload owner still pending";return false;}
        return true;
    }
    bool stage_phase_ready(StageResourceEffects::Phase phase)const override{return stage_uploads.ready(phase);}
    void finish_stage_phases(StageResources& stage,u32)override{stage_uploads.finish(stage);}
    void cancel_stage_phases(StageResources& stage,u32)override{
        // Queued raw resource references must disappear before GPU teardown
        // or StageResources destruction. release also covers boot ownership.
        stage_uploads.cancel(stage);release(stage);
    }
    bool defer_ending_loading()const override{return true;}
    bool begin_ending_loading()override{
        if(!boot_loading.begin(session.animations,session.resources.core.ascii)){graphics.error="TH14 ending loading animation creation failed";return false;}
        return true;
    }
    void finish_ending_loading()override{boot_loading.finish(session.animations);std::printf("[loading14] ending ANM ready; interrupt1 delivered\n");}
#endif
    const std::string& last_error()const override{return graphics.error;}
    void release(StageResources& stage)override{
#if PORT_TITLE == 14
        stage_uploads.cancel(stage);
        if(boot_stage_owner==&stage){boot_uploads.clear();boot_upload_index=0;boot_stage_owner=nullptr;boot_loading.finish(session.animations);}
#endif
        renderer.flush();renderer.invalidate();
        for(auto* file:{&stage.background,&stage.logo,&stage.enemies})graphics.unload(*file);
#if PORT_TITLE == 14 || PORT_TITLE == 16
        for(auto& file:stage.ecl_animations)graphics.unload(file);
#endif
    }
    bool prepare_animation(AnmResource& file)override{renderer.flush();return graphics.preload(file);}
#if PORT_TITLE == 14
    bool prepare_manual_image(AnmResource& file,u32 index,const u8* bytes,u32 size)override{renderer.flush();renderer.invalidate();return graphics.manual_image(file,index,bytes,size);}
#endif
    void release_animation(AnmResource& file)override{renderer.flush();renderer.invalidate();graphics.unload(file);}
    bool read_replay(const std::string& path,std::vector<u8>& bytes)override{return read_file(path.c_str(),bytes,64*1024*1024);}

    bool read_archive() {
        SDL_IOStream* io=SDL_IOFromFile("/th11.dat","rb");
        if(!io){error="Unable to open /th11.dat";return false;}
        const Sint64 size=SDL_GetIOSize(io);
        if(size<=0||size>256*1024*1024){SDL_CloseIO(io);error="Invalid th11.dat size";return false;}
        archive.resize(size_t(size));
        const size_t got=SDL_ReadIO(io,archive.data(),archive.size());
        SDL_CloseIO(io);
        if(got!=archive.size()){error="Unable to read /th11.dat";return false;}
        return resources.open_archive(archive.data(),u32(archive.size()));
    }

    bool initialize() {
        if(initialized){if(!audio.initialize(resources)){error=audio.error;return false;}return true;}
        if(!graphics.initialize()){error=graphics.error;return false;}
#if PORT_TITLE == 14
        session.animations.texture_high_precision=false;
        graphics.texture_high_precision=&session.animations.texture_high_precision;
        std::printf("[clock14] monotonic ticks=%u; initial seed=%u\n",initial_ticks,u32(u16(initial_ticks)));
#endif
        if(!read_archive()){if(error.empty())error=resources.error();return false;}
        if(!audio.initialize(resources)){error=audio.error;return false;}
        if(!fonts.initialize(
#if PORT_TITLE==14
            &session.font_bitmap
#endif
        )){error=fonts.error;return false;}
        mkdir("/save",0777);mkdir("/save/replay",0777);
        if(SDL_GetPathInfo(score_path,nullptr)){std::vector<u8> saved;if(!read_file(score_path,saved,4*1024*1024)||!session.load_scores(saved.data(),u32(saved.size()))){error=std::string("Invalid ")+score_path+": "+session.scores.error;return false;}}
        if(SDL_GetPathInfo(config_path,nullptr)){std::vector<u8> saved;if(!read_file(config_path,saved,u32(session.config.bytes.size()))||!session.config.open(saved.data(),u32(saved.size()))){error=std::string("Invalid ")+config_path;return false;}saved_config_state=saved;}
        audio.music_volume=session.config.music_volume();audio.effects.master_volume=session.config.sound_volume();audio.refresh_volume();
        session.recording_timestamp=u64(std::time(nullptr));
        if(!session.open_title(resources,true)){error=session.error;return false;}
        auto& core=session.resources.core;
#if PORT_TITLE == 14
        // Upload real pending resources between frames so the original loading
        // ANM can update and draw while GPU work remains. Its random children
        // follow script17's own clock, never a captured RNG count.
        for(auto* file:{&core.ascii,&core.text})if(!graphics.preload(*file)){error=graphics.error;return false;}
        if(!boot_loading.begin(session.animations,core.ascii)){error="TH14 loading animation creation failed";return false;}
        boot_uploads={{&core.effect,8},{&core.bullet,7},{&core.enemy,9},{&core.front,5},{&core.title,24},{&core.title_variant,25},{&core.players[0],7},{&core.players[1],7},{&core.players[2],7}};
        boot_upload_index=0;std::printf("[loading14] ascii script17 started; %u resource uploads pending\n",u32(boot_uploads.size()));
        boot_stage_owner=nullptr;
#else
#if PORT_TITLE == 16
        if(!graphics.preload(core.effect)){error=graphics.error;return false;}
#endif
        for(AnmResource* file:{&core.text,&core.ascii,&core.bullet,&core.enemy,&core.front,&core.title,&core.title_variant,&core.players[0],&core.players[1],&core.players[2]})
            if(!graphics.preload(*file)){error=graphics.error;return false;}
#if PORT_TITLE == 16
        if(!graphics.preload(core.players[3])){error=graphics.error;return false;}
        for(auto& file:core.season_players)if(!graphics.preload(file)){error=graphics.error;return false;}
#endif
#endif
        renderer.viewport={0,0,640,480,0,1};
        // GameBattle's STD owner creates backdrop VMs and publishes its camera.
        frame_statistics.window_start=double(SDL_GetTicks())*.001;
        initialized=true;return audio_events()&&text_events();
    }

    bool restart(u32 stage=1,i32 character=0,i32 subtype=0,i32 difficulty=1) {
#if PORT_TITLE == 14
        audio.discard_paused_sounds();
#endif
        if(!initialize())return false;
#if PORT_TITLE == 14
        if(!core_loading_done){if(!session.resources.prepare_core()){error=session.resources.error;return false;}core_loading_done=true;}
        boot_loading.finish(session.animations);boot_uploads.clear();boot_upload_index=0;
        boot_stage_owner=nullptr;stage_uploads.cancel_all();
#endif
        if(!save_scores())return false;session.recording_timestamp=u64(std::time(nullptr));
        renderer.invalidate();
        auto& core=session.resources.core;
#if PORT_TITLE == 14 || PORT_TITLE == 16
        graphics.unload(core.effect);
#endif
        for(AnmResource* file:{&core.text,&core.ascii,&core.bullet,&core.enemy,&core.front,&core.title,&core.title_variant,&core.players[0],&core.players[1],&core.players[2]})graphics.unload(*file);
#if PORT_TITLE == 16
        graphics.unload(core.players[3]);for(auto& file:core.season_players)graphics.unload(file);
#endif
        if(session.resources.stage)for(AnmResource* file:{&session.resources.stage->background,&session.resources.stage->logo,&session.resources.stage->enemies})graphics.unload(*file);
#if PORT_TITLE == 14 || PORT_TITLE == 16
        if(session.resources.stage)for(auto& file:session.resources.stage->ecl_animations)graphics.unload(file);
#endif
        if(!session.begin(resources,stage,character,subtype,difficulty,false)){error=session.error;return false;}
        frame_statistics.reset_run();
#if PORT_TITLE == 14 || PORT_TITLE == 16
        if(!graphics.preload(core.effect)){error=graphics.error;return false;}
#endif
        for(AnmResource* file:{&core.text,&core.ascii,&core.bullet,&core.enemy,&core.front,&core.title,&core.title_variant,&core.players[0],&core.players[1],&core.players[2],&session.resources.stage->background,&session.resources.stage->logo,&session.resources.stage->enemies})
            if(!graphics.preload(*file)){error=graphics.error;return false;}
#if PORT_TITLE == 16
        if(!graphics.preload(core.players[3])){error=graphics.error;return false;}
        for(auto& file:core.season_players)if(!graphics.preload(file)){error=graphics.error;return false;}
#endif
        if constexpr(kPortTitle==14)audio.discard_saved_music();
#if PORT_TITLE == 14
        if(session.state.phase==GameSessionPhase::loading)return true;
#endif
        if(!play_stage_music(session.state.stage,true))return false;
        return audio_events()&&text_events();
    }

    bool tick(u32 held,bool pause_key=false) {
        if(!initialize())return false;
#if PORT_TITLE == 14
        if(stage_uploads.pending()){
            renderer.flush();graphics.error.clear();
            if(!stage_uploads.advance([&](const auto& job){return graphics.preload_chunk(*job.resource,job.chunk);})){ 
                error=graphics.error.empty()?"TH14 staged resource upload failed":graphics.error;return false;
            }
            // A successful stage upload continues through the normal session,
            // Player/HUD/old Stage callbacks and draw below, without a second
            // ANM update or a loading-frame return.
        }
        if(boot_upload_index<boot_uploads.size()){
            if(!session.animations.update(true)||!session.animations.update(false)){error="TH14 loading ANM update failed";return false;}
            const auto job=boot_uploads[boot_upload_index];
            if(!core_loading_done&&!session.resources.load_core_job(boot_upload_index)){error=session.resources.error;return false;}
            if(!graphics.preload(*job.resource)){error=graphics.error;return false;}
            if(!session.animations.prepare_resource(*job.resource,job.file)){error=session.animations.last_error_text();return false;}
            if(++boot_upload_index==boot_uploads.size()){
                core_loading_done=true;
                boot_loading.finish(session.animations);boot_uploads.clear();boot_upload_index=0;
                boot_stage_owner=nullptr;
                std::printf("[loading14] resource uploads complete; interrupt1 delivered\n");reset_frame_window();
                if(session.state.phase==GameSessionPhase::loading){
                    const bool existing_battle=bool(session.battle);
                    if(!session.finish_loading()){error=session.error;return false;}
                    if(!existing_battle){frame_statistics.reset_run();audio.effects.reset();
                        if(session.state.phase==GameSessionPhase::stage&&!play_stage_music(session.state.stage,true))return false;}
                    if(!audio_events()||!text_events())return false;
                }
            }
            // Resource work still owns a physical draw/present callback.
            // Keep session/input advancement held while its loading ANM draws.
            if(!session.draw(renderer,&frame_text)){error=session.error;return false;}
            th14_consume_deferred_captures(session.animations.deferred_captures,session,graphics,renderer);
            graphics.present();
            if(!session.sample_spell_clock(double(SDL_GetTicksNS())*1e-9)){error="Invalid spell timing state";return false;}
            return true;
        }
#endif
        const auto before=session.state.phase;
#if PORT_TITLE == 14
        const bool ending_load_pending=session.ending&&session.ending->resource_loading();
#endif
        const GameSessionInput input{held,0,0,pause_key,bool(held&0x100),bool(held&0x2),frame_statistics.fps};
#if PORT_TITLE == 14
        if(session.battle)session.battle->th14_current_music=audio.current_music();
#endif
        if(!session.update(input)){error=session.error;return false;}
#if PORT_TITLE == 14
        if(session.ending&&session.ending->resource_loading()){
            if(ending_load_pending){
                if(!session.ending->finish_resource_loading()){error=session.ending->error;return false;}
            }else std::printf("[loading14] ending ANM pending: %s\n",session.ending->resource_loading_name().c_str());
        }
#endif
        const auto after=session.state.phase;
#if PORT_TITLE == 14
        const bool death_event=session.battle&&std::any_of(session.battle->events.begin(),session.battle->events.end(),[](const auto& event){return event.kind==BattleEventKind::GameOver;});
        const bool resume_event=session.battle&&std::any_of(session.battle->events.begin(),session.battle->events.end(),[](const auto& event){return event.kind==BattleEventKind::PauseResume;});
        const bool was_menu=before==GameSessionPhase::paused||before==GameSessionPhase::game_over;
        const bool is_menu=after==GameSessionPhase::paused||after==GameSessionPhase::game_over;
        if(was_menu&&!is_menu&&!resume_event)audio.discard_paused_sounds();
        if(!was_menu&&after==GameSessionPhase::paused&&!death_event)audio.pause_sounds(true);
#endif
        if(before!=GameSessionPhase::stage&&after==GameSessionPhase::stage&&session.state.frame==0)frame_statistics.reset_run();
        if(session.pause_menu)session.pause_menu->slowdown=frame_statistics.slowdown();
        if(session.title&&session.title->screen==TitleScreen::Results)session.title->result_slowdown=frame_statistics.slowdown();
        if(before!=GameSessionPhase::stage&&after==GameSessionPhase::stage
#if PORT_TITLE == 14
            &&!resume_event
#endif
        ){
            if(before==GameSessionPhase::paused&&session.state.frame!=0){if(music_follows_pause())audio.pause_music(false);}
            else if(kPortTitle==14&&before==GameSessionPhase::game_over&&session.state.frame!=0){
                if(!audio.restore_music()){error="Continue battle music restoration failed";return false;}
            }
            else{audio.effects.reset();if(!play_stage_music(session.state.stage,true))return false;}
        }
        if(kPortTitle==14&&before==GameSessionPhase::game_over&&after!=GameSessionPhase::game_over
#if PORT_TITLE == 14
            &&!resume_event
#endif
        )audio.discard_saved_music();
        if(before!=GameSessionPhase::paused&&after==GameSessionPhase::paused&&music_follows_pause()
#if PORT_TITLE == 14
            &&!death_event
#endif
        )audio.pause_music(true);
        if(before!=GameSessionPhase::game_over&&after==GameSessionPhase::game_over){
            session.pause_menu->timestamp=u64(std::time(nullptr));
#if PORT_TITLE != 14
            audio.pause_music(false);if(!audio.music(17)){error=audio.error;return false;}
#endif
        }
        if(before==GameSessionPhase::ending&&session.title)session.title->result_timestamp=u64(std::time(nullptr));
        if(session.title&&session.title->replay_scan_requested)scan_replays();
        if(session.title&&session.title->screen==TitleScreen::ReplaySave){auto& menu=*session.title;
            if(menu.substate==3&&!menu.pending_replay){const u64 stamp=u64(std::time(nullptr));std::memcpy(session.recording.header.data()+12,&stamp,8);auto entry=std::make_shared<ReplayMenuEntry>();
                if(!session.save_replay("        ",entry->file,true,frame_statistics.slowdown())||!entry->replay.open(entry->file.data(),u32(entry->file.size()))){error="Completed replay metadata unavailable";return false;}menu.pending_replay=std::move(entry);
            }
            if(menu.replay_save_requested){if(!save_replay(menu.replay_file+1,menu.entered_name.data()))return false;menu.replay_save_requested=false;menu.pending_replay.reset();scan_replays();if(!save_scores())return false;}
        }
        if(session.pause_menu){auto& menu=*session.pause_menu;
            if(menu.capture_requested){
                auto* vm=session.animations.find(menu.background_animation);if(!vm||!vm->sprite||!vm->resource){error="Pause screenshot sprite missing";return false;}
                const auto& sprite=*vm->sprite;const u32 target=graphics.texture(*vm->resource,sprite.texture);renderer.flush();
                i32 from[]={32,16,416,464};u32 source=GraphicsDevice::screen;
#if PORT_TITLE == 14
                const auto capture=th14_immediate_capture_source(session);
                std::copy(capture.rectangle,capture.rectangle+4,from);
                if(capture.text_intermediate){source=graphics.texture(session.resources.core.text,3);if(!source){error="Pause capture source texture missing";return false;}}
#endif
                const i32 to[]={i32(sprite.x),i32(sprite.y),i32(sprite.x+sprite.width),i32(sprite.y+sprite.height)};
                if(!graphics.backend.resample(source,from,target,to,nullptr,0,0)){error="Pause GPU capture failed";return false;}
                graphics.changed(target);renderer.invalidate();menu.capture_requested=false;
            }
            if(menu.scan_requested)scan_replays();
            if(menu.recording_metadata_requested){menu.timestamp=u64(std::time(nullptr));std::memcpy(session.recording.header.data()+12,&menu.timestamp,8);}
            if(menu.save_requested){if(!save_replay(menu.cursor.selected+1,menu.entered_name.data()))return false;menu.save_requested=false;scan_replays();if(!save_scores())return false;}
        }
#if PORT_TITLE != 14
        if(session.battle&&after==GameSessionPhase::stage&&!session.battle->spell_timing.update(session.battle->spell_flags,session.battle->spells.frame_count,double(SDL_GetTicks())*.001,session.state.replay)){error="Invalid spell timing state";return false;}
#endif
        if(!audio_events(
#if PORT_TITLE == 14
            before!=GameSessionPhase::game_over&&after==GameSessionPhase::game_over&&!death_event
#endif
        )||!text_events())return false;
        audio.update();audio.pump();
        frame_statistics.sample(double(SDL_GetTicks())*.001,after==GameSessionPhase::stage&&session.battle&&session.battle->stage_active&&!session.state.replay);
        frame_text.clear();const auto label=frame_statistics.label();frame_text.add(label.text.c_str(),label.position,label.style);
        if(!session.draw(renderer,&frame_text)){error=session.error;return false;}
#if PORT_TITLE == 14
        th14_consume_deferred_captures(session.animations.deferred_captures,session,graphics,renderer);
#endif
        graphics.present();
#if PORT_TITLE == 14
        // 46a6d7/46a933 call41c800 whenever the spell manager is alive,
        // including the frame that opens the spell-result menu.
        if(!session.sample_spell_clock(double(SDL_GetTicksNS())*1e-9)){error="Invalid spell timing state";return false;}
#endif
        return true;
    }
    bool return_to_title(){
#if PORT_TITLE == 14
        audio.discard_paused_sounds();
#endif
        if(!save_scores())return false;
        if(!session.return_to_title()){error=session.error;return false;}
        if constexpr(kPortTitle==14)audio.discard_saved_music();
        audio.effects.reset();return true;
    }
    void scan_replays(){
        if(!session.title&&!session.pause_menu)return;
        auto load=[&](u32 slot,const std::string& path){std::vector<u8> bytes;if(!read_file(path.c_str(),bytes,64*1024*1024))return;
            auto entry=std::make_shared<TitleMenu::ReplayEntry>();if(!entry->replay.open(bytes.data(),u32(bytes.size())))return;
            entry->path=path;entry->replay.retain_metadata();if(session.title)session.title->replay_files[slot]=std::move(entry);else if(slot<25)session.pause_menu->replay_files[slot]=std::move(entry);};
        for(u32 slot=0;slot<25;++slot){char path[80];std::snprintf(path,sizeof(path),"/save/replay/%s_%.2u.rpy",replay_prefix,slot+1);load(slot,path);load(slot,std::string(path)+"x");}
        if(session.title&&session.title->screen==TitleScreen::Replays){std::vector<std::string> names;auto* dir=opendir("/save/replay");if(dir){while(auto* e=readdir(dir)){const std::string n=e->d_name;if(n.size()>=15&&n.rfind(std::string(replay_prefix)+"_ud",0)==0&&(n.substr(11)==".rpy"||n.substr(11)==".rpyx"))names.push_back(n);}closedir(dir);}
            std::sort(names.begin(),names.end());for(u32 i=0;i<names.size()&&i<50;++i)load(25+i,"/save/replay/"+names[i]);}
        if(session.title&&session.title->screen==TitleScreen::Replays)session.title->replay_scan_complete();
    }
};
Application app;
struct Key {const char* code;const char* sdl;u32 scan,vk;bool hosted=false;SDL_Scancode native=SDL_SCANCODE_UNKNOWN;};
#include "../../../portable/input/KeyboardMap.inc"
touhou::input::TouchController gestures;
touhou::sdl::FrameCadence cadence;
bool running=false,suspended=false;u32 loop_epoch=0;double previous_frame=-1;
std::array<u8,256> previous_scans{};
SDL_Joystick* controller=nullptr;
void add_controller(SDL_JoystickID id){if(!controller)controller=SDL_OpenJoystick(id);}
void initialize_controller(){
    if(controller){SDL_CloseJoystick(controller);controller=nullptr;}
    SDL_InitSubSystem(SDL_INIT_JOYSTICK);int count=0;auto* ids=SDL_GetJoysticks(&count);
    for(int i=0;i<count;++i)add_controller(ids[i]);SDL_free(ids);
}
u32 sample_controller(){
    if(app.session.title)app.session.title->controller_buttons=0;
    if(!controller)return 0;std::array<u8,128> buttons{};
    for(int i=0;i<std::min(128,SDL_GetNumJoystickButtons(controller));++i)if(SDL_GetJoystickButton(controller,i)){
        buttons[i]=128;if(i<32&&app.session.title)app.session.title->controller_buttons|=1u<<i;
    }
    const auto axis=[&](int index){const int value=index<SDL_GetNumJoystickAxes(controller)?SDL_GetJoystickAxis(controller,index):0;return i32(std::floor((value<0?value/32768.:value/32767.)*1000+.5));};
    i32 x=axis(0),y=axis(1);const auto hat=SDL_GetNumJoystickHats(controller)?SDL_GetJoystickHat(controller,0):0;
    if(hat&SDL_HAT_LEFT)x=-1000;if(hat&SDL_HAT_RIGHT)x=1000;if(hat&SDL_HAT_UP)y=-1000;if(hat&SDL_HAT_DOWN)y=1000;
    return controller_keys(0,buttons.data(),u32(buttons.size()),x,y,app.session.config.bytes.data());
}
touhou::input::TouchState touch_state(){
    touhou::input::TouchState s;auto& session=app.session;
    if(session.state.phase!=GameSessionPhase::stage||!session.battle||!session.battle->player)return s;
    if(session.state.replay){s.context=3;return s;}
    if(session.battle->dialogue&&session.battle->dialogue->active){s.context=2;return s;}
    const auto& player=*session.battle->player;const auto& p=player.motion.state;
    s.context=1;s.instance=int(session.state.stage);s.ready=player.state.life_state==1;
    s.x=p.position.x;s.y=p.position.y;s.fast=float(p.normal_speed)/128;s.slow=float(p.focus_speed)/128;
    s.min_x=-184;s.max_x=184;s.min_y=32;s.max_y=432;return s;
}
void clear_inputs(){th11_reset_browser_keyboard();SDL_ResetKeyboard();for(auto& k:keyboard_map)k.hosted=false;previous_scans.fill(0);gestures.reset();if(app.session.battle)app.session.battle->player_input.movement.touch_mode=0;}
void touch_event(unsigned type,int id,float x,float y){
    if(std::isfinite(x)&&std::isfinite(y))gestures.pointer(type,id,x,y,SDL_GetTicks(),touch_state(),false);
}
void cancel_touch(){
    gestures.cancel_transient();
    if(app.session.battle)app.session.battle->player_input.movement.touch_mode=0;
}
bool sample_and_tick(){
    SDL_Event event;while(SDL_PollEvent(&event)){
#if PORT_TITLE == 14
        if(event.type==SDL_EVENT_WINDOW_CLOSE_REQUESTED||event.type==SDL_EVENT_QUIT)app.session.request_host_close();
#endif
        // SDL owns gestures that start on the canvas; the browser bridge only
        // forwards gestures originating outside it, avoiding double delivery.
        if(event.type==SDL_EVENT_FINGER_CANCELED){cancel_touch();continue;}
        if(event.type==SDL_EVENT_FINGER_DOWN||event.type==SDL_EVENT_FINGER_MOTION||event.type==SDL_EVENT_FINGER_UP)
            touch_event(event.type==SDL_EVENT_FINGER_DOWN?0:event.type==SDL_EVENT_FINGER_MOTION?1:2,
                        int(event.tfinger.fingerID),event.tfinger.x,event.tfinger.y);
        if(event.type==SDL_EVENT_WINDOW_FOCUS_LOST)clear_inputs();
        else if(event.type==SDL_EVENT_JOYSTICK_ADDED)add_controller(event.jdevice.which);
        else if(event.type==SDL_EVENT_JOYSTICK_REMOVED&&controller&&SDL_GetJoystickID(controller)==event.jdevice.which){SDL_CloseJoystick(controller);controller=nullptr;int count=0;auto* ids=SDL_GetJoysticks(&count);for(int i=0;i<count;++i)add_controller(ids[i]);SDL_free(ids);}
    }
    bool keys[256]{};std::array<u8,256> scans{};const auto* physical=th11_browser_keyboard()?nullptr:SDL_GetKeyboardState(nullptr);
    for(const auto& k:keyboard_map)if(k.hosted||(physical&&k.native!=SDL_SCANCODE_UNKNOWN&&physical[k.native])){if(k.scan<256)scans[k.scan]=128;if(k.vk<256)keys[k.vk]=true;if(k.vk>=160&&k.vk<=165)keys[16+(k.vk-160)/2]=true;if(k.scan==28||k.scan==156)keys[13]=true;}
    if(app.session.title){auto& title=*app.session.title;for(u32 i=0;i<256;++i)title.key_edges[i]=scans[i]&~previous_scans[i];title.number_keys=0;for(u32 i=0;i<9;++i)if(keys[49+i])title.number_keys|=1u<<i;}
    previous_scans=scans;
    const auto sample=gestures.sample(touch_state(),SDL_GetTicks(),keys[16],keys[37]||keys[38]||keys[39]||keys[40]);
    for(u32 n=0;n<256;++n)keys[n]=keys[n]||sample.keys[n];
    if(auto* b=app.session.battle.get()){b->player_input.movement.touch_mode=sample.motion;b->player_input.movement.touch_x=sample.x;b->player_input.movement.touch_y=sample.y;}
    const u32 raw=sample_controller()|keyboard_keys(keys);
    const u32 held=(raw&~0x80100u)|((raw&0x80000)?256:0);
    return app.tick(held,(raw&256)!=0);
}
}
}

extern "C" {
EMSCRIPTEN_KEEPALIVE int th11_validate_file(unsigned kind,const unsigned char* data,unsigned size){
    if(kind==0){th11::ScoreFile scores;return scores.open(data,size);}
    if(kind==1){th11::Replay replay;return replay.open(data,size);}
    if(kind==2){th11::GameConfig config;return config.open(data,size);}
    return 0;
}
EMSCRIPTEN_KEEPALIVE int th11_save_scores(){return th11::sdl::app.save_scores();}
EMSCRIPTEN_KEEPALIVE int th11_save_replay(unsigned slot,const char* name){return th11::sdl::app.save_replay(slot,name);}
EMSCRIPTEN_KEEPALIVE int th11_initialize(){if(!th11::sdl::app.initialize())return 0;for(auto& k:th11::sdl::keyboard_map)k.native=SDL_GetScancodeFromName(k.sdl);th11::sdl::initialize_controller();return 1;}
// Readable while a load is in flight, which is the point: it is the only way to see where a load that never
// returns had got to. The browser harness polls it and shows it while the welcome panel is up.
EMSCRIPTEN_KEEPALIVE const char* th11_last_resource(){return th11::last_resource.c_str();}
#if TH11_DEVELOPMENT_HARNESS
EMSCRIPTEN_KEEPALIVE int th11_tick(unsigned held){return !th11::sdl::running&&th11::sdl::app.tick(held)?1:0;}
EMSCRIPTEN_KEEPALIVE int th11_probe_platform_tick(){return !th11::sdl::running&&th11::sdl::sample_and_tick()?1:0;}
EMSCRIPTEN_KEEPALIVE float th11_probe_player_x(){return th11::sdl::touch_state().x;}
EMSCRIPTEN_KEEPALIVE int th11_probe_touch_motion(){const auto* b=th11::sdl::app.session.battle.get();return b?b->player_input.movement.touch_mode:0;}
EMSCRIPTEN_KEEPALIVE int th11_probe_stage(unsigned stage,int character,int subtype,int difficulty){return th11::sdl::app.restart(stage,character,subtype,difficulty);}
EMSCRIPTEN_KEEPALIVE int th11_probe_finish(){auto& s=th11::sdl::app.session;if(!s.battle)return 0;s.economy.score_units=1234567;s.battle->completion.state.exit=th11::StageExit::Ending;return 1;}
EMSCRIPTEN_KEEPALIVE int th11_probe_complete(){auto& s=th11::sdl::app.session;
#if PORT_TITLE == 14
    if(s.state.phase!=th11::GameSessionPhase::stage||!s.battle||!s.battle->stage_active||s.battle->transitioning||s.battle->pending_stage)return 0;
#endif
    return s.battle&&s.battle->dialogue_stage_complete();}
EMSCRIPTEN_KEEPALIVE int th11_probe_dialogue(int id){auto& app=th11::sdl::app;return app.session.battle&&app.session.battle->start_dialogue(id)&&app.text_events();}
// A verification hook, not a game feature, and it sits with the other probes for that reason: the browser run's
// policy cannot dodge, so "the campaign reaches stage six and the ending" cannot be shown from the browser without
// staying alive. The stage machinery is what is under test there, not the player's dodging.
EMSCRIPTEN_KEEPALIVE int th11_probe_invincibility(unsigned frames){
    auto& s=th11::sdl::app.session;if(!s.battle||!s.battle->player)return 0;
    s.battle->player->state.invincibility.set(int(frames),&s.animations.rate);return 1;
}
EMSCRIPTEN_KEEPALIVE unsigned th11_text_writes(){return th11::sdl::app.fonts.writes;}
EMSCRIPTEN_KEEPALIVE int th11_audio_probe(unsigned command,int value,float x){
    auto& a=th11::sdl::app.audio;
    if(command==0)return a.music(value);
    if(command==1){a.effects.positioned(value,x);a.update();return 1;}
    if(command==2){for(unsigned n=1;n<=56;++n)a.sound_stop(n);a.effects.reset();return a.music(-1);}
    if(command==3){a.fade_music(value);return 1;}
    if(command==4){a.update();return 1;}
    return 0;
}
EMSCRIPTEN_KEEPALIVE const float* th11_audio_samples(){static float pcm[2048];return th11::sdl::app.audio.mix(pcm,1024)?pcm:nullptr;}
#endif
EMSCRIPTEN_KEEPALIVE const char* th11_error(){return th11::sdl::app.error.c_str();}
EMSCRIPTEN_KEEPALIVE unsigned th11_frame(){return th11::sdl::app.session.state.frame;}
EMSCRIPTEN_KEEPALIVE unsigned th11_phase(){return unsigned(th11::sdl::app.session.state.phase);}
// The stage is what tells a browser run apart from the title demo: the attract demo plays a fixed replay, so a
// stage number that changes, and a frame counter that advances inside it, is the evidence that a game is running.
EMSCRIPTEN_KEEPALIVE unsigned th11_stage(){return th11::sdl::app.session.state.stage;}
EMSCRIPTEN_KEEPALIVE unsigned th11_stage_frame(){const auto& s=th11::sdl::app.session.state;return s.frame;}
EMSCRIPTEN_KEEPALIVE int th11_return_title(){return th11::sdl::app.return_to_title()?1:0;}
EMSCRIPTEN_KEEPALIVE int th11_restart(){return th11::sdl::app.restart()?1:0;}
// The title menu's own state. A run that never leaves the title needs to say *where* in the title it is: the
// screen, its substate, the cursor and whether a start was requested are what separate "the keys never arrived"
// from "the keys arrived and the menu did not act on them".
EMSCRIPTEN_KEEPALIVE int th11_title(unsigned kind){const auto& s=th11::sdl::app.session;if(!s.title)return -1;
    switch(kind){case 0:return int(s.title->screen);case 1:return s.title->substate;case 2:return s.title->cursor.selected;
    case 3:return s.title->start_requested?1:0;case 4:return s.title->cursor.count;
#if PORT_TITLE == 14
    case 5:return s.title->unlock_progress;case 6:return s.title->unlock_timeout;
#endif
    default:return -1;}}
// What the game's own input object holds after a tick. The page can show that a key is down and the menu can show
// that it did not move, and those two together still cannot say whether the edge was ever produced in between.
EMSCRIPTEN_KEEPALIVE unsigned th11_input(unsigned kind){const auto& g=th11::sdl::app.session.game_input;
    switch(kind){case 0:return g.held;case 1:return g.pressed;case 2:return g.long_repeat;case 3:return g.released;default:return 0;}}
// Diagnostics for the page's health readout. These report what the allocator actually holds, so a run that
// ends in an out-of-bounds access can be told apart from one that merely grew: a footprint that climbs with
// every stage change is a leak, while a flat footprint at the moment of failure is corruption.
EMSCRIPTEN_KEEPALIVE unsigned th11_heap_bytes(){return unsigned(emscripten_get_heap_size());}
EMSCRIPTEN_KEEPALIVE unsigned th11_dynamic_allocs(){return unsigned(mallinfo().uordblks);}
EMSCRIPTEN_KEEPALIVE int th11_pause(){return th11::sdl::app.pause()?1:0;}
EMSCRIPTEN_KEEPALIVE int th11_resume(){return th11::sdl::app.resume()?1:0;}
EMSCRIPTEN_KEEPALIVE void th11_key(unsigned scan,unsigned down){for(auto& k:th11::sdl::keyboard_map)if(k.scan==scan)k.hosted=down!=0;}
EMSCRIPTEN_KEEPALIVE void th11_keys_clear(){th11::sdl::clear_inputs();}
EMSCRIPTEN_KEEPALIVE void th11_music_enabled(unsigned on){using namespace th11::sdl;app.audio.music_enabled=on!=0;app.audio.refresh_volume();}
EMSCRIPTEN_KEEPALIVE const unsigned* th11_audio_statistics(){return th11::sdl::app.audio.statistics();}
EMSCRIPTEN_KEEPALIVE void th11_loop_pause(unsigned on){using namespace th11::sdl;suspended=on!=0;app.audio.suspend(suspended);previous_frame=-1;cadence.reset();clear_inputs();app.reset_frame_window();}
EMSCRIPTEN_KEEPALIVE void th11_loop_stop(){using namespace th11::sdl;running=false;++loop_epoch;previous_frame=-1;cadence.reset();clear_inputs();app.audio.suspend(true);app.reset_frame_window();}
EMSCRIPTEN_KEEPALIVE void th11_audio_close(){th11::sdl::app.audio.close();}
EMSCRIPTEN_KEEPALIVE void th11_loop_start(){
    using namespace th11::sdl;if(running||!app.initialized)return;
    running=true;suspended=false;previous_frame=-1;cadence.reset();clear_inputs();app.audio.suspend(false);app.reset_frame_window();
    emscripten_request_animation_frame_loop([](double time,void* epoch)->EM_BOOL{
        if(!running||uintptr_t(epoch)!=loop_epoch)return EM_FALSE;
        const double begin=emscripten_get_now(),delta=previous_frame<0?0:(time-previous_frame)/1000.;previous_frame=time;
        if(suspended){cadence.reset();return EM_TRUE;}
        const auto ticks=cadence.advance(delta);bool ok=true;app.graphics.backend.defer=true;
        for(unsigned n=0;n<ticks&&ok;++n)ok=sample_and_tick();
        app.graphics.backend.commit();app.graphics.backend.defer=false;
        app.audio.pump();
        if(ticks)th11_browser_frame(ok?1:0,emscripten_get_now()-begin,ticks);
        if(!ok)running=false;return running?EM_TRUE:EM_FALSE;
    },reinterpret_cast<void*>(uintptr_t(++loop_epoch)));
}
EMSCRIPTEN_KEEPALIVE void th11_touch(unsigned type,int id,float x,float y){th11::sdl::touch_event(type,id,x,y);}
EMSCRIPTEN_KEEPALIVE void th11_touch_cancel(){th11::sdl::cancel_touch();}
EMSCRIPTEN_KEEPALIVE void th11_touch_options(unsigned enabled,unsigned mode,float sensitivity,unsigned two_finger,unsigned double_tap){using namespace th11::sdl;gestures.enabled=enabled!=0;gestures.unlimited=mode==1;gestures.sensitivity=std::isfinite(sensitivity)?std::clamp(sensitivity,1.f,3.f):1;gestures.two_finger=two_finger!=0;gestures.double_tap=double_tap!=0;if(gestures.set_mode(mode<=3?int(mode):0))if(app.session.battle)app.session.battle->player_input.movement.touch_mode=0;if(!enabled)gestures.cancel();}
EMSCRIPTEN_KEEPALIVE void th11_touch_controls(unsigned enabled,unsigned fire,unsigned focus,unsigned bomb,unsigned escape){using namespace th11::sdl;gestures.enabled=enabled!=0;gestures.controls(fire!=0,focus!=0,bomb,escape,0,0);}
EMSCRIPTEN_KEEPALIVE void th11_touch_stick(float x,float y){using namespace th11::sdl;gestures.stick_x=std::isfinite(x)?std::clamp(x/32767.f,-1.f,1.f):0;gestures.stick_y=std::isfinite(y)?std::clamp(y/32767.f,-1.f,1.f):0;}
// Shared-host ABI (mirrors th10/th20 cpp/sdl/GameHost.cpp). The portable
// eagler-host.mjs drives touch through these names; game entry points above
// stay TH11-specific for the development harness.
__attribute__((export_name("sdl_touch"))) void sdl_touch(unsigned type,int id,float x,float y){th11_touch(type,id,x,y);}
__attribute__((export_name("sdl_touch_cancel"))) void sdl_touch_cancel(){th11_touch_cancel();}
__attribute__((export_name("sdl_touch_options"))) void sdl_touch_options(unsigned on,unsigned free,float speed){using namespace th11::sdl;gestures.enabled=on!=0;gestures.unlimited=free!=0;gestures.sensitivity=std::isfinite(speed)?std::clamp(speed,1.f,3.f):1;if(!on)gestures.cancel();}
__attribute__((export_name("sdl_touch_gestures"))) void sdl_touch_gestures(unsigned two,unsigned taps){using namespace th11::sdl;gestures.two_finger=two!=0;gestures.double_tap=taps!=0;}
__attribute__((export_name("sdl_touch_mode"))) void sdl_touch_mode(unsigned mode){using namespace th11::sdl;if(gestures.set_mode(mode<=3?int(mode):0))if(app.session.battle)app.session.battle->player_input.movement.touch_mode=0;}
__attribute__((export_name("sdl_touch_controls"))) void sdl_touch_controls(unsigned shoot,unsigned slow,unsigned bomb,unsigned escape,float x,float y){using namespace th11::sdl;gestures.controls(shoot!=0,slow!=0,bomb,escape,x,y);}
__attribute__((export_name("sdl_loop_pause"))) void sdl_loop_pause(unsigned on){th11_loop_pause(on);}
__attribute__((export_name("sdl_music_resource_changed"))) void sdl_music_resource_changed(){}
}

