#pragma once
#include <cstdint>
#include <cstring>
namespace th11 {
// Explicit data for the reference Win32 call stack. These are virtual ABI
// addresses, not pointers into Wasm memory or values derived from game RNG.
struct NativeStackTh14 {
    using Word=std::uint32_t;
    static constexpr Word reference_geometry_frame=0x001b0000u-0x137cu;
    // Standalone hosts get the CRT's normalized fallback input. The Web host
    // supplies an independent process nonce before the first game callback.
    Word cookie=0xbb40e64fu,frame=reference_geometry_frame,scratch=0;
    static bool preinitialized_cookie(Word value)noexcept{return value!=0xbb40e64eu&&(value&0xffff0000u);}
    void configure(Word opaque_cookie,Word geometry_frame=reference_geometry_frame)noexcept{
        cookie=opaque_cookie;frame=geometry_frame;scratch=0;
    }
    void beam_effect_published(Word handle)noexcept{scratch=handle;}
    void rectangle_intersection_y(float y)noexcept{std::memcpy(&scratch,&y,4);}
    // The pinned reference dsound.dll pushes STRSAFE_MAX_CCH at+25bab.
    void reference_pan_call()noexcept{scratch=0x7ffffffeu;}
    void geometry_mode1_call()noexcept{scratch=cookie^frame;}
    static Word fallback_bits(Word bits)noexcept{
        // 45286f..4528a6: addss8; comiss0; store; jbe; optional zero.
        // Explicitly retain the quieted NaN payload across Wasm engines.
        if((bits&0x7f800000u)==0x7f800000u&&(bits&0x007fffffu))return bits|0x00400000u;
        float value;std::memcpy(&value,&bits,4);value=value+8.f;
        if(0.f>value)value=0.f;
        std::memcpy(&bits,&value,4);return bits;
    }
};
}
