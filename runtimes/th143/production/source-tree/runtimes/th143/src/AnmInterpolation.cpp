#include "AnmInterpolation.hpp"
#include <cmath>

namespace th143 {
namespace {
u32 truncate(float v) {
    return v >= -2147483648.f && v < 2147483648.f ? u32(i32(v)) : 0x80000000;
}
float power(float v, u32 n) { float r = v; while (--n) r *= v; return r; }
bool advance(AnmView t, AnmTimerHost& host) {
    float rate = 1.f;
    const u32 pointer = t.get(12), current = t.get(4);
    if (pointer && !host.timer_rate(pointer, rate)) return false;
    t.put(0, current);
    if (pointer && !(rate > real(0x3f7d70a4) && rate < real(0x3f8147ae))) {
        const float fraction = t.floating(8) + rate;
        t.put(4, truncate(fraction)); t.put(8, word(fraction));
    } else {
        t.put(4, current + 1); t.put(8, word(t.floating(8) + 1.f));
    }
    return true;
}
void finish(AnmView t, u32 duration, AnmTimerHost& host) {
    if (!(t.get(16) & 1)) { t.put(12, host.global_rate_token()); t.put(16, t.get(16) | 1); }
    t.put(0, duration - 1); t.put(4, duration); t.put(8, word(float(signed_word(duration))));
}
struct Hermite { float start, target, from, to; };
Hermite hermite(float elapsed, float duration) {
    const float t = elapsed / duration;
    const float a = t - 1.f;
    const float b = t * 2.f;
    const float c = 1.f - t;
    return {(a * a) * (b + 1.f), (3.f - b) * (t * t), (c * c) * t, (a * t) * t};
}
}
bool anm_easing(i32 mode, float elapsed, float duration, float& result) {
    // UCOMISS+LAHF treats zero (including -0) as the immediate-one case.
    if (duration == 0.f) { result = 1.f; return true; }
    float t = elapsed / duration;
    if (mode >= 1 && mode <= 3) result = power(t, u32(mode + 1));
    else if (mode >= 4 && mode <= 6) result = 1.f - power(1.f - t, u32(mode - 2));
    else if (mode >= 9 && mode <= 11) {
        t *= 2.f;
        result = t < 1.f ? power(t, u32(mode - 7)) * .5f : (2.f - power(2.f - t, u32(mode - 7))) * .5f;
    } else if (mode >= 12 && mode <= 14) {
        t *= 2.f;
        result = t < 1.f ? .5f - power(1.f - t, u32(mode - 10)) * .5f : power(t - 1.f, u32(mode - 10)) * .5f + .5f;
    } else if (mode == 15) result = 0.f;
    else if (mode == 16) result = 1.f;
    else if (mode >= 18 && mode <= 21) {
        const float pi = real(0x40490fdb), half_pi = real(0x3fc90fdb);
        const auto sine = [](float phase) { return float(std::sin(double(phase))); };
        if (mode == 18 || mode == 19) {
            t *= pi; t *= .5f;
            if (mode == 19) { t += half_pi; result = 1.f - sine(t); }
            else result = sine(t);
        } else {
            t *= 2.f;
            const bool first = t < 1.f;
            if (mode == 20) {
                t *= pi; t *= .5f;
                result = first ? sine(t) * .5f : (1.f - sine(t)) * .5f + .5f;
            } else if (first) {
                t *= pi; t *= .5f; t += half_pi; result = (1.f - sine(t)) * .5f;
            } else { t -= 1.f; t *= pi; t *= .5f; result = .5f + sine(t) * .5f; }
        }
    }
    else if (mode >= 22 && mode <= 31) {
        constexpr u32 constants[5][4] = {
            {0x3e800000, 0x3f100000, 0x3de38e39, 0x3f638e39},
            {0x3e99999a, 0x3efae147, 0x3e3c14e7, 0x3f50fac6},
            {0x3eb33333, 0x3ed851ea, 0x3e947320, 0x3f35c670},
            {0x3ec28f5c, 0x3ec4d014, 0x3ec0553e, 0x3f1fd561},
            {0x3ecccccd, 0x3eb851ec, 0x3ee38e39, 0x3f0e38e4},
        };
        const auto& c = constants[(mode - 22) % 5];
        float v = mode >= 27 ? 1.f - t : t;
        v -= real(c[0]); v *= v; v /= real(c[1]); v -= real(c[2]); v /= real(c[3]);
        result = mode >= 27 ? 1.f - v : v;
    } else result = t;
    return true;
}
bool anm_interpolate_integer(AnmView s, AnmTimerHost& host, u32& result) {
    i32 duration = signed_word(s.get(0x28));
    const i32 mode = signed_word(s.get(0x2c));
    if (duration > 0) {
        if (!advance(s.sub(0x14), host)) return false;
        if (signed_word(s.get(0x18)) >= duration) {
            finish(s.sub(0x14), u32(duration), host); s.put(0x28, 0); duration = 0;
        }
    }
    if (!duration) { result = s.get(mode == 7 || mode == 17 ? 0 : 4); return true; }
    if (mode == 7) result = s.get(0) + s.get(4), s.put(0, result);
    else if (mode == 17) {
        result = s.get(0) + s.get(12); s.put(0, result); s.put(12, s.get(4) + s.get(12));
    } else if (mode == 8) {
        const auto h = hermite(s.floating(0x1c), float(duration));
        // Integer and vector native specializations add the first two terms in opposite order.
        float value = h.target * float(signed_word(s.get(4))) + h.start * float(signed_word(s.get(0)));
        value += h.from * float(signed_word(s.get(8))); value += h.to * float(signed_word(s.get(12)));
        result = truncate(value);
    } else {
        float fraction;
        if (!anm_easing(mode, s.floating(0x1c), float(duration), fraction)) return false;
        float value = fraction * float(signed_word(s.get(4) - s.get(0)));
        value += float(signed_word(s.get(0))); result = truncate(value);
    }
    s.put(0x10, result); return true;
}
bool anm_interpolate_vec2(AnmView s, AnmTimerHost& host, std::array<u32, 2>& result) {
    i32 duration = signed_word(s.get(0x3c));
    const i32 mode = signed_word(s.get(0x40));
    if (duration > 0) {
        if (!advance(s.sub(0x28), host)) return false;
        if (signed_word(s.get(0x2c)) >= duration) {
            finish(s.sub(0x28), u32(duration), host); s.put(0x3c, 0); duration = 0;
        }
    }
    if (!duration) {
        const u32 at = mode == 7 || mode == 17 ? 0 : 8;
        result = {s.get(at), s.get(at + 4)}; return true;
    }
    float fraction = 0.f;
    Hermite h{};
    if (mode == 8) h = hermite(s.floating(0x30), float(duration));
    else if (mode != 7 && mode != 17 && !anm_easing(mode, s.floating(0x30), float(duration), fraction)) return false;
    for (u32 i = 0; i != 2; ++i) {
        const u32 at = i * 4;
        float value;
        if (mode == 7 || mode == 17) {
            value = s.floating(at + (mode == 7 ? 8 : 0x18)) + s.floating(at);
            s.put(at, word(value));
            if (mode == 17) s.put(at + 0x18, word(s.floating(at + 8) + s.floating(at + 0x18)));
        } else if (mode == 8) {
            value = s.floating(at) * h.start + s.floating(at + 8) * h.target;
            value += s.floating(at + 0x10) * h.from; value += s.floating(at + 0x18) * h.to;
        } else value = s.floating(at) + (s.floating(at + 8) - s.floating(at)) * fraction;
        result[i] = word(value); s.put(0x20 + at, result[i]);
    }
    return true;
}
bool anm_interpolate_vec3(AnmView s, AnmTimerHost& host, bool integer, std::array<u32,3>& result) {
    i32 duration=signed_word(s.get(0x50)), mode=signed_word(s.get(0x54));
    if(duration>0){
        if(!advance(s.sub(0x3c),host))return false;
        if(signed_word(s.get(0x40))>=duration){finish(s.sub(0x3c),u32(duration),host);s.put(0x50,0);duration=0;}
    }
    if(!duration){for(u32 i=0;i<3;++i)result[i]=s.get(i*4+((mode==7||mode==17)?0:12));return true;}
    float fraction=0;Hermite h{};
    if(mode==8)h=hermite(s.floating(0x44),float(duration));
    else if(mode!=7&&mode!=17&&!anm_easing(mode,s.floating(0x44),float(duration),fraction))return false;
    for(u32 i=0;i<3;++i){
        const u32 at=i*4;
        if(integer){
            u32 value;
            if(mode==7||mode==17){value=s.get(at)+s.get(at+(mode==7?12:36));s.put(at,value);if(mode==17)s.put(at+36,s.get(at+12)+s.get(at+36));}
            else if(mode==8){
                value=truncate(float(signed_word(s.get(at)))*h.start)+truncate(float(signed_word(s.get(at+12)))*h.target);
                value+=truncate(float(signed_word(s.get(at+24)))*h.from);value+=truncate(float(signed_word(s.get(at+36)))*h.to);
            }else value=s.get(at)+truncate(float(signed_word(s.get(at+12)-s.get(at)))*fraction);
            result[i]=value;
        }else{
            float value;
            if(mode==7||mode==17){value=s.floating(at+(mode==7?12:36))+s.floating(at);s.put(at,word(value));if(mode==17)s.put(at+36,word(s.floating(at+36)+s.floating(at+12)));}
            else if(mode==8){value=s.floating(at)*h.start+s.floating(at+12)*h.target;value+=s.floating(at+24)*h.from;value+=s.floating(at+36)*h.to;}
            else value=s.floating(at)+(s.floating(at+12)-s.floating(at))*fraction;
            result[i]=word(value);
        }
        s.put(0x30+at,result[i]);
    }
    return true;
}
bool anm_interpolate(AnmView s, AnmTimerHost& host) {
    for (const u32 at : {0x1fcu, 0x380u, 0x3b0u}) if (s.get(at)) return false;
    for(const u32 at : {0x9cu,0xf4u,0x17cu,0x2d0u}){
        if(!s.get(at+0x50))continue;
        const bool integer=at==0xf4||at==0x2d0;
        std::array<u32,3> value;
        if(!anm_interpolate_vec3(s.sub(at),host,integer,value))return false;
        const u32 target=at==0x9c?((s.get(0x18)&0x400)?0x4ec:0x3c):at==0x17c?0x48:at==0xf4?0x534:0x538;
        for(u32 i=0;i<3;++i){if(integer)s.data[target+i]=u8(value[i]);else s.put(target+i*4,value[i]);}
        if(at==0x17c)s.put(0x18,s.get(0x18)|4);
    }
    if (s.get(0x174)) {
        u32 alpha;
        if (!anm_interpolate_integer(s.sub(0x14c), host, alpha)) return false;
        s.data[0x537] = u8(alpha);
    }
    for (const u32 at : {0x204u, 0x248u, 0x28cu}) {
        if (!s.get(at + 0x3c)) continue;
        std::array<u32, 2> scale;
        if (!anm_interpolate_vec2(s.sub(at), host, scale)) return false;
        const u32 target = at == 0x204 ? 0x60 : at == 0x248 ? 0x68 : 0x78;
        s.put(target, scale[0]); s.put(target + 4, scale[1]); s.put(0x18, s.get(0x18) | (at == 0x28c ? 0x10 : 8));
    }
    if (s.get(0x350)) {
        u32 alpha;
        if (!anm_interpolate_integer(s.sub(0x328), host, alpha)) return false;
        s.data[0x53b] = u8(alpha);
    }
    return true;
}
}
