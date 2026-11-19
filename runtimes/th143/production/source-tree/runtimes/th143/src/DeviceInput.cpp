#include "DeviceInput.hpp"
namespace th143 {
void initialize_device_bindings(DeviceInputState& state){auto s=state.view();s.put(0x234,0x10000);s.put(0x238,0x50002);const u16 invalid=0xffff,three=3;std::memcpy(s.data+0x246,&three,2);for(u32 at:{0x244u,0x23cu,0x23eu,0x240u,0x242u})std::memcpy(s.data+at,&invalid,2);}
void advance_device_buttons(DeviceInputState& state){
    auto s=state.view();u32 held=s.get(0),bit=1;s.put(8,0);s.put(0x22c,0);
    for(u32 i=0;i<32;++i,held>>=1,bit<<=1){const u32 at=0x14+i*4;if(held&1){s.put(at,s.get(at)+1);s.put(at+0x100,s.get(at+0x100)+1);if(s.get(at)>=8)s.put(0x22c,s.get(0x22c)|bit);if(s.get(at)>=26){s.put(8,s.get(8)|bit);s.put(at,s.get(at)-8);}}else{s.put(at,0);s.put(at+0x100,0);}}
    held=s.get(0);const u32 changed=s.get(4)^held;s.put(12,changed&held);s.put(16,changed&~held);
}
namespace {
u32 keyboard_bits(const std::array<u8,256>& k,bool direct){
    // The two raw OS layouts use the same shift/OR sequence, including C's
    // two output bits and the four combined numpad direction masks.
    const std::array<u8,25> win{0x79,0x52,0x44,0x0d,0x24,0x50,0x53,0x51,0x43,0x11,0x1b,0x58,0x5a,0x10,0x26,0x68,0x28,0x62,0x25,0x64,0x27,0x66,0x63,0x69,0x61};
    const std::array<u8,25> dik{0x44,0x13,0x20,0x1c,0x19,0xc7,0x1f,0x10,0x2e,0x1d,0x01,0x2d,0x2c,0x2a,0x48,0xc8,0x50,0xd0,0x4b,0xcb,0x4d,0xcd,0x51,0x49,0x4f};
    const auto& keys=direct?dik:win;auto high=[&](u32 i){return u32(k[keys[i]]&0x80);};auto pair=[&](u32 a,u32 b){return u32((k[keys[a]]|k[keys[b]])&0x80);};
    u32 s=high(0)<<2;s|=high(1);s=(s<<1)|high(2);s=(s<<1)|high(3);s=(s<<1)|pair(4,5);s=(s<<1)|high(6);s=(s<<1)|high(7);s=(s<<5)|high(8);s=(s<<2)|high(9)|high(8);s=(s<<1)|high(10);s<<=1;
    u32 d=(high(11)|(u32(k[keys[12]])>>1))>>2;d=(d|high(13))>>1;d=(d|pair(14,15))>>1;d=(d|pair(16,17))>>1;d=(d|pair(18,19))>>1;s|=d|pair(20,21);
    if(high(22))s|=0xa0;if(high(23))s|=0x90;if(high(24))s|=0x60;const u8 diagonal=direct?0x47:0x67;if(k[diagonal]&0x80)s|=0x50;return s;
}
}
bool poll_device_keyboard(DeviceInputState& state,bool enabled,u32 config,DeviceInputHost& host,u32& held){
    if(config&0x800)return false;held=0;
    if(enabled){std::array<u8,256> keys;u32 status;if(!host.keyboard_state((config&0x400)!=0,keys,status))return false;if((config&0x400)&&status){if(!host.acquire_keyboard(status))return false;}else held=keyboard_bits(keys,(config&0x400)!=0);}
    u32 joystick_error;if(!host.missing_winmm_joystick(joystick_error)||!joystick_error)return false;
    auto s=state.view();s.put(4,s.get(0));s.put(0,held);advance_device_buttons(state);return true;
}
}
