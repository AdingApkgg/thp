#pragma once
#include "AudioControlMainPump.hpp"
#include "MusicPlaybackRelocate.hpp"
namespace th143 {
struct AudioTrackMainPumpHost:AudioControlMainPumpHost,MusicPlaybackRelocateHost {
    virtual bool sound_voice_call(u32 buffer,u32 method,const u32* args,u32 count,u32& result)override=0;
    virtual bool music_track_table(u32 token,const u8*& data,u32& bytes)=0;
};
// Extends the frozen control-domain main pump with original command9 lookup,
// position/metadata handoff, relocation, compaction and following SFX dispatch.
bool pump_audio_track_main(AnmView audio,u32 bytes,u8 music_enabled,u8 sound_enabled,
                           AudioTrackMainPumpHost&,u32& result);
}
