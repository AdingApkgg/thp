#pragma once
#include "ApplicationCameras.hpp"
#include "GameApplicationTargets.hpp"
#include "GameFrameTimingRuntime.hpp"
#include "GameRenderRuntime.hpp"
#include "FontInitialize.hpp"
namespace th143 {
struct GameApplicationBootHost {
    virtual ~GameApplicationBootHost()=default;
    virtual bool open_application_archive(const char*,u32& result)=0;
    // A successful service call may return a null pointer for a missing file.
    virtual bool read_application_version(const char*,u32& token,u32& bytes)=0;
    virtual bool application_boot_error(bool archive_missing)=0;
    virtual bool application_boot_ticks(u32&)=0;
    virtual bool launch_application_audio(u32 entry,u32 argument,u32 flags,u32& id,u32& handle)=0;
};
// Actual4437f0/4438a0 startup, after the caller has supplied its device,
// Scheduler and ANM pool. Audio thread execution belongs to the host.
class GameApplicationBoot final:private FontInitializeHost {
public:
    GameApplicationBoot(GameRenderRuntime& render,GameApplicationTargets& targets,
        GameFrameTimingRuntime& timing,AnmResourceWorld& world,Rng& gameplay,AnmView audio,
        AnmRenderMemory& memory,AnmStaticMeshDevice& mesh_device,
        GameApplicationBootHost& host,FontInitializeHost& font_host):render(render),targets(targets),
        timing(timing),world(world),gameplay(gameplay),audio(audio),memory(memory),mesh_device(mesh_device),host(host),font_host(font_host){}
    FontInitializeState fonts;
    u32 audio_thread=0,temporary_shots=0,temporary_stage=0;
    i32 version_result=0;
    bool initialize(const FontFamilyNames&,i32& result);
private:
    GameRenderRuntime& render;GameApplicationTargets& targets;GameFrameTimingRuntime& timing;
    AnmResourceWorld& world;Rng& gameplay;AnmView audio;AnmRenderMemory& memory;AnmStaticMeshDevice& mesh_device;
    GameApplicationBootHost& host;FontInitializeHost& font_host;
    bool version();
    void publish_font_rng(){world.animation_rng=fonts.animation;}
    bool font_screen_dc(u32& p)override{publish_font_rng();return font_host.font_screen_dc(p);}
    bool enumerate_font_families(u32 p,const std::array<u8,60>& q,std::vector<std::array<u8,124>>& r)override{publish_font_rng();return font_host.enumerate_font_families(p,q,r);}
    bool release_font_screen_dc(u32 p)override{publish_font_rng();return font_host.release_font_screen_dc(p);}
    bool initialize_font_bitmap(u32 f,u32& r)override{publish_font_rng();return font_host.initialize_font_bitmap(f,r);}
    bool create_initialized_font(const TextFont& f,u32& p)override{publish_font_rng();return font_host.create_initialized_font(f,p);}
};
}
