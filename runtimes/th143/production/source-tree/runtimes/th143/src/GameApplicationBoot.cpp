#include "GameApplicationBoot.hpp"
namespace th143 {
bool GameApplicationBoot::version(){
    version_result=-1;u32 opened;if(!host.open_application_archive("th143.dat",opened))return false;
    if(!(opened&255))return host.application_boot_error(true);
    u32 token=0,bytes=0;if(!host.read_application_version("th143_0100a.ver",token,bytes))return false;
    auto app=AnmView{render.application.data()};app.put(0xa14,token);app.put(0xa10,bytes);
    if(!token)return host.application_boot_error(false);version_result=0;return true;
}
bool GameApplicationBoot::initialize(const FontFamilyNames& names,i32& result){
    if(!version())return false;world.rate=1.f;auto app=AnmView{render.application.data()};app.put(0xa30,0xff000000);
    if(!initialize_application_cameras(app,{world.width,world.height,app.get(0x20c),world.viewport.scale},world.viewport.second_origin))return false;
    u32 ticks;if(!host.application_boot_ticks(ticks))return false;app.put(0x728,ticks);gameplay.seed=u16(ticks);world.animation_rng.seed=u16(ticks);
    u32 id;if(!audio.data||!host.launch_application_audio(0x4721f0,0x53b1e0,0,id,audio_thread))return false;audio.put(0x5790,audio_thread);
    u32 timing_owner;if(!timing.create(timing_owner))return false;
    i32 mesh_result;if(!initialize_anm_static_mesh(0x72000000,render.static_scratch,memory,mesh_device,mesh_result))return false;
    fonts.animation=world.animation_rng;if(!initialize_fonts(fonts,names,*this))return false;publish_font_rng();
    if(!targets.construct())return false;temporary_shots=temporary_stage=0;result=0;return true;
}
}
