#include "th14-music-restore-fixture.cpp"
#include <cstring>
API(stop_all) void stop_all(){for(u32 n=1;n<=sound_voice_count;++n)audio.sound_stop(n);audio.effects.reset();audio.music(-1);}
API(sound_start) void sound_start(i32 id,float x){audio.effects.positioned(id,x);audio.update();}
API(sound_frames) u32 sound_frames(u32 id){
    std::vector<u8> wav;if(id>=sound_voice_count||!source.read(sound_samples[sound_definitions[id].sample],wav))return 0;
    const auto word=[&](u32 p){u32 v;std::memcpy(&v,wav.data()+p,4);return v;};
    const auto short_word=[&](u32 p){u16 v;std::memcpy(&v,wav.data()+p,2);return v;};
    u32 rate=0,align=0,bytes=0;
    for(u32 p=12;p+8<=wav.size();){const u32 size=word(p+4);if(p+8+u64(size)>wav.size())return 0;
        if(std::memcmp(wav.data()+p,"fmt ",4)==0&&size>=16){rate=word(p+12);align=short_word(p+20);}
        if(std::memcmp(wav.data()+p,"data",4)==0)bytes=size;
        p+=8+size+(size&1);
    }
    return rate&&align?u32((u64(bytes/align)*44100+rate-1)/rate):0;
}
API(sound_flags) u32 sound_flags(u32 id){return sound_definitions[id].play_flags;}
API(fade) void fade(i32 frames){audio.fade_music(frames);}
API(update) void update(){audio.update();}
API(master) void master(i32 level){audio.music_volume=level;audio.refresh_volume();}
