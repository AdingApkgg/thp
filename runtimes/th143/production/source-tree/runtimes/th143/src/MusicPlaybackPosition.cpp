#include "MusicPlaybackPosition.hpp"
#include <cmath>
namespace th143 {
static double read_double(AnmView v,u32 at){double d;std::memcpy(&d,v.data+at,8);return d;}
static u32 read_half(AnmView v,u32 at){std::uint16_t n;std::memcpy(&n,v.data+at,2);return n;}
bool music_playback_position(AnmView object,u32 bytes,AnmView meta,u32 metadata_bytes,double clock,double& position){
    if(!object.data||bytes<0xa0||!meta.data||metadata_bytes<0x34)return false;
    double elapsed=read_double(object,0x40);elapsed+=read_double(object,0x30);elapsed=clock-elapsed;
    const u32 raw_rate=meta.get(0x24);double rate=double(signed_word(raw_rate));rate+=(raw_rate>>31)?4294967296.:0.;
    const double bits=double(read_half(meta,0x2e)),channels=double(read_half(meta,0x22));
    double end=double(signed_word(meta.get(0x1c)));const double bytes_rate=rate*0.125;end/=bytes_rate;end/=bits;end/=channels;
    double cycle=double(signed_word(meta.get(0x1c)-meta.get(0x18)));cycle/=rate;const double bytes_per_sample=bits*0.125;cycle/=bytes_per_sample;cycle/=channels;
    if(!std::isfinite(elapsed)||!std::isfinite(end)||!std::isfinite(cycle)||end<=0.||cycle<=0.)return false;
    // Defined finite service domain; do not silently hang on malformed metadata.
    u32 steps=0;while(elapsed>=end){if(steps++==1000000)return false;elapsed-=cycle;}
    position=elapsed;return true;
}
}
