#include "th14-audio-mixer-fixture.cpp"
#define MA_NO_DEVICE_IO
#define MA_NO_RESOURCE_MANAGER
#define MA_NO_MP3
#define MA_NO_ENCODING
#define MA_NO_THREADING
#include "../../../portable/sdl/third_party/miniaudio.h"
#include "../../cpp/game/MusicCatalog.hpp"
static ma_decoder direct;
static bool direct_ready=false;
API(direct_open) i32 direct_open(i32 cue){
    if(direct_ready)ma_decoder_uninit(&direct);direct_ready=false;
    for(const auto& t:music_tracks)if(t.cue==cue){const auto path=std::string("/music/")+t.file+".flac";auto config=ma_decoder_config_init(ma_format_f32,2,44100);direct_ready=ma_decoder_init_file(path.c_str(),&config,&direct)==MA_SUCCESS;return direct_ready;}
    return 0;
}
API(direct_mix) const float* direct_mix(u32 frames){static float samples[2048];ma_uint64 read=0;return direct_ready&&frames<=1024&&ma_decoder_read_pcm_frames(&direct,samples,frames,&read)==MA_SUCCESS&&read==frames?samples:nullptr;}
