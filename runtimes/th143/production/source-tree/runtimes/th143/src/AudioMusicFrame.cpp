#include "AudioMusicFrame.hpp"
namespace th143 {
struct AudioMusicFrameHost final:MusicFrameHost {
    AnmView audio,globals;MusicFrameHost& parent;
    AudioMusicFrameHost(AnmView a,AnmView g,MusicFrameHost& p):audio(a),globals(g),parent(p){}
    void refresh(){globals.put(0,audio.get(0x5778));globals.put(4,audio.get(0x57a4));}
    bool music_frame_region(u32 token,u32 bytes,AnmView& out)override{return parent.music_frame_region(token,bytes,out);}
    bool sound_voice_call(u32 token,u32 method,const u32* args,u32 count,u32& hr)override{if(!parent.sound_voice_call(token,method,args,count,hr))return false;refresh();return true;}
};
bool update_audio_music_frame(AnmView audio,u32 bytes,MusicFrameHost& parent,u32& result){
    if(!audio.data||bytes<0x57b0)return false;u8 logical[8];AudioMusicFrameHost host{audio,{logical},parent};host.refresh();if(!update_music_frame({logical},8,host))return false;result=0;return true;
}
}
