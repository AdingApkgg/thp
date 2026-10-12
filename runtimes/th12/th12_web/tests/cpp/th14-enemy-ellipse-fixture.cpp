#include "th14-enemy-orbit-fixture.cpp"
API(ellipse_value) u32 ellipse_value(u32 index,u32 n){
    const auto& v=index?enemy.relative_ellipse:enemy.absolute_ellipse;
    if(n<8){u32 word;std::memcpy(&word,reinterpret_cast<const u8*>(&v)+4*n,4);return word;}
    const u32 words[]={u32(v.timer.previous),u32(v.timer.current),float_bits(v.timer.fractional),v.timer.rate?1u:0u,v.timer.flags,u32(v.duration),u32(v.mode)};
    return words[n-8];
}
