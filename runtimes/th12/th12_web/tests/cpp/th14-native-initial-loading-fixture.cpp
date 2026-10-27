// Additional component observations and actual worker lifecycle entry points.
// This adapter is never compiled into the browser release.
#include "th14-native-title-fixture.cpp"
extern "C" {
EMSCRIPTEN_KEEPALIVE const unsigned* component_initial_loading_state(){
    auto& a=th11::sdl::app;auto& s=a.session;static unsigned words[14];
    words[0]=unsigned(s.state.phase);words[1]=s.state.stage;words[2]=s.battle?s.battle->frame:0;
    words[3]=a.initial_upload_waiting;words[4]=a.initial_decode_complete;
    words[5]=a.boot_worker_work==decltype(a.boot_worker_work)::InitialDecode?1:
        a.boot_worker_work==decltype(a.boot_worker_work)::InitialResume?2:0;
    words[6]=a.boot_upload_index;words[7]=unsigned(a.boot_uploads.size());
    words[8]=words[9]=words[10]=~0u;
    if(a.boot_upload_index<a.boot_uploads.size()){const auto& job=a.boot_uploads[a.boot_upload_index];
        words[8]=job.file;words[9]=job.chunk;words[10]=unsigned(job.resource->textures.size());}
    words[11]=s.battle&&s.battle->player;words[12]=a.boot_stage_owner!=nullptr;words[13]=unsigned(a.boot_worker_generation);
    std::fflush(stdout);return words;
}
EMSCRIPTEN_KEEPALIVE const char* component_initial_last_resource(){return th11::last_resource.c_str();}
EMSCRIPTEN_KEEPALIVE void component_initial_suspend(){th11::sdl::app.suspend_boot_worker();}
EMSCRIPTEN_KEEPALIVE void component_initial_resume(){th11::sdl::app.resume_boot_worker();}
}
