#include "SoundWaveChunk.hpp"
#include <cstring>
namespace th143 {
bool find_sound_wave_chunk(const u8* data,u32 mapped_bytes,const u8* tag,
                          u32 remaining,u32& chunk_bytes,u32& payload_offset){
    payload_offset=0;u32 offset=0;
    while(remaining){
        if(!data||!tag||offset>mapped_bytes||mapped_bytes-offset<8)return false;
        std::memcpy(&chunk_bytes,data+offset+4,4);
        if(!std::memcmp(data+offset,tag,4)){payload_offset=offset+8;return true;}
        // The original does not round odd chunk sizes to a RIFF word boundary,
        // and its remaining counter is unsigned. Preserve both operations.
        const u32 step=chunk_bytes+8;
        if(step>0xffffffffu-offset)return false;
        offset+=step;remaining-=step;
    }
    return true;
}
}
