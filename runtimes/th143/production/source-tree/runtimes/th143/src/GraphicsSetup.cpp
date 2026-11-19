#include "GraphicsSetup.hpp"
#include <array>
namespace th143 {
bool initialize_graphics(u32 manager,AnmRenderMemory& memory,AnmSpriteDevice& device){
    constexpr std::array<std::array<u32,2>,21> states{{{7,1},{137,0},{22,1},{27,1},{206,0},{9,2},{19,5},{20,6},{23,8},{171,1},{15,1},{24,1},{25,7},{28,1},{38,0x3f800000},{35,0},{140,3},{34,0xffa0a0a0},{36,0x447a0000},{37,0x459c4000},{161,0}}};
    for(auto p:states)if(!device.render_state(p[0],p[1]))return false;
    constexpr std::array<std::array<u32,2>,8> stages{{{4,4},{5,2},{6,3},{1,4},{2,2},{3,3},{24,2},{11,0}}};
    for(auto p:stages)if(!device.texture_stage_state(0,p[0],p[1]))return false;
    constexpr std::array<std::array<u32,2>,6> samplers{{{7,0},{5,2},{6,2},{3,3},{1,1},{2,1}}};
    for(auto p:samplers)if(!device.sampler_state(0,p[0],p[1]))return false;
    if(manager){const u16 format=0xff0a;const u8 invalid=255;const u32 zero=0;if(!memory.write_render_memory(manager+0xbc819c,&format,2)||!memory.write_render_memory(manager+0xbc819e,&invalid,1)||!memory.write_render_memory(manager+0xbc8198,&zero,4)||!memory.write_render_memory(manager+0xbc81a0,&invalid,1))return false;}
    return true;
}
}
