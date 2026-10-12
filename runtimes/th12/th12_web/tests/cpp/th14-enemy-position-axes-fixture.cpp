#include "th14-enemy-movement-fixture.cpp"
API(position_initialize) void position_initialize(u32 index,const u32* words,const u32* modes){
    auto& v=index?enemy.relative_position:enemy.absolute_position;
    std::memcpy(&v,words,48);v.timer.previous=i32(words[12]);v.timer.current=i32(words[13]);v.timer.fractional=float_bits(words[14]);v.timer.rate=words[15]?&environment.rate:nullptr;v.timer.flags=words[16];v.duration=i32(words[17]);v.mode=InterpolationMode(words[18]);
    auto& a=index?enemy.th14_relative_position_modes:enemy.th14_absolute_position_modes;std::memcpy(&a,modes,16);
}
API(axis_value) u32 axis_value(u32 index,u32 n){const auto& a=index?enemy.th14_relative_position_modes:enemy.th14_absolute_position_modes;return n<3?u32(a.axis[n]):a.flags;}
