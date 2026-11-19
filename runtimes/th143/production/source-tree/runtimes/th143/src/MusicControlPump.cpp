#include "MusicControlPump.hpp"
namespace th143 {
bool pump_music_control(AnmView audio,u32 bytes,u8 enabled,MusicControlPumpHost& host,bool& reached_sfx,u32& scratch){
    reached_sfx=false;scratch=0;if(!audio.data||bytes<0x57b0)return false;
    if(!audio.get(12))return true;
    const u32 command=audio.get(0x24f8);if(command<5||command>8)return false;
    u32 cursor=0x24f8;const u32 token=audio.get(0x5778);bool compact=true;
    if(command==5){
        if(token){AnmView object{nullptr};u32 available=0;if(!host.music_control_object(token,object,available)||!object.data||available<0xa0)return false;
            float scaled=float(signed_word(audio.get(cursor+4)));scaled*=60.f;
            const u32 duration=scaled>=-2147483648.f&&scaled<2147483648.f?u32(i32(scaled)):0x80000000u;
            object.put(0x1c,1);object.put(0x14,duration);object.put(0x18,duration);
        }
    }else if(command==6||command==7){
        if(enabled==1){AnmView object{nullptr};u32 available=0;if(!token||!host.music_control_object(token,object,available)||!object.data||available<0xa0)return false;
            if(object.get(0x9c))compact=false;
            else if(!host.music_control_call(command==6?0x486570:0x486600,token,nullptr,0))return false;
        }
    }else if(token){const u32 zero=0;if(!host.music_control_call(0x486470,token,&zero,1))return false;}
    if(compact)for(u32 copied=0;copied<31&&audio.get(cursor);++copied){std::memcpy(audio.data+cursor,audio.data+cursor+0x10c,0x10c);cursor+=0x10c;}
    scratch=0x53b1e0+cursor;reached_sfx=true;return true;
}
}
