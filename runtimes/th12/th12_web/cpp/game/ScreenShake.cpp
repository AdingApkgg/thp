#include "ScreenShake.hpp"
namespace th11 {
i32 ScreenShake::update(Rng& rng,Vec2& offset,bool stopped) noexcept {
    if(stopped)return 7;
    timer.tick();
    if(phased){
        const i32 middle=wrapping_add(ramp,hold),last=wrapping_add(middle,fall);float fraction=1;
        if(timer.current<ramp)fraction=timer.fractional/float(ramp);
        else if(timer.current>=middle){if(timer.current>=last)return 7;fraction=(float(u32(last))-timer.fractional)/float(u32(fall));}
        const float amplitude=float(start)*fraction;const auto axis=[&](){const u32 choice=rng.next32()%3;return choice==0?0.f:choice==1?amplitude:-amplitude;};
        offset.x=axis();offset.y=axis();return 1;
    }
    if(timer.current>=duration)return 7;
    // Preserve the x87 stores between multiply, divide and integer addition.
    // TH14 46cda0 converts both integers before the SSE multiply/divide/add.
    // Large signed amplitudes distinguish it from the older x87 path.
    const float product=kPortTitle==14||kPortTitle==16?float(float(wrapping_sub(end,start))*timer.fractional):float(double(wrapping_sub(end,start))*timer.fractional);
    const float quotient=kPortTitle==14||kPortTitle==16?float(product/float(duration)):float(double(product)/duration);
    const float amplitude=kPortTitle==14||kPortTitle==16?float(quotient+float(start)):float(double(quotient)+start);
    const auto axis=[&](){const u32 choice=rng.next32()%3;return choice==0?0.f:choice==1?amplitude:-amplitude;};
    offset.x=axis();offset.y=axis();return 1;
}
}
