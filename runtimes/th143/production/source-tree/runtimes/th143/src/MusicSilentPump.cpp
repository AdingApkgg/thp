#include "MusicSilentPump.hpp"
namespace th143 {
bool pump_silent_music_owner(AnmView audio,bool streamed,bool playback,u8 music_enabled,u8 sound_enabled,u32& result){
    if(!audio.data)return false;result=0;if(!audio.get(12))return true;if(playback||audio.get(0x5778)||sound_enabled)return false;constexpr u32 queue=0x24f8,stride=0x10c;const u32 kind=audio.get(queue);if(kind<1||kind>9){result=kind;return true;}
    if(kind==9||(kind==1&&streamed)||((kind==6||kind==7)&&music_enabled==1)||audio.get(queue+31*stride))return false;
    if(kind==1){const u32 slot=audio.get(queue+4);if(slot>=16)return false;u32 n=0;while(n<256&&audio.data[queue+12+n])++n;if(n==256)return false;std::memcpy(audio.data+0x4678+slot*256,audio.data+queue+12,n+1);}
    // Native advances EDI while shifting; kind1's retry starts at the empty
    // tail, rather than consuming the new queue head in the same pump.
    for(u32 i=0;i<31&&audio.get(queue+i*stride);++i)std::memmove(audio.data+queue+i*stride,audio.data+queue+(i+1)*stride,stride);
    result=audio.get(queue);return true;
}
}
