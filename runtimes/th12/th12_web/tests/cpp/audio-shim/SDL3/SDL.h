#pragma once
// Deterministic device boundary for tests of the production PCM mixer.
// No hardware output or queued playback is claimed by this fixture.
#include <cstdint>
struct SDL_AudioStream {};
struct SDL_AudioSpec {int format,channels,freq;};
constexpr int SDL_AUDIO_F32=1,SDL_INIT_AUDIO=1,SDL_AUDIO_DEVICE_DEFAULT_PLAYBACK=1;
#define SDL_HINT_AUDIO_DEVICE_SAMPLE_FRAMES "sample-frames"
inline bool SDL_SetHint(const char*,const char*){return true;}
inline bool SDL_InitSubSystem(int){return true;}
inline SDL_AudioStream* SDL_OpenAudioDeviceStream(int,const SDL_AudioSpec*,void*,void*){static SDL_AudioStream s;return &s;}
inline void SDL_DestroyAudioStream(SDL_AudioStream*){}
inline bool SDL_ResumeAudioStreamDevice(SDL_AudioStream*){return true;}
inline bool SDL_PauseAudioStreamDevice(SDL_AudioStream*){return true;}
inline int SDL_GetAudioStreamQueued(SDL_AudioStream*){return 0;}
inline bool SDL_PutAudioStreamData(SDL_AudioStream*,const void*,int){return true;}
inline const char* SDL_GetError(){return "SDL test boundary";}
