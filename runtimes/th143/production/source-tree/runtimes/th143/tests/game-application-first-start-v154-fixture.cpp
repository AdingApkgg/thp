#include "../src/ReclaimingAnmMenuWorldV1.hpp"
#include "../src/EnemyBulletTransformReset.hpp"
#include "../src/EnemyBossCounterTransfer.hpp"
#include "../src/EnemyManagerFloatCells.hpp"
#include "../src/HudScriptMessageInit.hpp"
#include "../src/HudScriptMessageFactory.hpp"
#include "../src/HudMessageTextDecode.hpp"
#include "../src/HudMessageControl.hpp"
#include "../src/HudMessageFlow.hpp"
#include "../src/HudMessageDialogInstruction.hpp"
#include "../src/TitleSceneNotice.hpp"
#include "campaign-preview-files-v61.hpp"
#include "campaign-score-file-v66.hpp"
static bool campaign_cold_title_active=false;
static std::vector<th143::u8> campaign_preview_input_pixels,campaign_preview_decoded_pixels;
#include "../src/HudMessage.hpp"
#include "../src/HudSpecialMessage.hpp"
#include "../src/MessageDialogFactory.hpp"
#include "../src/MessageDialogLoad.hpp"
#include "../src/MessageDialogUpdate.hpp"
#include "../src/MessageDialogPage.hpp"
#include "../src/MessageDialogCleanup.hpp"
#include "../src/ManualDialogFactory.hpp"
#include "../src/ManualDialogWorkers.hpp"
#include "../src/ManualDialogCleanup.hpp"
#include "../src/ManualDialogUpdate.hpp"
#include "../src/TitleManualPage.hpp"
#include "../src/TitleMusicEntry.hpp"
#include "../src/TitleOptionView.hpp"
#include "../src/TitleReplayWorker.hpp"
#include "../src/TitleReplayControlV2.hpp"
#include "../src/TitleReplayReturnActivation.hpp"
#include "../src/TitleReplayDraw.hpp"
#include "../src/ReplayPercentFormatV2.hpp"
#include "../src/GameReplayFileLoad.hpp"
#include "../src/TitleCleanup.hpp"
#include "../src/GameManagerReplayInit.hpp"
#include "../src/GameManagerReplayFrame.hpp"
#include "../src/GameReplayEndEntry.hpp"
#include "../src/FrameTimingCounter.hpp"
#include "../src/GameReplayFileWriteV3.hpp"
#include "../src/ReplaySaveControl.hpp"
#include "../src/ReplayNameControl.hpp"
#include "../src/PauseReplayPage.hpp"
#include "../src/ReplayNameDraw.hpp"
#include "../src/ReplaySaveDraw.hpp"
#include "../src/TitleNicknameEntry.hpp"
#include "../src/TitleNicknameControl.hpp"
#include "../src/TitleNicknameDraw.hpp"
#include "../src/NicknameKeyboardCapture.hpp"
#include "../src/TitleQuitControl.hpp"
#include "../src/ApplicationOwnerCleanup.hpp"
#include "../src/ExitConfigurationWrite.hpp"
#include "../src/CommonCleanup.hpp"
#include "../src/TitlePadConfigControl.hpp"
#include "../src/TitlePadConfigViewV2.hpp"
#include "../src/DevicePadButtonRead.hpp"
#include "../src/CheatAnimation.hpp"
#include "../src/AnmPositionInterpolationBegin.hpp"
#include "../src/PauseManualPage.hpp"
#include "../src/RootTransition.hpp"
#include <cstdio>
static th143::u32 campaign_dialog_owner=0;
static th143::AnmView campaign_dialog_view(th143::u32);
static bool campaign_dialog_create();
static bool campaign_dialog_read(th143::u32,void*,th143::u32);
static bool campaign_dialog_pump();
static bool campaign_manual_pump();
static bool campaign_manual_update(th143::u32,th143::u32&);
static bool campaign_manual_title(th143::u32&);
static bool campaign_manual_pause(th143::AnmView,th143::u32,th143::u32);
namespace th143 {struct PauseMenu;}
static bool campaign_failure_subpage_v152(th143::PauseMenu&,th143::u32);
static bool campaign_replay_pause(th143::AnmView,th143::u32,th143::u32);
static bool campaign_replay_playback_frame(th143::u32,th143::u32&);
static th143::TitleReplayCleanupHost* campaign_replay_cleanup_host();
static void campaign_replay_player_sample();
static bool campaign_replay_save_draw(th143::u32,th143::AnmView);
namespace th143 {struct PauseReplayPageHost;}
static th143::PauseReplayPageHost& campaign_results_replay_host();
namespace th143 {struct PauseManualPageHost;}
static th143::PauseManualPageHost& campaign_results_manual_host();
static bool campaign_replay_menu_recording_destroy(th143::u32);
static bool campaign_scene_menu_recording_destroy(th143::u32);
static bool campaign_scene_menu_recording_free(th143::u32);
static bool campaign_dialog_update(th143::u32,th143::u32&);
static bool campaign_dialog_destroy(th143::u32);

#include "../src/HudMessagePortraitCreate.hpp"
#include "../src/HudMessagePortraitControl.hpp"
#include "../src/HudMessageTextCallback.hpp"
#include "../src/HudMessageWindow.hpp"
#include "../src/HudMessageIndicatorPosition.hpp"
#include "../src/HudMessageText.hpp"
static bool campaign_message_storage(th143::u32,th143::AnmView&);
static bool campaign_message_release(th143::u32,bool);
static bool campaign_message_create(th143::i32);
static bool campaign_message_update(th143::u32,th143::i32&);
static bool campaign_message_destroy(th143::u32);
static bool campaign_hud_open_results(th143::HudMessageGlobals*);
#include "../src/EmitterInlineName.hpp"
#include "../src/EnemyPlayerSwap.hpp"
#include "../src/EnemyAnimationSignal.hpp"
#include "../src/EnemyRectangleClear.hpp"
#include "../src/EnemyActorExists.hpp"
#include "../src/EnemyBulletRandomApproach.hpp"
#include "../src/EnemyBulletRandomTurnApproach.hpp"

#include "../src/EnemyAnimationLayer.hpp"
#include "../src/EnemyPositionCopy.hpp"
#include "../src/EnemyActorLookup.hpp"
#include "../src/EclExternalRootReset.hpp"
#include "../src/EclThreadLifetime.hpp"
#include "../src/EnemyScriptFloatCells.hpp"
#include "../src/EnemyEffectSpawnRotated.hpp"
#include "../src/EnemyManagerIntegerCells.hpp"
#include "../src/EnemyScriptIntegerCells.hpp"
static bool campaign_laser_draw(unsigned,unsigned);
#include "../src/GameSceneMarker.hpp"
#include "../src/EnemyAnimationSecondaryAlpha.hpp"
#include "../src/TitleSceneReturn.hpp"
#include "../src/EclVariableTweenRuntime.hpp"
#include "../src/EnemyAnimationScale.hpp"
#include "../src/EnemyAnimationAlpha.hpp"
#include "../src/EnemyEffectSpawn.hpp"
static bool campaign_title_preview_launch();
static bool day1_notice_resume();
static bool campaign_achievement_unlock(th143::u32);
static bool campaign_achievement_callback(th143::u32,th143::u32,th143::u32&);
static const th143::u8* campaign_achievement_region(th143::u32,th143::u32);
static bool day1_notice_callback(th143::u32,th143::u32,th143::u32&);
static bool day1_notice_results_gate(th143::u32&,bool&);
static const th143::u8* day1_notice_region(th143::u32,th143::u32);

#include "../src/CameraOptionCleanup.hpp"
#include "../src/ResultsMenuDraw.hpp"
#include "../src/ResultsMenuIdle.hpp"
#include "../src/ResultsMenuExitV4.hpp"
static bool title_dodge_results_frame(th143::u32&);
#include "../src/SceneCompletionDays.hpp"
#include "../src/PlayerClearExit.hpp"
#include "../src/HudClearBonus.hpp"
#include "../src/ResultsMenu.hpp"
static bool title_dodge_complete_scene();
static bool campaign_finish_cleared_replay();
#include "../src/EnemyTimeScale.hpp"
#include "../src/EclThreadLifetime.hpp"
#include "../src/ScreenShakeLifecycle.hpp"
static bool title_shooting_create_shake(th143::i32,th143::i32,th143::i32);
static bool title_shooting_effect_callback(th143::u32,th143::u32,th143::u32&);
#include "../src/EnemyActorLifetime.hpp"
#include "../src/GameEnemyManagerSweepRuntime.hpp"
#include "../src/EnemySceneCommands.hpp"
#include "../src/SpecialCard.hpp"
#include "../src/AnmCenteredText.hpp"
static bool title_scene_special_update();
#include "../src/EnemyActorAddressSpace.hpp"
#include "../src/GamePlayerCameraAim.hpp"
static bool title_second_start_preview_join();
#include "../src/TitlePreviewTask.hpp"
#include "../src/GameEnemyManagerCleanupRuntime.hpp"
#include "../src/ManualDialogFactory.hpp"
#include "../src/ManualDialogWorkers.hpp"
#include "../src/ManualDialogCleanup.hpp"
#include "../src/ManualDialogUpdate.hpp"
#include "../src/TitleManualPage.hpp"
#include "../src/TitleMusicEntry.hpp"
#include "../src/TitleOptionView.hpp"
#include "../src/TitleReplayWorker.hpp"
#include "../src/TitleReplayControlV2.hpp"
#include "../src/TitleReplayReturnActivation.hpp"
#include "../src/TitleReplayDraw.hpp"
#include "../src/ReplayPercentFormatV2.hpp"
#include "../src/GameReplayFileLoad.hpp"
#include "../src/TitleCleanup.hpp"
#include "../src/GameManagerReplayInit.hpp"
#include "../src/GameManagerReplayFrame.hpp"
#include "../src/GameReplayEndEntry.hpp"
#include "../src/FrameTimingCounter.hpp"
#include "../src/GameReplayFileWriteV3.hpp"
#include "../src/ReplaySaveControl.hpp"
#include "../src/ReplayNameControl.hpp"
#include "../src/PauseReplayPage.hpp"
#include "../src/ReplayNameDraw.hpp"
#include "../src/ReplaySaveDraw.hpp"
#include "../src/TitleNicknameEntry.hpp"
#include "../src/TitleNicknameControl.hpp"
#include "../src/TitleNicknameDraw.hpp"
#include "../src/NicknameKeyboardCapture.hpp"
#include "../src/TitleQuitControl.hpp"
#include "../src/ApplicationOwnerCleanup.hpp"
#include "../src/ExitConfigurationWrite.hpp"
#include "../src/CommonCleanup.hpp"
#include "../src/TitlePadConfigControl.hpp"
#include "../src/TitlePadConfigViewV2.hpp"
#include "../src/DevicePadButtonRead.hpp"
#include "../src/CheatAnimation.hpp"
#include "../src/AnmPositionInterpolationBegin.hpp"
#include "../src/PauseManualPage.hpp"
#include "../src/RootTransition.hpp"
#include "../src/TitleReturnActivation.hpp"

// Original fixture composition: game-title-retry-reload-fixture.cpp

// Original fixture composition: game-title-retry-cleanup-fixture.cpp

// Original fixture composition: game-title-first-scene-failure-fixture.cpp

// Original fixture composition: game-title-first-scene-long-fixture.cpp

// Original fixture composition: game-title-graphics-session-fixture.cpp

// Original fixture composition: game-title-application-update-fixture.cpp

// Original fixture composition: game-title-device-input-fixture.cpp

// Original fixture composition: game-title-gameplay-draw-fixture.cpp

// Original fixture composition: game-title-gameplay-fixture.cpp

// Original fixture composition: game-title-root-start-fixture.cpp

// Original fixture composition: game-title-root-load-fixture.cpp

// Original fixture composition: game-title-root-factory-fixture.cpp

// Original fixture composition: game-title-scene-handoff-fixture.cpp

// Original fixture composition: game-title-scene-confirm-fixture.cpp

// Original fixture composition: game-title-scene-session-fixture.cpp

// Original fixture composition: game-title-scene-page-fixture.cpp

// Original fixture composition: game-title-saved-preview-image-fixture.cpp

// Original fixture composition: game-title-saved-preview-worker-fixture.cpp

// Original fixture composition: game-title-preview-image-fixture.cpp

// Original fixture composition: game-title-preview-worker-fixture.cpp

// Original fixture composition: game-title-scene-entry-fixture.cpp

// Original fixture composition: game-title-ready-control-fixture.cpp

// Original fixture composition: game-title-activation-fixture.cpp

// Original fixture composition: game-title-main-intro-fixture.cpp

// Original fixture composition: game-title-load-fixture.cpp

// Original fixture composition: game-common-draw-dispatch-fixture.cpp

// Original fixture composition: game-common-composition-fixture.cpp

// Original fixture composition: game-common-pooled-textures-fixture.cpp

// Original fixture composition: game-common-texture-targets-fixture.cpp

// Original fixture composition: game-common-texture-load-fixture.cpp

// Original fixture composition: game-common-load-fixture.cpp

// Original fixture composition: game-common-factory-fixture.cpp

// Original fixture composition: game-ascii-factory-fixture.cpp

// Original fixture composition: game-owner-runtime-fixture.cpp
#include "../src/GameOwnerRuntime.hpp"
#include "../src/AnmResourceWorld.hpp"
#include <cstdlib>
#include <memory>
#include <map>
using namespace th143;
#define API(name) extern "C" __attribute__((export_name(#name)))
static u32 campaign_selector4_diagnostic[4]{};
API(campaign_selector4_diagnostic) u32 campaign_selector4_diagnostic_read(u32 i){return i<4?campaign_selector4_diagnostic[i]:0;}
static std::map<std::string,std::vector<u8>> files;
static std::vector<std::array<u32,2>> allocations;
static std::vector<u32> frees;
static u32 fill=0,heap=0x6f000000;
struct FileServices:AnmResourceServices {
    bool read_animation_file(const std::string& n,bool,std::vector<u8>& out)override{auto i=files.find(n);if(i==files.end())return false;out=i->second;return true;}
    bool release_animation_texture(u32)override{return true;}
    bool create_animation_texture(const AnmTextureRequest& r,ResourceLoaderHost& memory,i32& status,u32& w,u32& h)override{
        if(r.kind==AnmTextureRequest::external)return false;
        u32 texture,vtable;if(!memory.allocate_resource_storage(16,false,texture)||!memory.allocate_resource_storage(0x60,false,vtable))return false;
        std::array<u8,0x60> zero{};const u32 describe=0x7002d000;
        if(!memory.write(vtable,zero.data(),zero.size())||!memory.write(texture,&vtable,4)||!memory.write(r.entry,&texture,4)||!memory.write(vtable+0x44,&describe,4))return false;
        status=0;w=r.width;h=r.height;return true;
    }
}file_services;
struct FrameServices:GameFrameServices {
    bool frame_input(GameInputFrame&)override{return false;}
    bool before_game_callback(u32,u32)override{return false;}
    bool after_game_callback(u32,u32,u32)override{return false;}
}frame_services;
static std::unique_ptr<AnmResourceWorld> world;
static std::unique_ptr<GameFrameRuntime> frames;
static std::unique_ptr<GameOwnerRuntime> owners;
struct OwnerServices:GameOwnerServices {
    bool reserve_game_owner(u32 token,u32 bytes)override{allocations.push_back({token,bytes});return true;}
    bool allocate_game_storage(u32 n,u32& token)override{token=heap;heap+=(std::max(1u,n)+15)&~15u;allocations.push_back({token,n});return true;}
    bool release_game_storage(u32 p)override{frees.push_back(p);return true;}
    bool request_game_resource(u32 slot,const char* n,u32& token)override{return world->request(slot,n,token);}
    bool read_player_shots(std::vector<u8>& out)override{auto i=files.find("pl00a.sht");if(i==files.end())return false;out=i->second;return true;}
    u8 game_allocation_fill()const override{return u8(fill);}
}owner_services;
static GameManagerInitGlobals globals;
static std::vector<u8> output;
API(allocate) void* allocate(u32 n){return std::malloc(n);}
API(release) void release(void* p){std::free(p);}
API(add_file) void add_file(const char* n,u32 nn,const u8* p,u32 pn){files[std::string(n,nn)]={p,p+pn};}
API(initialize) void initialize(u32 f){owners.reset();frames.reset();world.reset();allocations.clear();frees.clear();fill=f;heap=0x6f000000;world=std::make_unique<AnmResourceWorld>(file_services);frames=std::make_unique<GameFrameRuntime>(frame_services);owners=std::make_unique<GameOwnerRuntime>(*frames,*world,owner_services);world->viewport.scale=0;globals={};globals.new_game=1;globals.root_present=true;globals.random={54321,0,0};globals.game_state[8]=5;globals.game_state[9]=8;globals.game_state[12]=1;globals.game_state[13]=512;globals.game_state[14]=1;}
API(load_file) u32 load_file(u32 slot,const char* name,u32 nn){u32 token;if(!world->request(slot,std::string(name,nn),token))return 0;bool ready=false;while(!ready){i32 result;if(!world->pump(result)||result||!world->ready(ready))return 0;}return token;}
API(template_data) const u8* template_data(u32 p){return world->resource(p)->templates[0].data();}
API(create) u32 create(u32 entry,u32 mode){u32 result;if(!owners->create(entry,mode,globals,result))return 0;return result;}
API(dispatch) i32 dispatch(u32 draw){i32 result;if(!frames->dispatch(draw!=0,result))return -100;return result;}
API(region_data) const u8* region_data(u32 p,u32 n){output.resize(n);if(!owners->read(p,output.data(),n))return nullptr;return output.data();}
API(allocation_count) u32 allocation_count(){return allocations.size();}
API(allocation_token) u32 allocation_token(u32 i){return allocations[i][0];}
API(allocation_size) u32 allocation_size(u32 i){return allocations[i][1];}
API(owner_word) u32 owner_word(u32 i){static constexpr u32 tokens[]={GameOwnerRuntime::player_self,GameOwnerRuntime::equipment_self,GameOwnerRuntime::input_self,BulletPool::token_base,ItemPool::token_base,GameOwnerRuntime::laser_self,ScorePopups::token};return (owners->created&(1u<<i))?tokens[i]:0;}
API(game_data) const u32* game_data(){return globals.game_state.data();}
API(rng_data) const u8* rng_data(){static std::array<u8,16> r;std::memcpy(r.data(),&world->animation_rng,8);std::memcpy(r.data()+8,&globals.random,8);return r.data();}
API(free_count) u32 free_count(){return frees.size();}
API(free_word) u32 free_word(u32 i){return frees[i];}


#include "../src/GameAsciiRuntime.hpp"
static std::unique_ptr<GameAsciiRuntime> game_ascii;
API(ascii_create) u32 ascii_create(u32 font){game_ascii=std::make_unique<GameAsciiRuntime>(*frames,*world,owner_services);u32 result;return game_ascii->create(u8(font),result)?result:0;}
API(ascii_factory_data) const u8* ascii_factory_data(){return game_ascii->data.data();}
API(ascii_factory_global) u32 ascii_factory_global(){return game_ascii->global_owner;}
API(ascii_resource_data) const u8* ascii_resource_data(u32 p,u32 n){output.resize(n);return world->read(p,output.data(),n)?output.data():nullptr;}


#include "../src/GameCommonRuntime.hpp"
static std::unique_ptr<GameCommonRuntime> common_owner;
static std::vector<u8> common_launch;
static bool common_launch_failure=false;
struct CommonFactoryHost:RootFactoryHost {
    bool allocate_root(u32&)override{return false;}
    bool evict_managed_textures()override{return false;}
    bool wait_worker(u32,u32,u32&)override{return false;}
    bool sleep_worker(u32)override{return false;}
    bool close_worker(u32)override{return false;}
    bool launch_worker(u32 entry,u32 argument,u32 flags,u32& id,u32& handle)override{
        const u32 args[]={0,0,entry,argument,flags,GameCommonRuntime::self+0x18};
        const auto append=[&](const void* p,u32 n){auto* b=static_cast<const u8*>(p);common_launch.insert(common_launch.end(),b,b+n);};
        append(args,sizeof args);append(common_owner->data.data(),common_owner->data.size());append(frames->scheduler.data.data(),frames->scheduler.data.size());const u32 globals[]={common_owner->global_owner,game_ascii?game_ascii->global_owner:0};append(globals,sizeof globals);
        if(common_launch_failure)handle=0;else{id=0x55667788;handle=0x77770002;}return true;
    }
}common_factory_host;
API(common_initialize) void common_initialize(u32 f,u32 failure){common_owner.reset();game_ascii.reset();initialize(f);common_launch.clear();common_launch_failure=failure!=0;}
API(common_create) u32 common_create(){common_owner=std::make_unique<GameCommonRuntime>(*frames,owner_services,common_factory_host);u32 result;return common_owner->create(result)?result:0;}
API(common_owner_data) const u8* common_owner_data(){return common_owner->data.data();}
API(common_global) u32 common_global(){return common_owner->global_owner;}
API(common_launch_data) const u8* common_launch_data(){return common_launch.data();}
API(common_launch_bytes) u32 common_launch_bytes(){return common_launch.size();}


#include "../src/CommonLoad.hpp"
static std::array<std::vector<u8>,3> common_load_logs;
static GameFrameServices* common_load_frame_services=&frame_services;
static AnmResourceWorld* (*common_load_world_factory)(AnmResourceServices&)=nullptr;
static void (*common_load_storage_release_observer)(u32)=nullptr;
static std::vector<std::array<u32,2>> common_resource_allocations;
static void common_load_log(u32 kind,u32 value,const std::string& name){auto& b=common_load_logs[kind];const u32 header[]={value,u32(name.size())};auto* h=reinterpret_cast<const u8*>(header);b.insert(b.end(),h,h+8);b.insert(b.end(),name.begin(),name.end());}
struct CommonLoadFiles:FileServices {
    bool read_animation_file(const std::string& name,bool external,std::vector<u8>& out)override{common_load_log(1,external,name);const auto at=name.find_last_of("/\\");auto i=files.find(at==std::string::npos?name:name.substr(at+1));if(i==files.end())return false;out=i->second;return true;}
    void animation_storage_allocated(u32 p,u32 n,bool)override{common_resource_allocations.push_back({p,n});}
}common_load_files;
static AnmResourceServices* common_load_resource_services=&common_load_files;
struct CommonLoadOwnerServices:OwnerServices {
    bool release_game_storage(u32 p)override{if(common_load_storage_release_observer)common_load_storage_release_observer(p);return OwnerServices::release_game_storage(p);}
    bool request_game_resource(u32 slot,const char* name,u32& token)override{common_load_log(0,slot,name);return OwnerServices::request_game_resource(slot,name,token);}
}common_load_storage;
static bool common_archive=false;
static std::vector<u32> common_achievements;
struct CommonLoadPlatform:CommonLoadHost {
    bool read_common_file(const char* name,bool external,std::vector<u8>& out,bool& found)override{found=common_load_files.read_animation_file(name,external,out);return true;}
    bool common_archive_exists(const char* name,bool& found)override{found=common_archive;common_load_log(2,found,name);return true;}
    bool achievement(u32 id)override{common_achievements.push_back(id);return campaign_achievement_unlock(id);}
}common_load_platform;
struct CommonLoadAuxServices:GameAuxServices {
    bool auxiliary_surface(u32,u32,u32&)override{return false;}
    bool release_auxiliary_surface(u32)override{return false;}
    bool release_auxiliary_storage(u32,bool)override{return false;}
}common_load_aux_services;
static std::unique_ptr<GameAuxRuntime> common_auxiliary;
static std::unique_ptr<SaveData> common_save;
static std::unique_ptr<GameSaveRuntime> common_save_runtime;
static std::unique_ptr<GameSavedFile> common_loaded_save;
static std::unique_ptr<TrophyCatalog> common_trophies;
static std::unique_ptr<CommonLoadBindings> common_load_bindings;
static std::array<u8,0xa34> common_load_application;
static std::array<u8,0x57b0> common_load_audio;
#include "../src/GameCommonAudioPlatformV3.hpp"
#include "../src/OwnedCommonLoadAudio.hpp"
#include "../src/SoundPauseResume.hpp"
#include "../src/MusicSilentPump.hpp"
static std::array<u8,0xe0> natural_initial_game{};
API(campaign_initial_game) void campaign_initial_game(const u8* p,u32 n){if(n==natural_initial_game.size())std::memcpy(natural_initial_game.data(),p,n);}
static GameCommonAudioPlatformV3 campaign_audio_host{{common_load_audio.data()}};
#include "../src/ApplicationConfigurationMemoryPlatform.hpp"
struct CampaignConfigurationV82:ApplicationConfigurationMemoryPlatform {
 u32 generation=0;
 void reset(){ApplicationConfigurationMemoryPlatform::reset();generation=0;}
 bool write_configuration(u32 name,AnmView in,u32 n,u32& result)override{if(!ApplicationConfigurationMemoryPlatform::write_configuration(name,in,n,result))return false;++generation;return true;}
};
static CampaignConfigurationV82 campaign_configuration;
API(campaign_config_generation)u32 campaign_config_generation(){return campaign_configuration.generation;}
API(campaign_config_keyboard) void campaign_config_keyboard(const u8* p,u32 n){if(n==20)std::memcpy(campaign_configuration.keyboard.data(),p,n);}
API(campaign_config_file) void campaign_config_file(const u8* p,u32 n){campaign_configuration.file.assign(p,p+n);}
API(campaign_config_written) const u8* campaign_config_written(){return campaign_configuration.written.data();}
API(campaign_config_written_bytes) u32 campaign_config_written_bytes(){return campaign_configuration.written.size();}
API(campaign_config_events) const u32* campaign_config_events(){return campaign_configuration.events.data();}
API(campaign_config_event_words) u32 campaign_config_event_words(){return campaign_configuration.events.size();}
API(campaign_config_info) u32 campaign_config_info(u32 field){const u32 v[]={campaign_configuration.loads,campaign_configuration.last_read_present?1u:0u,u32(campaign_configuration.result)};return field<3?v[field]:0;}
static OwnedCommonLoadAudio campaign_common_audio{campaign_audio_host,campaign_audio_host};
API(campaign_audio_worker_field) u32 campaign_audio_worker_field(u32 i){const auto& p=campaign_audio_host;const u32 values[]={p.workers_started?1u:0u,p.preload_done?1u:0u,p.device_done?1u:0u,p.device_closed?1u:0u,p.archive_closed?1u:0u,p.bank.sleeps,p.bank.audio.get(0x57a0)};return i<7?values[i]:0;}
static void campaign_audio_reset_state(){campaign_audio_host.reset();}
API(campaign_audio_assets_reset) void campaign_audio_assets_reset(){campaign_configuration.reset();campaign_audio_reset_state();campaign_audio_host.bank.catalog.clear();campaign_audio_host.bank.waves.clear();campaign_audio_host.metadata.clear();campaign_audio_host.archive.clear();campaign_audio_host.device.filenames.clear();}
API(campaign_audio_catalog) void campaign_audio_catalog(const u8* p,u32 n){campaign_audio_host.bank.catalog.assign(p,p+n);}
API(campaign_audio_metadata) void campaign_audio_metadata(const u8* p,u32 n){campaign_audio_host.metadata.assign(p,p+n);}
API(campaign_audio_add_wave) void campaign_audio_add_wave(const char* name,const u8* p,u32 n){SoundBankWave w;w.name=name;w.original.assign(p,p+n);campaign_audio_host.bank.waves.push_back(std::move(w));}
API(campaign_audio_prepare) u32 campaign_audio_prepare(){return campaign_audio_host.prepare();}
API(campaign_audio_prepared) u32 campaign_audio_prepared(){return campaign_audio_host.prepared;}
API(campaign_audio_events_data) const u8* campaign_audio_events_data(){return campaign_audio_host.bank.events.data();}
API(campaign_audio_events_bytes) u32 campaign_audio_events_bytes(){return campaign_audio_host.bank.events.size();}
API(campaign_audio_clear_events) void campaign_audio_clear_events(){campaign_audio_host.bank.events.clear();}
API(campaign_audio_buffer_count) u32 campaign_audio_buffer_count(){return campaign_audio_host.bank.buffers.size();}
API(campaign_audio_buffer_info) u32 campaign_audio_buffer_info(u32 i,u32 field){const auto& list=campaign_audio_host.bank.buffers;if(i>=list.size())return 0;const auto& b=list[i];const u32 values[]={b.token,b.sample,u32(b.bytes->size()),b.playing,b.position,b.pan,b.volume,b.flags};return field<8?values[field]:0;}
API(campaign_audio_buffer_format) const u8* campaign_audio_buffer_format(u32 i){const auto& list=campaign_audio_host.bank.buffers;return i<list.size()?list[i].format.data():nullptr;}
API(campaign_audio_buffer_data) const u8* campaign_audio_buffer_data(u32 i){const auto& list=campaign_audio_host.bank.buffers;return i<list.size()?list[i].bytes->data():nullptr;}
API(campaign_audio_buffer_state) u32 campaign_audio_buffer_state(u32 token,u32 playing,u32 position){auto* b=campaign_audio_host.bank.buffer(token);if(!b)return 0;b->playing=playing&1;b->position=position;return 1;}
API(campaign_audio_filename_tokens) void campaign_audio_filename_tokens(const u8* p,u32 n){if(n%4)return;campaign_audio_host.device.filenames.resize(n/4);std::memcpy(campaign_audio_host.device.filenames.data(),p,n);}
API(campaign_audio_device_field) u32 campaign_audio_device_field(u32 i){const auto& d=campaign_audio_host.device;const u32 values[]={d.wrapper_live?1u:0u,d.device_ref,d.primary_ref,d.silent_ref,d.silent_locked,d.silent_playing,d.timer_window};return i<7?values[i]:0;}
API(campaign_audio_archive) void campaign_audio_archive(const u8* p,u32 n){campaign_audio_host.archive.assign(p,p+n);}
API(campaign_music_reused_buffers) u32 campaign_music_reused_buffers(){return campaign_audio_host.reused_buffers;}
API(campaign_music_allocation_top) u32 campaign_music_allocation_top(){return campaign_audio_host.next_allocation;}
API(campaign_music_buffer_count) u32 campaign_music_buffer_count(){return campaign_audio_host.music_buffers.size();}
API(campaign_music_buffer_info) u32 campaign_music_buffer_info(u32 i,u32 field){const auto& list=campaign_audio_host.music_buffers;if(i>=list.size())return 0;const auto& b=list[i];const u32 values[]={b.token,b.sample,u32(b.pcm.size()),b.playing,b.position,b.pan,b.volume,b.flags,b.alive?1u:0u,u32(b.notifications.size()/2)};return field<10?values[field]:0;}
API(campaign_music_buffer_format) const u8* campaign_music_buffer_format(u32 i){const auto& list=campaign_audio_host.music_buffers;return i<list.size()?list[i].format.data():nullptr;}
API(campaign_music_buffer_data) const u8* campaign_music_buffer_data(u32 i){const auto& list=campaign_audio_host.music_buffers;return i<list.size()?list[i].pcm.data():nullptr;}
API(campaign_music_buffer_notification) u32 campaign_music_buffer_notification(u32 i,u32 n){const auto& list=campaign_audio_host.music_buffers;return i<list.size()&&n<list[i].notifications.size()/2?list[i].notifications[n*2]:0;}
API(campaign_music_buffer_notification_event) u32 campaign_music_buffer_notification_event(u32 i,u32 n){const auto& list=campaign_audio_host.music_buffers;return i<list.size()&&n<list[i].notifications.size()/2?list[i].notifications[n*2+1]:0;}
API(campaign_music_event_live) u32 campaign_music_event_live(u32 event){return campaign_audio_host.event_handles.count(event);}
API(campaign_music_buffer_state) u32 campaign_music_buffer_state(u32 token,u32 playing,u32 position,u32 write){auto* b=campaign_audio_host.music_buffer(token);if(!b||position>=b->pcm.size()||write>=b->pcm.size())return 0;b->playing=playing&1;b->position=position;b->write_position=write;return 1;}
API(campaign_music_dispatch) u32 campaign_music_dispatch(){return campaign_audio_host.dispatch(0);}
API(campaign_music_clock) void campaign_music_clock(double value){campaign_audio_host.clock=value;}
API(campaign_music_region) const u8* campaign_music_region(u32 token,u32 n){AnmView v{nullptr};return campaign_audio_host.music_region(token,n,v)?v.data:nullptr;}
API(campaign_music_preview_start) u32 campaign_music_preview_start(u32 index){if(index>=10||AnmView{common_load_audio.data()}.get(0x5778))return 0;u32 result=0;const char* name=reinterpret_cast<const char*>(campaign_audio_host.metadata.data()+index*52);if(!preload_music_pcm({common_load_audio.data()},common_load_audio.size(),campaign_audio_host.metadata.data(),campaign_audio_host.metadata.size(),0,name,16,0x10,campaign_audio_host,result)||result)return 0;auto v=AnmView{common_load_audio.data()};std::memset(v.data+0x24f8,0,32*0x10c);v.put(0x24f8,2);return 1;}
static bool campaign_pump_audio(u32& result){if(!campaign_audio_host.prepared&&!campaign_audio_host.prepare())return false;return pump_audio_action_main({common_load_audio.data()},common_load_audio.size(),common_load_application[0x1f1],common_load_application[0x1f2],u8(AnmView{common_load_application.data()}.get(0x20c)),campaign_audio_host,result);}

static Rng common_gameplay;
static std::array<u32,4> common_equipment,common_saved_equipment;
static i32 common_load_return=0;
API(common_load_initialize) u32 common_load_initialize(u32 f,u32 font,u32 options,u32 archive){
    common_load_bindings.reset();common_loaded_save.reset();common_save_runtime.reset();common_save.reset();common_trophies.reset();common_auxiliary.reset();common_initialize(f,0);
    if(common_load_frame_services!=&frame_services)frames=std::make_unique<GameFrameRuntime>(*common_load_frame_services);
    world.reset(common_load_world_factory?common_load_world_factory(*common_load_resource_services):new AnmResourceWorld(*common_load_resource_services));world->viewport.scale=0;common_load_application.fill(0);common_load_audio.fill(0);campaign_audio_reset_state();AnmView app{common_load_application.data()};app.put(0x724,0x180);app.data[0x1f3]=u8(font);app.put(0x20c,options);common_archive=archive!=0;common_gameplay={54321,0,0};for(u32 i=0;i<4;++i){common_equipment[i]=AnmView{natural_initial_game.data()}.get(0x20+i*4);common_saved_equipment[i]=AnmView{natural_initial_game.data()}.get(0x3c+i*4);}
    common_resource_allocations.clear();for(auto& b:common_load_logs)b.clear();common_achievements.clear();common_load_return=0;
    common_auxiliary=std::make_unique<GameAuxRuntime>(frames->scheduler,*world,common_load_storage,common_load_aux_services);game_ascii=std::make_unique<GameAsciiRuntime>(*frames,*world,common_load_storage);common_save=std::make_unique<SaveData>();common_save_runtime=std::make_unique<GameSaveRuntime>(*common_save,common_load_storage);common_trophies=std::make_unique<TrophyCatalog>();
    common_loaded_save=std::make_unique<GameSavedFile>(*common_save,common_load_storage);
    if(!common_create())return 0;common_load_bindings=std::make_unique<CommonLoadBindings>(CommonLoadBindings{*common_owner,*frames,*game_ascii,*common_auxiliary,*common_trophies,*common_save,*common_save_runtime,*world,common_load_storage,{common_load_application.data()},{common_load_audio.data()},common_gameplay,common_equipment,common_saved_equipment});common_load_bindings->loaded_save=common_loaded_save.get();campaign_audio_host.resources=world.get();if(!campaign_configuration.load({common_load_application.data()}))return 0;if(!campaign_audio_host.start_workers())return 0;return 1;
}
API(common_load_run) u32 common_load_run(){return ([&](){campaign_common_audio.music_volume=common_load_application[0x1f6];campaign_common_audio.sound_volume=common_load_application[0x1f7];return load_common_with_audio(*common_load_bindings,common_load_platform,u8(AnmView{common_load_application.data()}.get(0x20c)),campaign_common_audio,common_load_return);})();}
API(common_load_failed_entry) u32 common_load_failed_entry(){return common_load_bindings->last_entry;}
API(common_load_error) u32 common_load_error(){return world->error;}
API(common_load_pump) u32 common_load_pump(){i32 result;return world->pump(result)&&!result;}
API(common_load_pending) u32 common_load_pending(u32 slot){u32 resource,pending;if(!world->read(0x72bc7b0c+slot*4,&resource,4)||!resource||!world->read(resource+0x128,&pending,4))return 0;return pending;}
API(common_load_region_data) const u8* common_load_region_data(u32 p,u32 n){
    auto region=[&](u32 base,u8* b,u32 size)->const u8*{return p>=base&&std::uint64_t(p)+n<=std::uint64_t(base)+size?b+p-base:nullptr;};
    for(auto r:{std::array<u32,2>{GameCommonRuntime::self,GameCommonRuntime::bytes},{GameAsciiRuntime::self,GameAsciiRuntime::bytes},{0x6d000000,SaveData::bytes},{GameAuxRuntime::effects_self,0x30},{0x4e47d0,0xa34},{0x53b1e0,0x57b0},{TrophyCatalog::self,TrophyCatalog::bytes}}){u8* bytes=r[0]==GameCommonRuntime::self?common_owner->data.data():r[0]==GameAsciiRuntime::self?game_ascii->data.data():r[0]==0x6d000000?common_save->data.data():r[0]==GameAuxRuntime::effects_self?common_auxiliary->effects.data():r[0]==0x4e47d0?common_load_application.data():r[0]==0x53b1e0?common_load_audio.data():common_trophies->data.data();if(auto* out=region(r[0],bytes,r[1]))return out;}
    if(auto* out=region(frames->scheduler.self,frames->scheduler.data.data(),frames->scheduler.data.size()))return out;
    for(auto& [base,b]:frames->scheduler.records)if(auto* out=region(base,b.data(),b.size()))return out;
    output.resize(n);return world->read(p,output.data(),n)||common_save_runtime->read(p,output.data(),n)||common_loaded_save->read(p,output.data(),n)?output.data():nullptr;
}
API(common_load_log_data) const u8* common_load_log_data(u32 kind){return common_load_logs[kind].data();}
API(common_load_log_bytes) u32 common_load_log_bytes(u32 kind){return common_load_logs[kind].size();}
API(common_load_achievements_data) const u32* common_load_achievements_data(){return common_achievements.data();}
API(common_load_achievements_words) u32 common_load_achievements_words(){return common_achievements.size();}
API(common_load_frees_data) const u32* common_load_frees_data(){return world->releases.data();}
API(common_load_frees_words) u32 common_load_frees_words(){return world->releases.size();}
API(common_load_resource_count) u32 common_load_resource_count(){return common_resource_allocations.size();}
API(common_load_resource_token) u32 common_load_resource_token(u32 i){return common_resource_allocations[i][0];}
API(common_load_resource_bytes) u32 common_load_resource_bytes(u32 i){return common_resource_allocations[i][1];}
API(common_load_globals_data) const u32* common_load_globals_data(){static std::array<u32,4> b;b={common_owner->global_owner,game_ascii->global_owner,common_auxiliary->effects_owner,common_load_bindings->save_owner};return b.data();}
API(common_load_equipment_data) const u32* common_load_equipment_data(){static std::array<u32,8> b;std::copy(common_equipment.begin(),common_equipment.end(),b.begin());std::copy(common_saved_equipment.begin(),common_saved_equipment.end(),b.begin()+4);return b.data();}
API(common_load_rng_data) const u8* common_load_rng_data(){static std::array<u8,16> b;std::memcpy(b.data(),&world->animation_rng,8);std::memcpy(b.data()+8,&common_gameplay,8);return b.data();}


#include "../src/GameTextureResources.hpp"
static std::unique_ptr<GameTextureResources> common_texture_resources;
static std::vector<u32> common_image_events;
struct CommonTextureDevice:AnmTextureStoreDevice {
    bool select_texture_layout(const AnmDeviceTextureRequest& r,AnmTextureLayout& layout,i32& status)override{layout={r.format==20?22u:r.format==29?21u:r.format,r.width,r.height};status=0;return anm_texture_pixel_bytes(layout.format)&&layout.width&&layout.height;}
    bool texture_created(u32 p,const AnmTexturePixels&)override{common_image_events.insert(common_image_events.end(),{0,p,1});return true;}
    bool texture_uploaded(u32 p,const AnmTexturePixels&)override{common_image_events.insert(common_image_events.end(),{2,p,common_texture_resources->textures.images.at(p).references});return true;}
    bool texture_reference_changed(u32 p,u32 refs)override{common_image_events.insert(common_image_events.end(),{1,p,refs});return true;}
    bool texture_destroyed(u32 p)override{common_image_events.insert(common_image_events.end(),{3,p,0});return true;}
}common_texture_device;
API(common_texture_initialize) u32 common_texture_initialize(u32 f,u32 width,u32 height,u32 scale,u32 font){
    common_image_events.clear();common_texture_resources=std::make_unique<GameTextureResources>(common_load_files,common_texture_device,205);common_texture_resources->scale=real(scale);common_load_resource_services=common_texture_resources.get();
    if(!common_load_initialize(f,font,0,1))return 0;world->width=width;world->height=height;world->viewport.scale=real(scale);auto app=AnmView{common_load_application.data()};app.put(8,0x7002c000);app.put(0xfc,21);return 1;
}
static auto common_image(u32 i){auto p=common_texture_resources->textures.images.begin();std::advance(p,i);return p;}
API(common_image_count) u32 common_image_count(){return common_texture_resources->textures.images.size();}
API(common_image_token) u32 common_image_token(u32 i){return common_image(i)->first;}
API(common_image_format) u32 common_image_format(u32 i){return common_image(i)->second.pixels.format;}
API(common_image_width) u32 common_image_width(u32 i){return common_image(i)->second.pixels.width;}
API(common_image_height) u32 common_image_height(u32 i){return common_image(i)->second.pixels.height;}
API(common_image_refs) u32 common_image_refs(u32 i){return common_image(i)->second.references;}
API(common_image_bytes) u32 common_image_bytes(u32 i){return common_image(i)->second.pixels.data.size();}
API(common_image_data) const u8* common_image_data(u32 i){return common_image(i)->second.pixels.data.data();}
API(common_image_events_data) const u32* common_image_events_data(){return common_image_events.data();}
API(common_image_events_words) u32 common_image_events_words(){return common_image_events.size();}


#include "../src/GameApplicationTargets.hpp"
static std::unique_ptr<GameApplicationTargets> common_application_targets;
static ApplicationTargetGlobals common_texture_target_globals;
static CommonApplicationGlobals common_texture_application_globals;
static std::vector<u32> common_backbuffer_events;
static u32 common_backbuffer_refs=1;
struct CommonBackbuffer:GameApplicationTargetDevice {
    bool application_backbuffer(u32 device,u32& out)override{if(device!=0x7002c000)return false;out=0x70018000;++common_backbuffer_refs;common_backbuffer_events.insert(common_backbuffer_events.end(),{0,out,common_backbuffer_refs});return true;}
    bool release_application_backbuffer(u32 p)override{if(p!=0x70018000||common_backbuffer_refs<=1)return false;--common_backbuffer_refs;common_backbuffer_events.insert(common_backbuffer_events.end(),{1,p,common_backbuffer_refs});return true;}
}common_backbuffer;
API(common_texture_targets_initialize) u32 common_texture_targets_initialize(u32 f,u32 width,u32 height,u32 scale,u32 font){
    common_application_targets.reset();if(!common_texture_initialize(f,width,height,scale,font))return 0;
    common_backbuffer_events.clear();common_backbuffer_refs=1;common_texture_target_globals={width,real(scale),0};common_texture_application_globals={7};
    common_application_targets=std::make_unique<GameApplicationTargets>(AnmView{common_load_application.data()},*world,common_texture_resources->textures,common_load_storage,common_backbuffer);return common_application_targets->construct();
}
API(common_texture_targets_run) u32 common_texture_targets_run(u32 operation){
    if(operation==1)return common_application_targets->release(common_texture_target_globals);
    if(operation==2)common_owner->view().put(0,common_owner->view().get(0)|2);
    if(operation==3)return common_application_targets->initialize(common_texture_target_globals);
    u32 result;return common_owner->update({common_load_application.data()},common_texture_target_globals,common_texture_application_globals,*common_application_targets,*common_application_targets,*game_ascii,result)?result:0;
}
API(common_texture_targets_region) const u8* common_texture_targets_region(u32 p,u32 n){output.resize(n);if(common_application_targets->read_render_memory(p,output.data(),n))return output.data();return common_load_region_data(p,n);}
API(common_texture_targets_globals) const u32* common_texture_targets_globals(){static std::array<u32,5> values;values={common_texture_target_globals.width,word(common_texture_target_globals.scale),common_texture_target_globals.auxiliary,common_texture_application_globals.presentation,common_backbuffer_refs};return values.data();}
API(common_backbuffer_events_data) const u32* common_backbuffer_events_data(){return common_backbuffer_events.data();}
API(common_backbuffer_events_words) u32 common_backbuffer_events_words(){return common_backbuffer_events.size();}


#include "../src/GameAnimationPool.hpp"
#include "../src/GameCommonFrameServices.hpp"
#include "../src/AsciiFrame.hpp"
static AnmPoolGlobals common_pool_globals;
static AnmOverlay common_pool_overlay;
static std::vector<u32> common_pool_formats,common_pool_trace;
static std::unique_ptr<GameAnimationPool> common_pool_services;
static bool (*common_pool_extra_update)(u32,u32,u32&)=nullptr;
struct CommonPoolDevice:GameAnimationPoolDevice {
    bool animation_pool_vertex_format(u32 f)override{common_pool_formats.push_back(f);return f==0;}
}common_pool_device;
struct CommonPoolFollowing:GameFrameServices {
    bool frame_input(GameInputFrame& g)override{g={};return true;}
    bool before_game_callback(u32 e,u32 o)override{common_pool_trace.insert(common_pool_trace.end(),{e,o});return true;}
    bool after_game_callback(u32,u32,u32)override{return true;}
    bool other_game_callback(u32 e,u32 o,u32& result)override{if(e==0x468100||e==0x468110)return campaign_achievement_callback(e,o,result);if(e==0x434d50)return campaign_manual_update(o,result);if(e==0x4472d0&&common_pool_extra_update)return common_pool_extra_update(e,o,result);if((o==0x6e040000||o==0x6b004000)&&common_pool_extra_update)return common_pool_extra_update(e,o,result);result=1;return e==0x40b590&&o==GameAsciiRuntime::self&&advance_ascii_frame(game_ascii->view());}
}common_pool_following;
static GameCommonFrameServices common_pool_frame_services{common_pool_following};
API(common_pooled_textures_initialize) u32 common_pooled_textures_initialize(u32 f,u32 width,u32 height,u32 scale,u32 font){
    common_application_targets.reset();common_pool_services.reset();common_load_frame_services=&common_pool_frame_services;
    if(!common_texture_initialize(f,width,height,scale,font))return 0;
    common_pool_globals={};common_pool_overlay.draws.fill(0);common_pool_formats.clear();common_pool_trace.clear();
    common_pool_services=std::make_unique<GameAnimationPool>(*frames,common_load_storage,common_pool_device);if(!world->enable_pool(common_pool_globals,*common_pool_services))return 0;
    common_backbuffer_events.clear();common_backbuffer_refs=1;common_texture_target_globals={width,real(scale),0};common_texture_application_globals={7};
    common_application_targets=std::make_unique<GameApplicationTargets>(AnmView{common_load_application.data()},*world,common_texture_resources->textures,common_load_storage,common_backbuffer);if(!common_application_targets->construct())return 0;
    frames->animations=world.get();frames->overlay=&common_pool_overlay;
    common_pool_frame_services.bindings={common_owner.get(),game_ascii.get(),world.get(),{common_load_application.data()},&common_texture_target_globals,&common_texture_application_globals,common_application_targets.get(),common_application_targets.get()};return 1;
}
API(common_pool_formats_data) const u32* common_pool_formats_data(){return common_pool_formats.data();}
API(common_pool_formats_words) u32 common_pool_formats_words(){return common_pool_formats.size();}
API(common_pool_transforms_data) const u8* common_pool_transforms_data(){return common_pool_globals.transforms.data();}
API(common_pooled_region) const u8* common_pooled_region(u32 p,u32 n){if(p>=AnmPoolGlobals::base&&std::uint64_t(p)+n<=std::uint64_t(AnmPoolGlobals::base)+common_pool_globals.transforms.size())return common_pool_globals.transforms.data()+p-AnmPoolGlobals::base;return common_texture_targets_region(p,n);}
API(common_pool_frame_prepare) void common_pool_frame_prepare(){common_owner->view().put(0,common_owner->view().get(0)|2);}
API(common_pool_frame_step) u32 common_pool_frame_step(u32 rate){world->rate=real(rate);common_pool_trace.clear();i32 result;if(!frames->dispatch(false,result))return 0;u32 draw_result;if(!common_pool_frame_services.other_game_callback(0x4436b0,GameCommonRuntime::self,draw_result)||draw_result!=1)return 0;return u32(result);}
API(common_pool_failed_entry) u32 common_pool_failed_entry(){return frames->failed_entry;}
API(common_pool_trace_data) const u32* common_pool_trace_data(){return common_pool_trace.data();}
API(common_pool_trace_words) u32 common_pool_trace_words(){return common_pool_trace.size();}
API(common_pool_allocations_data) const u32* common_pool_allocations_data(){return world->allocations.data();}
API(common_pool_allocations_words) u32 common_pool_allocations_words(){return world->allocations.size();}


#include "../src/GameApplicationComposition.hpp"
static std::unique_ptr<GameStageRuntime> common_render_stage;
static std::unique_ptr<GameRenderRuntime> common_renderer;
static std::unique_ptr<GameApplicationComposition> common_composition;
static ApplicationFrameGlobals common_composition_frame;
static ApplicationCompositionGlobals common_composition_globals;
static bool common_composition_static_mesh=false;
struct CommonRenderDevice:GameRenderDevice {
    std::vector<u8> calls;u32 count=0,triangles=0;
    std::array<u8,720> vertices{};
    u32 game_device_token()const override{return 0x7002c000;}
    void emit(u32 kind,std::initializer_list<u32> args,const void* data=nullptr,u32 n=0){const u32 header[]={kind,u32(args.size()*4),n};auto append=[&](const void* p,u32 bytes){const auto* b=static_cast<const u8*>(p);if(bytes)calls.insert(calls.end(),b,b+bytes);};append(header,12);append(args.begin(),args.size()*4);append(data,n);++count;}
    bool texture_stage_state(u32 a,u32 b,u32 c)override{emit(3,{a,b,c});return true;}
    bool vertex_format(u32 value)override{emit(4,{value});return true;}
    bool draw_triangles(u32 count,u32 stride,const u8* data,u32 n)override{emit(5,{4,count,stride},data,n);triangles+=count;return true;}
    bool render_state(u32 a,u32 b)override{emit(2,{a,b});return true;}
    bool sampler_state(u32 a,u32 b,u32 c)override{emit(7,{a,b,c});return true;}
    bool texture(u32 a,u32 b)override{emit(6,{a,b});return true;}
    bool clear_application(u32 device,const ApplicationClear& clear)override{if(device!=game_device_token())return false;emit(14,{clear.rectangle_count,clear.flags,clear.color,clear.depth,clear.stencil},clear.rectangle.data(),clear.rectangle_count*16);return true;}
    bool application_render_target(u32 device,u32 a,u32 b)override{if(device!=game_device_token())return false;emit(15,{a,b});return true;}
    bool application_transform(u32 device,u32 kind,const u8* matrix)override{if(device!=game_device_token())return false;emit(0,{kind},matrix,64);return true;}
    bool application_viewport(u32 device,const u8* viewport)override{if(device!=game_device_token())return false;emit(1,{},viewport,24);return true;}
    bool primitive_upload(u32 type,u32 count,u32 stride,const u8* data,u32 n)override{emit(5,{type,count,stride},data,n);if(type>=4)triangles+=count;return true;}
    bool read_game_render_memory(u32 p,void* out,u32 n)override{if(p<0x6e038000||std::uint64_t(p)+n>std::uint64_t(0x6e038000)+vertices.size())return false;std::memcpy(out,vertices.data()+p-0x6e038000,n);return true;}
    bool write_game_render_memory(u32 p,const void* in,u32 n)override{if(p<0x6e038000||std::uint64_t(p)+n>std::uint64_t(0x6e038000)+vertices.size())return false;std::memcpy(vertices.data()+p-0x6e038000,in,n);return true;}
    bool mesh_stream(u32 a,u32 b,u32 c,u32 d)override{emit(8,{a,b,c,d});return true;}
    bool mesh_primitive(u32 a,u32 b,u32 c)override{emit(9,{a,b,c});return true;}
    bool create_static_mesh(u32 bytes,u32 usage,u32 format,u32 pool,u32& token)override{if(bytes!=vertices.size())return false;emit(11,{bytes,usage,format,pool});token=0x6e037000;return true;}
    bool lock_static_mesh(u32 buffer,u32 offset,u32 bytes,u32 flags,u32& data)override{if(buffer!=0x6e037000)return false;emit(12,{buffer,offset,bytes,flags});data=0x6e038000;return true;}
    bool unlock_static_mesh(u32 buffer)override{emit(13,{buffer});return buffer==0x6e037000;}
    bool bind_static_mesh(u32 stream,u32 buffer,u32 offset,u32 stride,i32& result)override{result=0;return mesh_stream(stream,buffer,offset,stride);}
}common_render_device;
struct CommonRenderStageFiles:GameStageServices {bool read_game_stage_file(const std::string&,std::vector<u8>&)override{return false;}}common_render_stage_files;
struct CommonCompositionCallbacks:GameApplicationCompositionCallbacks {bool application_composition_callback(u32)override{return false;}}common_composition_callbacks;
API(legacy_common_composition_initialize) u32 legacy_common_composition_initialize(u32 f,u32 width,u32 height,u32 scale,u32 font){
    common_composition.reset();common_renderer.reset();common_render_stage.reset();common_application_targets.reset();common_pool_services.reset();common_load_frame_services=&common_pool_frame_services;
    if(!common_texture_initialize(f,width,height,scale,font))return 0;
    common_pool_globals={};common_pool_overlay.draws.fill(0);common_pool_formats.clear();common_pool_trace.clear();common_pool_services=std::make_unique<GameAnimationPool>(*frames,common_load_storage,common_pool_device);if(!world->enable_pool(common_pool_globals,*common_pool_services))return 0;
    auto app=AnmView{common_load_application.data()};app.put(0xa30,0xff000000);if(!initialize_application_cameras(app,{width,height,0,real(scale)},world->viewport.second_origin))return 0;
    owners=std::make_unique<GameOwnerRuntime>(*frames,*world,common_load_storage);common_render_stage=std::make_unique<GameStageRuntime>(*frames,*world,common_load_storage,common_render_stage_files);common_renderer=std::make_unique<GameRenderRuntime>(*owners,*common_render_stage,*world,common_render_device);
    if(!common_renderer->initialize(common_load_application.data(),0x6e0,common_pool_globals,common_composition_static_mesh))return 0;common_renderer->application=common_load_application;app={common_renderer->application.data()};
    common_backbuffer_events.clear();common_backbuffer_refs=1;common_texture_target_globals={width,real(scale),0};common_texture_application_globals={7};
    common_application_targets=std::make_unique<GameApplicationTargets>(app,*world,common_texture_resources->textures,common_load_storage,common_backbuffer);if(!common_application_targets->construct())return 0;
    common_load_bindings->application=app;frames->animations=world.get();frames->overlay=&common_pool_overlay;common_pool_frame_services.bindings={common_owner.get(),game_ascii.get(),world.get(),app,&common_texture_target_globals,&common_texture_application_globals,common_application_targets.get(),common_application_targets.get()};
    common_composition=std::make_unique<GameApplicationComposition>(*common_renderer,*common_application_targets,*world,common_render_device,common_composition_callbacks);common_composition_frame={};common_composition_globals={};common_composition_globals.scale=real(scale);common_render_device.calls.clear();common_render_device.count=common_render_device.triangles=0;return 1;
}
API(common_composition_targets_run) u32 common_composition_targets_run(u32 operation){if(operation==1)return common_application_targets->release(common_texture_target_globals);if(operation==2)common_owner->view().put(0,common_owner->view().get(0)|2);if(operation==3)return common_application_targets->initialize(common_texture_target_globals);u32 result;return common_owner->update({common_renderer->application.data()},common_texture_target_globals,common_texture_application_globals,*common_application_targets,*common_application_targets,*game_ascii,result)?result:0;}
API(common_composition_region) const u8* common_composition_region(u32 p,u32 n){
    if(p>=0x4e47d0&&std::uint64_t(p)+n<=std::uint64_t(0x4e47d0)+common_renderer->application.size())return common_renderer->application.data()+p-0x4e47d0;
    if(p>=0x540a60&&std::uint64_t(p)+n<=std::uint64_t(0x540a60)+96)return common_renderer->static_scratch.data()+p-0x540a60;
    if(p>=0x6e038000&&std::uint64_t(p)+n<=std::uint64_t(0x6e038000)+720)return common_render_device.vertices.data()+p-0x6e038000;
    if(p>=AnmPoolGlobals::base&&std::uint64_t(p)+n<=std::uint64_t(AnmPoolGlobals::base)+common_pool_globals.transforms.size()){static std::array<u8,0xf0> copy;copy=common_pool_globals.transforms;std::memcpy(copy.data()+0x60,common_renderer->quad.vertices.data(),112);std::memcpy(copy.data()+0xd0,common_renderer->static_scratch.data(),32);return copy.data()+p-AnmPoolGlobals::base;}
    return common_pooled_region(p,n);
}
API(common_composition_run) u32 common_composition_run(u32 pass){common_render_device.calls.clear();common_render_device.count=common_render_device.triangles=0;if(!pass){auto app=AnmView{common_renderer->application.data()};auto& g=common_composition_frame;g.device=common_render_device.game_device_token();g.width=world->width;g.height=world->height;g.render_target=app.get(0x1ac);g.clear_color=app.get(0xa30);g.first_origin=world->viewport.first_origin;std::memcpy(g.stage_viewport.data(),app.data+0x694,16);if(!common_composition->begin_frame(g))return 0;common_composition_globals.logical_width=g.logical_width;common_composition_globals.logical_height=g.logical_height;return 1;}if(pass==1)return common_renderer->flush();if(!common_composition->draw(ApplicationCompositionPass(pass),common_composition_globals))return 0;common_composition_frame.logical_width=common_composition_globals.logical_width;common_composition_frame.logical_height=common_composition_globals.logical_height;return 1;}
API(common_composition_globals_data) const u32* common_composition_globals_data(){static std::array<u32,6> g;g={common_composition_globals.logical_height,common_composition_globals.logical_width,u32(world->viewport.second_origin[0]),u32(world->viewport.second_origin[1]),u32(world->viewport.first_origin[0]),u32(world->viewport.first_origin[1])};return g.data();}
API(common_composition_calls_data) const u8* common_composition_calls_data(){return common_render_device.calls.data();}
API(common_composition_calls_bytes) u32 common_composition_calls_bytes(){return common_render_device.calls.size();}
API(common_composition_calls_count) u32 common_composition_calls_count(){return common_render_device.count;}
API(common_composition_quad_data) const u8* common_composition_quad_data(){return reinterpret_cast<const u8*>(common_renderer->quad.vertices.data());}

#include "../src/GameApplicationBoot.hpp"
#include "../src/GraphicsSetup.hpp"
static std::unique_ptr<GameFrameTimingRuntime> boot_timing;
static std::unique_ptr<GameApplicationBoot> application_boot;
static FontFamilyNames boot_names;
static TextRaster boot_raster;
static u32 boot_ticks=54321,boot_created_fonts=0;
static std::vector<std::array<u8,124>> boot_enum_records;
static std::vector<u32> boot_events;
static std::vector<TextFont> boot_created_definitions;
struct BootMemory:AnmRenderMemory {
    bool read_render_memory(u32 p,void* b,u32 n)override{return world->read(p,b,n)||common_render_device.read_game_render_memory(p,b,n);}
    bool write_render_memory(u32 p,const void* b,u32 n)override{return world->write(p,b,n)||common_render_device.write_game_render_memory(p,b,n);}
}boot_memory;
struct BootPlatform:GameApplicationBootHost,FontInitializeHost {
    bool open_application_archive(const char* name,u32& result)override{if(std::string(name)!="th143.dat")return false;boot_events.insert(boot_events.end(),{0,0x538f50});result=1;return true;}
    bool read_application_version(const char* name,u32& p,u32& n)override{return world->read_resource_file(name,false,p,n);}
    bool application_boot_error(bool)override{return false;}
    bool application_boot_ticks(u32& value)override{boot_events.insert(boot_events.end(),{2,boot_ticks});value=boot_ticks;return true;}
    bool launch_application_audio(u32 e,u32 a,u32 f,u32& id,u32& handle)override{boot_events.insert(boot_events.end(),{1,0,0,e,a,f});if(f||!campaign_audio_host.create_sound_archive_worker(e,a,handle))return false;id=0x6d430000;return true;}
    bool font_screen_dc(u32& p)override{p=0x1234;return true;}
    bool enumerate_font_families(u32 dc,const std::array<u8,60>& query,std::vector<std::array<u8,124>>& out)override{
        if(dc!=0x1234||query[23]!=1)return false;out=boot_enum_records;return true;
    }
    bool release_font_screen_dc(u32 p)override{return p==0x1234;}
    bool initialize_font_bitmap(u32 format,u32& result)override{result=boot_raster.initialize(format,application_boot->fonts.alternative!=0,{})?1:0;return true;}
    bool create_initialized_font(const TextFont& f,u32& p)override{boot_created_definitions.push_back(f);p=0x4000+boot_created_fonts++;return true;}
}boot_platform;
API(boot_family_name) void boot_family_name(u32 i,const u8* p,u32 n){boot_names[i]={p,p+n};}
API(boot_font_record) void boot_font_record(const u8* p){std::array<u8,124> r;std::memcpy(r.data(),p,124);boot_enum_records.push_back(r);}
API(boot_prepare) u32 boot_prepare(u32 f,u32 width,u32 height,u32 scale,u32 ticks,u32 font){
    application_boot.reset();boot_timing.reset();common_composition.reset();common_renderer.reset();common_render_stage.reset();common_application_targets.reset();common_pool_services.reset();common_load_frame_services=&common_pool_frame_services;
    boot_events.clear();boot_created_fonts=0;boot_created_definitions.clear();boot_enum_records.clear();boot_ticks=ticks;
    if(!common_texture_initialize(f,width,height,scale,font))return 0;
    common_pool_globals={};common_pool_overlay.draws.fill(0);common_pool_formats.clear();common_pool_trace.clear();common_pool_services=std::make_unique<GameAnimationPool>(*frames,common_load_storage,common_pool_device);if(!world->enable_pool(common_pool_globals,*common_pool_services))return 0;
    AnmView{common_load_application.data()}.put(0xa30,0xff000000);
    owners=std::make_unique<GameOwnerRuntime>(*frames,*world,common_load_storage);common_render_stage=std::make_unique<GameStageRuntime>(*frames,*world,common_load_storage,common_render_stage_files);common_renderer=std::make_unique<GameRenderRuntime>(*owners,*common_render_stage,*world,common_render_device);
    if(!common_renderer->initialize(common_load_application.data(),0x6e0,common_pool_globals,false))return 0;common_renderer->application=common_load_application;
    auto app=AnmView{common_renderer->application.data()};common_application_targets=std::make_unique<GameApplicationTargets>(app,*world,common_texture_resources->textures,common_load_storage,common_backbuffer);
    boot_timing=std::make_unique<GameFrameTimingRuntime>(frames->scheduler,common_load_storage);
    application_boot=std::make_unique<GameApplicationBoot>(*common_renderer,*common_application_targets,*boot_timing,*world,common_gameplay,AnmView{common_load_audio.data()},boot_memory,common_render_device,boot_platform,boot_platform);
    common_load_bindings->application=app;common_render_device.calls.clear();common_render_device.count=common_render_device.triangles=0;return 1;
}
API(boot_graphics) u32 boot_graphics(){return initialize_graphics(0x72000000,boot_memory,common_render_device);}
API(boot_clear_device) void boot_clear_device(){common_render_device.calls.clear();common_render_device.count=common_render_device.triangles=0;}
API(boot_run) u32 boot_run(){i32 result;if(!application_boot->initialize(boot_names,result))return 0;boot_raster.fonts=application_boot->fonts.fonts;return result==0;}
API(boot_region) const u8* boot_region(u32 p,u32 n){
    if(boot_timing&&p==GameFrameTimingRuntime::self&&n<=boot_timing->data.size())return boot_timing->data.data();
    if(p==0x72000000&&n==AnmPool::bytes)return world->pool->data.data();
    if(auto v=common_application_targets->target_animation(p);v.data&&n<=AnmView::bytes)return v.data;
    return common_composition_region(p,n);
}
API(boot_noise) const u8* boot_noise(){return application_boot->fonts.noise.data();}
API(boot_bitmap_header) const u8* boot_bitmap_header(){return boot_raster.header.data();}
API(boot_bitmap_descriptor) const u32* boot_bitmap_descriptor(){static std::array<u32,9> d;d={boot_raster.format,1024,128,boot_raster.stride*128,boot_raster.stride,0x2000,0x3001,0x1000,0x63000000};return d.data();}
API(boot_handles) const u32* boot_handles(){return application_boot->fonts.handles.data();}
API(boot_audio_thread) u32 boot_audio_thread(){return application_boot->audio_thread;}
API(boot_event_data) const u32* boot_event_data(){return boot_events.data();}
API(boot_event_words) u32 boot_event_words(){return boot_events.size();}
API(boot_created_font_argument) i32 boot_created_font_argument(u32 i,u32 j){return boot_created_definitions[i].arguments[j];}
API(boot_created_font_face) const u8* boot_created_font_face(u32 i){return boot_created_definitions[i].face.data();}
API(boot_created_font_face_bytes) u32 boot_created_font_face_bytes(u32 i){return boot_created_definitions[i].face.size();}


static std::vector<u8> boot_graphics_calls,boot_mesh_calls;
API(common_composition_initialize) u32 common_composition_initialize(u32 f,u32 width,u32 height,u32 scale,u32 font){
 if(!boot_prepare(f,width,height,scale,54321,font)||!boot_graphics())return 0;boot_graphics_calls=common_render_device.calls;boot_clear_device();if(!boot_run())return 0;boot_mesh_calls=common_render_device.calls;
 auto app=AnmView{common_renderer->application.data()};common_backbuffer_events.clear();common_backbuffer_refs=1;common_texture_target_globals={width,real(scale),0};common_texture_application_globals={7};frames->animations=world.get();frames->overlay=&common_pool_overlay;
 common_pool_frame_services.bindings={common_owner.get(),game_ascii.get(),world.get(),app,&common_texture_target_globals,&common_texture_application_globals,common_application_targets.get(),common_application_targets.get()};common_composition=std::make_unique<GameApplicationComposition>(*common_renderer,*common_application_targets,*world,common_render_device,common_composition_callbacks);common_composition_frame={};common_composition_globals={};common_composition_globals.scale=real(scale);boot_clear_device();return 1;
}


#include "../src/GameApplicationDraw.hpp"
#include "../src/GameDrawRuntime.hpp"
static std::unique_ptr<GameDrawRuntime> common_owner_drawing;
static std::unique_ptr<GameApplicationDraw> common_registered_drawing;
static bool (*common_registered_extra_draw)(u32,u32,u32&)=nullptr;
static bool title_natural_clear_results_draw(u32,AnmView);
struct CommonOwnerDrawPlatform:GameDrawServices {bool draw_laser_virtual(u32 entry,u32 owner)override{return campaign_laser_draw(entry,owner);}bool draw_menu_page(u32 entry,AnmView menu)override{if(entry==0x449780||entry==0x449890)return campaign_replay_save_draw(entry,menu);return title_natural_clear_results_draw(entry,menu);}}common_owner_draw_platform;
struct CommonRegisteredDrawServices:GameApplicationDrawServices {
    bool application_owner_draw(u32 entry,u32 owner,u32& result)override{if(entry==0x468100||entry==0x468110)return campaign_achievement_callback(entry,owner,result);if(entry==0x4472e0)return day1_notice_callback(entry,owner,result);if(entry==0x434d60){result=1;return true;}common_owner_drawing->globals.application_state=AnmView{common_renderer->application.data()}.get(0x6ec);if(owner==GameCommonRuntime::self)return common_pool_frame_services.other_game_callback(entry,owner,result);if((owner==0x6e040000||owner==0x6b004000)&&common_registered_extra_draw)return common_registered_extra_draw(entry,owner,result);return common_owner_drawing->invoke(entry,owner,result);}
}common_registered_draw_services;
API(common_registered_initialize) u32 common_registered_initialize(u32 f,u32 width,u32 height,u32 scale,u32 font){
    common_registered_drawing.reset();common_owner_drawing.reset();common_composition_static_mesh=true;if(!common_composition_initialize(f,width,height,scale,font))return 0;
    common_owner_drawing=std::make_unique<GameDrawRuntime>(*owners,*common_render_stage,*world,*common_renderer,common_render_device,common_owner_draw_platform);common_owner_drawing->bindings.ascii=game_ascii->view();common_owner_drawing->bindings.timing=boot_timing->view();
    common_registered_drawing=std::make_unique<GameApplicationDraw>(frames->scheduler,common_load_storage,*common_composition,*common_application_targets,*common_renderer,*world,common_registered_draw_services);return common_registered_drawing->register_callbacks();
}
API(common_registered_probe) u32 common_registered_probe(){u32 handle;return world->create_at(AnmView{common_renderer->application.data()}.get(0x71c),52,33,{0,0,0},handle);}
API(common_registered_frame) u32 common_registered_frame(u32 rate){world->rate=real(rate);common_pool_trace.clear();i32 result;if(!frames->dispatch(false,result)||result!=5)return 0;common_render_device.calls.clear();common_render_device.count=common_render_device.triangles=0;common_registered_drawing->independent_signals=common_auxiliary->independent.signals;common_registered_drawing->menu_owner=0;return common_registered_drawing->dispatch(result)?u32(result):0;}
API(common_registered_failed) u32 common_registered_failed(){return common_registered_drawing->failed_entry?common_registered_drawing->failed_entry:common_owner_drawing->failed_entry;}
API(common_registered_render_error) u32 common_registered_render_error(){return common_renderer->error;}
API(common_registered_trace_data) const u32* common_registered_trace_data(){return common_registered_drawing->trace.data();}
API(common_registered_trace_words) u32 common_registered_trace_words(){return common_registered_drawing->trace.size();}
API(common_registered_globals_data) const u32* common_registered_globals_data(){static std::array<u32,6> g;g={common_registered_drawing->globals.logical_height,common_registered_drawing->globals.logical_width,u32(world->viewport.second_origin[0]),u32(world->viewport.second_origin[1]),u32(world->viewport.first_origin[0]),u32(world->viewport.first_origin[1])};return g.data();}


#include "../src/TitleLoad.hpp"
static std::unique_ptr<GameTitleRuntime> title_owner;
static std::unique_ptr<GameCheatRuntime> title_cheat;
static std::unique_ptr<TitleLoadBindings> title_bindings;
static u32 title_alternate=0,title_global_538de4=0,title_io_mode=0,title_write_cursor=0,title_sleeps=0;
static std::vector<u8> title_launch,title_io_events;
static std::vector<std::vector<u8>> title_save_writes;
static void title_io_event(u32 kind,std::initializer_list<u32> args){auto append=[&](const void* p,u32 n){const auto* b=static_cast<const u8*>(p);if(n)title_io_events.insert(title_io_events.end(),b,b+n);};const u32 header[]={kind,u32(args.size())};append(header,8);append(args.begin(),args.size()*4);append(title_owner->data.data(),title_owner->data.size());append(common_save->data.data(),common_save->data.size());append(common_renderer->application.data(),common_renderer->application.size());append(common_owner->data.data(),common_owner->data.size());
    const u32 globals[]={title_owner->global_owner,common_owner->global_owner,common_load_bindings->save_owner,title_cheat->global_owner,common_texture_application_globals.presentation,title_global_538de4,title_alternate};append(globals,sizeof globals);append(common_equipment.data(),16);append(common_saved_equipment.data(),16);append(common_load_rng_data(),16);for(u32 p:{title_owner->view().get(12),title_owner->view().get(16),title_cheat->view().get(8),title_cheat->view().get(12)}){auto cb=frames->scheduler.at(p);const u32 flags=cb.data?cb.get(4):0;append(&flags,4);}}
struct TitleFactoryPlatform:RootFactoryHost {
    bool allocate_root(u32&)override{return false;}bool evict_managed_textures()override{return false;}bool wait_worker(u32,u32,u32&)override{return false;}bool sleep_worker(u32)override{return false;}bool close_worker(u32)override{return false;}
    bool launch_worker(u32 entry,u32 argument,u32 flags,u32& id,u32& handle)override{if(entry!=0x45ef60||argument!=GameTitleRuntime::self||flags)return false;auto append=[&](const void* p,u32 n){const auto* b=static_cast<const u8*>(p);title_launch.insert(title_launch.end(),b,b+n);};const u32 args[]={0,0,entry,argument,flags,GameTitleRuntime::self+0xe100};append(args,sizeof args);append(title_owner->data.data(),title_owner->data.size());const u32 globals[]={title_owner->global_owner,common_texture_application_globals.presentation};append(globals,sizeof globals);id=0x11223344;handle=0x77770003;return true;}
}title_factory_platform;
struct TitlePlatform:TitleLoadHost {
    bool read_title_file(const char* name,std::vector<u8>& out)override{return common_load_files.read_animation_file(name,false,out);}
    bool title_file_padding(u32,u32,std::vector<u8>& out)override{out.assign(64,0);return true;}
    bool sleep_title_worker(u32 milliseconds)override{if(milliseconds!=1&&milliseconds!=16)return false;title_io_event(12,{milliseconds});++title_sleeps;if(milliseconds==1){i32 result;return world->pump(result)&&!result;}u32 result;return common_pool_frame_services.other_game_callback(0x4436b0,GameCommonRuntime::self,result)&&result==1;}
    bool title_resource_error()override{return false;}
    bool save_directory(bool restore)override{title_io_event(7,{u32(restore)});return true;}
    bool open_save_file(i32& status,u32& handle)override{status=title_io_mode==1?1:0;handle=status?0xffffffff:0x1234;title_io_event(8,{u32(status),handle});if(!title_io_mode&&!campaign_score_file.open(handle))return false;return true;}
    bool write_save_file_bytes(u32 handle,const u8* bytes,u32 n,u32& written)override{if(handle!=0x1234)return false;const bool short_write=(title_io_mode==2&&!title_write_cursor)||(title_io_mode==3&&title_write_cursor==1);++title_write_cursor;written=short_write?n-1:n;title_save_writes.emplace_back(bytes,bytes+n);title_io_event(9,{handle,n,written});if(!title_io_mode&&!campaign_score_file.write(handle,bytes,written))return false;return true;}
    bool close_save_file(u32 handle)override{if(handle!=0x1234)return false;title_io_event(10,{handle});if(!title_io_mode&&!campaign_score_file.close(handle))return false;return true;}
    bool save_file_error()override{title_io_event(11,{});return true;}
}title_platform;
API(title_load_initialize) u32 title_load_initialize(u32 f,u32 width,u32 height,u32 scale,u32 font){title_bindings.reset();title_owner.reset();title_cheat.reset();title_alternate=title_global_538de4=title_io_mode=title_write_cursor=title_sleeps=0;title_launch.clear();title_io_events.clear();title_save_writes.clear();return common_registered_initialize(f,width,height,scale,font);}
API(title_load_prepare) u32 title_load_prepare(u32 variant,u32 io){title_io_mode=io;title_alternate=37;title_global_538de4=0x6b003000;auto app=AnmView{common_renderer->application.data()};app.put(0x724,variant==1?0x180:0);common_owner->view().put(0x60c,variant==0?179:variant==1?0:0xffffffff);auto save=common_save->view();if(variant){save.put(0xef2c,75);save.data[0xefe0]=variant==1?1:0;if(variant==2)save.put(0xf16c,15);}title_cheat=std::make_unique<GameCheatRuntime>(*frames,*world,common_pool_overlay,common_load_storage);title_owner=std::make_unique<GameTitleRuntime>(common_load_storage,title_factory_platform,common_texture_application_globals.presentation);u32 result;if(!title_owner->create(result)||result!=GameTitleRuntime::self)return 0;title_bindings=std::make_unique<TitleLoadBindings>(TitleLoadBindings{*title_owner,*common_owner,*frames,*title_cheat,*world,common_load_storage,*common_save,app,common_texture_application_globals,common_equipment,common_saved_equipment,title_alternate,title_global_538de4});title_bindings->loaded_save=common_loaded_save.get();return 1;}
API(title_load_run) u32 title_load_run(){i32 result;return load_title(*title_bindings,title_platform,result)&&!result;}
API(title_load_failed_entry) u32 title_load_failed_entry(){return title_bindings->last_entry;}
API(title_load_globals_data) const u32* title_load_globals_data(){static std::array<u32,7> g;g={title_owner?title_owner->global_owner:0,common_owner->global_owner,common_load_bindings->save_owner,title_cheat?title_cheat->global_owner:0,common_texture_application_globals.presentation,title_global_538de4,title_alternate};return g.data();}
API(title_load_region) const u8* title_load_region(u32 p,u32 n){auto region=[&](u32 base,const u8* bytes,u32 size)->const u8*{return p>=base&&std::uint64_t(p)+n<=std::uint64_t(base)+size?bytes+p-base:nullptr;};if(title_owner)if(auto* b=region(GameTitleRuntime::self,title_owner->data.data(),title_owner->data.size()))return b;if(title_cheat)if(auto* b=region(GameCheatRuntime::self,title_cheat->data.data(),title_cheat->data.size()))return b;return common_composition_region(p,n);}
API(title_load_launch_data) const u8* title_load_launch_data(){return title_launch.data();}API(title_load_launch_bytes) u32 title_load_launch_bytes(){return title_launch.size();}
API(title_load_io_data) const u8* title_load_io_data(){return title_io_events.data();}API(title_load_io_bytes) u32 title_load_io_bytes(){return title_io_events.size();}
API(title_load_write_count) u32 title_load_write_count(){return title_save_writes.size();}API(title_load_write_data) const u8* title_load_write_data(u32 i){return title_save_writes[i].data();}API(title_load_write_bytes) u32 title_load_write_bytes(u32 i){return title_save_writes[i].size();}
API(title_load_sleeps) u32 title_load_sleeps(){return title_sleeps;}


#include "../src/GameTitleFrameServices.hpp"
static GameTitleFrameServices title_intro_services{common_pool_following};
static i32 title_intro_update_result=0;
static bool title_intro_update(u32 e,u32 o,u32& result){return title_intro_services.other_game_callback(e,o,result);}
API(title_intro_initialize) u32 title_intro_initialize(u32 f,u32 width,u32 height,u32 scale,u32 font){common_pool_extra_update=nullptr;common_registered_extra_draw=nullptr;title_intro_services.title=nullptr;title_intro_services.world=nullptr;return title_load_initialize(f,width,height,scale,font);}
API(title_intro_prepare) u32 title_intro_prepare(u32 variant){if(!select_title_state(*title_owner,1))return 0;auto title=title_owner->view();title.put(0x20,variant==1?3:0);title.put(0xe000,variant?0:2);title.put(0x28,variant==2?2:0);auto callback=frames->scheduler.at(title.get(16));if(!callback.data)return 0;callback.put(4,callback.get(4)|2u);title_intro_services.title=title_owner.get();title_intro_services.world=world.get();common_pool_extra_update=title_intro_update;common_registered_extra_draw=title_intro_update;return 1;}
API(title_intro_frame) u32 title_intro_frame(u32 rate){world->rate=real(rate);common_pool_trace.clear();if(!frames->dispatch(false,title_intro_update_result))return 0;common_render_device.calls.clear();common_render_device.count=common_render_device.triangles=0;common_registered_drawing->independent_signals=common_auxiliary->independent.signals;common_registered_drawing->menu_owner=0;i32 draw;return common_registered_drawing->dispatch(draw)?u32(draw):0;}
API(title_intro_update_result) u32 title_intro_update_result_value(){return u32(title_intro_update_result);}
API(title_intro_substate) u32 title_intro_substate(){return title_owner->view().get(0x24);}
API(title_intro_error) u32 title_intro_error(){return frames->failed_entry?frames->failed_entry:world->error?world->error:common_registered_failed();}


#include "../src/GameTitleActivationFrameServices.hpp"
static std::unique_ptr<TitleActivationBindings> title_activation_bindings;
static TitleActivationGlobals title_activation_globals;
static GameTitleActivationFrameServices title_activation_services{title_intro_services};
struct TitleActivationCheatHost:CheatControllerHost,CheatDrawHost {
    bool cheat_item_level(u32,bool)override{return false;}bool cheat_persist()override{return false;}bool cheat_sound(u32)override{return false;}
    bool cheat_draw_format(const std::array<float,3>&,const char*,double)override{return false;}bool cheat_draw_number(const std::array<float,3>&,i32)override{return false;}
}title_activation_cheat_host;
static bool title_activation_update(u32 e,u32 o,u32& result){return title_activation_services.other_game_callback(e,o,result);}
API(title_activation_initialize) u32 title_activation_initialize(u32 f,u32 width,u32 height,u32 scale,u32 font){title_activation_services.bindings=nullptr;title_activation_bindings.reset();return title_intro_initialize(f,width,height,scale,font);}
API(title_activation_prepare) u32 title_activation_prepare(u32 variant){common_save->view().put(0xf16c,0);title_activation_globals={0,0,0,variant==1?0x80u:0u,1,0};auto app=AnmView{common_renderer->application.data()};title_activation_bindings=std::make_unique<TitleActivationBindings>(TitleActivationBindings{*title_owner,*title_cheat,*game_ascii,*frames,*world,*common_save,app,{common_load_audio.data()},title_activation_globals});title_activation_services.bindings=title_activation_bindings.get();title_activation_services.cheat_globals={};title_activation_services.cheat_update=&title_activation_cheat_host;title_activation_services.cheat_draw=&title_activation_cheat_host;common_pool_extra_update=title_activation_update;common_registered_extra_draw=title_activation_update;title_intro_services.title=title_owner.get();title_intro_services.world=world.get();return 1;}
API(title_activation_globals_data) const u32* title_activation_globals_data(){static std::array<u32,6> values;auto& g=title_activation_globals;values={g.return_mode,g.trophy_owner,g.fade_handle,g.startup_flags,g.game_state,g.cached_game_state};return values.data();}


#include "../src/GameTitleMainFrameServices.hpp"
#include "../src/SoundQueue.hpp"
static std::vector<u32> title_ready_sounds;
struct TitleReadySoundHost:TitleMainHost {
    bool title_sound(u32 id)override{title_ready_sounds.push_back(id);SoundQueue queue;std::memcpy(queue.data.data(),common_load_audio.data()+0x1c,queue.data.size());if(!queue.request(id,false))return false;std::memcpy(common_load_audio.data()+0x1c,queue.data.data(),queue.data.size());return true;}
}title_ready_sound_host;
static GameTitleMainFrameServices title_ready_services{title_activation_services,title_ready_sound_host};
static bool title_ready_update(u32 e,u32 o,u32& result){return title_ready_services.other_game_callback(e,o,result);}
API(title_control_prepare) u32 title_control_prepare(u32 started){if(title_owner->view().get(0x24)!=2)return 0;title_ready_services.title=title_owner.get();title_ready_services.world=world.get();title_ready_services.keys={};title_ready_services.keys.started_before=started!=0;common_save->data[0xefb8]=u8(started);title_ready_sounds.clear();common_pool_extra_update=title_ready_update;common_registered_extra_draw=title_ready_update;return 1;}
API(title_control_frame) u32 title_control_frame(u32 rate,u32 fresh,u32 repeated,u32 drawing){world->rate=real(rate);title_ready_services.keys.fresh=fresh;title_ready_services.keys.repeated=repeated;common_pool_trace.clear();common_registered_drawing->trace.clear();common_render_device.calls.clear();common_render_device.count=common_render_device.triangles=0;if(!frames->dispatch(false,title_intro_update_result))return 0;if(!drawing)return 0;common_registered_drawing->independent_signals=common_auxiliary->independent.signals;common_registered_drawing->menu_owner=0;i32 result;return common_registered_drawing->dispatch(result)?u32(result):0;}
API(title_control_sounds_data) const u32* title_control_sounds_data(){return title_ready_sounds.data();}
API(title_control_sounds_words) u32 title_control_sounds_words(){return title_ready_sounds.size();}
API(title_control_state) u32 title_control_state(){return title_owner->view().get(0x1c);}


#include "../src/TitleSceneEntry.hpp"
static u32 title_scene_reset=1;
static std::vector<u8> title_scene_events;
static void title_scene_event(std::initializer_list<u32> args){const auto* p=reinterpret_cast<const u8*>(args.begin());title_scene_events.insert(title_scene_events.end(),p,p+args.size()*4);title_scene_events.insert(title_scene_events.end(),title_owner->data.begin(),title_owner->data.end());}
struct TitleSceneWorker:RootFactoryHost {
    bool allocate_root(u32&)override{return false;}bool evict_managed_textures()override{return false;}bool sleep_worker(u32)override{return false;}
    bool wait_worker(u32 handle,u32 milliseconds,u32& result)override{if(handle!=0x77770003||milliseconds!=200)return false;title_scene_event({1,handle,milliseconds});result=0;return true;}
    bool close_worker(u32 handle)override{if(handle!=0x77770003)return false;title_scene_event({2,handle});return true;}
    bool launch_worker(u32 entry,u32 argument,u32 flags,u32& id,u32& handle)override{if(entry!=0x464b20||argument!=GameTitleRuntime::self||flags)return false;if(!campaign_title_preview_launch())return false;title_scene_event({3,0,0,entry,argument,flags,GameTitleRuntime::self+0xe100});id=0x11223345;handle=0x77770004;return true;}
}title_scene_worker;
static bool title_scene_update(u32 e,u32 o,u32& result){if(o==GameTitleRuntime::self&&title_owner->view().get(0x1c)==11){if(e==0x45fb20){TitleSceneEntryBindings bindings{*title_activation_bindings,common_equipment,common_saved_equipment,title_alternate,title_scene_reset,title_scene_worker};return enter_title_scene_page(bindings,result);}if(e==0x45fb30&&title_owner->view().get(0x24)==1){result=1;return true;}}return title_ready_update(e,o,result);}
API(title_scene_entry) u32 title_scene_entry(){title_scene_reset=1;title_scene_events.clear();common_pool_extra_update=title_scene_update;common_registered_extra_draw=title_scene_update;return title_control_frame(word(1.f),0,0,1);}
API(title_scene_events_data) const u8* title_scene_events_data(){return title_scene_events.data();}
API(title_scene_events_bytes) u32 title_scene_events_bytes(){return title_scene_events.size();}


#include "../src/TitlePreviewWorker.hpp"
static std::vector<u8> title_preview_events;
static u32 title_preview_sleeps=0;
struct TitlePreviewHost:TitlePreviewWorkerHost {
    bool read_scene_preview(const std::string& name,std::vector<u8>& out,bool& found)override{found=common_load_files.read_animation_file(name,false,out);return true;}
    bool read_saved_preview(const std::string&,u32&)override{return false;}
    bool sleep_scene_preview(u32 milliseconds)override{if(milliseconds!=1&&milliseconds!=10)return false;const u32 args[]={1,milliseconds};const auto* p=reinterpret_cast<const u8*>(args);title_preview_events.insert(title_preview_events.end(),p,p+sizeof args);title_preview_events.insert(title_preview_events.end(),title_owner->data.begin(),title_owner->data.end());title_preview_events.insert(title_preview_events.end(),common_renderer->application.begin(),common_renderer->application.end());auto title=title_owner->view();if(milliseconds==10){for(u32 field:{0xe530u,0xe738u,0xe940u})title.put(field,0);}else if(++title_preview_sleeps==2)title.put(0xe000,title.get(0xe000)|0x10u);return true;}
}title_preview_host;
API(title_preview_prepare) void title_preview_prepare(u32 variant){title_preview_events.clear();title_preview_sleeps=0;auto app=AnmView{common_renderer->application.data()};app.put(0x724,variant==1?0x180:0);app.put(0x998,77);app.put(0x99c,88);auto title=title_owner->view();title.put(0xe328,2);title.put(0xe128,0);title.put(0xe12c,1);if(variant==2)title.put(0xe000,title.get(0xe000)|0x10u);}
API(title_preview_run) u32 title_preview_run(){return run_title_preview_worker(*title_owner,*world,{common_renderer->application.data()},title_preview_host);}
API(title_preview_events_data) const u8* title_preview_events_data(){return title_preview_events.data();}
API(title_preview_events_bytes) u32 title_preview_events_bytes(){return title_preview_events.size();}


#include "../src/TitlePreviewImage.hpp"
static std::vector<u8> title_preview_preloads;
struct TitlePreviewPreloadDevice:TitlePreviewImageDevice {
    bool preload_preview_texture(u32 token)override{u32 resource=title_owner->view().get(0x14),table,n;if(!world->read(resource+0x124,&table,4)||!world->read(resource+0x110,&n,4))return false;n*=24;const u32 header[]={token,resource,table,n};const auto* p=reinterpret_cast<const u8*>(header);title_preview_preloads.insert(title_preview_preloads.end(),p,p+sizeof header);title_preview_preloads.insert(title_preview_preloads.end(),title_owner->data.begin(),title_owner->data.end());title_preview_preloads.insert(title_preview_preloads.end(),common_renderer->application.begin(),common_renderer->application.end());for(auto r:{std::array<u32,2>{resource,0x13c},{table,n}}){std::vector<u8> bytes(r[1]);if(!world->read(r[0],bytes.data(),r[1]))return false;title_preview_preloads.insert(title_preview_preloads.end(),bytes.begin(),bytes.end());}return true;}
}title_preview_preload_device;
API(title_preview_image_rearm) void title_preview_image_rearm(){auto title=title_owner->view();title.put(0xe000,title.get(0xe000)&~0x10u);title_preview_prepare(0);}
API(title_preview_image_prepare) u32 title_preview_image_prepare(){title_preview_preloads.clear();for(auto& p:common_texture_resources->textures.images){u32 vtable;if(!world->read(p.first,&vtable,4))return 0;for(auto field:{std::array<u32,2>{0x24,12},{0x30,0},{0x34,4},{0x38,8}}){const u32 token=0x7002d100+field[1];if(!world->write(vtable+field[0],&token,4))return 0;}}return 1;}
API(title_preview_image_run) u32 title_preview_image_run(){world->rate=1.f;GameTitlePreviewImages images{*world,common_texture_resources->textures,common_texture_device,title_preview_preload_device};u32 result;return advance_title_scene_png_pending(*title_owner,*world,images,result)?result:0;}
API(title_preview_preloads_data) const u8* title_preview_preloads_data(){return title_preview_preloads.data();}
API(title_preview_preloads_bytes) u32 title_preview_preloads_bytes(){return title_preview_preloads.size();}


#include "../src/GameSavedPreviewFiles.hpp"
static std::vector<u8> title_saved_source,title_saved_sleep_events;
static std::vector<u32> title_saved_io;
static u32 title_saved_present=0,title_saved_sleeps=0;
struct TitleSavedFileServices:SavedPreviewFileServices {
    bool saved_preview_directory(bool restore)override{title_saved_io.insert(title_saved_io.end(),{0,u32(restore)});return true;}
    bool saved_preview_exists(const std::string& name,bool& found)override{if(name!="savedata/sc01_02.dat")return false;found=title_saved_present!=0;title_saved_io.insert(title_saved_io.end(),{1,u32(found)});return true;}
    bool read_saved_preview_bytes(const std::string& name,std::vector<u8>& out)override{title_saved_io.insert(title_saved_io.end(),{2,u32(title_saved_source.size())});return common_load_files.read_animation_file(name,true,out);}
}title_saved_file_services;
struct TitleSavedMemory:GameSavedPreviewFiles {
    using GameSavedPreviewFiles::GameSavedPreviewFiles;
    bool allocate_saved_preview_array(u32 n,u32& token)override{if(!GameSavedPreviewFiles::allocate_saved_preview_array(n,token))return false;title_saved_io.insert(title_saved_io.end(),{3,token,n});return true;}
    bool release_saved_preview_array(u32 token)override{title_saved_io.insert(title_saved_io.end(),{4,token});return GameSavedPreviewFiles::release_saved_preview_array(token);}
};
struct TitleSavedWorkerHost:TitlePreviewWorkerHost {
    bool read_scene_preview(const std::string& name,std::vector<u8>& out,bool& found)override{return title_preview_host.read_scene_preview(name,out,found);}
    bool read_saved_preview(const std::string&,u32&)override{return false;}
    bool sleep_scene_preview(u32 ms)override{if(ms!=1&&ms!=10)return false;const u32 args[]={1,ms};const auto* p=reinterpret_cast<const u8*>(args);title_saved_sleep_events.insert(title_saved_sleep_events.end(),p,p+sizeof args);title_saved_sleep_events.insert(title_saved_sleep_events.end(),title_owner->data.begin(),title_owner->data.end());title_saved_sleep_events.insert(title_saved_sleep_events.end(),common_renderer->application.begin(),common_renderer->application.end());auto title=title_owner->view();if(ms==10){title.put(0xed50,0);title.put(0xef58,0);}else if(++title_saved_sleeps==2)title.put(0xe000,title.get(0xe000)|0x10u);return true;}
}title_saved_worker_host;
API(title_saved_worker_set_file) void title_saved_worker_set_file(const u8* p,u32 n,u32 present){title_saved_source.assign(p,p+n);title_saved_present=present;if(present)files["sc01_02.dat"]=title_saved_source;else files.erase("sc01_02.dat");}
API(title_saved_worker_prepare) void title_saved_worker_prepare(){title_saved_io.clear();title_saved_sleep_events.clear();title_saved_sleeps=0;auto title=title_owner->view();title.put(0xe000,title.get(0xe000)&~0x10u);title.put(0xe328,0);title.put(0xeb48,1);title.put(0xe948,102);title.put(0xed50,0);title.put(0xef58,0);auto app=AnmView{common_renderer->application.data()};app.put(0x724,0);app.put(0x998,77);app.put(0x99c,88);}
API(title_saved_worker_run) u32 title_saved_worker_run(){TitleSavedMemory memory{*world,title_saved_file_services};GameTitleSavedPreviewWorker host{title_saved_worker_host,memory,common_save->codec};return run_title_preview_worker(*title_owner,*world,{common_renderer->application.data()},host);}
API(title_saved_worker_io_data) const u32* title_saved_worker_io_data(){return title_saved_io.data();}
API(title_saved_worker_io_words) u32 title_saved_worker_io_words(){return title_saved_io.size();}
API(title_saved_worker_events_data) const u8* title_saved_worker_events_data(){return title_saved_sleep_events.data();}
API(title_saved_worker_events_bytes) u32 title_saved_worker_events_bytes(){return title_saved_sleep_events.size();}
API(title_saved_codec_data) const u8* title_saved_codec_data(){return common_save->codec.dictionary;}


#include "../src/TitleSavedPreviewImage.hpp"
API(title_saved_image_prepare) void title_saved_image_prepare(){title_preview_preloads.clear();auto title=title_owner->view();title.put(0x28,2);title.put(0x1d8,0);title.put(0x2b4,18);title.put(0x2b8,19);title.put(0x2bc,word(19.f));}
API(title_saved_image_run) u32 title_saved_image_run(){world->rate=1.f;GameTitleSavedPreviewImages images{*world,common_texture_resources->textures,common_texture_device,title_preview_preload_device};u32 result;return advance_title_scene_saved_pending(*title_owner,*world,images,result)?result:0;}


#include "../src/TitleScenePage.hpp"
static std::vector<u8> title_dialog_calls;
static bool boot_title_draw_literal(AnmView,const std::vector<u8>&);
struct TitleDialogRecorder:TitleDialogHost {
    bool title_dialog_text(AnmView vm,const std::vector<u8>& text)override{if(!vm.data)return false;u32 token=0;for(u32 i=0;i<world->states.size();++i)if(world->states[i]->data()==vm.data){token=world->state_tokens[i];break;}if(!token)return false;const u32 header[]={token,u32(text.size())};const auto* p=reinterpret_cast<const u8*>(header);title_dialog_calls.insert(title_dialog_calls.end(),p,p+sizeof header);title_dialog_calls.insert(title_dialog_calls.end(),text.begin(),text.end());title_dialog_calls.insert(title_dialog_calls.end(),vm.data,vm.data+AnmView::bytes);title_dialog_calls.insert(title_dialog_calls.end(),title_owner->data.begin(),title_owner->data.end());return boot_title_draw_literal(vm,text);}
}title_dialog_recorder;
API(title_dialog_show) u32 title_dialog_show(u32 record,u32 variant,u32 x,u32 y){if(record>=title_owner->view().get(0x5cec))return 0;auto row=title_owner->view().sub(0x5cf0+record*0x20c);if(variant==1)row.data[0x108]='\\';auto text=[&](u32 at){std::vector<u8> bytes;for(u32 i=0;i<256&&row.data[at+i];++i)bytes.push_back(row.data[at+i]);return bytes;};title_dialog_calls.clear();return show_title_dialog(*title_owner,*world,title_dialog_recorder,text(8),text(0x108),real(x),real(y),row.floating(0x208));}
API(title_dialog_clear) u32 title_dialog_clear(){return clear_title_dialog(*title_owner,*world);}
API(title_dialog_calls_data) const u8* title_dialog_calls_data(){return title_dialog_calls.data();}
API(title_dialog_calls_bytes) u32 title_dialog_calls_bytes(){return title_dialog_calls.size();}

API(title_scene_page_prepare) void title_scene_page_prepare(){auto title=title_owner->view(),save=common_save->view();save.put(0xf084,9);for(u32 at=0xf088;at<0xf08c;++at)save.data[at]=1;title.put(0x1e0,10);}
API(title_scene_page_frame) u32 title_scene_page_frame(u32 fresh,u32 repeated){title_dialog_calls.clear();title_ready_sounds.clear();world->rate=1.f;GameTitlePreviewImages png{*world,common_texture_resources->textures,common_texture_device,title_preview_preload_device};GameTitleSavedPreviewImages saved{*world,common_texture_resources->textures,common_texture_device,title_preview_preload_device};TitleScenePageBindings bindings{*title_activation_bindings,title_dialog_recorder,title_ready_sound_host,png,saved,common_equipment,common_saved_equipment};u32 result;return advance_title_scene_page(bindings,{fresh,repeated,false},result)?result:0;}


#include "../src/GameTitleSceneFrameServices.hpp"
static GameTitleSceneFrameServices title_scene_session_services{title_ready_services};
static std::unique_ptr<GameTitlePreviewImages> title_session_png;
static std::unique_ptr<GameTitleSavedPreviewImages> title_session_saved;
static std::unique_ptr<TitleScenePageBindings> title_session_page;
static std::unique_ptr<GameTitleCheatServices> title_session_cheat;
static i32 title_scene_session_result=0;
static bool title_scene_session_callback(u32 e,u32 o,u32& result){return title_scene_session_services.other_game_callback(e,o,result);}
API(title_scene_session_prepare) void title_scene_session_prepare(){title_scene_page_prepare();title_session_png=std::make_unique<GameTitlePreviewImages>(*world,common_texture_resources->textures,common_texture_device,title_preview_preload_device);title_session_saved=std::make_unique<GameTitleSavedPreviewImages>(*world,common_texture_resources->textures,common_texture_device,title_preview_preload_device);title_session_page=std::make_unique<TitleScenePageBindings>(TitleScenePageBindings{*title_activation_bindings,title_dialog_recorder,title_ready_sound_host,*title_session_png,*title_session_saved,common_equipment,common_saved_equipment});title_session_cheat=std::make_unique<GameTitleCheatServices>(*common_save,*world,title_platform,common_load_platform,common_saved_equipment,title_scene_session_services.cheat_globals.secondary,AnmView{common_load_audio.data()},game_ascii->view(),common_loaded_save.get());title_scene_session_services.page=title_session_page.get();title_scene_session_services.cheat=title_session_cheat.get();title_scene_session_services.cheat_globals={};common_pool_extra_update=title_scene_session_callback;common_registered_extra_draw=title_scene_session_callback;}
API(title_scene_session_frame) u32 title_scene_session_frame(u32 fresh,u32 repeated){title_dialog_calls.clear();title_ready_sounds.clear();world->rate=1.f;title_scene_session_services.keys={fresh,repeated,false};common_pool_trace.clear();common_registered_drawing->trace.clear();common_render_device.calls.clear();common_render_device.count=common_render_device.triangles=0;if(!frames->dispatch(false,title_scene_session_result))return 0;common_registered_drawing->independent_signals=common_auxiliary->independent.signals;common_registered_drawing->menu_owner=0;i32 result;return common_registered_drawing->dispatch(result)?u32(result):0;}
API(title_scene_session_update_result) i32 title_scene_session_update_result(){return title_scene_session_result;}


#include "../src/TitleSceneConfirm.hpp"
#include "../src/GameMenuApplicationDrawV2.hpp"
static std::unique_ptr<GameMenuApplicationDrawV2> title_scene_confirm_drawing;
static ReclaimingAnmMenuWorldV1* campaign_reclaim_world=nullptr;
struct TitleReturnedResourceWorld:ReclaimingAnmMenuWorldV1 {
// ANM10016..10021 read the same live camera region that the Stage callback
// updates. This is our own runtime camera, never an observed original operand.
    bool read(u32 pointer,void* output,u32 bytes)override{
        constexpr u32 base=0x4e4d84;
        if(common_render_stage&&pointer>=base&&std::uint64_t(pointer)+bytes<=std::uint64_t(base)+common_render_stage->camera.size()){
            std::memcpy(output,common_render_stage->camera.data()+pointer-base,bytes);return true;
        }
        return AnmMenuWorld::read(pointer,output,bytes);
    }

    using ReclaimingAnmMenuWorldV1::ReclaimingAnmMenuWorldV1;bool next_shared_file=false;
    bool allocate_resource_storage(u32 n,bool array,u32& token)override{if(!next_shared_file)return ReclaimingAnmMenuWorldV1::allocate_resource_storage(n,array,token);next_shared_file=false;if(!common_load_storage.allocate_game_storage(n,token)||!token)return false;regions.push_back({token,std::vector<u8>(std::max(1u,n),u8(fill))});return true;}
};
static AnmResourceWorld* title_scene_confirm_world(AnmResourceServices& services){campaign_reclaim_world=new TitleReturnedResourceWorld(services);return campaign_reclaim_world;}
static bool title_scene_confirm_callback(u32 e,u32 o,u32& result){if(e==0x45fb30&&o==GameTitleRuntime::self&&!title_owner->view().get(0x1c)){result=1;return true;}if(e==0x45fb20&&o==GameTitleRuntime::self&&title_owner->view().get(0x1c)==11&&title_owner->view().get(0x24)==4)return advance_title_scene_confirmation(*title_session_page,static_cast<AnmMenuWorld&>(*world),result);return title_scene_session_callback(e,o,result);}
API(title_scene_confirm_initialize) u32 title_scene_confirm_initialize(u32 f,u32 width,u32 height,u32 scale,u32 font){title_scene_confirm_drawing.reset();common_load_world_factory=title_scene_confirm_world;return title_activation_initialize(f,width,height,scale,font);}
API(title_scene_confirm_prepare) void title_scene_confirm_prepare(){title_scene_session_prepare();title_scene_confirm_drawing=std::make_unique<GameMenuApplicationDrawV2>(*common_registered_drawing,frames->scheduler,*common_composition,*common_renderer,common_render_device,static_cast<AnmMenuWorld&>(*world),common_registered_draw_services);common_pool_extra_update=title_scene_confirm_callback;common_registered_extra_draw=title_scene_confirm_callback;}
API(title_scene_confirm_frame) u32 title_scene_confirm_frame(u32 fresh,u32 repeated){title_dialog_calls.clear();title_ready_sounds.clear();world->rate=1.f;title_scene_session_services.keys={fresh,repeated,false};common_pool_trace.clear();common_registered_drawing->trace.clear();common_render_device.calls.clear();common_render_device.count=common_render_device.triangles=0;if(!frames->dispatch(false,title_scene_session_result))return 0;common_registered_drawing->independent_signals=common_auxiliary->independent.signals;common_registered_drawing->menu_owner=0;i32 result;return title_scene_confirm_drawing->dispatch(result)?u32(result):0;}


#include "../src/TitleSceneStart.hpp"
static std::array<u8,0xe0> title_scene_handoff_game;
static u32 title_scene_handoff_descriptor=0;
struct TitleSceneHandoffWorker:RootFactoryHost {
    bool allocate_root(u32&)override{return false;}bool evict_managed_textures()override{return false;}bool sleep_worker(u32)override{return false;}bool launch_worker(u32,u32,u32,u32&,u32&)override{return false;}
    bool wait_worker(u32 handle,u32 ms,u32& result)override{if(handle!=0x77770004||ms!=200)return false;title_scene_event({1,handle,ms});if(!title_second_start_preview_join())return false;result=0;return true;}
    bool close_worker(u32 handle)override{if(handle!=0x77770004)return false;title_scene_event({2,handle});return true;}
}title_scene_handoff_worker;
static void title_scene_handoff_sync(){auto game=AnmView{title_scene_handoff_game.data()};for(u32 i=0;i<4;++i){game.put(0x20+i*4,common_equipment[i]);game.put(0x3c+i*4,common_saved_equipment[i]);}game.put(12,title_activation_globals.game_state);game.put(0xa8,title_activation_globals.cached_game_state);game.put(0x38,title_alternate);game.put(0xc0,title_activation_globals.startup_flags);}
static bool title_scene_handoff_callback(u32 e,u32 o,u32& result){
    if(o==GameTitleRuntime::self&&e==0x45fb20&&title_owner->view().get(0x1c)==11&&(title_owner->view().get(0x24)==3||title_owner->view().get(0x24)==6))return advance_title_scene_return(*title_session_page,title_platform,common_loaded_save.get(),result);
    if(o==GameTitleRuntime::self&&e==0x45fb30&&title_owner->view().get(0x1c)==2){result=1;return true;}
    if(o==GameTitleRuntime::self&&e==0x45fb20&&title_owner->view().get(0x1c)==11&&title_owner->view().get(0x24)==4&&signed_word(title_owner->view().get(0x2b8))>=38){title_scene_handoff_sync();TitleSceneStartBindings bindings{*title_owner,*common_save,*world,{common_renderer->application.data()},{common_load_audio.data()},{title_scene_handoff_game.data()},common_equipment,common_saved_equipment,title_scene_handoff_descriptor,title_activation_globals.return_mode,title_scene_handoff_worker,title_platform,common_loaded_save.get(),title_session_page.get()};const bool ok=start_selected_title_scene(bindings,result);title_activation_globals.startup_flags=AnmView{title_scene_handoff_game.data()}.get(0xc0);title_activation_globals.game_state=AnmView{title_scene_handoff_game.data()}.get(12);return ok;}
    return title_scene_confirm_callback(e,o,result);
}
API(title_scene_handoff_prepare) void title_scene_handoff_prepare(){title_scene_confirm_prepare();title_scene_handoff_game.fill(0);title_scene_handoff_descriptor=0;common_pool_extra_update=title_scene_handoff_callback;common_registered_extra_draw=title_scene_handoff_callback;}
API(title_scene_handoff_frame) u32 title_scene_handoff_frame(u32 fresh,u32 repeated){return title_scene_confirm_frame(fresh,repeated);}
API(title_scene_handoff_game_data) const u8* title_scene_handoff_game_data(){title_scene_handoff_sync();return title_scene_handoff_game.data();}
API(title_scene_handoff_globals_data) const u32* title_scene_handoff_globals_data(){static std::array<u32,2> g;g={title_scene_handoff_descriptor,title_activation_globals.return_mode};return g.data();}


#include "../src/GameTitleRootApplication.hpp"
static RootState title_root_state;
static BackgroundWorker title_root_worker;
static RootFactoryGlobals title_root_globals;
static ApplicationStateGlobals title_root_application_globals;
static std::vector<u8> title_root_events;
static void title_root_event(u32 kind,std::initializer_list<u32> args){const u32 header[]={kind,u32(args.size())};auto append=[&](const void* p,u32 n){const auto* b=static_cast<const u8*>(p);title_root_events.insert(title_root_events.end(),b,b+n);};append(header,8);append(args.begin(),args.size()*4);append(title_root_state.data.data(),RootState::bytes);append(title_owner->data.data(),GameTitleRuntime::bytes);append(common_renderer->application.data(),common_renderer->application.size());const u32 globals[]={title_owner->global_owner,title_cheat->global_owner,title_root_globals.root,common_texture_application_globals.presentation};append(globals,sizeof globals);}
struct TitleRootPlatform:RootFactoryHost {
    bool allocate_root(u32& token)override{token=0x6e004000;if(!common_load_storage.reserve_game_owner(token,RootState::bytes))return false;title_root_state.data.fill(u8(fill));title_root_event(0,{RootState::bytes});return true;}
    bool evict_managed_textures()override{common_render_device.emit(16,{});title_root_event(1,{});return true;}
    bool wait_worker(u32 h,u32 ms,u32& result)override{if((h!=0x77770004&&h!=0x77770005)||ms!=200)return false;title_scene_event({1,h,ms});result=0;return true;}
    bool sleep_worker(u32)override{return false;}
    bool close_worker(u32 h)override{if(h!=0x77770004&&h!=0x77770005)return false;title_scene_event({2,h});return true;}
    bool launch_worker(u32 entry,u32 argument,u32 flags,u32& id,u32& handle)override{if(entry!=0x432a20||argument||flags)return false;title_root_event(2,{0,0,entry,argument,flags,0x4e47d0+0x994});id=0x11223346;handle=0x77770005;return true;}
}title_root_platform;
struct TitleRootFollowing:ApplicationStateServices {
    bool lock_application_state(bool)override{return false;}
    bool application_state_call(u32,u32,u32,u32&)override{return false;}
    bool application_root_mode(u32&)override{return false;}
}title_root_following;
static void title_root_storage_release(u32 p){world->releases.insert(world->releases.end(),{2,p});}
API(title_root_prepare) void title_root_prepare(){auto app=AnmView{common_renderer->application.data()};app.put(0x6e8,4);title_root_state={};title_root_worker={};title_root_globals={};title_root_application_globals={};title_root_events.clear();}
API(title_root_run) i32 title_root_run(){common_load_storage_release_observer=title_root_storage_release;auto app=AnmView{common_renderer->application.data()};GameTitleRootApplication services{app,*title_bindings,title_root_state,title_root_worker,title_root_globals,common_texture_application_globals.presentation,title_root_platform,title_root_following};services.replays=campaign_replay_cleanup_host();common_render_device.calls.clear();common_render_device.count=common_render_device.triangles=0;i32 result;const bool ok=transition_application_state(app,title_root_application_globals,services,result);common_load_storage_release_observer=nullptr;return ok?result:-2;}
API(title_root_data) const u8* title_root_data(){return title_root_state.data.data();}
API(title_root_globals_data) const u32* title_root_globals_data(){static std::array<u32,2> g;g={title_root_globals.root,common_texture_application_globals.presentation};return g.data();}
API(title_root_events_data) const u8* title_root_events_data(){return title_root_events.data();}
API(title_root_events_bytes) u32 title_root_events_bytes(){return title_root_events.size();}


#include "../src/GameRootReplayLoadRuntime.hpp"
#include "../src/GameReadyOwnerServices.hpp"
#include "../src/MusicSilentPump.hpp"
#include "../src/ApplicationLoading.hpp"
#include "../src/MusicScene.hpp"
#include <new>

static std::vector<AnmWorld::Region> title_load_rom;
static std::array<u8,256> title_root_filename{};
static std::map<u32,u32> title_root_load_words;
static std::vector<std::vector<u32>> title_root_load_yields;
static std::unique_ptr<GameReadyOwnerServices> title_root_ready;
static std::unique_ptr<GameHudRuntime> title_root_hud;
static std::unique_ptr<GameMenuRuntime> title_root_menu;
static std::unique_ptr<GameEnemyRuntime> title_root_enemy;
static std::unique_ptr<GameCheatRuntime> title_root_cheat;
static std::unique_ptr<GameAuxRuntime> title_root_aux;
static std::unique_ptr<GameFrameTimingRuntime> title_root_timing;
static std::unique_ptr<GameRootReplayLoadRuntime> title_root_loader;
static std::vector<GameOwnerRuntime::Storage> title_root_messages;
static GameManagerInitGlobals title_root_game;
static GameRootReplayInputHost& campaign_replay_input_host();
static bool title_root_loading=false;

static bool title_root_rom_read(u32 p,void* out,u32 n){
    for(const auto& r:title_load_rom)if(p>=r.token&&std::uint64_t(p)+n<=std::uint64_t(r.token)+r.bytes.size()){std::memcpy(out,r.bytes.data()+p-r.token,n);return true;}
    return false;
}
static bool title_root_name(u32 p,std::string& out){out.clear();for(u32 i=0;i<256;++i){u8 b;if(!title_root_rom_read(p+i,&b,1))return false;if(!b)return true;out.push_back(char(b));}return false;}
struct TitleRootLoadWait:GameResourceWaitHost {
    bool resource_wait(u32 ms)override{
        std::vector<u32> row{ms};for(u32 i=0;i<30;++i){u32 r,pending;if(!world->read(0x72bc7b0c+i*4,&r,4))return false;if(r){if(!world->read(r+0x128,&pending,4))return false;if(pending)row.insert(row.end(),{i,pending});}}
        u32 music;i32 pump;if(!campaign_pump_audio(music)||!world->pump(pump)||pump)return false;
        row.push_back(music);row.push_back(u32(pump));title_root_load_yields.push_back(std::move(row));return true;
    }
}title_root_load_wait;
struct TitleRootReady:GameReadyOwnerServices {
    using GameReadyOwnerServices::GameReadyOwnerServices;
    bool request_game_resource(u32 slot,const char* name,u32& token)override{
        // ECL's metadata loader calls4820a0 directly. This inherited protocol
        // records482140 entries; metadata effects still compare in full state.
        if(slot<10||slot>15)common_load_log(0,slot,name);
        return GameReadyOwnerServices::request_game_resource(slot,name,token);
    }
    bool read_player_shots(std::vector<u8>& out)override{return common_load_files.read_animation_file("pl00a.sht",false,out);}
};
struct TitleRootStageFiles:GameStageServices {
    bool read_game_stage_file(const std::string& n,std::vector<u8>& b)override{return common_load_files.read_animation_file(n,false,b);}
}title_root_stage_files;
struct TitleRootHudFiles:GameHudServices {
    bool hud_load_read(u32 p,void* out,u32 n)override{if(p>=0x541050&&std::uint64_t(p)+n<=0x541150){std::memcpy(out,title_root_filename.data()+p-0x541050,n);return true;}return title_root_rom_read(p,out,n);}
    bool hud_load_write(u32 p,const void* in,u32 n)override{if(p<0x541050||std::uint64_t(p)+n>0x541150)return false;std::memcpy(title_root_filename.data()+p-0x541050,in,n);return true;}
    bool load_hud_scene_animation(u32 p,u32& token)override{std::string n;return title_root_name(p,n)&&title_root_ready->request_game_resource(6,n.c_str(),token);}
    bool read_hud_message_file(u32 p,u32& token)override{if(p!=0x541050)return false;std::vector<u8> b;if(!common_load_files.read_animation_file(reinterpret_cast<const char*>(title_root_filename.data()),false,b)||!title_root_ready->allocate_game_storage(u32(b.size()),token))return false;title_root_messages.push_back({token,std::move(b)});return true;}
    bool hud_load_error()override{return false;}bool hud_cached_file_log(u32)override{return false;}
    bool game_hud_message_storage(u32 p,AnmView& v)override{return campaign_message_storage(p,v);}
    bool release_game_hud_storage(u32 p,bool array)override{return campaign_message_release(p,array);}bool release_game_hud_resource(u32)override{return false;}
}title_root_hud_files;
struct TitleRootMenuFiles:GameMenuServices {
    bool read_game_menu_file(const char* n,std::vector<u8>& b)override{return common_load_files.read_animation_file(n,false,b);}
    bool release_game_menu_storage(u32,bool)override{return false;}bool destroy_game_menu_recording(u32 token)override{return campaign_replay_menu_recording_destroy(token);}
}title_root_menu_files;
struct TitleRootEnemyFiles:GameEnemyServices {
    bool read_enemy_file(const char* n,std::vector<u8>& b)override{return common_load_files.read_animation_file(n,false,b);}
    bool release_enemy_storage(u32 p,bool array)override{world->releases.insert(world->releases.end(),{array?1u:2u,p});return true;}
}title_root_enemy_files;
struct TitleRootAuxFiles:GameAuxServices {
    bool auxiliary_surface(u32 texture,u32 level,u32& surface)override{i32 result;return common_texture_resources->textures.surface(texture,level,surface,result)&&!result;}
    bool release_auxiliary_surface(u32 p)override{return common_texture_resources->textures.release(p);}
    bool release_auxiliary_storage(u32,bool)override{return false;}
}title_root_aux_files;
static bool title_root_load_read(u32 p,void* out,u32 n){
    auto region=[&](u32 base,const void* data,u32 size){if(p<base||std::uint64_t(p)+n>std::uint64_t(base)+size)return false;std::memcpy(out,static_cast<const u8*>(data)+p-base,n);return true;};
    if(region(0x4e46f0,title_scene_handoff_game.data(),0xe0)||region(0x4e47d0,common_renderer->application.data(),0xa34)||region(0x53b1e0,common_load_audio.data(),0x57b0)||region(0x541050,title_root_filename.data(),256)||region(0x6e004000,title_root_state.data.data(),0x9c)||title_root_rom_read(p,out,n))return true;
    if(title_root_timing&&region(GameFrameTimingRuntime::self,title_root_timing->data.data(),title_root_timing->data.size()))return true;
    if(title_root_hud&&title_root_hud->globals.owner&&region(GameHudRuntime::self,title_root_hud->data.data(),title_root_hud->data.size()))return true;
    if(title_root_menu&&title_root_menu->global_owner){if(region(GameMenuRuntime::self,title_root_menu->menu.data.data(),title_root_menu->menu.data.size())||region(title_root_menu->hint_token,title_root_menu->menu.hints.data(),title_root_menu->menu.hints.size()))return true;}
    if(title_root_cheat&&title_root_cheat->global_owner&&region(GameCheatRuntime::self,title_root_cheat->data.data(),title_root_cheat->data.size()))return true;
    for(const auto& s:title_root_messages)if(region(s.token,s.bytes.data(),s.bytes.size()))return true;
    if(owners->read(p,out,n)||common_render_stage->read(p,out,n)||(title_root_enemy&&title_root_enemy->read(p,out,n))||(title_root_aux&&title_root_aux->read(p,out,n)))return true;
    if(n==4){auto i=title_root_load_words.find(p);if(i!=title_root_load_words.end()){std::memcpy(out,&i->second,4);return true;}}
    return false;
}
struct TitleRootLoaderPlatform:RootLoadHost {
    bool load_read(u32 p,void* out,u32 n)override{
        if(n==4){u32 v;bool found=true;switch(p){case 0x538de8:v=0x72000000;break;case 0x4e6bac:v=title_scene_handoff_descriptor;break;case 0x53b0ec:v=world->width;break;case 0x4e40b0:v=word(world->rate);break;default:found=false;}if(found){std::memcpy(out,&v,4);return true;}}
        return title_root_load_read(p,out,n);
    }
    bool load_write(u32 p,const void* in,u32 n)override{if(n!=4)return false;u32 v;std::memcpy(&v,in,4);if(p==0x4e40b0){world->rate=real(v);return true;}if(p>=0x4e47d0&&std::uint64_t(p)+4<=0x4e5204){AnmView{common_renderer->application.data()}.put(p-0x4e47d0,v);return true;}auto i=title_root_load_words.find(p);if(i==title_root_load_words.end())return false;i->second=v;return true;}
    bool load_call(u32 e,u32 owner,std::initializer_list<u32> args,u32& result)override{
        result=0;
        if(e==0x444660&&args.size()==2){std::string n;MusicCommandQueue queue;MusicScene music;if(!title_root_name(*(args.begin()+1),n))return false;std::memcpy(queue.data.data(),common_load_audio.data()+0x24f8,queue.data.size());if(!music.load(queue,n.c_str()))return false;std::memcpy(common_load_audio.data()+0x24f8,queue.data.data(),queue.data.size());result=1;return true;}
        if(e==0x444e00&&owner==0x4e47d0&&!args.size()){auto app=AnmView{common_renderer->application.data()};ApplicationLoading g{app.get(0x9ac),{title_root_load_words[0x540de8],title_root_load_words[0x540dec],title_root_load_words[0x540df0]},title_root_load_words[0x4e6b7c]};if(!finish_application_loading(g,*world))return false;app.put(0x9ac,g.state);title_root_load_words[0x4e6b7c]=g.context;for(u32 i=0;i<3;++i)title_root_load_words[0x540de8+i*4]=g.visuals[i];return true;}
        if(e==0x418240&&!args.size()){auto vm=common_application_targets->target_animation(owner);return vm.data&&signal_animation_vm(*world,vm,2,false);}
        return false;
    }
    bool load_signal(u32 p,i32 signal,bool immediate)override{return signal_animation_vm(*world,common_application_targets->target_animation(p),signal,immediate);}
    bool load_sleep(u32 ms)override{return title_root_load_wait.resource_wait(ms);}
    bool load_float_environment()override{return true;}
}title_root_loader_platform;

API(title_root_load_rom_clear) void title_root_load_rom_clear(){title_load_rom.clear();}
API(title_root_load_rom_add) void title_root_load_rom_add(u32 token,const u8* data,u32 n){title_load_rom.push_back({token,{data,data+n}});}
API(title_root_load_initialize) u32 title_root_load_initialize(u32 f,u32 width,u32 height,u32 scale,u32 font){title_root_loading=false;title_root_loader.reset();title_root_hud.reset();title_root_menu.reset();title_root_enemy.reset();title_root_cheat.reset();title_root_aux.reset();title_root_timing.reset();title_root_ready.reset();title_root_game={};title_load_rom.clear();return title_scene_confirm_initialize(f,width,height,scale,font);}
API(title_root_load_prepare) u32 title_root_load_prepare(){
    if(owners->created||common_render_stage->created||!title_root_globals.root||title_owner->global_owner||title_cheat->global_owner)return 0;
    title_root_loading=true;title_root_load_yields.clear();title_root_messages.clear();title_root_filename.fill(0);title_root_load_words.clear();
    for(u32 p:{0x4e47a4,0x4e47c0,0x4e516c,0x4e5168,0x538de4,0x4e6b78,0x4e6b74,0x4e4790,0x4e4794,0x4e47a8,0x4e47ac,0x4e6b7c,0x540de8,0x540dec,0x540df0})title_root_load_words[p]=0;
    title_root_ready=std::make_unique<TitleRootReady>(common_load_storage,*world,title_root_load_wait);
    // These holders are cold and already referenced by the menu renderer.
    // Reconstruct at the same addresses to bind the cooperative loading host.
    owners->~GameOwnerRuntime();new(owners.get()) GameOwnerRuntime(*frames,*world,*title_root_ready);
    common_render_stage->~GameStageRuntime();new(common_render_stage.get()) GameStageRuntime(*frames,*world,*title_root_ready,title_root_stage_files);
    title_root_hud=std::make_unique<GameHudRuntime>(*frames,*world,*title_root_ready,title_root_hud_files);
    title_root_menu=std::make_unique<GameMenuRuntime>(*frames,*world,common_pool_overlay,*title_root_ready,title_root_menu_files);
    title_root_enemy=std::make_unique<GameEnemyRuntime>(frames->scheduler,*title_root_ready,title_root_enemy_files,&title_root_filename);
    title_root_cheat=std::make_unique<GameCheatRuntime>(*frames,*world,common_pool_overlay,*title_root_ready);
    // Common Effects remains live in its existing owner. The cold gameplay
    // auxiliary component only creates Special/screenshot owners; its immutable
    // Effects interface names the same retained resource owner.
    title_root_aux=std::make_unique<GameAuxRuntime>(frames->scheduler,*world,*title_root_ready,title_root_aux_files);title_root_aux->effects=common_auxiliary->effects;title_root_aux->effects_owner=common_auxiliary->effects_owner;
    title_root_timing=std::move(boot_timing);if(!title_root_timing||!title_root_timing->global_owner)return 0;
    auto app=AnmView{common_renderer->application.data()};app.put(0x6f8,1);app.put(0x724,0);AnmView{common_load_audio.data()}.put(12,0x6e033000);
    title_scene_handoff_sync();std::memcpy(title_root_game.game_state.data(),title_scene_handoff_game.data(),160);title_root_game.new_game=1;title_root_game.scene=AnmView{title_scene_handoff_game.data()}.get(0xac);title_root_game.game_flags=AnmView{title_scene_handoff_game.data()}.get(0xc0);title_root_game.random=common_gameplay;std::memcpy(title_root_game.root_snapshot.data(),app.data+0x1d4,92);
    common_render_stage->loading.scene=title_root_game.scene;std::memcpy(common_render_stage->loading.camera_defaults.data(),app.data+0x5b4,300);
    title_root_loader=std::make_unique<GameRootReplayLoadRuntime>(title_root_state,0x6e004000,title_root_game,*common_save,0x6d000000,*frames,*owners,*common_render_stage,*title_root_hud,*title_root_menu,*title_root_enemy,*title_root_cheat,*title_root_aux,*title_root_timing,*world,*title_root_ready,title_root_loader_platform,campaign_replay_input_host());
    return 1;
}
API(title_root_load_run) i32 title_root_load_run(){common_load_storage_release_observer=title_root_storage_release;i32 result;const bool ok=title_root_loader->load(result);common_load_storage_release_observer=nullptr;
    std::memcpy(title_scene_handoff_game.data(),title_root_game.game_state.data(),160);AnmView{title_scene_handoff_game.data()}.put(0xc0,title_root_game.game_flags);common_gameplay=title_root_game.random;title_activation_globals.startup_flags=title_root_game.game_flags;title_alternate=title_root_game.game_state[14];std::copy_n(title_root_game.game_state.begin()+8,4,common_equipment.begin());std::copy_n(title_root_game.game_state.begin()+15,4,common_saved_equipment.begin());title_global_538de4=title_root_load_words[0x538de4];
    for(const auto& [p,v]:title_root_load_words)if(p>=0x4e4790&&p+4<=0x4e47d0)AnmView{title_scene_handoff_game.data()}.put(p-0x4e46f0,v);
    common_texture_target_globals.auxiliary=title_root_aux->descriptor;
    if(common_render_stage->created)std::memcpy(common_renderer->application.data()+0x5b4,common_render_stage->camera.data(),300);
    return ok?result:-2;
}
API(title_root_load_last_entry) u32 title_root_load_last_entry(){return title_root_loader->last_entry;}
API(title_root_load_last_address) u32 title_root_load_last_address(){return title_root_loader->last_address;}
API(title_root_load_region) const u8* title_root_load_region(u32 p,u32 n){if(!title_root_loading)return title_load_region(p,n);output.resize(n);if(title_root_load_read(p,output.data(),n))return output.data();return title_load_region(p,n);}
API(title_root_load_title_globals) const u32* title_root_load_title_globals(){if(!title_root_loading||AnmView{common_renderer->application.data()}.get(0x6e8)==4)return title_load_globals_data();static std::array<u32,7> g;g={0,common_owner->global_owner,common_load_bindings->save_owner,title_root_cheat->global_owner,common_texture_application_globals.presentation,title_global_538de4,title_alternate};return g.data();}
API(title_root_load_yield_count) u32 title_root_load_yield_count(){return title_root_load_yields.size();}
API(title_root_load_yield_data) const u32* title_root_load_yield_data(u32 i){return title_root_load_yields[i].data();}
API(title_root_load_yield_words) u32 title_root_load_yield_words(u32 i){return title_root_load_yields[i].size();}
API(title_root_load_global) u32 title_root_load_global(u32 p){if(p==0x4e6b68&&AnmView{common_renderer->application.data()}.get(0x6e8)==4)return title_cheat->global_owner;
    switch(p){case 0x4e6b88:return owners->created&1?GameOwnerRuntime::player_self:0;case 0x4e6b90:return owners->created&2?GameOwnerRuntime::equipment_self:0;case 0x4e6b98:return owners->created&4?GameOwnerRuntime::input_self:0;case 0x4e6a08:return owners->created&8?BulletPool::token_base:0;case 0x4e6b64:return owners->created&16?ItemPool::token_base:0;case 0x4e6b6c:return owners->created&32?GameOwnerRuntime::laser_self:0;case 0x4e6ba4:return owners->created&64?ScorePopups::token:0;case 0x4e6a00:return common_render_stage->loading.current;case 0x4e6a54:return title_root_hud->globals.owner;case 0x4e6b84:return title_root_menu->global_owner;case 0x4e6a48:return title_root_enemy->global_owner;case 0x4e6b68:return title_root_cheat->global_owner;case 0x4e6a0c:return title_root_aux->special_owner;case 0x4e6a50:return title_root_timing->global_owner;
    case 0x4e6a10:return title_root_aux->independent.pixels;case 0x4e6a14:return title_root_aux->width;case 0x4e6a18:return title_root_aux->height;case 0x4e6a1c:return title_root_aux->bytes_per_pixel;case 0x4e6a20:return title_root_aux->independent.resource;case 0x4e6a24:return title_root_aux->independent.surface;case 0x4e6a28:return title_root_aux->independent.signals;case 0x4e6a2c:return title_root_aux->independent.active;case 0x4e6a34:return title_root_aux->independent.animations[0];case 0x4e6a38:return title_root_aux->independent.animations[1];default:if(p>=0x4e47d0&&p+4<=0x4e5204)return AnmView{common_renderer->application.data()}.get(p-0x4e47d0);return title_root_load_words[p];}
}


#include "../src/GameOwnerStartup.hpp"
#include "../src/GameEnemyStartup.hpp"
#include "../src/RootFrameStartup.hpp"
#include "../src/GameClock.hpp"
#include "../src/SoundQueue.hpp"
static SoundQueue title_start_audio;
static u32 title_start_last_read=0,title_start_last_write=0,title_start_last_service=0,title_start_last_owner=0;
static std::vector<u32> title_start_clock_values;
static bool campaign_host_clock_ready=false;
static u32 campaign_host_clock_ticks=0,campaign_host_clock_samples=0;
API(campaign_host_clock_set)void campaign_host_clock_set(u32 ticks){campaign_host_clock_ready=true;campaign_host_clock_ticks=ticks;}
API(campaign_host_clock_diagnostic)u32 campaign_host_clock_diagnostic(u32 i){const u32 v[]={u32(campaign_host_clock_ready),campaign_host_clock_ticks,campaign_host_clock_samples};return i<3?v[i]:0;}

struct TitleStartClock:GameClockHost {
    bool performance_counter(std::uint64_t&)override{return false;}
    bool millisecond_ticks(u32& value)override{if(!campaign_host_clock_ready)return false;value=campaign_host_clock_ticks;++campaign_host_clock_samples;title_start_clock_values.push_back(value);return true;}
}title_start_clock;
struct TitleStartGlobals {u32 game_flags=0,config=0,application_state=0,presentation=0;GameClock clock;double statistics_time=0;}title_start_globals;
static std::unique_ptr<GameOwnerStartup> title_start_owners;
static std::unique_ptr<GameEnemyStartup> title_start_enemies;
static RootStartupGlobals title_start_state;
static std::vector<u32> title_start_services,title_start_commands;
static std::array<u32,3> title_start_transitions{};
struct StartupOwnerHost:GameOwnerStartupHost {
    bool reset_lives(i32,u32)override{return title_root_hud->view().get(0x58)==0;}
    bool reset_visual_callback(u32,AnmView vm,i32 signal)override{return signal_animation_vm(*world,vm,signal,false);}
    bool startup_laser_destructor(u32)override{return false;}
    bool startup_secondary_visual(i32 child_script,i32 signal)override{auto c=title_root_cheat->view();return signal_cheat_child(c,c.get(0x2b8),child_script,signal,*world);}
}startup_owner_host;
struct StartupEnemyHost:EnemyScriptServices,EmitterSink {
    bool prepare_actor(EclOwner& owner)override{campaign_tweens_reset(owner.root,u8(fill));std::memset(owner.root.stack,u8(fill),sizeof owner.root.stack);owner.root.flags=(fill*0x01010101u)&~1u;return true;}
    Rng* gameplay_rng()override{return &title_root_game.random;}
    bool aim_position(float& x,float& y)override{const auto& p=owners->player;const u32 at=p.get(0x1847c)&0x100?0x184b4:0x5e0;x=p.floating(at);y=p.floating(at+4);return true;}
    bool create_visual(i32 file,i32 script,i32 layer,EnemyVisual& out)override{if(file<0||file>=6)return false;return world->create(title_root_enemy->view().get(0xa0+file*4),script,layer,out.handle)&&visual(out.handle,out);}
    bool visual(u32 handle,EnemyVisual& out)override{auto vm=world->find(handle);if(!vm.data)return false;out={handle,vm.get(0x18),vm.get(0x1c),vm.floating(0x80),vm.floating(0x84),vm.floating(0x60),vm.floating(0x64)};return true;}
    bool rotate_visual(u32 handle,float angle)override{auto vm=world->find(handle);if(!vm.data)return false;vm.put(0x50,word(angle));vm.put(0x18,vm.get(0x18)|4);return true;}
    bool retire_visual(u32 h)override{return world->mark_retirement(h);}
    bool flag_visual(u32 h,bool enabled)override{return world->flag(h,enabled);}
    bool position_visual(u32 h,const std::array<float,3>& position)override{auto vm=world->find(h);if(!vm.data)return false;for(u32 i=0;i<3;++i)vm.put(0x59c+i*4,word(position[i]));return true;}
    bool change_visual(u32 previous,i32 script,i32 layer,EnemyVisual& out)override{auto vm=world->find(previous);if(!vm.data)return false;const u32 resource=vm.get(0x30);const std::array<float,3> position{vm.floating(0x3c),vm.floating(0x40),vm.floating(0x44)};return world->mark_retirement(previous)&&world->create_at(resource,script,layer,position,out.handle)&&visual(out.handle,out);}
    bool sound(i32 id,float x)override{return title_start_audio.request(u32(id),true,x);}
    bool message_select(i32 id)override{title_root_hud->view().put(0x2a8,u32(id));return true;}
    bool hud_value(i32 value)override{title_root_hud->view().put(0x15c,u32(value));return true;}
    bool message_active()const override{return title_root_hud->view().get(0x198)!=0;}
    bool root_special()const override{return (title_root_state.view().get(0x80)&0x4000)!=0;}
    u32 game_flags()const override{return title_start_globals.game_flags;}
    // Native421e30 observes external commands;91/92 execute inside nativeVM.
    void command(u32 actor,const Vm& vm)override{if(vm.instruction->opcode==91||vm.instruction->opcode==92)return;title_start_commands.insert(title_start_commands.end(),{actor,vm.instruction->opcode});}
    bool launch(const u8*,u32,u32)override{return false;}
}startup_enemy_host;
struct StartupHost:RootStartupHost {
    bool startup_read(u32 p,u32& value)override{title_start_last_read=p;
        switch(p){
        case 0x4e69fc:value=0;return true;case 0x4e69f8:value=0x71000000;return true;case 0x4daef4:value=0x4e40b8;return true;
        case 0x4e40c4:case 0x4e40c8:value=0;return true;
        case 0x710191e8:value=game_ascii->view().get(0x191e8);return true;case 0x710191ec:value=game_ascii->view().get(0x191ec);return true;case 0x4e49a0:value=AnmView{common_renderer->application.data()}.get(0x1d0);return true;
        case 0x4e6b68:value=title_root_cheat->global_owner;return true;case 0x4e6b84:value=title_root_menu->global_owner;return true;
        case 0x4e6b88:value=owners->created&1?GameOwnerRuntime::player_self:0;return true;case 0x4e6a08:value=owners->created&8?BulletPool::token_base:0;return true;
        case 0x4e6a48:value=title_root_enemy->global_owner;return true;case 0x4e6b64:value=owners->created&16?ItemPool::token_base:0;return true;
        case 0x4e6b6c:value=owners->created&32?GameOwnerRuntime::laser_self:0;return true;case 0x4e6a40:value=title_root_aux->effects_owner;return true;
        case 0x4e6ba4:value=owners->created&64?ScorePopups::token:0;return true;case 0x4e6a0c:value=title_root_aux->special_owner;return true;
        case 0x4e6a54:value=title_root_hud->globals.owner;return true;case 0x4e6bac:value=title_scene_handoff_descriptor;return true;
        }
        auto field=[&](u32 base,AnmView v,u32 n){if(p<base||p-base>n-4)return false;value=v.get(p-base);return true;};
        if(field(GameCheatRuntime::self,title_root_cheat->view(),title_root_cheat->data.size())||field(GameMenuRuntime::self,title_root_menu->menu.view(),PauseMenu::bytes)||field(GameHudRuntime::self,title_root_hud->view(),title_root_hud->data.size()))return true;
        return owners->read(p,&value,4)||title_root_enemy->read(p,&value,4)||title_root_aux->read(p,&value,4)||common_auxiliary->read(p,&value,4)||title_root_hud_files.hud_load_read(p,&value,4);
    }
    bool startup_write(u32 p,u32 value)override{title_start_last_write=p;
        if(p==0x710191e8||p==0x710191ec){game_ascii->view().put(p-0x71000000,value);return true;}if(p==0x4e49a0){AnmView{common_renderer->application.data()}.put(0x1d0,value);return true;}
        return owners->write(p,&value,4)||title_root_aux->write(p,&value,4)||common_auxiliary->write(p,&value,4);
    }
    bool startup_clock(std::array<u32,2>& out)override{title_start_services.push_back(0x46f4e0);double value;if(!title_start_globals.clock.sample(title_start_clock,value))return false;std::memcpy(out.data(),&value,8);title_start_globals.statistics_time=value;return true;}
    bool startup_service(RootStartupService service,u32 owner)override{
        title_start_last_service=u32(service);title_start_last_owner=owner;title_start_services.push_back(u32(service));using S=RootStartupService;
        switch(service){
        case S::hud_begin:return title_root_hud->begin_scene();case S::stage_activate:return common_render_stage->activate();
        case S::bullets_reset:return title_start_owners->bullets();case S::player_reset:return title_start_owners->player(signed_word(title_root_game.game_state[27]),title_root_game.game_state[28]);
        case S::items_reset:return owner==ItemPool::token_base&&title_start_owners->items();case S::enemies_reset:return owner==GameEnemyRuntime::self&&title_start_enemies->reset_empty();
        case S::lasers_reset:return title_start_owners->lasers();
        case S::statistics_begin:{GameManagerSceneGlobals g;g.new_game=title_root_game.new_game;g.scene=title_root_game.scene;g.game_state=title_root_game.game_state;if(!title_start_owners->statistics(g))return false;title_root_game.game_state=g.game_state;return true;}
        case S::equipment_activate:{PlayerEquipmentGlobals g{title_root_game.game_state[8],title_root_game.game_state[9],title_root_game.game_state[14],title_root_game.game_state[12],title_root_game.game_state[13]};return title_start_owners->equipment(g);}
        case S::hud_initialize:{HudInitializeGlobals g{title_start_globals.game_flags,title_root_game.game_state[11]};return title_root_hud->initialize(g);}
        default:return false;
        }
    }
    bool startup_spawn_main(const std::array<u32,21>& words)override{title_start_services.push_back(0x41e270);for(u32 v:words)if(v)return false;return title_start_enemies->spawn_main(title_root_game.game_state[3]);}
    bool startup_signal(u32 handle,i32 signal)override{title_start_services.push_back(0x484320);return static_cast<AnmMenuWorld&>(*world).screen_transition_signal(handle,signal);}
    bool startup_music(i32 parameter,u32 track)override{title_start_services.push_back(0x4446e0);MusicCommandQueue queue;std::memcpy(queue.data.data(),common_load_audio.data()+0x24f8,queue.data.size());if(!queue.start(*common_save,u32(parameter),track,title_root_game.root_snapshot[14]))return false;std::memcpy(common_load_audio.data()+0x24f8,queue.data.data(),queue.data.size());return true;}
}startup_host;

struct TitleStartLive:RootFrameHost {
    bool timer_rate(u32 p,float& rate)override{return world->timer_rate(p,rate);}
    bool start_or_restart(RootState&,RootFrameGlobals&)override{return false;}
    bool notice(u32,u32,u32)override{return false;}bool replay_exit()override{return false;}bool erase_previous_dialog()override{return false;}
    bool animate_backgrounds()override{auto app=AnmView{common_renderer->application.data()};for(u32 i=0;i<4;++i){auto vm=common_application_targets->target_animation(app.get(0x1bc+i*4));if(!vm.data||anm_step(vm,static_cast<AnmWorld&>(*world))==-2)return false;}return true;}
}title_start_live;
API(title_root_start_prepare) u32 title_root_start_prepare(){
    title_start_services.clear();title_start_commands.clear();title_start_clock_values.clear();title_start_state={};title_start_globals={};auto app=AnmView{common_renderer->application.data()};title_start_globals.game_flags=title_root_game.game_flags;title_start_globals.config=app.get(0x724);title_start_globals.application_state=app.get(0x6ec);title_start_globals.presentation=common_texture_application_globals.presentation;
    std::memcpy(title_start_audio.data.data(),common_load_audio.data()+0x1c,title_start_audio.data.size());
    title_start_owners=std::make_unique<GameOwnerStartup>(*owners,*world,*title_root_ready,startup_owner_host);title_start_enemies=std::make_unique<GameEnemyStartup>(*title_root_enemy,*world,frames->scheduler,startup_enemy_host,startup_enemy_host);return 1;
}
API(title_root_start_run) i32 title_root_start_run(){
    const auto previous_release_observer=common_load_storage_release_observer;common_load_storage_release_observer=title_root_storage_release;
    RootFrameGlobals g;g.game_flags=title_root_game.game_flags;g.config=title_start_globals.config;g.application_state=title_start_globals.application_state;g.presentation=title_start_globals.presentation;g.score=title_root_game.game_state[2];g.scene=title_root_game.game_state[4];g.high_score=title_root_load_words[0x4e4790];g.high_score_scene=title_root_load_words[0x4e4794];g.frames=title_root_load_words[0x4e47a8];g.scene_frames=title_root_load_words[0x4e47ac];
    const i32 result=root_frame_with_startup(title_root_state,title_root_hud->view(),g,title_start_state,title_start_live,startup_host);common_load_storage_release_observer=previous_release_observer;
    title_root_game.game_flags=g.game_flags;std::memcpy(title_scene_handoff_game.data(),title_root_game.game_state.data(),160);AnmView{title_scene_handoff_game.data()}.put(0xc0,g.game_flags);title_activation_globals.startup_flags=g.game_flags;title_root_load_words[0x4e4790]=g.high_score;title_root_load_words[0x4e4794]=g.high_score_scene;title_root_load_words[0x4e47a8]=g.frames;title_root_load_words[0x4e47ac]=g.scene_frames;
    for(const auto& [p,v]:title_root_load_words)if(p>=0x4e4790&&p+4<=0x4e47d0)AnmView{title_scene_handoff_game.data()}.put(p-0x4e46f0,v);
    std::memcpy(title_scene_handoff_game.data()+0xd4,&title_start_globals.statistics_time,8);
    common_gameplay=title_root_game.random;common_texture_application_globals.presentation=g.presentation;AnmView{common_renderer->application.data()}.put(0x6ec,g.application_state);
    std::memcpy(common_load_audio.data()+0x1c,title_start_audio.data.data(),title_start_audio.data.size());
    std::memcpy(common_renderer->application.data()+0x5b4,common_render_stage->camera.data(),300);
    return world->synchronize_resources()?result:-100;
}
API(title_root_start_clock_data) const u32* title_root_start_clock_data(){return title_start_clock_values.data();}
API(title_root_start_clock_count) u32 title_root_start_clock_count(){return title_start_clock_values.size();}
API(title_root_start_clock_state) const double* title_root_start_clock_state(){return &title_start_globals.clock.origin;}
API(title_root_start_statistics) const double* title_root_start_statistics(){return &title_start_globals.statistics_time;}
API(title_root_start_services_data) const u32* title_root_start_services_data(){return title_start_services.data();}
API(title_root_start_services_count) u32 title_root_start_services_count(){return title_start_services.size();}
API(title_root_start_debug_word) u32 title_root_start_debug_word(u32 i){const u32 a[]={title_start_last_read,title_start_last_write,title_start_last_service,title_start_last_owner,u32(title_start_enemies->scripts.error_opcode),u32(title_start_enemies->scripts.failed),title_root_state.view().get(0x14)};return a[i];}
static EnemyScripts::Actor* title_start_actor(u32 i){auto p=title_start_enemies->scripts.live.begin();std::advance(p,i);return *p;}
API(title_root_start_actor_count) u32 title_root_start_actor_count(){return title_start_enemies->scripts.live.size();}
API(title_root_start_actor_info) u32 title_root_start_actor_info(u32 i,u32 k){auto* a=title_start_actor(i);return k==0?a->token:k==1?a->state.id:a->state.parent;}
API(title_root_start_actor_data) const u8* title_root_start_actor_data(u32 i){static std::array<u8,0x41e8> b;auto* a=title_start_actor(i);std::memcpy(b.data(),a->state.fields.data.data(),Emitters::bytes);std::memcpy(b.data()+Emitters::bytes,a->state.tail.data(),a->state.tail.size());return b.data();}
static Vm* title_start_context(u32 i,u32 k){auto* p=&title_start_actor(i)->owner.threads;while(k--)p=p->next;return p->value;}
API(title_root_start_context_count) u32 title_root_start_context_count(u32 i){u32 n=0;for(auto* p=&title_start_actor(i)->owner.threads;p;p=p->next)++n;return n;}
API(title_root_start_context_word) u32 title_root_start_context_word(u32 i,u32 k,u32 f){auto* v=title_start_context(i,k);switch(f){case 0:return word(v->time);case 1:return u32(reinterpret_cast<std::uintptr_t>(v->instruction));case 2:return v->top;case 3:return v->frame;case 4:return v->thread_id;case 5:return v->state;case 6:return v->difficulty;case 7:return v->flags;}return 0;}
API(title_root_start_context_stack) const u8* title_root_start_context_stack(u32 i,u32 k){return reinterpret_cast<const u8*>(title_start_context(i,k)->stack);}
API(title_root_start_code) u32 title_root_start_code(u32 i,u32 f){auto& b=title_root_enemy->program.files[i]->bytes;return f==0?u32(reinterpret_cast<std::uintptr_t>(b.data())):f==1?b.size():title_root_enemy->file_tokens[i];}


#include "../src/GamePlayAllOptionsNov14.hpp"
static std::unique_ptr<GamePlayAllOptionsNov14Runtime> title_gameplay;
static u32 campaign_time_scale_diagnostic[8]{};
API(time_scale_diagnostic) u32 time_scale_diagnostic(u32 i){return i<8?campaign_time_scale_diagnostic[i]:0;}
API(diagnostic_actor_storage_count) u32 diagnostic_actor_storage_count(){return title_start_enemies?u32(title_start_enemies->scripts.storage.size()):0;}
API(diagnostic_actor_root_word) u32 diagnostic_actor_root_word(u32 index,u32 k){if(!title_start_enemies||index>=title_start_enemies->scripts.storage.size())return 0;auto& a=*title_start_enemies->scripts.storage[index];auto& v=a.owner.root;switch(k){case 0:return a.state.id;case 1:return u32(reinterpret_cast<std::uintptr_t>(v.instruction));case 2:return u32(v.top);case 3:return u32(v.frame);case 4:return u32(v.error_opcode);case 5:return v.failed;case 6:return word(v.time);}return 0;}
API(diagnostic_actor_root_stack) const u8* diagnostic_actor_root_stack(u32 index){return title_start_enemies&&index<title_start_enemies->scripts.storage.size()?title_start_enemies->scripts.storage[index]->owner.root.stack:nullptr;}
API(kind2_laser_diagnostic) u32 kind2_laser_diagnostic(u32 i){return title_gameplay&&i<12?title_gameplay->lasers.diagnostic[i]:0;}

static bool campaign_laser_draw(u32 entry,u32 token){return title_gameplay&&title_gameplay->lasers.draw(entry,token);}
namespace th143 {i32 campaign_laser_command(Emitters& actor,Vm& vm,VmHost& host){return title_gameplay?laser_emitter_launch(actor,vm,host,title_gameplay->lasers):-2;}}

static u32 title_gameplay_keys=0,title_gameplay_fresh=0,title_gameplay_repeated=0;
static std::vector<u32> title_gameplay_trace,title_gameplay_returns;
static GameOverGlobals title_gameplay_menu_globals;
static CheatControllerGlobals title_gameplay_controls;
static void title_gameplay_save_event(u32 kind,std::initializer_list<u32> args){
    auto append=[&](const void* p,u32 n){const auto* b=static_cast<const u8*>(p);if(n)title_io_events.insert(title_io_events.end(),b,b+n);};const u32 header[]={kind,u32(args.size())};append(header,8);append(args.begin(),args.size()*4);append(title_owner->data.data(),title_owner->data.size());append(common_save->data.data(),common_save->data.size());append(common_renderer->application.data(),common_renderer->application.size());append(common_owner->data.data(),common_owner->data.size());
    const u32 globals[]={title_owner->global_owner,common_owner->global_owner,common_load_bindings->save_owner,title_root_cheat->global_owner,common_texture_application_globals.presentation,title_global_538de4,title_alternate};append(globals,sizeof globals);append(common_equipment.data(),16);append(common_saved_equipment.data(),16);append(common_load_rng_data(),16);for(u32 p:{title_owner->view().get(12),title_owner->view().get(16),title_root_cheat->view().get(8),title_root_cheat->view().get(12)}){auto cb=frames->scheduler.at(p);const u32 flags=cb.data?cb.get(4):0;append(&flags,4);}
}
struct TitleGameplaySave:SaveFileServices {
    bool save_directory(bool restore)override{title_gameplay_save_event(7,{u32(restore)});return true;}
    bool open_save_file(i32& status,u32& handle)override{status=title_io_mode==1?1:0;handle=status?0xffffffff:0x1234;title_gameplay_save_event(8,{u32(status),handle});if(!title_io_mode&&!campaign_score_file.open(handle))return false;return true;}
    bool write_save_file_bytes(u32 handle,const u8* bytes,u32 n,u32& written)override{if(handle!=0x1234)return false;const bool short_write=(title_io_mode==2&&!title_write_cursor)||(title_io_mode==3&&title_write_cursor==1);++title_write_cursor;written=short_write?n-1:n;title_save_writes.emplace_back(bytes,bytes+n);title_gameplay_save_event(9,{handle,n,written});if(!title_io_mode&&!campaign_score_file.write(handle,bytes,written))return false;return true;}
    bool close_save_file(u32 handle)override{if(handle!=0x1234)return false;title_gameplay_save_event(10,{handle});if(!title_io_mode&&!campaign_score_file.close(handle))return false;return true;}
    bool save_file_error()override{title_gameplay_save_event(11,{});return true;}
}title_gameplay_save;
static void sync_gameplay_equipment_selection(){
 const auto& g=title_gameplay_controls;title_root_game.game_state[8]=common_equipment[0]=g.primary;title_root_game.game_state[9]=common_equipment[1]=g.secondary;
 title_root_game.game_state[15]=common_saved_equipment[0]=g.saved_primary;title_root_game.game_state[16]=common_saved_equipment[1]=g.saved_secondary;
}
struct TitleGameplayController:CheatControllerHost {
    bool cheat_item_level(u32 id,bool notify)override{sync_gameplay_equipment_selection();return common_save->item_level(id,notify,title_gameplay_controls.secondary,common_load_platform);}
    bool cheat_persist()override{sync_gameplay_equipment_selection();return write_save_file(*common_save,common_saved_equipment,*world,title_gameplay_save,common_loaded_save.get());}
    bool cheat_sound(u32 id)override{return title_start_audio.request(id,false,0);}
}title_gameplay_controller;
#include "../src/PauseEquipmentPage.hpp"
struct GameplayPauseEquipment:PauseEquipmentPageHost {
 bool equipment_page_read(u32 p,void* out,u32 n)override{
  u32 value;if(n==4&&(p==0x4e4710||p==0x4e4714||p==0x4e6b68)){value=p==0x4e6b68?title_root_cheat->global_owner:title_root_game.game_state[p==0x4e4710?8:9];std::memcpy(out,&value,4);return true;}
  const u32 base=GameCheatRuntime::self;if(p>=base&&std::uint64_t(p)+n<=std::uint64_t(base)+title_root_cheat->data.size()){std::memcpy(out,title_root_cheat->data.data()+p-base,n);return true;}return false;
 }
 bool equipment_page_write(u32 p,const void* in,u32 n)override{
  if(p==0x4e4ebc&&n==4){u32 state;std::memcpy(&state,in,4);title_gameplay_menu_globals.application_state=state;return true;}
  const u32 base=GameCheatRuntime::self;if(p>=base&&std::uint64_t(p)+n<=std::uint64_t(base)+title_root_cheat->data.size()){std::memcpy(title_root_cheat->data.data()+p-base,in,n);return true;}return false;
 }
 bool equipment_page_call(u32 e,u32 owner,std::initializer_list<u32> args,u32& result)override{
  const auto a=args.begin();result=0;auto m=title_root_menu->menu.view();
  if(e==0x484730||e==0x4846f0)return args.size()==0&&owner==GameMenuRuntime::self+0x1e8&&world->flag(m.get(0x1e8),e==0x4846f0);
  if(e==0x436ee0)return args.size()==0&&title_root_cheat->end_scene();
  if(e==0x438380)return args.size()==0&&owner==title_root_cheat->global_owner&&title_root_cheat->position();
  if(e==0x438350){if(args.size())return false;result=title_root_cheat->view().get(0x2b0);return true;}
  if(e==0x436c30){if(args.size()!=1)return false;CheatSceneGlobals g{title_root_game.game_state[14],title_root_game.game_state[8],title_root_game.game_state[9],title_root_game.scene,true,m.get(0x3e4),common_save->data[0xefac],common_save->data[0xf08a],{0,6,3,1,7,4,2,5,8}};return title_root_cheat->begin_scene(signed_word(a[0]),g);}
  if(e==0x472be0)return args.size()==1&&title_start_audio.request(a[0],false,0);
  if(e==0x447630){if(args.size()!=1||owner!=GameMenuRuntime::self)return false;title_root_menu->menu.substate(signed_word(a[0]),world->global_rate_token());return true;}
  if(e==0x484320)return args.size()==2&&signal_animation(*world,a[0],signed_word(a[1]),false);
  return false;
 }
}gameplay_pause_equipment;
struct TitleGameplayMenu:PauseControlHost,SoundQueueHost {
    bool achievement(u32 id)override{return common_load_platform.achievement(id);}
    bool performance_counter(std::uint64_t&)override{return false;}
    bool millisecond_ticks(u32& value)override{return title_start_clock.millisecond_ticks(value);}
    bool stop_buffer(u32 token,u32& status)override{u32 ignored=0;return campaign_audio_host.query_sound_status(token,status,ignored)&&campaign_audio_host.sound_voice_call(token,0x48,nullptr,0,ignored);}
    bool pause_audio()override{std::memcpy(common_load_audio.data()+0x1c,title_start_audio.data.data(),title_start_audio.data.size());if(!pause_sound_bank({common_load_audio.data()},common_load_audio.size(),0,campaign_audio_host))return false;std::memcpy(title_start_audio.data.data(),common_load_audio.data()+0x1c,title_start_audio.data.size());return true;}
    bool sound_and_flush(u32 id)override{if(!title_start_audio.enqueue(id,100))return false;std::memcpy(common_load_audio.data()+0x1c,title_start_audio.data.data(),title_start_audio.data.size());u32 result=0;if(!campaign_pump_audio(result))return false;std::memcpy(title_start_audio.data.data(),common_load_audio.data()+0x1c,title_start_audio.data.size());return true;}
    bool menu_sound(u32 id)override{return title_start_audio.request(id,false,0);}
    bool hint_text(u32,const u8*)override{return false;}
    bool other_substate(PauseMenu& menu,u32 sub)override{if(sub==11)return advance_pause_equipment_page(menu,gameplay_pause_equipment);if(sub>=8&&sub<=10)return campaign_replay_pause(menu.view(),menu.self,sub);return campaign_manual_pause(menu.view(),menu.self,sub);}
    bool resume_pause_audio()override{std::memcpy(common_load_audio.data()+0x1c,title_start_audio.data.data(),title_start_audio.data.size());if(!resume_sound_bank({common_load_audio.data()},common_load_audio.size(),campaign_audio_host))return false;std::memcpy(title_start_audio.data.data(),common_load_audio.data()+0x1c,title_start_audio.data.size());return true;}
    bool pause_message_owner(u32,bool)override{return false;}
    bool pause_exit_fade()override{return false;}
}title_gameplay_menu_host;
struct TitleGameplayServices:GamePlayServices {
    bool gameplay_game_over(bool)override{return false;}
    bool gameplay_lives(i32,u32)override{return title_root_hud->view().get(0x58)==0;}
    bool gameplay_bombs(u32,u32)override{return title_root_hud->view().get(0x78)==0;}
}title_gameplay_services;
struct TitleGameplayEnemy:StartupEnemyHost {
    bool prepare_actor(EclOwner& owner)override{if(!StartupEnemyHost::prepare_actor(owner))return false;owner.prepare_thread=[](Vm& vm,void* context){const u8 f=u8(reinterpret_cast<std::uintptr_t>(context));campaign_tweens_reset(vm,f);std::memset(vm.stack,f,sizeof vm.stack);vm.state=vm.flags=u32(f)*0x01010101u;return true;};owner.thread_context=reinterpret_cast<void*>(std::uintptr_t(fill));return true;}
    bool launch(const u8* p,u32 n,u32 owner)override{return title_gameplay&&title_gameplay->launch(p,n,owner);}
}title_gameplay_enemy;
struct TitleGameplayHud:HudFrameHost,HudMessageHost {
    HudMessageGlobals* message_globals=nullptr;
    std::map<u32,std::array<u8,0x53d8>> actor_views;
    bool timer_rate(u32 p,float& rate)override{return world->timer_rate(p,rate);}
    bool hud_owner(u32 global,AnmView& out)override{switch(global){case 0x4e6b88:out={owners->player.data.data()};return true;case 0x4e6a48:out=title_root_enemy->view();return true;case 0x4e6a0c:out=title_root_aux->special_view();return true;}return false;}
    bool hud_actor(u32 token,AnmView& out)override{for(auto* a:title_start_enemies->scripts.live)if(a->token==token){auto& b=actor_views[token];b.fill(0);std::memcpy(b.data()+0x11f0,a->state.fields.data.data(),Emitters::bytes);std::memcpy(b.data()+0x11f0+Emitters::bytes,a->state.tail.data(),a->state.tail.size());AnmView v{b.data()};v.put(0x11e4,a->state.id);v.put(0x11e8,a->state.parent);out=v;return true;}out={nullptr};return true;}
    bool hud_sound(u32 id)override{return title_start_audio.request(id,false,0);}
    bool create_hud_message(i32 id)override{if(!campaign_message_create(id))return false;if(message_globals)message_globals->root_flags=title_root_state.view().get(0x80);return true;}
    bool update_hud_message_owner(u32 p,i32& result)override{const bool ok=campaign_message_update(p,result);if(message_globals)message_globals->dialog=campaign_dialog_owner;return ok;}
    bool hud_message_view(u32 p,AnmView& out)override{return campaign_message_storage(p,out);}
    bool destroy_hud_message_owner(u32 p)override{return campaign_message_destroy(p);}
    bool hud_dialog_view(u32 p,AnmView& out)override{out=campaign_dialog_view(p);return out.data!=nullptr;}
    bool request_hud_dialog_result()override{return campaign_hud_open_results(message_globals);}
    bool destroy_hud_dialog(u32 p)override{return campaign_dialog_destroy(p);}
}title_gameplay_hud;
struct TitleGameplayFrames:GameFrameServices {
    bool frame_input(GameInputFrame& g)override{g={true,title_root_state.view().get(0x80),0,title_gameplay_keys,0,title_root_timing->view().floating(0x34)};return true;}
    bool before_game_callback(u32 e,u32 owner)override{
        title_gameplay_trace.insert(title_gameplay_trace.end(),{e,owner});if(AnmView{common_renderer->application.data()}.get(0x6e8)==4)return common_pool_frame_services.before_game_callback(e,owner);
        if(e==0x438330){auto& g=title_gameplay_controls;g.fresh=title_gameplay_fresh;g.repeated=title_gameplay_repeated;g.primary=title_root_game.game_state[8];g.secondary=title_root_game.game_state[9];g.saved_primary=title_root_game.game_state[15];g.saved_secondary=title_root_game.game_state[16];g.menu_token=title_root_menu->global_owner;g.menu_animation=title_root_menu->menu.view().get(0x3f0);auto count=[&](u32 token){u32 n=0;if(token&&!owners->read(token+0x18,&n,4))return 0xffffffffu;return n;};auto equip=owners->equipment.view();g.primary_count=count(equip.get(0x10));g.secondary_count=count(equip.get(0x14));g.secondary_enabled=equip.get(0x20)!=0;g.unlock=common_save->data[0xefac];}
        if(e==0x433720||e==0x41edb0){title_start_enemies->scripts.signal_flags=title_root_aux->independent.signals;title_start_enemies->scripts.signal_count=title_root_aux->independent.active;}
        return title_gameplay->before(e,title_root_state.view().get(0x80));
    }
    bool after_game_callback(u32 e,u32 owner,u32 result)override{if(AnmView{common_renderer->application.data()}.get(0x6e8)==4){title_gameplay_returns.push_back(result);return common_pool_frame_services.after_game_callback(e,owner,result);}if(!title_gameplay->after(e))return false;if(e==0x44e3d0)campaign_replay_player_sample();if(e==0x433720||e==0x41edb0){title_root_aux->independent.signals=title_start_enemies->scripts.signal_flags;title_root_aux->independent.active=title_start_enemies->scripts.signal_count;}title_gameplay_returns.push_back(result);return true;}
    bool release_game_callback(u32 p)override{return common_load_storage.release_game_storage(p);}
    bool other_game_callback(u32 e,u32 owner,u32& result)override{if(e==0x468100||e==0x468110)return campaign_achievement_callback(e,owner,result);if(e==0x434d50)return campaign_manual_update(owner,result);if(e==0x4472d0)return day1_notice_callback(e,owner,result);if(e==0x471650||e==0x471a30)return title_shooting_effect_callback(e,owner,result);if(AnmView{common_renderer->application.data()}.get(0x6e8)==4)return common_pool_frame_services.other_game_callback(e,owner,result);
        result=1;
        switch(e){
        case 0x455430:return campaign_replay_playback_frame(owner,result);
        case 0x433720:{auto app=AnmView{common_renderer->application.data()};title_start_globals.game_flags=title_root_game.game_flags;title_start_globals.config=app.get(0x724);title_start_globals.application_state=app.get(0x6ec);title_start_globals.presentation=common_texture_application_globals.presentation;const i32 r=title_root_start_run();result=u32(r);return r!=-2&&r!=-100;}
        case 0x438330:{const bool okay=owner==GameCheatRuntime::self&&title_root_cheat->update(title_gameplay_controls,title_gameplay_controller);if(okay)sync_gameplay_equipment_selection();return okay;}
        case 0x40e830:{const i32 r=common_render_stage->update();result=u32(r);return r!=-2;}
        case 0x418e10:return title_scene_special_update();
        case 0x42ecd0:return title_root_hud->update(title_gameplay_hud);
        case 0x468a20:return campaign_dialog_update(owner,result);
        case 0x42ece0:{HudMessageGlobals g;g.dialog=campaign_dialog_owner;g.transition=title_root_load_words[0x4daf58];g.player_state=owners->player.get(0x684);g.root_mode=title_root_state.view().get(0x94);g.root_flags=title_root_state.view().get(0x80);g.game_flags=title_root_game.game_flags;auto app=AnmView{common_renderer->application.data()};g.config=app.get(0x724);g.application_state=app.get(0x6ec);g.presentation=title_activation_globals.return_mode;title_gameplay_hud.message_globals=&g;const bool message_ok=title_root_hud->message(common_save->view(),g,title_gameplay_hud);title_gameplay_hud.message_globals=nullptr;if(!message_ok)return false;title_root_load_words[0x4daf58]=g.transition;title_root_state.view().put(0x80,g.root_flags);title_root_game.game_flags=g.game_flags;app.put(0x6ec,g.application_state);title_activation_globals.return_mode=g.presentation;return true;}
        case 0x448170:{auto& g=title_gameplay_menu_globals;auto app=AnmView{common_renderer->application.data()};g.root_mode=title_root_state.view().get(0x94);g.root_flags=title_root_state.view().get(0x80);g.config=app.get(0x724);g.game_flags=title_root_game.game_flags;g.application_state=app.get(0x6ec);g.presentation=common_texture_application_globals.presentation;g.rate=world->rate;PauseMenuInput input;input.fresh=title_gameplay_fresh;input.repeated=title_gameplay_repeated;input.root_time=signed_word(title_root_state.view().get(0x14));auto cb=frames->scheduler.at(title_root_state.view().get(8));input.root_update_enabled=cb.data&&(cb.get(4)&2);input.score=title_root_game.game_state[2];input.high_score=title_root_load_words[0x4e4790];input.scene=title_root_game.scene;input.deaths=title_root_enemy->view().get(0x10);const i32 r=title_root_menu->update(*common_save,g,input,title_root_hud->view(),title_gameplay_menu_host);title_root_state.view().put(0x80,g.root_flags);title_root_game.game_flags=g.game_flags;app.put(0x6ec,g.application_state);common_texture_application_globals.presentation=g.presentation;world->rate=g.rate;result=u32(r);return r!=-2;}
        default:return common_pool_frame_services.other_game_callback(e,owner,result);
        }
    }
}title_gameplay_frame_services;
API(title_gameplay_constant) void title_gameplay_constant(u32 p,const u8* b,u32 n){world->regions.push_back({p,{b,b+n}});}
API(title_gameplay_prepare) u32 title_gameplay_prepare(){
    for(auto& v:campaign_selector4_diagnostic)v=0;
    if(!title_root_start_prepare())return 0;title_start_enemies=std::make_unique<GameEnemyStartup>(*title_root_enemy,*world,frames->scheduler,title_gameplay_enemy,title_gameplay_enemy);
    common_render_stage->script.render_option=AnmView{common_renderer->application.data()}.get(0xa30);
    title_gameplay=std::make_unique<GamePlayAllOptionsNov14Runtime>(*owners,*title_start_enemies,*title_root_enemy,*title_root_cheat,*title_root_aux,*title_root_hud,*world,title_start_audio,title_root_game.game_state,title_root_game.random,title_gameplay_services,common_load_storage,*common_renderer,common_render_device);
    // This declared boot prefix leaves53b0f8/fc at their original BSS zero.
    // The earlier isolated gameplay fixture declared128/16 separately.
    common_renderer->playfield_origin={0,0};title_gameplay->shooting.viewport_origin=common_renderer->playfield_origin;
    // Preserve the actual registry and its member address while changing the
    // session's frame services after menu destruction. All factories retain
    // their references to this same GameFrameRuntime and Scheduler.
    auto scheduler=std::move(frames->scheduler);frames->~GameFrameRuntime();new(frames.get()) GameFrameRuntime(title_gameplay_frame_services);frames->scheduler=std::move(scheduler);
    frames->animations=world.get();frames->overlay=&common_pool_overlay;frames->input=&owners->input;frames->player=&owners->player;frames->equipment=&owners->equipment;frames->bullets=&owners->bullets;frames->items=&owners->items;frames->scores=&owners->scores;frames->score_host=static_cast<AnmVmHost*>(static_cast<AnmWorld*>(world.get()));frames->laser_manager=GameOwnerRuntime::laser_self;title_gameplay->bind_option_services(game_ascii->view(),[](i32 pan){auto& bank=campaign_audio_host.bank;const u32 token=bank.view().get(0x1a84+84*24),arg=u32(pan);u32 hr=0;return !token||bank.sound_voice_call(token,0x40,&arg,1,hr);});title_gameplay->bind_camera_overlay(common_pool_overlay);title_gameplay->bind(*frames);
    title_gameplay_menu_globals={};title_gameplay_controls={};title_gameplay_hud.actor_views.clear();title_gameplay_keys=title_gameplay_fresh=title_gameplay_repeated=0;return 1;
}
API(title_gameplay_frame) i32 title_gameplay_frame(u32 keys,u32 fresh,u32 repeated){
    if(!campaign_dialog_pump())return -100;
    common_render_stage->script.render_option=AnmView{common_renderer->application.data()}.get(0xa30);
    title_gameplay_keys=keys;title_gameplay_fresh=fresh;title_gameplay_repeated=repeated;title_gameplay_trace.clear();title_gameplay_returns.clear();title_start_services.clear();title_start_commands.clear();title_start_clock_values.clear();
    common_load_storage_release_observer=title_root_storage_release;i32 result;const bool ok=frames->dispatch(false,result);common_load_storage_release_observer=nullptr;
    std::memcpy(title_scene_handoff_game.data(),title_root_game.game_state.data(),160);AnmView{title_scene_handoff_game.data()}.put(0xc0,title_root_game.game_flags);for(const auto& [p,v]:title_root_load_words)if(p>=0x4e4790&&p+4<=0x4e47d0)AnmView{title_scene_handoff_game.data()}.put(p-0x4e46f0,v);std::memcpy(title_scene_handoff_game.data()+0xd4,&title_start_globals.statistics_time,8);common_gameplay=title_root_game.random;title_activation_globals.startup_flags=title_root_game.game_flags;
    std::memcpy(common_load_audio.data()+0x1c,title_start_audio.data.data(),title_start_audio.data.size());std::memcpy(common_renderer->application.data()+0x5b4,common_render_stage->camera.data(),300);AnmView{common_renderer->application.data()}.put(0xa30,common_render_stage->script.render_option);
    return ok&&world->synchronize_resources()?result:-100;
}
API(title_gameplay_trace_data) const u32* title_gameplay_trace_data(){return title_gameplay_trace.data();}
API(title_gameplay_trace_count) u32 title_gameplay_trace_count(){return title_gameplay_trace.size();}
API(title_gameplay_returns_data) const u32* title_gameplay_returns_data(){return title_gameplay_returns.data();}
API(title_gameplay_returns_count) u32 title_gameplay_returns_count(){return title_gameplay_returns.size();}
API(title_gameplay_commands_data) const u32* title_gameplay_commands_data(){return title_start_commands.data();}
API(title_gameplay_commands_count) u32 title_gameplay_commands_count(){return title_start_commands.size();}
API(title_gameplay_keyboard) const u8* title_gameplay_keyboard(){return owners->input.input.keyboard.data();}
API(title_gameplay_failed_entry) u32 title_gameplay_failed_entry(){return frames->failed_entry;}
API(title_gameplay_failed_opcode) i32 title_gameplay_failed_opcode(){return title_start_enemies->scripts.error_opcode;}
API(title_gameplay_clip_data) const i32* title_gameplay_clip_data(){return title_gameplay->shooting.viewport_origin.data();}


#include "../src/GameGameplayApplicationDraw.hpp"
static std::unique_ptr<GameGameplayApplicationDraw> title_gameplay_drawing;
static i32 title_gameplay_draw_result=0;
struct TitleGameplayDrawServices:GameApplicationDrawServices {
    bool application_owner_draw(u32 e,u32 owner,u32& result)override{if(e==0x468100||e==0x468110)return campaign_achievement_callback(e,owner,result);if(e==0x468a30||e==0x434d60){result=1;return true;}if(e==0x4472e0)return day1_notice_callback(e,owner,result);if(owner==GameCommonRuntime::self)return common_pool_frame_services.other_game_callback(e,owner,result);return common_owner_drawing->invoke(e,owner,result);}
}title_gameplay_draw_services;
API(title_gameplay_draw_prepare) u32 title_gameplay_draw_prepare(){
    if(!title_gameplay_prepare())return 0;auto app=AnmView{common_renderer->application.data()};
    common_owner_drawing->bindings={title_root_state.view(),game_ascii->view(),title_root_hud->view(),title_root_enemy->view(),title_root_aux->special_view(),title_root_cheat->view(),title_root_menu->menu.view(),common_save->view(),title_root_timing->view(),common_application_targets->target_animation(app.get(0x1c8)),frames->equipment_host,common_renderer.get()};
    title_gameplay_drawing=std::make_unique<GameGameplayApplicationDraw>(*common_registered_drawing,frames->scheduler,*common_composition,*common_renderer,common_render_device,static_cast<AnmMenuWorld&>(*world),title_gameplay_draw_services,title_root_menu->menu.view());return 1;
}
API(title_gameplay_draw_frame) i32 title_gameplay_draw_frame(u32 keys,u32 fresh,u32 repeated){
    const i32 update=title_gameplay_frame(keys,fresh,repeated);if(update<0)return update;common_render_device.calls.clear();common_render_device.count=common_render_device.triangles=0;common_owner_drawing->failed_entry=0;
    common_owner_drawing->globals={title_root_game.game_flags,AnmView{common_renderer->application.data()}.get(0x6ec),{title_root_load_words[0x4e4790],title_root_load_words[0x4e4794],title_root_game.game_state[4]}};
    common_registered_drawing->independent_signals=title_root_aux->independent.signals;common_registered_drawing->menu_owner=title_root_menu->global_owner;
    if(!title_gameplay_drawing->dispatch(title_gameplay_draw_result)||!world->synchronize_resources())return -200;
    return update;
}
API(title_gameplay_draw_count) i32 title_gameplay_draw_count(){return title_gameplay_draw_result;}


#include "../src/GameDeviceInput.hpp"
static DeviceInputState title_device;
static std::vector<u32> title_device_events;
#include "../src/DeviceInputV2.hpp"
static DeviceInputV2Host& campaign_input_platform();
struct TitleDeviceHost:DeviceInputHost {
    std::array<u8,256> keys{};u32 keyboard=0,acquire=0,joystick=1;
    bool keyboard_state(bool direct,std::array<u8,256>& out,u32& status)override{out=keys;status=keyboard;title_device_events.insert(title_device_events.end(),{direct?2u:1u,status});return true;}
    bool acquire_keyboard(u32& status)override{status=acquire;title_device_events.insert(title_device_events.end(),{3,status});return true;}
    bool missing_winmm_joystick(u32& error)override{error=joystick;title_device_events.insert(title_device_events.end(),{4,error});return true;}
}title_device_host;
API(title_device_prepare) u32 title_device_prepare(){if(!title_gameplay_draw_prepare())return 0;AnmView{common_renderer->application.data()}.put(0x20,0x70021000);title_device.data.fill(0);record_input_to_device(owners->input,title_device);initialize_device_bindings(title_device);return 1;}
API(title_device_frame) i32 title_device_frame(const u8* keys,u32 enabled,u32 config,u32 keyboard,u32 acquire,u32 joystick){
    title_device_events.clear();AnmView{common_renderer->application.data()}.put(0x724,config);std::memcpy(title_device_host.keys.data(),keys,256);title_device_host.keyboard=keyboard;title_device_host.acquire=acquire;title_device_host.joystick=joystick;u32 held;
    if(!poll_device_input_v2(title_device,enabled!=0,config,campaign_input_platform(),held))return -300;
    device_input_to_record(title_device,owners->input);auto v=title_device.view();const i32 result=title_gameplay_draw_frame(held,v.get(12),v.get(8));record_input_to_device(owners->input,title_device);return result;
}
API(title_device_data) const u8* title_device_data(){return title_device.data.data();}
API(title_device_events_data) const u32* title_device_events_data(){return title_device_events.data();}
API(title_device_events_words) u32 title_device_events_words(){return title_device_events.size();}


#include "../src/GameApplicationFullAudioUpdateRuntimeV2.hpp"
static std::unique_ptr<GameApplicationFullAudioUpdateRuntimeV2> title_application_update;
static std::array<u32,5> title_application_update_words;
static i32 title_application_update_result=0;
API(title_application_update_prepare) u32 title_application_update_prepare(){
    if(!title_device_prepare())return 0;auto app=AnmView{common_renderer->application.data()};app.put(0x9a8,0);
    if(!campaign_audio_host.prepare())return 0;title_application_update=std::make_unique<GameApplicationFullAudioUpdateRuntimeV2>(app,AnmView{common_load_audio.data()},title_device,campaign_input_platform(),static_cast<AnmMenuWorld&>(*world),title_root_application_globals,title_root_following,campaign_audio_host,campaign_audio_host);
    title_application_update->globals={2,world->width,world->height,u32(world->viewport.first_origin[0]),u32(world->viewport.first_origin[1])};return 1;
}
API(title_application_update_frame) i32 title_application_update_frame(const u8* keys,u32 enabled,u32 config,u32 keyboard,u32 acquire,u32 joystick){
    title_device_events.clear();AnmView{common_renderer->application.data()}.put(0x724,config);std::memcpy(title_device_host.keys.data(),keys,256);title_device_host.keyboard=keyboard;title_device_host.acquire=acquire;title_device_host.joystick=joystick;
    title_application_update->enabled=enabled!=0;
    if(!title_application_update->update(title_application_update_result))return -400;
    auto& g=title_application_update->globals;world->viewport.first_origin={signed_word(g.center_x),signed_word(g.center_y)};
    // Keep the SFX bank shared with the subsequent live game callbacks.
    std::memcpy(title_start_audio.data.data(),common_load_audio.data()+0x1c,title_start_audio.data.size());
    device_input_to_record(title_device,owners->input);auto v=title_device.view();const i32 result=title_gameplay_draw_frame(v.get(0),v.get(12),v.get(8));record_input_to_device(owners->input,title_device);return result;
}
API(title_application_update_result_value) i32 title_application_update_result_value(){return title_application_update_result;}
API(title_application_update_globals) const u32* title_application_update_globals(){auto& g=title_application_update->globals;title_application_update_words={g.countdown,g.width,g.height,g.center_x,g.center_y};return title_application_update_words.data();}


#include "../src/GraphicsSetup.hpp"
struct TitleGraphicsMemory:AnmRenderMemory {
    bool read_render_memory(u32 p,void* out,u32 n)override{return world->read(p,out,n);}
    bool write_render_memory(u32 p,const void* in,u32 n)override{return world->write(p,in,n);}
}title_graphics_memory;
API(title_graphics_initialize) u32 title_graphics_initialize(u32 f,u32 width,u32 height,u32 scale,u32 font){return title_root_load_initialize(f,width,height,scale,font);}



#include "../src/GameApplicationCaptureDraw.hpp"
static std::unique_ptr<GameCaptureApplicationDraw> title_capture_drawing;
API(title_long_prepare) u32 title_long_prepare(){if(!title_application_update_prepare())return 0;title_capture_drawing=std::make_unique<GameCaptureApplicationDraw>(*common_registered_drawing,frames->scheduler,*common_composition,*common_renderer,common_render_device,static_cast<AnmMenuWorld&>(*world),title_gameplay_draw_services,*title_root_aux,title_root_menu->menu.view());return 1;}
API(title_long_frame) i32 title_long_frame(const u8* keys,u32 enabled,u32 config,u32 keyboard,u32 acquire,u32 joystick){
    title_device_events.clear();AnmView{common_renderer->application.data()}.put(0x724,config);std::memcpy(title_device_host.keys.data(),keys,256);title_device_host.keyboard=keyboard;title_device_host.acquire=acquire;title_device_host.joystick=joystick;title_application_update->enabled=enabled!=0;
    if(!title_application_update->update(title_application_update_result))return -400;
    auto& g=title_application_update->globals;world->viewport.first_origin={signed_word(g.center_x),signed_word(g.center_y)};std::memcpy(title_start_audio.data.data(),common_load_audio.data()+0x1c,title_start_audio.data.size());
    device_input_to_record(title_device,owners->input);auto v=title_device.view();const i32 result=title_gameplay_frame(v.get(0),v.get(12),v.get(8));if(result<0)return result;
    common_render_device.calls.clear();common_render_device.count=common_render_device.triangles=0;common_owner_drawing->failed_entry=0;
    common_owner_drawing->globals={title_root_game.game_flags,AnmView{common_renderer->application.data()}.get(0x6ec),{title_root_load_words[0x4e4790],title_root_load_words[0x4e4794],title_root_game.game_state[4]}};
    common_registered_drawing->independent_signals=title_root_aux->independent.signals;common_registered_drawing->menu_owner=title_root_menu->global_owner;
    if(!title_capture_drawing->dispatch(title_gameplay_draw_result)||!world->synchronize_resources())return -200;record_input_to_device(owners->input,title_device);return result;
}
API(title_long_debug_word) u32 title_long_debug_word(u32 i){switch(i){case 0:return common_registered_drawing->failed_entry;case 1:return common_owner_drawing->failed_entry;case 2:return common_renderer->error;case 3:return title_root_aux->independent.signals;case 4:return title_root_aux->independent.active;case 5:return title_root_menu->menu.view().get(0x91bc);default:return 0;}}


#include "../src/GameAnmText.hpp"

static std::array<TextFont,10> title_text_fonts;
static const TextFont* title_text_pending_font=nullptr;
static const std::vector<TextDraw>* title_text_pending_draws=nullptr;
static const AnmTexturePixels* title_text_pending_target=nullptr;
static u32 title_text_pending_token=0;
extern "C" __attribute__((import_module("th143"),import_name("title_glyphs"))) u32 title_reference_glyphs();
extern "C" __attribute__((import_module("th143"),import_name("title_text_upload"))) u32 title_reference_text_upload();
struct TitleTextGlyphProvider:TextRasterHost {
    bool glyphs(const std::array<u8,108>&,const TextFont& f,const std::vector<TextDraw>& d,std::vector<u8>&)override{title_text_pending_font=&f;title_text_pending_draws=&d;return title_reference_glyphs()!=0;}
    bool upload(const TextUpload&,const std::vector<u8>&)override{return false;}
}title_text_glyph_provider;
struct TitleTextDevice:AnmTextureStoreDevice {
    bool select_texture_layout(const AnmDeviceTextureRequest&,AnmTextureLayout&,i32&)override{return false;}
    bool texture_uploaded(u32 token,const AnmTexturePixels& image)override{title_text_pending_token=token;title_text_pending_target=&image;return title_reference_text_upload()!=0&&common_texture_device.texture_uploaded(token,image);}
}title_text_device;
static std::unique_ptr<GameAnmText> title_text_runtime;
struct TitleTextDialog:TitleDialogHost {
    bool title_dialog_text(AnmView vm,const std::vector<u8>& text)override{if(!vm.data||!title_text_runtime)return false;u32 token=0;for(u32 i=0;i<world->states.size();++i)if(world->states[i]->data()==vm.data){token=world->state_tokens[i];break;}if(!token)return false;const u32 args[]={token,u32(text.size())};const auto* p=reinterpret_cast<const u8*>(args);title_dialog_calls.insert(title_dialog_calls.end(),p,p+sizeof args);title_dialog_calls.insert(title_dialog_calls.end(),text.begin(),text.end());title_dialog_calls.insert(title_dialog_calls.end(),vm.data,vm.data+AnmView::bytes);title_dialog_calls.insert(title_dialog_calls.end(),title_owner->data.begin(),title_owner->data.end());return title_text_runtime->draw_literal(vm,text);}
}title_text_dialog;
API(title_text_font) void title_text_font(u32 i,const i32* args,const u8* face,u32 n){if(i>=10)return;for(u32 j=0;j<13;++j)title_text_fonts[i].arguments[j]=args[j];title_text_fonts[i].face.assign(face,face+n);}
API(title_text_prepare) u32 title_text_prepare(u32 format,u32 alternative){boot_raster.scratch_guard=u16(fill*0x101u);title_text_runtime=std::make_unique<GameAnmText>(*world,common_texture_resources->textures,title_text_device,boot_raster,title_text_glyph_provider);return 1;}
API(title_text_show) u32 title_text_show(u32 record,u32 variant,u32 x,u32 y){if(record>=title_owner->view().get(0x5cec))return 0;auto row=title_owner->view().sub(0x5cf0+record*0x20c);if(variant==1)row.data[0x108]='\\';auto text=[&](u32 at){std::vector<u8> bytes;for(u32 i=0;i<256&&row.data[at+i];++i)bytes.push_back(row.data[at+i]);return bytes;};title_dialog_calls.clear();return show_title_dialog(*title_owner,*world,title_text_dialog,text(8),text(0x108),real(x),real(y),row.floating(0x208));}
API(title_text_header) const u8* title_text_header(){return boot_raster.header.data();}
API(title_text_bitmap) const u8* title_text_bitmap(){return boot_raster.bitmap.data();}
API(title_text_bitmap_bytes) u32 title_text_bitmap_bytes(){return boot_raster.bitmap.size();}
API(title_text_font_word) i32 title_text_font_word(u32 i){return title_text_pending_font->arguments[i];}
API(title_text_face) const u8* title_text_face(){return title_text_pending_font->face.data();}
API(title_text_face_bytes) u32 title_text_face_bytes(){return title_text_pending_font->face.size();}
API(title_text_command_count) u32 title_text_command_count(){return title_text_pending_draws->size();}
API(title_text_command_word) u32 title_text_command_word(u32 i,u32 j){const auto& d=(*title_text_pending_draws)[i];return j==0?d.color:j==1?u32(d.x):j==2?u32(d.y):d.bytes.size();}
API(title_text_command_data) const u8* title_text_command_data(u32 i){return (*title_text_pending_draws)[i].bytes.data();}
API(title_text_target_word) u32 title_text_target_word(u32 i){return i==0?title_text_pending_token:i==1?title_text_pending_target->format:i==2?title_text_pending_target->width:i==3?title_text_pending_target->height:title_text_pending_target->data.size();}
API(title_text_target_data) const u8* title_text_target_data(){return title_text_pending_target->data.data();}

static bool boot_title_draw_literal(AnmView vm,const std::vector<u8>& bytes){return title_text_runtime&&title_text_runtime->draw_literal(vm,bytes);}

struct TitleFailureMenuHost:TitleGameplayMenu {
    bool other_substate(PauseMenu& menu,u32 sub)override{if(menu.view().get(0x3e4)!=2)return TitleGameplayMenu::other_substate(menu,sub);return sub==2?pause_exit_fade():campaign_failure_subpage_v152(menu,sub);}
    bool pause_exit_fade()override{u32 resource=0,handle=0;for(const auto& r:world->resources)if(r.file==28)resource=r.token;if(!resource)return false;auto& menu=static_cast<AnmMenuWorld&>(*world);if(!menu.create_screen_transition(resource,handle)||!menu.screen_transition_signal(handle,7))return false;AnmView{common_renderer->application.data()}.put(0x1d0,handle);auto ascii=game_ascii->view();u32 transition=ascii.get(0x191ec);if(!root_transition(*world,ascii.get(0x191e4),transition))return false;ascii.put(0x191ec,transition);return true;}

    bool hint_text(u32 handle,const u8* encoded)override{auto vm=world->find(handle);if(!vm.data||!title_text_runtime)return false;u32 n=0;while(n<256&&encoded[n])++n;return n<256&&anm_text_literal(vm,boot_raster,0x80c0c0,0,0,0,encoded,n,*title_text_runtime);}
}title_failure_menu_host;
static void title_failure_globals_read(){auto& g=title_gameplay_menu_globals;auto app=AnmView{common_renderer->application.data()};g.root_mode=title_root_state.view().get(0x94);g.root_flags=title_root_state.view().get(0x80);g.config=app.get(0x724);g.game_flags=title_root_game.game_flags;g.application_state=app.get(0x6ec);g.presentation=common_texture_application_globals.presentation;g.rate=world->rate;g.clock=title_start_globals.clock;g.statistics_time=title_start_globals.statistics_time;g.text_resource=app.get(0x71c);g.front_resource=title_root_hud->view().get(0x2ac);}
static void title_failure_globals_write(){auto& g=title_gameplay_menu_globals;title_root_state.view().put(0x80,g.root_flags);title_root_game.game_flags=g.game_flags;AnmView{common_renderer->application.data()}.put(0x6ec,g.application_state);common_texture_application_globals.presentation=g.presentation;world->rate=g.rate;title_start_globals.clock=g.clock;title_start_globals.statistics_time=g.statistics_time;}
struct TitleFailurePlayServices:TitleGameplayServices {
    bool gameplay_other_option(u32 token,bool draw)override{u32 table;if(!owners->read(token,&table,4)||table!=0x4c6cec)return false;if(draw)return true;AnmView option{nullptr};for(auto& s:owners->storage)if(token>=s.token&&std::uint64_t(token)+0x64<=std::uint64_t(s.token)+s.bytes.size()){option={s.bytes.data()+token-s.token};break;}if(!option.data)return false;PlayerCameraGlobals g;g.fresh=owners->input.fresh();g.held=owners->input.held();g.released=owners->input.released();g.secondary=title_root_game.game_state[9];g.screen_width=world->width;return update_game_player_camera_aim(option,*owners,*title_root_enemy,title_start_enemies->scripts,title_root_cheat->view(),g,*world);}

    bool gameplay_game_over(bool replay)override{if(replay)return campaign_finish_cleared_replay();title_failure_globals_read();if(!title_root_menu->failure(*common_save,title_gameplay_menu_globals,0,title_failure_menu_host))return false;title_failure_globals_write();for(u32 i=0;i<12;++i){title_gameplay->player_globals.sound_ids[i]=signed_word(title_start_audio.view().get(i*4));title_gameplay->player_globals.sound_parameters[i]=title_start_audio.view().get(0x30+i*4);}return true;}
}title_failure_play_services;
struct TitleFailureFrames:TitleGameplayFrames {
    bool other_game_callback(u32 e,u32 owner,u32& result)override{if(e==0x468100||e==0x468110)return campaign_achievement_callback(e,owner,result);
        if(e!=0x448170)return TitleGameplayFrames::other_game_callback(e,owner,result);
        if(title_root_menu->menu.view().get(0x3e4)==3)return title_dodge_results_frame(result);
        title_failure_globals_read();PauseMenuInput input;input.fresh=title_gameplay_fresh;input.repeated=title_gameplay_repeated;input.root_time=signed_word(title_root_state.view().get(0x14));auto cb=frames->scheduler.at(title_root_state.view().get(8));input.root_update_enabled=cb.data&&(cb.get(4)&2);input.score=title_root_game.game_state[2];input.high_score=title_root_load_words[0x4e4790];input.scene=title_root_game.scene;input.deaths=title_root_game.game_state[4];
        input.retry_credits=title_root_load_words[0x4e47c0];const i32 r=title_root_menu->update(*common_save,title_gameplay_menu_globals,input,title_root_hud->view(),title_failure_menu_host);title_root_load_words[0x4e4790]=input.high_score;title_failure_globals_write();result=u32(r);return r!=-2;
    }
}title_failure_frames;
API(title_failure_prepare) u32 title_failure_prepare(){
    if(!title_long_prepare())return 0;
    title_gameplay=std::make_unique<GamePlayAllOptionsNov14Runtime>(*owners,*title_start_enemies,*title_root_enemy,*title_root_cheat,*title_root_aux,*title_root_hud,*world,title_start_audio,title_root_game.game_state,title_root_game.random,title_failure_play_services,common_load_storage,*common_renderer,common_render_device);title_gameplay->shooting.viewport_origin=common_renderer->playfield_origin;
    auto scheduler=std::move(frames->scheduler);frames->~GameFrameRuntime();new(frames.get()) GameFrameRuntime(title_failure_frames);frames->scheduler=std::move(scheduler);
    frames->animations=world.get();frames->overlay=&common_pool_overlay;frames->input=&owners->input;frames->player=&owners->player;frames->equipment=&owners->equipment;frames->bullets=&owners->bullets;frames->items=&owners->items;frames->scores=&owners->scores;frames->score_host=static_cast<AnmVmHost*>(static_cast<AnmWorld*>(world.get()));frames->laser_manager=GameOwnerRuntime::laser_self;title_gameplay->bind_option_services(game_ascii->view(),[](i32 pan){auto& bank=campaign_audio_host.bank;const u32 token=bank.view().get(0x1a84+84*24),arg=u32(pan);u32 hr=0;return !token||bank.sound_voice_call(token,0x40,&arg,1,hr);});title_gameplay->bind_camera_overlay(common_pool_overlay);title_gameplay->bind(*frames);common_owner_drawing->bindings.equipment=frames->equipment_host;return 1;
}


#include "../src/GameOwnerCleanupRuntime.hpp"
#include "../src/GameEnemyCleanupRuntime.hpp"
#include "../src/StageCleanup.hpp"
#include "../src/RootCleanup.hpp"
#include "../src/ManualDialogFactory.hpp"
#include "../src/ManualDialogWorkers.hpp"
#include "../src/ManualDialogCleanup.hpp"
#include "../src/ManualDialogUpdate.hpp"
#include "../src/TitleManualPage.hpp"
#include "../src/TitleMusicEntry.hpp"
#include "../src/TitleOptionView.hpp"
#include "../src/TitleReplayWorker.hpp"
#include "../src/TitleReplayControlV2.hpp"
#include "../src/TitleReplayReturnActivation.hpp"
#include "../src/TitleReplayDraw.hpp"
#include "../src/ReplayPercentFormatV2.hpp"
#include "../src/GameReplayFileLoad.hpp"
#include "../src/TitleCleanup.hpp"
#include "../src/GameManagerReplayInit.hpp"
#include "../src/GameManagerReplayFrame.hpp"
#include "../src/GameReplayEndEntry.hpp"
#include "../src/FrameTimingCounter.hpp"
#include "../src/GameReplayFileWriteV3.hpp"
#include "../src/ReplaySaveControl.hpp"
#include "../src/ReplayNameControl.hpp"
#include "../src/PauseReplayPage.hpp"
#include "../src/ReplayNameDraw.hpp"
#include "../src/ReplaySaveDraw.hpp"
#include "../src/TitleNicknameEntry.hpp"
#include "../src/TitleNicknameControl.hpp"
#include "../src/TitleNicknameDraw.hpp"
#include "../src/NicknameKeyboardCapture.hpp"
#include "../src/TitleQuitControl.hpp"
#include "../src/ApplicationOwnerCleanup.hpp"
#include "../src/ExitConfigurationWrite.hpp"
#include "../src/CommonCleanup.hpp"
#include "../src/TitlePadConfigControl.hpp"
#include "../src/TitlePadConfigViewV2.hpp"
#include "../src/DevicePadButtonRead.hpp"
#include "../src/CheatAnimation.hpp"
#include "../src/AnmPositionInterpolationBegin.hpp"
#include "../src/PauseManualPage.hpp"
#include "../src/RootTransition.hpp"
#include "../src/CheatCleanup.hpp"
static std::map<const Vm*,std::array<u32,2>> title_retry_threads;
static u32 title_retry_script_allocations=0,title_retry_failed=0;
static std::unique_ptr<GameOwnerCleanupRuntime> title_retry_owner_cleanup;
static std::unique_ptr<GameEnemyCleanupRuntime> title_retry_enemy_cleanup;
static std::vector<u8> title_retry_update_device;
static bool title_retry_thread(Vm& vm,void*){campaign_tweens_reset(vm,u8(fill));std::memset(vm.stack,u8(fill),sizeof vm.stack);vm.state=vm.flags=u32(fill)*0x01010101u;const u32 base=0x51000000+title_retry_script_allocations*0x2000;title_retry_script_allocations+=2;title_retry_threads[&vm]={base,base+0x2000};return true;}
struct TitleRetryEnemy:TitleGameplayEnemy {bool prepare_actor(EclOwner& owner)override{if(!TitleGameplayEnemy::prepare_actor(owner))return false;owner.prepare_thread=title_retry_thread;owner.thread_context=nullptr;bind_ecl_thread_release(owner,[](const Vm& vm){campaign_tweens_forget(vm);const auto i=title_retry_threads.find(&vm);if(i==title_retry_threads.end()){title_retry_failed=1;return;}for(u32 token:i->second)world->release_enemy_storage(token,false);title_retry_threads.erase(i);});return true;}}title_retry_enemy;
static std::unique_ptr<GameEnemyManagerCleanupRuntime> title_return_enemy_cleanup;
struct TitleRetryCleanup:RootCleanupHost,ResourceCleanupMemory,SchedulerHost,SceneCleanupHost,StageCleanupHost,SupportOwnerCleanupHost,GameOwnerCleanupServices,GameEnemyCleanupServices {
    RootCleanupGlobals globals;
    bool release_owner_storage(u32 p,bool a)override{return world->release_enemy_storage(p,a);}
    bool destroy_equipment_option(AnmView owner,u32 at)override{const u32 token=owner.get(at);u32 table;if(!owners->read(token,&table,4))return false;if(table==0x4c6cec){for(auto& block:owners->storage)if(token>=block.token&&std::uint64_t(token)+0x40<=std::uint64_t(block.token)+block.bytes.size())return cleanup_camera_option({block.bytes.data()+token-block.token},*world);return false;}return table==0x4c6d08||table==0x4c6d5c||table==0x4c6cd0||table==0x4c6d40||table==0x4c6cb4||table==0x4c6c98||table==0x4c6c7c||table==0x4c6c60||table==0x4c6c44||table==0x4c6c28||table==0x4c6d24;}//44fc10/459120/459cd0/45a390; storage release follows in cleanup_player_auxiliary
    bool destroy_owned_laser(u32 token)override{i32 result=0;return title_gameplay&&title_gameplay->lasers.invoke(token,0x18,false,0,result);}
    bool enemy_thread_identity(const Vm& vm,u32& token,u32& node)override{auto i=title_retry_threads.find(&vm);if(i==title_retry_threads.end())return false;token=i->second[0];node=i->second[1];return true;}
    bool release_enemy_cleanup_storage(u32 p,bool a)override{return release_owner_storage(p,a);}
    bool read_enemy_cleanup_memory(u32 p,void* b,u32 n)override{return common_render_stage->read(p,b,n)||title_root_aux->read(p,b,n)||common_auxiliary->read(p,b,n)||title_retry_owner_cleanup->read_retained(p,b,n);}
    bool write_enemy_cleanup_memory(u32 p,const void* b,u32 n)override{return common_render_stage->write(p,b,n)||title_root_aux->write(p,b,n)||common_auxiliary->write(p,b,n)||owners->write(p,b,n);}
    u8 enemy_cleanup_allocation_fill()const override{return u8(fill);}
    bool read_enemy_memory(u32 p,void* b,u32 n)override{return read_enemy_cleanup_memory(p,b,n)||world->read(p,b,n);}
    bool write_enemy_memory(u32 p,const void* b,u32 n)override{return write_enemy_cleanup_memory(p,b,n)||world->write(p,b,n);}
    bool release_enemy_storage(u32 p,bool a)override{return release_owner_storage(p,a);}
    bool find_enemy_visual(u32 h,u32& p)override{return world->find_enemy_visual(h,p);}
    bool release_graphics_object(u32 p)override{return common_texture_resources->textures.release(p);}
    bool invoke(u32,u32,u32&)override{return false;}
    bool release_callback(u32 p)override{return release_owner_storage(p,false);}
    bool remove_callback(u32 p)override{return !p||frames->scheduler.remove(p,*this);}
    bool deactivate_callback(u32 p)override{if(!p)return true;auto cb=frames->scheduler.at(p);if(!cb.data)return false;cb.put(4,cb.get(4)&~2u);return true;}
    bool release_storage(u32 p,bool a)override{auto it=std::find(pending_menu_recording_free.begin(),pending_menu_recording_free.end(),p);if(it!=pending_menu_recording_free.end()){pending_menu_recording_free.erase(it);return campaign_scene_menu_recording_free(p);}for(const auto& chunk:title_root_messages)if(chunk.token==p)return campaign_message_release(p,a);return release_owner_storage(p,a);}
    std::vector<u32> pending_menu_recording_free;
    bool destroy_scene_choice(u32 token)override{if(!campaign_scene_menu_recording_destroy(token))return false;pending_menu_recording_free.push_back(token);return true;}
    bool destroy_message(u32 p)override{AnmView message;return campaign_message_storage(p,message)&&cleanup_hud_message(message,*world);}
    bool unload_message_resource()override{return world->unload(6);}
    bool read_stage_cleanup_memory(u32 p,void* b,u32 n)override{return common_render_stage->read(p,b,n);}
    bool write_stage_cleanup_memory(u32 p,const void* b,u32 n)override{return common_render_stage->write(p,b,n);}
    bool remove_stage_callback(u32 p)override{return remove_callback(p);}
    bool release_stage_storage(u32 p,bool a)override{return release_owner_storage(p,a);}
    bool cleanup_stage_collection(u32 p)override{return cleanup_graphic_collection(p,*this);}
    bool unload_stage_animation(u32 slot)override{return world->unload(slot);}
    bool remove_support_callback(u32 p)override{return remove_callback(p);}
    bool destroy_support_option(AnmView,u32)override{return false;}
    bool release_support_option(u32 p)override{return release_owner_storage(p,true);}
    void publish(){auto& g=globals;title_root_globals.root=g.root;common_texture_application_globals.presentation=g.presentation;title_root_game.game_flags=g.game_flags;title_root_game.game_state[4]=g.deaths;title_root_load_words[0x4e47a0]=g.previous_scene;title_scene_handoff_descriptor=g.scene_descriptor;title_root_load_words[0x4e6b78]=g.auxiliary1;title_root_load_words[0x4e6b74]=g.auxiliary2;title_global_538de4=g.shutdown;title_root_load_words[0x538de4]=g.shutdown;world->rate=g.rate;AnmView{common_renderer->application.data()}.put(0xa30,g.clear_color);}
    bool save_before_cleanup()override{common_texture_application_globals.presentation=globals.presentation;std::copy_n(title_root_game.game_state.begin()+8,4,common_equipment.begin());std::copy_n(title_root_game.game_state.begin()+15,4,common_saved_equipment.begin());common_gameplay=title_root_game.random;return write_save_file(*common_save,common_saved_equipment,*world,title_gameplay_save,common_loaded_save.get());}
    bool cleanup_transition()override{publish();u32 resource=0;for(auto& r:world->resources)if(r.file==2)resource=r.token;u32 handle=game_ascii->view().get(0x191ec);if(!resource||!root_transition(*world,resource,handle))return false;game_ascii->view().put(0x191ec,handle);return true;}
    bool independent_graphics()override{publish();const u32 active=title_root_aux->independent.active;if(!cleanup_independent_graphics(title_root_aux->independent,{world->instances.registry.primary_head,world->instances.registry.secondary_head},*this))return false;title_root_aux->independent.active=active;const u32 zero=0;return world->write(0x72bc7b70,&zero,4)&&world->synchronize_resources();}
    bool destroy_root_owner(RootOwner kind,u32 token,RootCleanupGlobals& g)override{
        title_retry_failed=u32(kind)+1;publish();auto& current=g.owner(kind);using O=RootOwner;
        switch(kind){
        case O::game:return title_retry_owner_cleanup->recording(current);
        case O::replay:{StageCleanupGlobals s{g.game_flags,common_render_stage->loading.current,g.owner(O::previous_replay)};if(token!=GameStageRuntime::self||!cleanup_stage(common_render_stage->state,token,s,*this))return false;common_render_stage->loading.current=s.current;g.owner(O::previous_replay)=s.previous;current=s.current;common_render_stage->created=false;return true;}
        case O::menu:{SceneCleanupGlobals s;s.game_flags=g.game_flags;s.menu=current;if(!cleanup_pause_menu(title_root_menu->menu,s,*this))return false;current=s.menu;title_root_menu->global_owner=s.menu;return true;}
        case O::hud:{SceneCleanupGlobals s;s.game_flags=g.game_flags;s.hud=current;s.saved_message=title_root_load_words[0x4e6a58];if(!cleanup_hud(title_root_hud->view(),*world,s,*this))return false;current=s.hud;title_root_hud->globals.owner=s.hud;title_root_hud->globals.scene.pending_file=s.saved_message;title_root_load_words[0x4e6a58]=s.saved_message;return true;}
        case O::player:return title_retry_owner_cleanup->player(g.game_flags,current,title_root_load_words[0x4e6b8c]);
        case O::player_aux:return title_retry_owner_cleanup->equipment(current);
        case O::bullets:return title_retry_owner_cleanup->bullets(current);
        case O::items:return title_retry_owner_cleanup->items(current);
        case O::lasers:return title_retry_owner_cleanup->lasers(current);
        case O::scores:return title_retry_owner_cleanup->scores(current);
        case O::cheats:if(!cleanup_cheat_owner(title_root_cheat->view(),current,frames->scheduler,*this,*world))return false;title_root_cheat->global_owner=current;return true;
        case O::enemies:if(!title_return_enemy_cleanup||!title_return_enemy_cleanup->cleanup())return false;current=title_root_enemy->global_owner;return true;
        case O::extra:if(!cleanup_scene_extra(title_root_aux->special_view(),*world,current,*this))return false;title_root_aux->special_owner=current;return true;
        default:return false;
        }
    }
    bool reset_root_enemies(u32 p)override{title_retry_failed=100;return p==GameEnemyRuntime::self&&title_retry_enemy_cleanup->reset();}
    bool cleanup_root_effects(u32 p)override{title_retry_failed=101;return cleanup_effect_resources(p,{world->instances.registry.primary_head,world->instances.registry.secondary_head},*this);}
    bool preserve_gameplay(RootCleanupGlobals&)override{return false;}
    bool remove_root_callback(u32 p)override{return remove_callback(p);}
    bool release_root_storage(u32 p)override{return release_owner_storage(p,false);}
    bool fade_root_audio()override{float duration=2.f;if(world->rate>0.f&&world->rate<=1.f)duration/=world->rate;const u32 parameter=duration>=-2147483648.f&&duration<2147483648.f?u32(i32(duration)):0x80000000;MusicCommandQueue queue;std::memcpy(queue.data.data(),common_load_audio.data()+0x24f8,queue.data.size());if(!queue.enqueue(5,parameter,""))return false;std::memcpy(common_load_audio.data()+0x24f8,queue.data.data(),queue.data.size());common_load_audio[0x23f8]=0;return true;}
    bool pause_root_audio()override{std::memcpy(title_start_audio.data.data(),common_load_audio.data()+0x1c,title_start_audio.data.size());if(!title_start_audio.pause(title_failure_menu_host))return false;std::memcpy(common_load_audio.data()+0x1c,title_start_audio.data.data(),title_start_audio.data.size());return true;}
    bool cleanup(bool deleting=true){auto app=AnmView{common_renderer->application.data()};auto& g=globals;g={};g.root=title_root_globals.root;g.presentation=common_texture_application_globals.presentation;g.game_flags=title_root_game.game_flags;g.application_state=app.get(0x6ec);g.current_scene=title_root_game.scene;g.previous_scene=title_root_load_words[0x4e47a0];g.deaths=title_root_game.game_state[4];g.scene_descriptor=title_scene_handoff_descriptor;g.rate=world->rate;g.clear_color=app.get(0xa30);
        const u32 values[]={title_root_load_global(0x4e6b98),common_render_stage->loading.current,0,title_root_menu->global_owner,title_root_hud->globals.owner,title_root_load_global(0x4e6b88),title_root_load_global(0x4e6b90),title_root_load_global(0x4e6a08),title_root_load_global(0x4e6b64),title_root_load_global(0x4e6b6c),title_root_load_global(0x4e6ba4),title_root_cheat->global_owner,title_root_enemy->global_owner,title_root_aux->effects_owner,title_root_aux->special_owner};std::copy(std::begin(values),std::end(values),g.owners.begin());
        if(!(deleting?destroy_current_root(title_root_state,g,*this):cleanup_root(title_root_state,g,*this)))return false;publish();title_retry_failed=0;return world->synchronize_resources();
    }
}title_retry_cleanup;
struct TitleRetryRootPlatform:TitleRootPlatform {bool wait_worker(u32 h,u32 ms,u32& result)override{if((h!=0x77770005&&(h<0x77770101||h>0x77770200))||ms!=200)return false;title_scene_event({1,h,ms});result=0;return true;}bool close_worker(u32 h)override{if(h!=0x77770005&&(h<0x77770101||h>0x77770200))return false;title_scene_event({2,h});return true;}}title_retry_platform;
struct TitleRetryFollowing:ApplicationStateServices {
    bool lock_application_state(bool)override{return false;}
    bool application_root_mode(u32& mode)override{mode=title_root_state.view().get(0x94);return true;}
    bool application_state_call(u32 e,u32,u32,u32& result)override{result=0;if(e==0x432f80)return title_retry_cleanup.cleanup();if(e==0x45f630){title_activation_globals.startup_flags=title_root_game.game_flags;title_activation_globals.game_state=title_root_game.game_state[3];title_activation_globals.cached_game_state=AnmView{title_scene_handoff_game.data()}.get(0xa8);return title_owner->create(result);}if(e==0x4467e0){title_root_game.scene=title_root_load_words[0x4e47a0];title_root_load_words[0x4e479c]=title_root_game.scene;title_scene_handoff_descriptor=0x4ddec0+title_root_game.scene*0xac;return true;}return false;}
}title_retry_following;
static std::unique_ptr<GameTitleRootApplication> title_retry_transitions;
API(title_retry_prepare) u32 title_retry_prepare(){
    if(!title_failure_prepare())return 0;title_retry_threads.clear();title_retry_script_allocations=title_retry_failed=0;
    title_root_load_words[0x4e47a0]=AnmView{title_scene_handoff_game.data()}.get(0xb0);
    title_start_enemies=std::make_unique<GameEnemyStartup>(*title_root_enemy,*world,frames->scheduler,title_retry_enemy,title_retry_enemy);
    title_gameplay=std::make_unique<GamePlayAllOptionsNov14Runtime>(*owners,*title_start_enemies,*title_root_enemy,*title_root_cheat,*title_root_aux,*title_root_hud,*world,title_start_audio,title_root_game.game_state,title_root_game.random,title_failure_play_services,common_load_storage,*common_renderer,common_render_device);title_gameplay->shooting.viewport_origin=common_renderer->playfield_origin;title_gameplay->bind_option_services(game_ascii->view(),[](i32 pan){auto& bank=campaign_audio_host.bank;const u32 token=bank.view().get(0x1a84+84*24),arg=u32(pan);u32 hr=0;return !token||bank.sound_voice_call(token,0x40,&arg,1,hr);});title_gameplay->bind_camera_overlay(common_pool_overlay);title_gameplay->bind(*frames);common_owner_drawing->bindings.equipment=frames->equipment_host;
    title_retry_owner_cleanup=std::make_unique<GameOwnerCleanupRuntime>(*owners,*frames,*world,title_retry_cleanup);title_retry_enemy_cleanup=std::make_unique<GameEnemyCleanupRuntime>(*title_root_enemy,title_start_enemies->scripts,*world,frames->scheduler,title_retry_cleanup);
    auto app=AnmView{common_renderer->application.data()};title_retry_transitions=std::make_unique<GameTitleRootApplication>(app,*title_bindings,title_root_state,title_root_worker,title_root_globals,common_texture_application_globals.presentation,title_retry_platform,title_retry_following);title_retry_transitions->replays=campaign_replay_cleanup_host();
    if(!campaign_audio_host.prepare())return 0;title_application_update=std::make_unique<GameApplicationFullAudioUpdateRuntimeV2>(app,AnmView{common_load_audio.data()},title_device,campaign_input_platform(),static_cast<AnmMenuWorld&>(*world),title_root_application_globals,*title_retry_transitions,campaign_audio_host,campaign_audio_host);title_application_update->globals={2,world->width,world->height,u32(world->viewport.first_origin[0]),u32(world->viewport.first_origin[1])};return 1;
}
API(title_retry_frame) i32 title_retry_frame(const u8* keys,u32 enabled,u32 config,u32 keyboard,u32 acquire,u32 joystick){
    common_render_device.calls.clear();common_render_device.count=common_render_device.triangles=0;
    title_device_events.clear();AnmView{common_renderer->application.data()}.put(0x724,config);std::memcpy(title_device_host.keys.data(),keys,256);title_device_host.keyboard=keyboard;title_device_host.acquire=acquire;title_device_host.joystick=joystick;title_application_update->enabled=enabled!=0;
    if(!title_application_update->update(title_application_update_result))return -400;title_retry_update_device=common_render_device.calls;
    auto& g=title_application_update->globals;world->viewport.first_origin={signed_word(g.center_x),signed_word(g.center_y)};std::memcpy(title_start_audio.data.data(),common_load_audio.data()+0x1c,title_start_audio.data.size());device_input_to_record(title_device,owners->input);auto v=title_device.view();
    const u32 clear_color=AnmView{common_renderer->application.data()}.get(0xa30);const i32 result=title_gameplay_frame(v.get(0),v.get(12),v.get(8));if(result<0)return result;if(!common_render_stage->created)AnmView{common_renderer->application.data()}.put(0xa30,clear_color);
    common_render_device.calls.clear();common_render_device.count=common_render_device.triangles=0;common_owner_drawing->failed_entry=0;common_owner_drawing->globals={title_root_game.game_flags,AnmView{common_renderer->application.data()}.get(0x6ec),{title_root_load_words[0x4e4790],title_root_load_words[0x4e4794],title_root_game.game_state[4]}};common_registered_drawing->independent_signals=title_root_aux->independent.signals;common_registered_drawing->menu_owner=title_root_menu->global_owner;
    if(!title_capture_drawing->dispatch(title_gameplay_draw_result)||!world->synchronize_resources())return -200;record_input_to_device(owners->input,title_device);return result;
}
API(title_retry_update_device_data) const u8* title_retry_update_device_data(){return title_retry_update_device.data();}
API(title_retry_update_device_bytes) u32 title_retry_update_device_bytes(){return title_retry_update_device.size();}
API(title_retry_failed_owner) u32 title_retry_failed_owner(){return title_retry_failed;}
API(title_retry_region) const u8* title_retry_region(u32 p,u32 n){if(!title_retry_owner_cleanup)return title_root_load_region(p,n);output.resize(n);auto region=[&](u32 base,const u8* b,u32 size){if(p<base||std::uint64_t(p)+n>std::uint64_t(base)+size)return false;std::memcpy(output.data(),b+p-base,n);return true;};if(region(GameHudRuntime::self,title_root_hud->data.data(),title_root_hud->data.size())||region(GameMenuRuntime::self,title_root_menu->menu.data.data(),title_root_menu->menu.data.size())||region(GameCheatRuntime::self,title_root_cheat->data.data(),title_root_cheat->data.size())||region(title_root_menu->hint_token,title_root_menu->menu.hints.data(),title_root_menu->menu.hints.size())||title_retry_owner_cleanup->read_retained(p,output.data(),n)||title_retry_enemy_cleanup->read_retained(p,output.data(),n))return output.data();return title_root_load_region(p,n);}


#include "../src/GameRootReplayReloadRuntime.hpp"
static std::unique_ptr<GameRootReplayReloadRuntime> title_retry_loader;
static std::vector<GameAuxRuntime::Storage> title_retry_aux_archive;
static std::vector<GameOwnerRuntime::Storage> title_retry_hint_archive;
static u32 title_retry_reload_frame_index=0,title_retry_reload_phase=0;
struct TitleRetryReloadHudFiles:TitleRootHudFiles {bool hud_cached_file_log(u32)override{return true;}}title_retry_reload_hud_files;
struct TitleRetryReloadStageFiles:TitleRootStageFiles {bool read_game_stage_file(const std::string& name,std::vector<u8>& bytes)override{if(name.size()>=title_root_filename.size())return false;std::memcpy(title_root_filename.data(),name.c_str(),name.size()+1);return TitleRootStageFiles::read_game_stage_file(name,bytes);}}title_retry_reload_stage_files;
static bool title_retry_reload_worker(){
    title_retry_reload_phase=1;
    title_retry_hint_archive.push_back({title_root_menu->hint_token,title_root_menu->menu.hints});
    for(auto& b:title_root_aux->storage)title_retry_aux_archive.push_back(std::move(b));
    const u32 descriptor=title_root_aux->descriptor,width=title_root_aux->width,height=title_root_aux->height,bpp=title_root_aux->bytes_per_pixel;const auto independent=title_root_aux->independent;
    title_root_aux->~GameAuxRuntime();new(title_root_aux.get()) GameAuxRuntime(frames->scheduler,*world,*title_root_ready,title_root_aux_files);
    title_root_aux->descriptor=descriptor;title_root_aux->width=width;title_root_aux->height=height;title_root_aux->bytes_per_pixel=bpp;title_root_aux->independent=independent;title_root_aux->effects=common_auxiliary->effects;title_root_aux->effects_owner=common_auxiliary->effects_owner;
    const auto hud_globals=title_root_hud->globals;const auto hud_data=title_root_hud->data;title_root_hud->~GameHudRuntime();new(title_root_hud.get()) GameHudRuntime(*frames,*world,*title_root_ready,title_retry_reload_hud_files);title_root_hud->globals=hud_globals;title_root_hud->data=hud_data;
    auto stage_storage=std::move(common_render_stage->storage);const auto stage_data=common_render_stage->state;const auto stage_loading=common_render_stage->loading;const auto stage_script=common_render_stage->script;const auto stage_camera=common_render_stage->camera;common_render_stage->~GameStageRuntime();new(common_render_stage.get()) GameStageRuntime(*frames,*world,*title_root_ready,title_retry_reload_stage_files);common_render_stage->storage=std::move(stage_storage);common_render_stage->state=stage_data;common_render_stage->loading=stage_loading;common_render_stage->script=stage_script;common_render_stage->camera=stage_camera;
    std::memcpy(common_render_stage->loading.camera_defaults.data(),common_renderer->application.data()+0x5b4,300);title_root_hud->globals.game_flags=title_root_game.game_flags;
    title_retry_loader=std::make_unique<GameRootReplayReloadRuntime>(title_root_state,0x6e004000,title_root_game,*common_save,0x6d000000,*frames,*owners,*common_render_stage,*title_root_hud,*title_root_menu,*title_root_enemy,*title_root_cheat,*title_root_aux,*title_root_timing,*world,*title_root_ready,title_root_loader_platform,campaign_replay_input_host());
    title_retry_loader->cached_shots=title_root_load_words[0x4e6b8c];title_root_load_yields.clear();common_load_storage_release_observer=title_root_storage_release;i32 result;const bool ok=title_retry_loader->load(result);common_load_storage_release_observer=nullptr;if(!ok||result)return false;
    title_root_load_words[0x4e6b8c]=title_retry_loader->cached_shots;title_root_load_words[0x4e6a58]=title_root_hud->globals.scene.pending_file;
    std::memcpy(title_scene_handoff_game.data(),title_root_game.game_state.data(),160);AnmView{title_scene_handoff_game.data()}.put(0xc0,title_root_game.game_flags);common_gameplay=title_root_game.random;title_activation_globals.startup_flags=title_root_game.game_flags;title_alternate=title_root_game.game_state[14];std::copy_n(title_root_game.game_state.begin()+8,4,common_equipment.begin());std::copy_n(title_root_game.game_state.begin()+15,4,common_saved_equipment.begin());title_global_538de4=title_root_load_words[0x538de4];
    for(const auto& [p,v]:title_root_load_words)if(p>=0x4e4790&&p+4<=0x4e47d0)AnmView{title_scene_handoff_game.data()}.put(p-0x4e46f0,v);
    common_texture_target_globals.auxiliary=title_root_aux->descriptor;std::memcpy(common_renderer->application.data()+0x5b4,common_render_stage->camera.data(),300);title_retry_reload_phase=2;return true;
}
API(title_retry_reload_prepare) u32 title_retry_reload_prepare(){title_retry_loader.reset();title_retry_aux_archive.clear();title_retry_hint_archive.clear();title_retry_reload_frame_index=title_retry_reload_phase=0;return title_retry_prepare();}
API(title_retry_reload_frame) i32 title_retry_reload_frame(const u8* keys,u32 enabled,u32 config,u32 keyboard,u32 acquire,u32 joystick){
    common_render_device.calls.clear();common_render_device.count=common_render_device.triangles=0;
    title_device_events.clear();AnmView{common_renderer->application.data()}.put(0x724,config);std::memcpy(title_device_host.keys.data(),keys,256);title_device_host.keyboard=keyboard;title_device_host.acquire=acquire;title_device_host.joystick=joystick;title_application_update->enabled=enabled!=0;
    if(!title_application_update->update(title_application_update_result))return -400;title_retry_update_device=common_render_device.calls;
    if(!owners->created&&title_root_globals.root&&!title_retry_reload_worker())return -500;
    auto& g=title_application_update->globals;world->viewport.first_origin={signed_word(g.center_x),signed_word(g.center_y)};std::memcpy(title_start_audio.data.data(),common_load_audio.data()+0x1c,title_start_audio.data.size());device_input_to_record(title_device,owners->input);auto v=title_device.view();
    const i32 result=title_gameplay_frame(v.get(0),v.get(12),v.get(8));if(result<0)return result;
    common_render_device.calls.clear();common_render_device.count=common_render_device.triangles=0;common_owner_drawing->failed_entry=0;common_owner_drawing->globals={title_root_game.game_flags,AnmView{common_renderer->application.data()}.get(0x6ec),{title_root_load_words[0x4e4790],title_root_load_words[0x4e4794],title_root_game.game_state[4]}};common_registered_drawing->independent_signals=title_root_aux->independent.signals;common_registered_drawing->menu_owner=title_root_menu->global_owner;
    if(!title_capture_drawing->dispatch(title_gameplay_draw_result)||!world->synchronize_resources())return -200;record_input_to_device(owners->input,title_device);++title_retry_reload_frame_index;return result;
}
API(title_retry_reload_last_entry) u32 title_retry_reload_last_entry(){return title_retry_loader?title_retry_loader->last_entry:0;}
API(title_retry_reload_last_address) u32 title_retry_reload_last_address(){return title_retry_loader?title_retry_loader->last_address:0;}
API(title_retry_reload_phase_value) u32 title_retry_reload_phase_value(){return title_retry_reload_phase;}
API(title_retry_reload_region) const u8* title_retry_reload_region(u32 p,u32 n){
    auto* existing=title_retry_region(p,n);if(existing)return existing;output.resize(n);
    auto region=[&](const auto& b){if(p<b.token||std::uint64_t(p)+n>std::uint64_t(b.token)+b.bytes.size())return false;std::memcpy(output.data(),b.bytes.data()+p-b.token,n);return true;};
    for(const auto& b:title_retry_hint_archive)if(region(b))return output.data();
    for(const auto& b:title_retry_aux_archive){if(p<b.token||std::uint64_t(p)+n>std::uint64_t(b.token)+b.bytes.size())continue;std::memcpy(output.data(),b.bytes.data()+p-b.token,n);return output.data();}
    return nullptr;
}

static std::vector<GameEnemyRuntime::Storage> title_second_start_enemy_archive;
API(game_boot_region) const u8* game_boot_region(u32 p,u32 n){if(auto* bytes=campaign_achievement_region(p,n))return bytes;if(auto* bytes=day1_notice_region(p,n))return bytes;for(const auto& b:title_second_start_enemy_archive)if(p>=b.token&&std::uint64_t(p)+n<=std::uint64_t(b.token)+b.bytes.size())return b.bytes.data()+p-b.token;if(AnmView{common_renderer->application.data()}.get(0x6e8)==4&&title_cheat&&p>=GameCheatRuntime::self&&std::uint64_t(p)+n<=GameCheatRuntime::self+title_cheat->data.size())return title_cheat->data.data()+p-GameCheatRuntime::self;if(title_root_loading)return title_retry_reload_region(p,n);if(auto* bytes=boot_region(p,n))return bytes;return title_load_region(p,n);}
API(boot_graphics_calls_data) const u8* boot_graphics_calls_data(){return boot_graphics_calls.data();}
API(boot_graphics_calls_bytes) u32 boot_graphics_calls_bytes(){return boot_graphics_calls.size();}

API(boot_mesh_calls_data) const u8* boot_mesh_calls_data(){return boot_mesh_calls.data();}
API(boot_mesh_calls_bytes) u32 boot_mesh_calls_bytes(){return boot_mesh_calls.size();}

static bool title_return_loaded=false;
struct TitleReturnedFiles:TitlePlatform {bool read_title_file(const char* name,std::vector<u8>& bytes)override{if(!TitlePlatform::read_title_file(name,bytes))return false;static_cast<TitleReturnedResourceWorld&>(*world).next_shared_file=true;return true;}}title_return_files;
static bool (*title_return_previous_update)(u32,u32,u32&)=nullptr;
namespace th143 {bool activate_returned_title_main(TitleSceneEntryBindings&,AnmMenuWorld&,u32&);}
#include "../src/TitleFinalNoticeV141.hpp"
static bool title_final_notice_gate_v141(u32&,bool&);
static bool title_return_update(u32 e,u32 owner,u32& result){
    if(title_return_loaded&&owner==GameTitleRuntime::self&&e==0x45fb20&&title_owner&&!title_owner->view().get(0x1c)){bool handled;if(!title_final_notice_gate_v141(result,handled))return false;if(handled)return true;}
    if(title_return_loaded&&AnmView{common_renderer->application.data()}.get(0x6e8)==4&&owner==GameTitleRuntime::self&&e==0x45fb20){auto title=title_owner->view();if(!title.get(0x1c)&&title_activation_globals.return_mode==1){TitleSceneEntryBindings entry{*title_activation_bindings,common_equipment,common_saved_equipment,title_alternate,title_scene_reset,title_scene_worker};return activate_returned_title_main(entry,static_cast<AnmMenuWorld&>(*world),result);}if(!title.get(0x1c)&&title_activation_globals.return_mode==6){TitleSceneEntryBindings entry{*title_activation_bindings,common_equipment,common_saved_equipment,title_alternate,title_scene_reset,title_scene_worker};return activate_returned_title_scene(entry,static_cast<AnmMenuWorld&>(*world),result);}if(!advance_title_return_music(*title_activation_bindings))return false;if(title.get(0x1c)==11&&title.get(0x24)==1&&(title.get(0xe000)&1)&&signed_word(title.get(0x2b8))<10)return tick_title_return_wait(*title_activation_bindings,result);}
    return title_return_previous_update&&title_return_previous_update(e,owner,result);
}
static EnemyActorAddressSpace title_second_start_actor_addresses;
static bool title_scene_special_update();
struct TitleSceneServices:EnemySceneCommandService,SpecialCardHost {
    std::map<EclOwner*,u32> external_restart_counters;
    u8* scene_reference(EnemyScripts& scripts,i32 id,bool floating)override{if(floating)if(auto* cell=enemy_manager_float_reference({title_root_enemy->data.data()},id))return cell;if(floating&&scripts.active)if(auto* cell=enemy_script_float_reference({scripts.active->state.fields.data.data()},id))return cell;if(!floating&&scripts.active)if(auto* cell=enemy_script_integer_reference({scripts.active->state.fields.data.data()},id))return cell;if(!floating)if(auto* cell=enemy_manager_integer_reference({title_root_enemy->data.data()},id))return cell;return nullptr;}
    SpecialCardGlobals globals(){SpecialCardGlobals g;g.ascii_resource=game_ascii->view().get(0x191e4);g.text_resource=AnmView{common_renderer->application.data()}.get(0x71c);g.effect_resource=title_root_aux->effects_view().get(0x10);u32 mode=0;if(!common_auxiliary->read(0x4e40f8,&mode,4))mode=0;g.mode=mode;g.difficulty=title_root_game.game_state[10];g.dirty=title_root_load_words[0x4e47a4];g.scene=title_root_game.scene;g.score=title_gameplay->shot_globals.score;return g;}
    bool special_create(u32 resource,i32 script,u32& h)override{if(resource&0x80000000u){const u32 slot=resource&0x7fffffff;if(slot>=6)return false;resource=title_root_enemy->view().get(0xa0+slot*4);}return world->create_at(resource,script,-1,{0,0,0},h);}
    AnmView special_visual(u32 h)override{return world->find(h);}
    AnmView special_child(AnmView vm,i32 script)override{return find_animation_child(*world,vm,script);}
    bool special_signal(u32 h,i32 signal)override{return signal_animation(*world,h,signal);}
    bool special_retire(u32 h)override{return world->mark_retirement(h);}
    bool special_text(AnmView vm,const u8* b,u32 n)override{return vm.data&&title_text_runtime&&anm_centered_text_literal(vm,boot_raster,0xffffff,0,0,0,b,n,*title_text_runtime);}
    bool special_sound(u32 id)override{return title_start_audio.request(id,false,0);}
    bool special_boss_position(std::array<float,3>& p,bool& exists)override{const u32 token=title_start_enemies->scripts.controls.bosses[0];exists=token!=0;if(!exists)return true;for(auto& a:title_start_enemies->scripts.storage)if(a->token==token){for(u32 i=0;i<3;++i)p[i]=a->state.fields.floating(0x44+i*4);return true;}return false;}
    bool special_background(bool paused)override{auto v=AnmView{common_render_stage->state.data.data()};v.put(0x4224,paused?v.get(0x4224)|1:v.get(0x4224)&~1u);return true;}
    i32 scene_command(EnemyScripts& scripts,Vm& vm)override{
        auto& actor=*scripts.active;auto& state=actor.state;const u32 op=vm.instruction->opcode;
        // Prototype543: actual41e060 field order, composed with verified world retirement propagation; full independent Scene26 comparison pending.
        // Prototype800 composes verified41dc40 lookup and41d350 reset. Self-target remains explicitly unsupported until its executing-context lifetime is reconstructed.
        if(op==640){
            const i32 emitter=vm.integer_argument(0,actor.owner),row=vm.integer_argument(1,actor.owner);if(vm.failed||vm.instruction->length<29)return -2;
            const auto pc=std::uintptr_t(vm.instruction);u32 inline_name=0;
            for(u32 i=0;i<title_root_enemy->program.files.size();++i){const auto& bytes=title_root_enemy->program.files[i]->bytes;const auto begin=std::uintptr_t(bytes.data());
                if(pc>=begin&&pc-begin+vm.instruction->length<=bytes.size()){
                    const auto offset=u32(pc-begin)+28;if(!std::memchr(bytes.data()+offset,0,vm.instruction->length-28))return -2;
                    inline_name=title_root_enemy->file_tokens[i]+offset;break;}}
            return inline_name&&set_emitter_inline_name({state.fields.data.data()},emitter,row,inline_name)?0:-2;
        }
        if(op==317){struct Signal:EnemyAnimationSignalHost{bool enemy_animation_signal(u32 h,i32 signal)override{return signal_animation(*world,h,signal);}} signals;return enemy_animation_signal_command({state.fields.data.data()},vm,actor.owner,signals);}
        if(op==712){
            struct Rectangle:EnemyRectangleClearHost{EnemyScripts& scripts;explicit Rectangle(EnemyScripts& s):scripts(s){}
                bool enemy_rectangle_animation(u32 h,float& angle)override{auto v=world->find(h);if(!v.data)return false;angle=v.floating(0x50);return true;}
                bool enemy_rectangle_clear(const std::array<float,3>& p,const std::array<float,3>& size,float angle,i32 kind)override{std::vector<SceneCancellation::Actor> actors;for(auto* a:scripts.live)actors.push_back({a->token,&a->state,&a->owner,a->death_callback});return title_gameplay->camera_rectangles.bind_actors(actors)&&title_gameplay->camera_rectangles.rectangle(p,size,angle,kind,title_root_aux->special_view().get(0x7c));}
            } rectangle{scripts};
            // Prototype explicit callerSizeZ=0. Actual scheduler-stack binding remains open.
            return enemy_rectangle_clear_command({state.fields.data.data()},vm,actor.owner,0,rectangle);
        }
        if(op==555){const u32 id=u32(vm.integer_argument(1,actor.owner));if(vm.failed)return -2;std::vector<EnemyActorIdentityEntry> entries;for(auto* a:scripts.live)entries.push_back({a->state.id,a->token});const u32 value=enemy_actor_exists(entries.data(),u32(entries.size()),id);u8* target=vm.reference(0,enemy_scene_vm_host(scripts),false);if(!target||vm.failed)return -2;std::memcpy(target,&value,4);return 0;}
        if(op==637){
            const i32 selector=vm.integer_argument(0,actor.owner);if(vm.failed||!title_gameplay)return -2;i32 result=0;
            if(selector==3)return enemy_bullet_random_approach(owners->bullets,title_root_game.random,result)?0:-2;
            if(selector==4){auto* d=campaign_selector4_diagnostic;++d[0];d[1]=title_root_game.random.calls;const bool ok=enemy_bullet_random_turn_approach(owners->bullets,title_root_game.random,result);d[2]=title_root_game.random.calls;d[3]=ok?0:1;return ok?0:-2;}
            if(selector==7){const u32 token=scripts.controls.bosses[0];AnmView boss{nullptr};if(token){for(auto& a:scripts.storage)if(a->token==token){boss={a->state.fields.data.data()};break;}if(!boss.data)return -2;}return transfer_enemy_boss_counter({state.fields.data.data()},boss);}
            if(selector==8)return reset_enemy_bullet_transforms(owners->bullets,result)?0:-2;
            if(selector!=6)return -2;
            struct Swap:EnemyPlayerSwapHost{bool enemy_swap_sound(u32 id,float x)override{return title_start_audio.request(id,true,x);}bool enemy_swap_visual(u32 r,i32 script,const std::array<float,3>& p)override{u32 handle;return world->create_at(r,script,-1,p,handle);}} swap;
            AnmView option{nullptr};const u32 token=owners->equipment.view().get(0x10);for(auto& b:owners->storage)if(token>=b.token&&std::uint64_t(token)+AnmView::bytes<=std::uint64_t(b.token)+b.bytes.size()){option={b.bytes.data()+token-b.token};break;}
            return swap_enemy_player({state.fields.data.data()},owners->player,option,title_start_audio,swap,result)?0:-2;
        }
        if(op==801){
            const u32 id=u32(vm.integer_argument(2,actor.owner));if(vm.failed)return -2;std::vector<EnemyActorIdentityEntry> entries;for(auto* a:scripts.live)entries.push_back({a->state.id,a->token});const u32 token=enemy_actor_lookup(entries.data(),u32(entries.size()),id);if(!token)return -2;
            for(auto* target:scripts.live)if(target->token==token)return copy_enemy_position({target->state.fields.data.data()},vm,enemy_scene_vm_host(scripts));return -2;
        }
        if(op==800){
            const u32 id=u32(vm.integer_argument(0,actor.owner));if(vm.failed)return -2;
            std::vector<EnemyActorIdentityEntry> entries;for(auto* a:scripts.live)entries.push_back({a->state.id,a->token});const u32 token=enemy_actor_lookup(entries.data(),u32(entries.size()),id);if(!token)return 0;
            EnemyScripts::Actor* target=nullptr;for(auto* a:scripts.live)if(a->token==token){target=a;break;}if(!target||target==scripts.active)return -2;
            if(vm.instruction->length<25)return -2;const char* name=reinterpret_cast<const char*>(vm.instruction)+24;if(!std::memchr(name,0,vm.instruction->length-24))return -2;
            auto& owner=target->owner;for(auto* node=owner.threads.next;node;){auto* next=node->next;campaign_tweens_forget(*node->value);release_ecl_thread_storage(owner,*node->value);delete node->value;delete node;node=next;}
            auto* tweens=const_cast<EclVariableTweens*>(campaign_tweens_state(owner.root));reset_external_ecl_root(owner,tweens,external_restart_counters[&owner]);owner.root.instruction=scripts.program.find(name);if(!owner.root.instruction)return -2;return 0;
        }
        if(op==543){auto special=title_root_aux->special_view();special.put(0x7c,special.get(0x7c)|0x10);title_gameplay->enemy_globals.phase.special_flags=special.get(0x7c);if(!world->mark_retirement(special.get(0x20)))return -2;special.put(0x20,0);return 0;}
        if(op==613)return title_gameplay->clear_cancellation.all(title_root_aux->special_view().get(0x7c))&&title_gameplay->scene_lasers_full(1,false)?0:-2;
        if(op==524){const u32 value=u32(vm.integer_argument(0,actor.owner));if(vm.failed)return -2;AnmView game{title_scene_handoff_game.data()};game.put(0xb4,title_root_load_words[0x4e47a4]);game.put(0xbc,title_root_load_words[0x4e47ac]);if(!set_game_scene_marker(game,value))return -2;title_root_load_words[0x4e47a4]=game.get(0xb4);title_root_load_words[0x4e47ac]=game.get(0xbc);return 0;}
        if(op==1006){if(title_root_menu->menu.view().get(0x10)==1)return -2;title_failure_globals_read();const bool ok=title_root_menu->failure(*common_save,title_gameplay_menu_globals,1,title_failure_menu_host);title_failure_globals_write();return ok?0:-2;}
        if(op==1005)return title_dodge_complete_scene()?0:-2;
        if(op==615||op==616){const float r=vm.float_argument(0,actor.owner);std::array<float,3> p;for(u32 i=0;i<3;++i)p[i]=state.fields.floating(0x44+i*4);std::vector<SceneCancellation::Actor> actors;for(auto* a:scripts.live)actors.push_back({a->token,&a->state,&a->owner,a->death_callback});if(!title_gameplay->cancellation.bind_actors(actors)||!title_gameplay->cancellation.circle(p,r,op==615?1:0,true,title_root_aux->special_view().get(0x7c)))return -2;
            return !vm.failed&&title_gameplay->scene_lasers_circle(p,r,op==615?1:0,true)?0:-2;}
        if(op==517){const i32 end=vm.integer_argument(2,actor.owner),start=vm.integer_argument(1,actor.owner),duration=vm.integer_argument(0,actor.owner);return !vm.failed&&title_shooting_create_shake(duration,start,end)?0:-2;}
        if(op==315){
            const i32 script=vm.integer_argument(1,actor.owner);if(vm.failed)return -2;
            const i32 file=vm.integer_argument(0,actor.owner);if(vm.failed||file<0||file>=6)return -2;
            u32 handle;return spawn_rotated_enemy_effect(*world,title_root_enemy->view().get(0xa0+file*4),script,{state.fields.data.data()},vm,actor.owner,handle)?0:-2;
        }
        if(op==307){const i32 file=vm.integer_argument(0,actor.owner),script=vm.integer_argument(1,actor.owner);if(vm.failed||file<0||file>=6)return -2;std::array<float,3> p;for(u32 i=0;i<3;++i)p[i]=state.fields.floating(0x44+i*4);u32 handle;return spawn_enemy_effect(*world,title_root_enemy->view().get(0xa0+file*4),script,p,handle)?0:-2;}
        if(op==547){auto* d=campaign_time_scale_diagnostic;d[0]=vm.instruction->argument(0);std::memcpy(d+1,reinterpret_cast<const u8*>(vm.instruction)+8,4);d[2]=vm.failed;d[3]=vm.top;d[4]=u32(reinterpret_cast<std::uintptr_t>(actor.owner.active));d[5]=u32(reinterpret_cast<std::uintptr_t>(&vm));u32 rate=word(world->rate);const i32 result=enemy_time_scale_command(state.fields,vm,actor.owner,rate);world->rate=real(rate);d[6]=u32(result);d[7]=vm.failed;return result;}
        if(op==545)return title_gameplay->scene_lasers_reset()?0:-2;
        auto g=globals();auto special=title_root_aux->special_view();bool okay=false;
        if(op==523){okay=stop_special_card(special,g,*this);if(okay)state.put(0x4030,state.get(0x4030)&~1u);}
        if(op==522){const u32 n=vm.instruction->argument(3);if(n==0||n>0x40||32+n>vm.instruction->length)return -2;const auto* b=reinterpret_cast<const u8*>(vm.instruction)+32;std::array<u8,0x40> text{};u8 key=0x77,step=7;for(u32 i=0;i<n;++i){text[i]=b[i]^key;key+=step;step+=0x10;}u32 length=0;while(length<n&&text[length])++length;if(length==n)return -2;
            const u32 card=u32(vm.integer_argument(0,actor.owner)),duration=u32(vm.integer_argument(1,actor.owner));vm.integer_argument(2,actor.owner);okay=!vm.failed&&start_special_card(special,g,card,text.data(),length,duration,static_cast<AnmVmHost&>(static_cast<AnmWorld&>(*world)),*this);if(okay){state.put(0x4030,state.get(0x4030)|1u);state.put(0x4024,state.get(0x4018)*7u);if(!(state.get(0x36c)&1)){state.put(0x368,world->global_rate_token());state.put(0x36c,state.get(0x36c)|1);}state.put(0x35c,0xffffffff);state.put(0x360,0);state.put(0x364,0);}}
        title_root_game.game_state[2]=g.score;title_gameplay->shot_globals.score=g.score;title_gameplay->enemy_globals.phase.special_flags=special.get(0x7c);title_gameplay->enemy_globals.phase.manager_phase=title_root_enemy->view().get(0x18);return okay&&!vm.failed?0:-2;
    }
}title_scene_services;
static bool title_scene_special_update(){auto g=title_scene_services.globals();return update_special_card(title_root_aux->special_view(),g,owners->player.floating(0x5e4),static_cast<AnmVmHost&>(static_cast<AnmWorld&>(*world)),title_scene_services);}
API(title_scene_debug) u32 title_scene_debug(u32 i){auto current=title_root_aux->special_view(),bound=common_owner_drawing->bindings.special;const u32 words[]={current.get(0x7c),bound.get(0x7c),current.get(0x1c),bound.get(0x1c),current.get(0x80),bound.get(0x80)};return i<6?words[i]:0;}

static std::unique_ptr<GameEnemyManagerSweepRuntime> title_scene_enemy_sweep;
struct TitleAttackActorLifetime:EnemyActorLifetime {
    std::map<u32,std::vector<u32>> pending;
    bool before_retirement(EnemyScripts::Actor& actor)override{auto& p=pending[actor.token];if(!p.empty())return false;for(auto* n=actor.owner.threads.next;n;n=n->next){const auto i=title_retry_threads.find(n->value);if(i==title_retry_threads.end())return false;p.insert(p.end(),i->second.begin(),i->second.end());title_retry_threads.erase(i);}return true;}
    bool after_retirement(EnemyScripts::Actor& actor)override{auto i=pending.find(actor.token);if(i==pending.end())return false;for(u32 token:i->second)if(!world->release_enemy_storage(token,false))return false;pending.erase(i);return world->release_enemy_storage(actor.token,false);}
}title_attack_actor_lifetime;

API(title_return_prepare) u32 title_return_prepare(){if(!title_retry_reload_prepare())return 0;title_second_start_actor_addresses={};bind_enemy_actor_address_space(title_start_enemies->scripts,&title_second_start_actor_addresses);bind_enemy_scene_commands(title_start_enemies->scripts,&title_scene_services);bind_enemy_actor_lifetime(title_start_enemies->scripts,&title_attack_actor_lifetime);title_scene_enemy_sweep=std::make_unique<GameEnemyManagerSweepRuntime>(*title_root_enemy,title_start_enemies->scripts,*world,owners->items,title_root_game.random,title_start_audio);title_return_loaded=false;title_return_enemy_cleanup=std::make_unique<GameEnemyManagerCleanupRuntime>(*title_root_enemy,*title_retry_enemy_cleanup,*world,frames->scheduler);title_return_previous_update=common_pool_extra_update;common_pool_extra_update=title_return_update;return 1;}
static TitlePreviewTask title_live_preview_task;
static u32 campaign_title_returns=0;static bool campaign_preview_running=false;
static std::vector<u8> title_live_preview_yields;
static std::vector<u32> title_live_preview_saved_io;
static u32 title_live_preview_frame=0;
struct TitleLivePreviewFiles:SavedPreviewFileServices {
    bool saved_preview_directory(bool restore)override{title_io_event(7,{u32(restore)});return true;}
    bool saved_preview_exists(const std::string& name,bool& found)override{if(name.rfind("savedata/sc",0)!=0)return false;if(!campaign_preview_files.exists(name,found))return false;title_saved_io.insert(title_saved_io.end(),{1,u32(found)});return true;}
    bool read_saved_preview_bytes(const std::string& name,std::vector<u8>& bytes)override{return campaign_preview_files.read(name,bytes);}
}title_live_preview_files;
struct TitleLivePreviewHost:TitlePreviewWorkerHost {
    bool read_scene_preview(const std::string& name,std::vector<u8>& bytes,bool& found)override{found=common_load_files.read_animation_file(name,false,bytes);if(found)static_cast<TitleReturnedResourceWorld&>(*world).next_shared_file=true;return true;}
    bool read_saved_preview(const std::string& name,u32& token)override{GameSavedPreviewFiles files{*world,title_live_preview_files};if(!load_saved_preview(name,common_save->codec,files,token))return false;if(token){std::array<u8,0x78> h{};if(!world->read(token,h.data(),h.size()))return false;auto v=AnmView{h.data()};const u32 n=v.get(0x10);if(n>0x4000000)return false;campaign_preview_decoded_pixels.resize(n);if(n&&!world->read(v.get(0x74),campaign_preview_decoded_pixels.data(),n))return false;}return true;}
    bool sleep_scene_preview(u32 milliseconds)override{auto append=[&](const void* p,u32 n){auto* b=static_cast<const u8*>(p);title_live_preview_yields.insert(title_live_preview_yields.end(),b,b+n);};const u32 header[]={title_live_preview_frame,milliseconds};append(header,sizeof header);append(title_owner->data.data(),title_owner->data.size());append(common_renderer->application.data(),common_renderer->application.size());return true;}
}title_live_preview_host;
static bool title_second_start_preview_join(){if(title_live_preview_frame<241)return true;return title_live_preview_task.resume(*title_owner,*world,{common_renderer->application.data()},title_live_preview_host)==0;}
static bool title_second_start_loaded=false;
API(title_second_start_frame) i32 title_second_start_frame(const u8* keys,u32 enabled,u32 config,u32 keyboard,u32 acquire,u32 joystick){
    if(!day1_notice_resume())return -540;
    if(!campaign_manual_pump())return -550;
    common_render_device.calls.clear();common_render_device.count=common_render_device.triangles=0;
    title_device_events.clear();AnmView{common_renderer->application.data()}.put(0x724,config);std::memcpy(title_device_host.keys.data(),keys,256);title_device_host.keyboard=keyboard;title_device_host.acquire=acquire;title_device_host.joystick=joystick;title_application_update->enabled=enabled!=0;
    common_load_storage_release_observer=title_root_storage_release;const bool updated=title_application_update->update(title_application_update_result);common_load_storage_release_observer=nullptr;if(!updated)return -400;title_retry_update_device=common_render_device.calls;
    if(AnmView{common_renderer->application.data()}.get(0x6e8)==4&&title_owner->global_owner&&!title_return_loaded){i32 loaded;if(!load_title(*title_bindings,title_return_files,loaded)||loaded)return -510;title_return_loaded=true;title_second_start_loaded=false;++campaign_title_returns;if(campaign_cold_title_active||campaign_title_returns>1){title_live_preview_task={};campaign_preview_running=false;}title_root_load_words[0x538de4]=title_global_538de4;}
    if(title_return_loaded&&AnmView{common_renderer->application.data()}.get(0x6e8)==7&&title_root_globals.root&&!title_second_start_loaded){
        title_scene_handoff_sync();auto app=AnmView{common_renderer->application.data()};std::memcpy(title_root_game.game_state.data(),title_scene_handoff_game.data(),160);title_root_game.new_game=app.get(0x6f8);title_root_load_words[0x4e47a0]=AnmView{title_scene_handoff_game.data()}.get(0xb0);title_root_game.scene=AnmView{title_scene_handoff_game.data()}.get(0xac);title_root_load_words[0x4e479c]=title_root_game.scene;title_root_game.game_flags=AnmView{title_scene_handoff_game.data()}.get(0xc0);title_root_game.random=common_gameplay;std::memcpy(title_root_game.root_snapshot.data(),app.data+0x1d4,92);
        for(auto& b:title_root_enemy->storage)title_second_start_enemy_archive.push_back(std::move(b));
        if(title_root_enemy->loader_token)title_second_start_enemy_archive.push_back({title_root_enemy->loader_token,std::vector<u8>(title_root_enemy->loader.begin(),title_root_enemy->loader.end())});
        title_root_enemy->~GameEnemyRuntime();new(title_root_enemy.get()) GameEnemyRuntime(frames->scheduler,*title_root_ready,title_root_enemy_files,&title_root_filename);
        if(!title_retry_reload_worker())return -530;title_second_start_loaded=true;title_return_loaded=false;
    }
    if(!title_return_loaded&&!owners->created&&title_root_globals.root){
        if(!(title_root_game.game_flags&0x11)){
            for(auto& block:title_root_enemy->storage)title_second_start_enemy_archive.push_back(std::move(block));
            if(title_root_enemy->loader_token)title_second_start_enemy_archive.push_back({title_root_enemy->loader_token,std::vector<u8>(title_root_enemy->loader.begin(),title_root_enemy->loader.end())});
            title_root_enemy->~GameEnemyRuntime();new(title_root_enemy.get()) GameEnemyRuntime(frames->scheduler,*title_root_ready,title_root_enemy_files,&title_root_filename);
        }
        if(!title_retry_reload_worker())return -531;
    }
    if(campaign_title_returns<=1&&title_live_preview_frame==241&&!title_preview_image_prepare())return -521;
    if((campaign_title_returns<=1?title_live_preview_frame>=241:campaign_preview_running)&&title_owner->global_owner){const i32 status=title_live_preview_task.resume(*title_owner,*world,{common_renderer->application.data()},title_live_preview_host);if(status<0)return -520;}
    auto& g=title_application_update->globals;world->viewport.first_origin={signed_word(g.center_x),signed_word(g.center_y)};std::memcpy(title_start_audio.data.data(),common_load_audio.data()+0x1c,title_start_audio.data.size());device_input_to_record(title_device,owners->input);auto v=title_device.view();if(title_return_loaded){title_scene_session_services.keys={v.get(12),v.get(8),common_save->data[0xefb8]!=0};title_ready_services.keys.fresh=v.get(12);title_ready_services.keys.repeated=v.get(8);title_ready_services.keys.started_before=common_save->data[0xefb8]!=0;}
    i32 result;if(!title_return_loaded){result=title_gameplay_frame(v.get(0),v.get(12),v.get(8));if(result<0)return result;}else{title_gameplay_keys=v.get(0);title_gameplay_fresh=v.get(12);title_gameplay_repeated=v.get(8);title_gameplay_trace.clear();title_gameplay_returns.clear();title_start_services.clear();title_start_commands.clear();title_start_clock_values.clear();common_load_storage_release_observer=title_root_storage_release;const bool ok=frames->dispatch(false,result);common_load_storage_release_observer=nullptr;if(!ok)return -100;}
    common_render_device.calls.clear();common_render_device.count=common_render_device.triangles=0;common_owner_drawing->failed_entry=0;common_owner_drawing->globals={title_root_game.game_flags,AnmView{common_renderer->application.data()}.get(0x6ec),{title_root_load_words[0x4e4790],title_root_load_words[0x4e4794],title_root_game.game_state[4]}};common_registered_drawing->independent_signals=title_root_aux->independent.signals;common_registered_drawing->menu_owner=title_root_menu->global_owner;
    if(!(title_return_loaded?title_scene_confirm_drawing->dispatch(title_gameplay_draw_result):title_capture_drawing->dispatch(title_gameplay_draw_result))||!world->synchronize_resources())return -200;
    //446290 cleared the same native camera fields; clear their mirrors too.
    for(u32 i=0;i<2;++i){const u32 value=AnmView{common_renderer->application.data()}.get(0x6b0+i*4);AnmView{common_render_stage->camera.data()}.put(0xfc+i*4,value);common_renderer->render_camera.view().put(0xfc+i*4,value);}
    if(title_return_loaded)title_scene_handoff_sync();record_input_to_device(owners->input,title_device);++title_retry_reload_frame_index;++title_live_preview_frame;return result;
}
API(title_return_phase) u32 title_return_phase(){return title_return_loaded;}

API(title_live_preview_yields_data) const u8* title_live_preview_yields_data(){return title_live_preview_yields.data();}
API(title_live_preview_yields_bytes) u32 title_live_preview_yields_bytes(){return title_live_preview_yields.size();}
API(title_live_preview_saved_io_data) const u32* title_live_preview_saved_io_data(){return title_live_preview_saved_io.data();}
API(title_live_preview_saved_io_words) u32 title_live_preview_saved_io_words(){return title_live_preview_saved_io.size();}

API(title_second_start_phase) u32 title_second_start_phase(){return title_second_start_loaded;}
API(title_second_start_preview_done) u32 title_second_start_preview_done(){return title_live_preview_task.phase==11;}

struct TitleShootingShakeHost:ScreenShakeLifecycleHost,SchedulerHost {
    AnmView view(u32 token){for(auto& s:title_root_aux->storage)if(s.token==token&&s.bytes.size()==0x44)return {s.bytes.data()};return {nullptr};}
    bool invoke(u32,u32,u32&)override{return false;}
    bool release_callback(u32 token)override{return common_load_storage.release_game_storage(token);}
    bool shake_allocate(u32 bytes,u32& token,AnmView& out)override{if(!common_load_storage.allocate_game_storage(bytes,token))return false;title_root_aux->storage.push_back({token,std::vector<u8>(bytes,u8(fill))});out={title_root_aux->storage.back().bytes.data()};return true;}
    bool shake_callback(u32 entry,u32& token,AnmView& out)override{if(!common_load_storage.allocate_game_storage(0x28,token)||!frames->scheduler.create(token,entry,u8(fill)))return false;out=frames->scheduler.at(token);return true;}
    bool shake_register(u32 token,i32 priority)override{u32 result;return frames->scheduler.add(token,priority,false,*this,result);}
    bool shake_remove(u32 token)override{return frames->scheduler.remove(token,*this);}
    bool shake_release(u32 token)override{return common_load_storage.release_game_storage(token);}
}title_shooting_shake;
static bool title_shooting_create_shake(i32 duration,i32 start,i32 end){u32 token;AnmView out;return create_screen_shake(duration,start,end,title_shooting_shake,token,out)&&token;}
static bool title_shooting_effect_callback(u32 entry,u32 owner,u32& result){
    auto view=title_shooting_shake.view(owner);if(!view.data)return false;
    if(entry==0x471a30){result=0;return destroy_screen_shake(view,owner,true,title_shooting_shake);}
    if(entry!=0x471650)return false;
    auto app=AnmView{common_renderer->application.data()};ScreenShakeGlobals g;g.paused=title_root_load_words[0x538de4];g.scale=word(world->viewport.scale);g.offsets={app.get(0x6b0),app.get(0x6b4),app.get(0x458),app.get(0x45c)};g.random=world->animation_rng;
    const i32 r=step_screen_shake(view,g,static_cast<AnmVmHost&>(static_cast<AnmWorld&>(*world)));if(r==-2)return false;
    result=u32(r);world->animation_rng=g.random;app.put(0x6b0,g.offsets[0]);app.put(0x6b4,g.offsets[1]);app.put(0x458,g.offsets[2]);app.put(0x45c,g.offsets[3]);
    // Native4e4e80/84 are also the pixel camera's fc/100 fields. Keep
    // both portable camera mirrors coherent before their next publication.
    AnmView stage_camera{common_render_stage->camera.data()};auto render_camera=common_renderer->render_camera.view();
    for(u32 i=0;i<2;++i){stage_camera.put(0xfc+i*4,g.offsets[i]);render_camera.put(0xfc+i*4,g.offsets[i]);}return true;
}

#include "natural-clear-preview-services-v65.hpp"
static u32 natural_clear_completion_stage=0;
API(title_natural_clear_stage) u32 title_natural_clear_stage(){return natural_clear_completion_stage;}
struct TitleDodgeCompletion:SceneCompletionHost,PlayerClearExitHost {
    bool achievement(u32 id)override{return common_load_platform.achievement(id);}
    bool clear_bonus(u32& score)override{award_hud_clear_bonus(title_root_hud->view(),score,world->global_rate_token());return true;}
    bool clear_exit_signal(u32 handle,i32 signal)override{return signal_animation(*world,handle,signal);}
    bool finish_player_shots()override{natural_clear_completion_stage=1;const bool okay=begin_player_clear_exit(owners->player,*this);if(okay)natural_clear_completion_stage=2;return okay;}
    // Non-empty audio objects and captured GPU previews retain their own services.
    bool stop_completion_audio()override{return false;}
    bool capture_clear_preview(u32 day,u32 within)override{natural_clear_completion_stage=3;const bool okay=title_natural_clear_preview(day,within);if(okay)natural_clear_completion_stage=4;return okay;}
    bool open_completion_message(i32 id)override{return campaign_message_create(id);}
    bool finish_replay()override{return campaign_finish_cleared_replay();}
    bool open_results_menu()override{
        natural_clear_completion_stage=5;title_failure_globals_read();
        const bool ok=th143::open_results_menu(title_root_menu->menu,*common_save,title_gameplay_menu_globals,*world,common_pool_overlay,title_root_game.game_state[8],title_root_game.scene,owners->equipment.view().get(0x18),title_failure_menu_host);
        title_failure_globals_write();if(ok)natural_clear_completion_stage=6;return ok;
    }
}title_dodge_completion;
static bool title_dodge_complete_scene(){
    SceneCompletionGlobals g;g.flags=title_root_game.game_flags;g.day=title_root_game.game_state[10];g.within_day=title_root_game.game_state[11];g.scene=title_root_game.scene;g.score=title_gameplay->shot_globals.score;g.primary=title_root_game.game_state[8];g.alternate=title_root_game.game_state[9];g.signals=title_root_aux->independent.active;g.root_mode=title_root_state.view().get(0x94);g.equipment_used=owners->equipment.view().get(0x18);g.audio_active=title_root_load_words[0x4e40f8]!=0;
    constexpr std::array<u32,10> first={1,7,13,20,27,35,43,51,58,66},counts={6,6,7,7,8,8,8,7,8,10};g.day_first=first;g.day_count=counts;
    const bool ok=complete_scene(*common_save,g,title_dodge_completion);title_root_game.game_state[2]=title_gameplay->shot_globals.score=g.score;
    if(ok)for(u32 i=0;i<12;++i){title_gameplay->player_globals.sound_ids[i]=signed_word(title_start_audio.view().get(i*4));title_gameplay->player_globals.sound_parameters[i]=title_start_audio.view().get(0x30+i*4);}
    return ok;
}

struct Day1ClearResultsExitHost final:ResultsMenuExitHost {
    bool achievement(u32 id)override{return title_failure_menu_host.achievement(id);}
    bool performance_counter(std::uint64_t& value)override{return title_failure_menu_host.performance_counter(value);}
    bool millisecond_ticks(u32& value)override{return title_failure_menu_host.millisecond_ticks(value);}
    bool pause_audio()override{return title_failure_menu_host.pause_audio();}
    bool sound_and_flush(u32 id)override{return title_failure_menu_host.sound_and_flush(id);}
    bool menu_sound(u32 id)override{return title_failure_menu_host.menu_sound(id);}
    bool hint_text(u32 handle,const u8* value)override{return title_failure_menu_host.hint_text(handle,value);}
    bool other_substate(PauseMenu& menu,u32 state)override{return title_failure_menu_host.other_substate(menu,state);}
    bool results_exit_fade()override{return title_failure_menu_host.pause_exit_fade();}
}day1_clear_results_exit_host;
static bool title_dodge_results_frame(u32& result){
    bool handled;if(!day1_notice_results_gate(result,handled))return false;if(handled)return true;
    title_failure_globals_read();ResultsMenuIdleInput input;input.fresh=title_gameplay_fresh;input.repeated=title_gameplay_repeated;input.score=title_root_game.game_state[2];input.high_score=title_root_load_words[0x4e4790];input.scene=title_root_game.scene;input.deaths=title_root_game.game_state[4];input.day=title_root_game.game_state[10];input.within_day=title_root_game.game_state[11];
    constexpr std::array<u32,10> counts={6,6,7,7,8,8,8,7,8,10};if(input.day>=counts.size())return false;input.day_scene_count=counts[input.day];input.message_owner=title_root_load_words[0x4e6b80];
    constexpr std::array<u32,10> first={1,7,13,20,27,35,43,51,58,66};
    const i32 r=results_menu_exit_frame_v4(title_root_menu->menu,*common_save,title_gameplay_menu_globals,input,*world,common_pool_overlay,title_root_hud->view(),day1_clear_results_exit_host,{reinterpret_cast<u8*>(title_root_game.game_state.data())},title_root_game.scene,first,campaign_results_replay_host(),gameplay_pause_equipment,campaign_results_manual_host());
    title_root_load_words[0x4e479c]=title_root_game.scene;AnmView{title_scene_handoff_game.data()}.put(0xac,title_root_game.scene);
    title_root_load_words[0x4e4790]=input.high_score;title_failure_globals_write();result=u32(r);return r!=-2;
}

struct NaturalClearResultsDrawHost final:ResultsMenuDrawHost,AnmTransformHost {
    AnmView transform_parent(u32 token)override{return world->state(token);}
    bool results_child_position(u32& handle,i32 script,std::array<float,3>& p)override{
        auto parent=world->find(handle);if(!parent.data){handle=0;return false;}
        auto child=find_animation_child(*world,parent,script);if(!child.data)return false;
        //484f20 passes its local position to431af0, including parent chains.
        return anm_position(child,world->viewport,*this,p);
    }
    bool results_number(const std::array<float,3>& p,u32 value)override{return queue_ascii_text(game_ascii->view(),p,format_ascii_number(value),world->viewport);}
    bool results_subpage(u32 entry,AnmView menu)override{return campaign_replay_save_draw(entry,menu);}
};
static bool title_natural_clear_results_draw(u32 entry,AnmView menu){
    if(entry!=0x44b4a0)return false;NaturalClearResultsDrawHost host;
    return draw_results_menu(menu,common_save->view(),game_ascii->view(),{title_root_game.scene,title_root_game.game_state[2],title_root_game.game_state[6],world->viewport.scale},host);
}

#include "day1-notice-wait-services-v84.hpp"
struct TitleFinalNoticeServicesV141 final:TitleFinalNoticeHost {
 bool final_notice_create(u32 id)override{u32 owner;if(!day1_notice_results_services.results_create_notice(id,owner))return false;title_activation_globals.trophy_owner=owner;return true;}
 bool final_notice_destroy()override{if(!day1_notice_results_services.results_destroy_notice(day1_notice_globals.owner))return false;title_activation_globals.trophy_owner=0;return true;}
}title_final_notice_services_v141;
static bool title_final_notice_gate_v141(u32& result,bool& handled){
 title_activation_globals.trophy_owner=day1_notice_globals.owner;
 return advance_title_final_notice_v141(*title_activation_bindings,static_cast<AnmMenuWorld&>(*world),day1_notice_view(),title_final_notice_services_v141,handled,result);
}
API(natural_private_final_notice_fixture) u32 natural_private_final_notice_fixture(){
 if(!title_return_loaded||!title_owner||title_owner->view().get(0x1c)!=11||day1_notice_globals.owner)return 0;
 auto title=title_owner->view(),save=common_save->view();title.put(0x1c,0);title.put(0x24,0);title_activation_globals.return_mode=6;save.put(0xf16c,1);save.put(0xf170,39);return 1;
}



// A fresh title creates a fresh464b20 worker. Retaining a returned coroutine's
// phase11 after later title creation leaves new PNG requests unprocessed.
static bool campaign_title_preview_launch(){
 if(campaign_cold_title_active||campaign_title_returns>1){title_live_preview_task={};campaign_preview_running=true;return title_preview_image_prepare()!=0;}
 return true;
}

namespace th143 {
i32 campaign_alpha_command(AnmView actor,Vm& vm,VmHost& host){
 struct Alpha final:EnemyAnimationAlphaHost {bool find_alpha_animation(u32 handle,AnmView& out)override{out=world->find(handle);return out.data!=nullptr;}} alpha;
 if(vm.instruction->opcode==336)return enemy_animation_layer(actor,vm,host,alpha);
 if(vm.instruction->opcode==331||vm.instruction->opcode==332)return enemy_animation_secondary_alpha(actor,vm,host,alpha,world->global_rate_token());
 return vm.instruction->opcode==328?enemy_animation_alpha(actor,vm,host,alpha,world->global_rate_token()):enemy_animation_scale(actor,vm,host,alpha,world->global_rate_token());
}
}

namespace th143 {bool campaign_vm_rate(float& value){return world&&world->timer_rate(world->global_rate_token(),value);}}
API(title_context_scalar_data) const u8* title_context_scalar_data(u32 i,u32 k){const auto* s=campaign_tweens_state(*title_start_context(i,k));return s?s->scalars.data():nullptr;}
API(title_context_scalar_origin) const u8* title_context_scalar_origin(u32 i,u32 k,u32 slot){const auto* s=campaign_tweens_state(*title_start_context(i,k));return s&&slot<8?reinterpret_cast<const u8*>(s->origins[slot]):nullptr;}

namespace th143 {u32 campaign_difficulty_index(){return title_root_game.game_state[3];}}

// Read-only failure evidence, including actors whose initial ECL rejected.
API(campaign_emitter_actor_count) u32 campaign_emitter_actor_count(){return title_start_enemies?title_start_enemies->scripts.storage.size():0;}
API(campaign_emitter_actor_token) u32 campaign_emitter_actor_token(u32 i){return title_start_enemies&&i<title_start_enemies->scripts.storage.size()?title_start_enemies->scripts.storage[i]->token:0;}
API(campaign_emitter_actor_data) const u8* campaign_emitter_actor_data(u32 i){return title_start_enemies&&i<title_start_enemies->scripts.storage.size()?title_start_enemies->scripts.storage[i]->state.fields.data.data():nullptr;}

#include "campaign-dialog-services-v54.hpp"
#include "campaign-special-message-services-v57.hpp"
#include "campaign-message-services-v58.hpp"

API(campaign_config_live) const u8* campaign_config_live(){return common_renderer?common_renderer->application.data()+0x1d4:common_load_application.data()+0x1d4;}

#include "../src/TitleFirstStartBody.hpp"
#include "../src/TitleRootPreparation.hpp"
#include "../src/ApplicationGameRequests.hpp"
#include "../src/GameStartupFlags.hpp"
#include "../src/ManualDialogFactory.hpp"
#include "../src/ManualDialogWorkers.hpp"
#include "../src/ManualDialogCleanup.hpp"
#include "../src/ManualDialogUpdate.hpp"
#include "../src/TitleManualPage.hpp"
#include "../src/TitleMusicEntry.hpp"
#include "../src/TitleOptionView.hpp"
#include "../src/TitleReplayWorker.hpp"
#include "../src/TitleReplayControlV2.hpp"
#include "../src/TitleReplayReturnActivation.hpp"
#include "../src/TitleReplayDraw.hpp"
#include "../src/ReplayPercentFormatV2.hpp"
#include "../src/GameReplayFileLoad.hpp"
#include "../src/TitleCleanup.hpp"
#include "../src/GameManagerReplayInit.hpp"
#include "../src/GameManagerReplayFrame.hpp"
#include "../src/GameReplayEndEntry.hpp"
#include "../src/FrameTimingCounter.hpp"
#include "../src/GameReplayFileWriteV3.hpp"
#include "../src/ReplaySaveControl.hpp"
#include "../src/ReplayNameControl.hpp"
#include "../src/PauseReplayPage.hpp"
#include "../src/ReplayNameDraw.hpp"
#include "../src/ReplaySaveDraw.hpp"
#include "../src/TitleNicknameEntry.hpp"
#include "../src/TitleNicknameControl.hpp"
#include "../src/TitleNicknameDraw.hpp"
#include "../src/NicknameKeyboardCapture.hpp"
#include "../src/TitleQuitControl.hpp"
#include "../src/ApplicationOwnerCleanup.hpp"
#include "../src/ExitConfigurationWrite.hpp"
#include "../src/CommonCleanup.hpp"
#include "../src/TitlePadConfigControl.hpp"
#include "../src/TitlePadConfigViewV2.hpp"
#include "../src/DevicePadButtonRead.hpp"
#include "../src/CheatAnimation.hpp"
#include "../src/AnmPositionInterpolationBegin.hpp"
#include "../src/PauseManualPage.hpp"
#include "../src/RootTransition.hpp"
static std::unique_ptr<GameMenuApplicationDrawV2> natural_first_drawing;
static u32 natural_first_requests=0,natural_first_transitions=0,natural_first_failed_entry=0;
struct NaturalFirstStartHost:TitleFirstStartHost,TitleRootPreparationHost {
    AnmView app(){return{common_renderer->application.data()};}
    AnmView game(){return{title_scene_handoff_game.data()};}
    bool first_start_transition(u32& handle)override{natural_first_failed_entry=0x41af40;u32 resource=0;if(!world->read(0x72bc7b0c+28*4,&resource,4)||!static_cast<AnmMenuWorld&>(*world).create_screen_transition(resource,handle))return false;++natural_first_transitions;return true;}
    bool first_start_signal(u32 handle,i32 id)override{natural_first_failed_entry=0x484320;return static_cast<AnmMenuWorld&>(*world).screen_transition_signal(handle,id,false);}
    bool first_start_ascii(u32 x,u32 y)override{natural_first_failed_entry=0x41ce10;auto ascii=game_ascii->view();u32 handle=ascii.get(0x191ec);if(!root_transition(*world,ascii.get(0x191e4),handle,real(x),real(y)))return false;ascii.put(0x191ec,handle);return true;}
    bool first_start_title_state(i32 value)override{natural_first_failed_entry=0x45e880;return select_title_state(*title_owner,value);}
    bool first_start_clear_title()override{natural_first_failed_entry=0x45f580;return prepare_title_for_root(title_owner->view(),*this);}
    bool first_start_fade(u32 duration)override{natural_first_failed_entry=0x444810;float rate;if(!world->timer_rate(world->global_rate_token(),rate))return false;u32 ignored;return request_application_music_fade({common_load_audio.data()},duration,word(rate),ignored);}
    bool first_start_initialize_game(u32 mode)override{natural_first_failed_entry=0x44b7b0;u32 ignored;return initialize_application_game_mode(game(),mode,ignored);}
    bool first_start_message(u32 value)override{natural_first_failed_entry=0x4674b0;u32 ignored;return set_application_scene_flags(game(),value,ignored);}
    bool stop_title_preview(AnmView target)override{
        BackgroundWorker worker;std::memcpy(worker.data.data(),target.data,worker.data.size());
        struct Bridge:RootFactoryHost {BackgroundWorker& worker;AnmView target;Bridge(BackgroundWorker& w,AnmView t):worker(w),target(t){}void publish(){std::memcpy(target.data,worker.data.data(),worker.data.size());}void refresh(){std::memcpy(worker.data.data(),target.data,worker.data.size());}
            bool allocate_root(u32&)override{return false;}bool evict_managed_textures()override{return false;}bool launch_worker(u32,u32,u32,u32&,u32&)override{return false;}
            bool wait_worker(u32 h,u32 ms,u32& status)override{publish();const bool ok=title_scene_worker.wait_worker(h,ms,status);refresh();return ok;}
            bool close_worker(u32 h)override{publish();const bool ok=title_scene_worker.close_worker(h);refresh();return ok;}
            bool sleep_worker(u32 ms)override{publish();const bool ok=title_scene_worker.sleep_worker(ms);refresh();return ok;}
        } bridge{worker,target};const bool ok=stop_background_worker(worker,bridge);bridge.publish();return ok;
    }
    bool title_preview_free(u32 token)override{return !token||world->release_enemy_storage(token,true);}
    bool title_preview_region(u32 token,u32 n,AnmView& out)override{for(auto& r:world->regions)if(token>=r.token&&std::uint64_t(token)+n<=std::uint64_t(r.token)+r.bytes.size()){out={r.bytes.data()+token-r.token};return true;}return false;}
}natural_first_host;
static bool campaign_hud_open_results(HudMessageGlobals* g){
 if(!title_dodge_completion.open_results_menu())return false;
 if(g){auto app=AnmView{common_renderer->application.data()};g->root_flags=title_root_state.view().get(0x80);g->game_flags=title_root_game.game_flags;g->application_state=app.get(0x6ec);g->presentation=title_activation_globals.return_mode;g->dialog=campaign_dialog_owner;}
 return true;
}
static void natural_return_bindings(){title_session_png=std::make_unique<GameTitlePreviewImages>(*world,common_texture_resources->textures,common_texture_device,title_preview_preload_device);title_session_saved=std::make_unique<GameTitleSavedPreviewImages>(*world,common_texture_resources->textures,common_texture_device,title_preview_preload_device);title_session_page=std::make_unique<TitleScenePageBindings>(TitleScenePageBindings{*title_activation_bindings,title_dialog_recorder,title_ready_sound_host,*title_session_png,*title_session_saved,common_equipment,common_saved_equipment});title_session_cheat=std::make_unique<GameTitleCheatServices>(*common_save,*world,title_platform,common_load_platform,common_saved_equipment,title_scene_session_services.cheat_globals.secondary,AnmView{common_load_audio.data()},game_ascii->view(),common_loaded_save.get());title_scene_session_services.page=title_session_page.get();title_scene_session_services.cheat=title_session_cheat.get();title_scene_session_services.cheat_globals={};
 title_scene_confirm_drawing=std::make_unique<GameMenuApplicationDrawV2>(*common_registered_drawing,frames->scheduler,*common_composition,*common_renderer,common_render_device,static_cast<AnmMenuWorld&>(*world),common_registered_draw_services);
}
#include "campaign-title-notice-services-v62.hpp"
#include "campaign-manual-services-v77.hpp"
struct ResultsManualServices:th143::PauseManualPageHost {
 bool pause_manual_read(u32 p,void* out,u32 n)override{return campaign_manual_services.pause_manual_read(p,out,n);}
 bool pause_manual_write(u32 p,const void* in,u32 n)override{return campaign_manual_services.pause_manual_write(p,in,n);}
 bool pause_manual_call(u32 entry,u32 owner,std::initializer_list<u32> args)override{if(entry==0x484320){const auto a=args.begin();return args.size()==2&&signal_animation(*world,a[0],signed_word(a[1]),false);}return campaign_manual_services.pause_manual_call(entry,owner,args);}
}results_manual_services;
static th143::PauseManualPageHost& campaign_results_manual_host(){return results_manual_services;}

#include "campaign-music-services-v78.hpp"
#include "campaign-option-services-v79.hpp"
#include "campaign-pad-services-v80.hpp"
#include "campaign-input-services-v83.hpp"
#include "campaign-nickname-services-v84.hpp"
#include "campaign-achievement-services-v134-nov14.hpp"
#include "campaign-replay-services-v136-nov14.hpp"
#include "campaign-replay-save-services-v93.hpp"
#include "campaign-failure-subpages-v152.hpp"
static th143::PauseReplayPageHost& campaign_results_replay_host(){return campaign_replay_save_services;}
static bool campaign_finish_shutdown_tail();
#include "campaign-quit-services-v132-nov14.hpp"
#include "campaign-replay-return-services-v96.hpp"
static bool natural_first_callback(u32 entry,u32 owner,u32& result){if(owner==GameTitleRuntime::self&&title_owner&&title_owner->global_owner&&!title_owner->view().get(0x1c)){if(entry==0x45fb30){result=1;return true;}if(entry==0x45fb20){bool handled;if(!title_final_notice_gate_v141(result,handled))return false;if(handled)return true;}}
if(entry==0x468100||entry==0x468110)return campaign_achievement_callback(entry,owner,result);
    if(owner==GameTitleRuntime::self&&entry==0x45fb20&&title_owner->global_owner&&title_owner->view().get(0x1c)==0&&title_activation_globals.return_mode==2)return campaign_replay_return_title(result);
    if(owner==GameTitleRuntime::self&&title_owner->global_owner&&title_owner->view().get(0x1c)==7){if(entry==0x45fb20)return campaign_replay_title(result);if(entry==0x45fb30)return campaign_replay_draw(result);}
    if(entry==0x4472d0)return campaign_nickname_notice(owner,result);
    if(owner==GameTitleRuntime::self&&title_owner->global_owner&&title_owner->view().get(0x1c)==12){if(entry==0x45fb20)return campaign_nickname_title(result);if(entry==0x45fb30)return campaign_nickname_draw(result);}
    if(owner==GameTitleRuntime::self&&title_owner->global_owner&&title_owner->view().get(0x1c)==2&&AnmView{common_renderer->application.data()}.get(0x6ec)!=7){if(entry==0x45fb20)return campaign_quit_title(result);if(entry==0x45fb30){result=1;return true;}}
    if(owner==GameTitleRuntime::self&&title_owner->global_owner&&title_owner->view().get(0x1c)==4){if(entry==0x45fb20)return campaign_pad_title(result);if(entry==0x45fb30){result=1;return true;}}
    if(owner==GameTitleRuntime::self&&title_owner->global_owner&&title_owner->view().get(0x1c)==3){if(entry==0x45fb20)return campaign_option_title(result);if(entry==0x45fb30){result=1;return true;}}
    if(owner==GameTitleRuntime::self&&title_owner->global_owner&&title_owner->view().get(0x1c)==6){if(entry==0x45fb20)return campaign_music_title(result);if(entry==0x45fb30){result=1;return true;}}
    if(owner==GameTitleRuntime::self&&title_owner->global_owner&&title_owner->view().get(0x1c)==5){if(entry==0x45fb20)return campaign_manual_title(result);if(entry==0x45fb30){result=1;return true;}}
    if(campaign_cold_title_active&&owner==GameTitleRuntime::self&&entry==0x45fb20&&title_owner->view().get(0x1c)==11&&title_owner->view().get(0x24)==0){TitleSceneEntryBindings entryBindings{*title_activation_bindings,common_equipment,common_saved_equipment,title_alternate,title_scene_reset,title_scene_worker};return enter_title_scene_page(entryBindings,result);}
    if(owner==GameTitleRuntime::self&&title_owner&&title_owner->global_owner&&title_owner->view().get(0x1c)==11&&entry==0x45fb20){bool handled;if(!campaign_title_notice_gate(result,handled))return false;if(handled)return true;}
    if(owner==GameCheatRuntime::self&&title_owner&&title_owner->global_owner&&title_owner->view().get(0x1c)==11)return title_scene_session_callback(entry,owner,result);
    if(owner==GameTitleRuntime::self&&title_owner&&title_owner->view().get(0x1c)==11)return title_scene_handoff_callback(entry,owner,result);
    if(owner==GameTitleRuntime::self&&title_owner&&title_owner->global_owner==owner){
        auto title=title_owner->view();
        if(entry==0x45fb20&&title.get(0x1c)==1&&title.get(0x24)==5){
            TitleFirstStartBindings b{title,{common_renderer->application.data()},{title_scene_handoff_game.data()},title_scene_handoff_descriptor};if(!advance_title_first_start_body(b,natural_first_host,result))return false;
            if(title.get(0x1c)==2){++natural_first_requests;auto game=AnmView{title_scene_handoff_game.data()};for(u32 i=0;i<4;++i){common_equipment[i]=game.get(0x20+i*4);common_saved_equipment[i]=game.get(0x3c+i*4);}title_activation_globals.startup_flags=game.get(0xc0);title_activation_globals.game_state=game.get(12);}
            auto timer=title.sub(0x2b4);const u32 previous=timer.get(4),token=timer.get(12);float rate=1;if(token&&!world->timer_rate(token,rate))return false;const bool unit=!token||(rate>real(0x3f7d70a4)&&rate<real(0x3f8147ae));const float next=timer.floating(8)+(unit?1.f:rate);timer.put(0,previous);timer.put(8,word(next));timer.put(4,unit?previous+1:next>=-2147483648.f&&next<2147483648.f?u32(i32(next)):0x80000000);natural_first_failed_entry=0;return world->synchronize_resources();
        }
        if(title.get(0x1c)==2&&(entry==0x45fb20||entry==0x45fb30)){result=1;return true;}
    }
    return title_ready_update(entry,owner,result);
}
API(natural_first_prepare) u32 natural_first_prepare(){natural_return_bindings();if(title_owner->view().get(0x1c)!=1||title_owner->view().get(0x24)!=2)return 0;title_scene_handoff_game=natural_initial_game;title_scene_handoff_descriptor=0;natural_first_requests=natural_first_transitions=natural_first_failed_entry=0;title_ready_services.title=title_owner.get();title_ready_services.world=world.get();title_ready_services.keys={};title_ready_services.keys.started_before=common_save->data[0xefb8]!=0;common_pool_extra_update=natural_first_callback;common_registered_extra_draw=natural_first_callback;natural_first_drawing=std::make_unique<GameMenuApplicationDrawV2>(*common_registered_drawing,frames->scheduler,*common_composition,*common_renderer,common_render_device,static_cast<AnmMenuWorld&>(*world),common_registered_draw_services);if(!campaign_recover_earned_achievements())return 0;return 1;}
API(natural_first_frame) u32 natural_first_frame(u32 fresh,u32 repeated){if(!campaign_manual_pump())return 0;if(natural_first_requests)return 1;world->rate=1.f;title_ready_services.keys.fresh=fresh;title_ready_services.keys.repeated=repeated;common_pool_trace.clear();common_registered_drawing->trace.clear();common_render_device.calls.clear();common_render_device.count=common_render_device.triangles=0;if(!frames->dispatch(false,title_intro_update_result))return 0;common_registered_drawing->independent_signals=common_auxiliary->independent.signals;common_registered_drawing->menu_owner=0;i32 result;return natural_first_drawing->dispatch(result)?1:0;}
API(natural_first_status) u32 natural_first_status(u32 i){auto title=title_owner->view(),app=AnmView{common_renderer->application.data()},game=AnmView{title_scene_handoff_game.data()};const u32 v[]={title.get(0x1c),title.get(0x24),title.get(0x2b8),app.get(0x6ec),game.get(0xac),game.get(0xb0),title_scene_handoff_descriptor,game.get(0xc0),common_save->data[0xefb8],natural_first_requests,natural_first_transitions,natural_first_failed_entry,world->error,u32(files.count("scoreth143.dat")),game.get(0x1c),app.get(0x1d0)};return i<16?v[i]:0;}

API(natural_return_diagnostic) u32 natural_return_diagnostic(u32 i){auto title=title_owner->view();auto save=common_save->view();switch(i){
 case 0:return title_activation_globals.return_mode;case 1:return common_texture_application_globals.presentation;case 2:return title_root_load_words[0x4daf58];case 3:return save.get(0xf16c);case 4:return save.data[0xefb8];case 5:return save.get(0x314+0x40);case 6:return title.get(0x1c);case 7:return title.get(0x24);case 8:return title.get(0x2b8);case 9:return title.get(0xe000);case 10:return title_live_preview_task.phase;case 11:return title_root_messages.size();case 12:return save.get(0xf084);case 13:return title_root_game.game_state[10];case 14:return title_root_game.game_state[11];case 15:return title_root_game.scene;case 16:return title_root_globals.root;case 17:return title_owner->global_owner;case 18:return campaign_preview_files.files.size();case 19:return campaign_preview_files.reads;case 20:return campaign_preview_files.hits;case 21:return campaign_preview_files.commits;case 22:return campaign_preview_files.last_read_bytes;case 23:return day1_notice_globals.owner;case 24:return day1_notice_failure;case 25:return day1_notice_pending_worker;case 26:{auto s=day1_notice_view();return s.data?s.get(0x120):0;}case 27:{auto s=day1_notice_view();return s.data?s.get(0x118):0;}default:return 0;}}

API(campaign_preview_file_count) u32 campaign_preview_file_count(){return campaign_preview_files.files.size();}
API(campaign_preview_file_bytes) u32 campaign_preview_file_bytes(u32 i){if(i>=campaign_preview_files.files.size())return 0;auto at=campaign_preview_files.files.begin();std::advance(at,i);return at->second.size();}
API(campaign_preview_file_data) const u8* campaign_preview_file_data(u32 i){if(i>=campaign_preview_files.files.size())return nullptr;auto at=campaign_preview_files.files.begin();std::advance(at,i);return at->second.data();}
API(campaign_preview_file_name) const char* campaign_preview_file_name(u32 i){if(i>=campaign_preview_files.files.size())return nullptr;auto at=campaign_preview_files.files.begin();std::advance(at,i);return at->first.c_str();}

API(campaign_preview_pixel_bytes) u32 campaign_preview_pixel_bytes(u32 decoded){return decoded?campaign_preview_decoded_pixels.size():campaign_preview_input_pixels.size();}
API(campaign_preview_pixel_data) const u8* campaign_preview_pixel_data(u32 decoded){return decoded?campaign_preview_decoded_pixels.data():campaign_preview_input_pixels.data();}

API(campaign_score_file_bytes) u32 campaign_score_file_bytes(){return campaign_score_file.committed.size();}
API(campaign_score_file_data) const u8* campaign_score_file_data(){return campaign_score_file.committed.data();}
API(campaign_score_file_generation) u32 campaign_score_file_generation(){return campaign_score_file.generation;}
// Import closed file bytes; SaveData::load owns original invalid-header/default behavior.
API(campaign_restore_score_file) u32 campaign_restore_score_file(const u8* p,u32 n){if(n>0x1000000||(!p&&n))return 0;auto& file=files["scoreth143.dat"];if(n)file.assign(p,p+n);else file.clear();campaign_score_file.committed=file;return 1;}
API(campaign_restore_preview_file) u32 campaign_restore_preview_file(const char* name,u32 nn,const u8* p,u32 n){const std::string key(name,nn);if(nn!=20||key.rfind("savedata/sc",0)!=0||key.substr(16)!=".dat"||n>0x4000000||(!p&&n))return 0;auto& bytes=campaign_preview_files.files[key];if(n)bytes.assign(p,p+n);else bytes.clear();return 1;}
API(campaign_persistence_field) u32 campaign_persistence_field(u32 i){auto s=common_save->view();const u32 v[]={s.data[0xefb8],s.get(0x354),s.get(0xf084),s.data[0xefac],s.data[0xefad],s.get(0xf16c),common_equipment[0],common_equipment[1],common_equipment[2],common_equipment[3],common_saved_equipment[0],common_saved_equipment[1],common_saved_equipment[2],common_saved_equipment[3],u32(files.count("scoreth143.dat")),u32(campaign_preview_files.files.size()),campaign_score_file.generation};return i<17?v[i]:0;}

API(campaign_cold_title_prepare) u32 campaign_cold_title_prepare(u32 initial_reset){if(!title_owner->global_owner||title_owner->view().get(0x1c)!=1||title_owner->view().get(0x24)!=2)return 0;campaign_cold_title_active=true;title_scene_reset=initial_reset;title_device.data.fill(0);initialize_device_bindings(title_device);return 1;}
API(campaign_cold_title_frame) i32 campaign_cold_title_frame(const u8* keys){
 if(!campaign_cold_title_active)return -600;if(!day1_notice_resume())return -540;
 title_live_preview_frame++;if(campaign_preview_running){const i32 r=title_live_preview_task.resume(*title_owner,*world,{common_renderer->application.data()},title_live_preview_host);if(r<0)return -520;}
 std::memcpy(title_device_host.keys.data(),keys,256);title_device_host.keyboard=1;title_device_host.joystick=1;u32 held;if(!poll_device_input_v2(title_device,true,AnmView{common_renderer->application.data()}.get(0x724),campaign_input_platform(),held))return -300;
 auto d=title_device.view();title_scene_session_services.keys={d.get(12),d.get(8),common_save->data[0xefb8]!=0};if(!natural_first_frame(d.get(12),d.get(8)))return -601;
 u32 result;if(!campaign_pump_audio(result))return -602;return 1;
}

API(campaign_title_input_prepare) u32 campaign_title_input_prepare(u32 initial_reset){return campaign_cold_title_prepare(initial_reset);}
API(campaign_title_input_frame) i32 campaign_title_input_frame(const u8* keys){return campaign_cold_title_frame(keys);}

#include "campaign-replay-playback-services-v92.hpp"
static bool campaign_finish_cleared_replay(){return campaign_replay_playback.end_manager_replay();}

#include "campaign-replay-repeat-trace-v95.hpp"
#include "../src/WindowMessageDispatch.hpp"
#include "../src/ApplicationShutdown.hpp"
#include "campaign-window-close-services-v99.hpp"

static bool campaign_scene_menu_recording_destroy(u32 token){return campaign_replay_services.replay_worker_destroy(token);}
static bool campaign_scene_menu_recording_free(u32 token){return campaign_replay_services.replay_worker_free(token);}

static std::uint64_t campaign_discarded_preview_trace_bytes=0,campaign_discarded_title_trace_bytes=0;
static u32 campaign_title_trace_fences=0;
API(campaign_storage_fence) u32 campaign_storage_fence(){
    if(!campaign_reclaim_world||campaign_reclaim_world!=world.get()||!campaign_reclaim_world->retire_consumed_storage())return 0;
    // The browser has consumed this frame; these are diagnostic snapshots,
    // never worker inputs or pending rendering/audio requests.
    campaign_discarded_preview_trace_bytes+=title_live_preview_yields.size();
    title_live_preview_yields.clear();
    // These buffers are independent observations, not the score-file writer,
    // worker queues, texture requests, or their callback results.
    campaign_discarded_title_trace_bytes+=title_io_events.size()+title_launch.size()+title_dialog_calls.size()+title_preview_preloads.size();
    for(const auto& write:title_save_writes)campaign_discarded_title_trace_bytes+=write.size();
    title_io_events.clear();title_launch.clear();title_dialog_calls.clear();title_preview_preloads.clear();title_save_writes.clear();
    ++campaign_title_trace_fences;return 1;
}
API(campaign_preview_trace_diagnostic) u32 campaign_preview_trace_diagnostic(u32 field){switch(field){case 0:return title_live_preview_yields.size();case 1:return title_live_preview_yields.capacity();case 2:return u32(campaign_discarded_preview_trace_bytes);case 3:return u32(campaign_discarded_preview_trace_bytes>>32);default:return 0;}}
API(campaign_storage_diagnostic) u32 campaign_storage_diagnostic(u32 field){return campaign_reclaim_world&&campaign_reclaim_world==world.get()?campaign_reclaim_world->storage_diagnostic(field):0;}

API(campaign_title_trace_diagnostic) u32 campaign_title_trace_diagnostic(u32 field){switch(field){
case 0:return title_io_events.size();case 1:return title_io_events.capacity();case 2:return title_launch.size();case 3:return title_dialog_calls.size();case 4:return title_preview_preloads.size();case 5:return title_save_writes.size();case 6:return u32(campaign_discarded_title_trace_bytes);case 7:return u32(campaign_discarded_title_trace_bytes>>32);case 8:return campaign_title_trace_fences;default:return 0;}}
