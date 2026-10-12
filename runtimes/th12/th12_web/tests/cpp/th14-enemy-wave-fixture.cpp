#include "th14-enemy-movement-fixture.cpp"
API(wave_initialize) void wave_initialize(const u32* words){
    std::memcpy(&enemy.th14_absolute_wave,words,16);std::memcpy(&enemy.th14_relative_wave,words+4,16);
}
API(wave_value) u32 wave_value(u32 n){u32 word;const auto& v=n<4?enemy.th14_absolute_wave:enemy.th14_relative_wave;std::memcpy(&word,reinterpret_cast<const u8*>(&v)+4*(n%4),4);return word;}

API(movement_modes) void movement_modes(u32 absolute,u32 relative){enemy.absolute.flags=absolute;enemy.relative.flags=relative;}
