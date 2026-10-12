#include "../../cpp/sdl/AudioDevice.hpp"
#include <cstdlib>
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static GameResources source;
static sdl::AudioDevice audio;
API(allocate) void* allocate(u32 n){return std::malloc(n);}
API(open_archive) i32 open_archive(const u8* p,u32 n){return source.open_archive(p,n)&&audio.initialize(source);}
API(audio_reset) i32 audio_reset(){audio.close();return audio.initialize(source);}
API(music) i32 music(i32 track){return audio.music(track);}
API(save) i32 save(){return audio.save_music();}
API(restore) i32 restore(){return audio.restore_music();}
API(discard) void discard(){audio.discard_saved_music();}
API(audio_pause) void audio_pause(i32 value){audio.pause_music(value!=0);}
API(mute) void mute(i32 value){audio.music_enabled=!value;audio.refresh_volume();}
API(audio_stat) u32 audio_stat(u32 n){return audio.statistics()[n];}
API(mix) const float* mix(u32 frames){static float samples[2048];return frames<=1024&&audio.mix(samples,frames)?samples:nullptr;}
API(error) const char* error(){return audio.error.c_str();}
