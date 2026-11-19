#include "SoundVoiceStart.hpp"
namespace th143 {
bool start_sound_voice(AnmView voice,AnmView descriptor,u32 pan,u32 volume,SoundVoiceStartHost& h,u32& result){
 const u32 buffer=voice.get(0);if(!buffer)return true;if(!descriptor.data)return false;
 const u32 zero=0;if(!h.sound_voice_call(buffer,0x48,nullptr,0,result)||!h.sound_voice_call(buffer,0x34,&zero,1,result)||!h.sound_voice_call(buffer,0x40,&pan,1,result))return false;
 voice.put(0x10,pan);u32 attenuation=0xffffd8f0;
 if(volume){float normalized=float(signed_word(volume));normalized/=100.f;float curve=1.f-normalized;float cubic=curve*curve;cubic*=curve;curve=1.f-cubic;const i32 base=i32(std::int16_t(descriptor.get(8)))+5000;curve*=float(base);const u32 value=curve>=-2147483648.f&&curve<2147483648.f?u32(i32(curve)):0x80000000u;attenuation=value-5000;}
 if(!h.sound_voice_call(buffer,0x3c,&attenuation,1,result))return false;
 const u32 play[]={0,0,descriptor.get(12)};return h.sound_voice_call(buffer,0x30,play,3,result);
}
}
