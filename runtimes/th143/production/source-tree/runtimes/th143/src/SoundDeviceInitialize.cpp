#include "SoundDeviceInitialize.hpp"
namespace th143 {
bool initialize_sound_device(AnmView audio,u32 bytes,const u8* catalog,u32 catalog_bytes,const u32* filenames,u32 filename_count,u32 window,u32 format_token,SoundDeviceInitializeHost& host,u32& result){
    if(!filenames||!prepare_sound_catalog(audio,bytes,catalog,catalog_bytes,0x4e1280))return false;
    u32 wrapper_token=0;if(!host.allocate_sound_wrapper(4,wrapper_token))return false;AnmView wrapper{nullptr};if(!host.sound_initialize_region(wrapper_token,4,wrapper)||!wrapper.data)return false;wrapper.put(0,0);audio.put(12,wrapper_token);
    auto failure=[&](){if(!host.log_sound_initialize(0x4c8fec,0))return false;const u32 current=audio.get(12);if(current){AnmView w{nullptr};if(!host.sound_initialize_region(current,4,w)||!w.data)return false;if(const u32 device=w.get(0)){u32 ignored=0;if(!host.release_sound_device(device,ignored))return false;w.put(0,0);}if(!host.free_sound_wrapper(current))return false;audio.put(12,0);}result=0xffffffff;return true;};
    u32 device=wrapper.get(0),hr=0;if(!host.create_sound_device(wrapper_token,device,hr))return false;wrapper.put(0,device);if(signed_word(hr)<0)return failure();
    if(!host.cooperative_sound_device(wrapper.get(0),window,2,hr))return false;if(signed_word(hr)<0)return failure();
    if(!configure_primary_sound_format(wrapper,4,host,hr))return false;
    //The primary-format HRESULT is deliberately ignored by471f10.
    AnmView current_wrapper{nullptr};if(!host.sound_initialize_region(audio.get(12),4,current_wrapper)||!current_wrapper.data)return false;audio.put(0,current_wrapper.get(0));audio.put(0x14,0);
    u8 descriptor[36]={};AnmView desc{descriptor};desc.put(0,36);desc.put(4,0x8008);desc.put(8,0x8000);desc.put(16,format_token);const u8 format[18]={1,0,2,0,0x44,0xac,0,0,0x10,0xb1,2,0,4,0,16,0,0,0};
    if(!host.create_silent_sound_buffer(audio.get(0),descriptor,format,audio,hr))return false;if(signed_word(hr)<0){result=0xffffffff;return true;}
    SoundDeviceLock lock;if(!host.lock_silent_sound_buffer(audio.get(4),lock,hr))return false;if(signed_word(hr)<0){result=0xffffffff;return true;}
    //The original clears32768 bytes through the first pointer, independently
    //of the lengths returned by Lock; callers must provide that writable span.
    if(!host.zero_silent_sound_bytes(lock.first,0x8000)||!host.unlock_silent_sound_buffer(audio.get(4),lock,hr)||!host.play_silent_sound_buffer(audio.get(4),hr))return false;
    audio.put(0x57a4,100);audio.put(0x57a8,100);if(!host.install_sound_timer(window,0,250,0))return false;audio.put(8,window);
    for(u32 i=0;i<88;++i){u32 abort=0;if(!host.sound_initialize_abort(abort))return false;if(abort==2){result=0xffffffff;return true;}if(catalog_bytes<i*20+8)return false;u32 file=0;std::memcpy(&file,catalog+i*20+4,4);if(file>=filename_count)return false;if(!host.initialize_device_voice(i,audio.sub(0x1a84+i*24),filenames[file],hr))return false;if(hr){if(!host.log_sound_initialize(0x4c901c,filenames[file]))return false;result=0xffffffff;return true;}}
    if(!host.log_sound_initialize(0x4c9054,0))return false;result=0;return true;
}
}
