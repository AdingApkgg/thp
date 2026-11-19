#include "AnmRenderState.hpp"
namespace th143 {
bool configure_anm_render(u32 p,u32 current,AnmView vm,AnmRenderMemory& memory,AnmSpriteDevice& device){
    if(!vm.data)return false;
    auto change=[&](u32 at,u8 value,bool& changed){u8 old;if(!memory.read_render_memory(p+at,&old,1))return false;changed=old!=value;if(!changed)return true;return flush_anm_quads(p,current,memory,device)&&memory.write_render_memory(p+at,&value,1);};
    bool changed;const u32 blend=(vm.get(0x18)>>5)&15;
    if(!change(0xbc819c,u8(blend),changed))return false;
    if(changed){if(!device.render_state(0xf,1))return false;
        if(blend<10){static constexpr u32 source[10]={5,5,5,2,10,9,4,7,5,5},destination[10]={6,2,2,1,4,1,6,8,2,2},operation[10]={1,1,3,1,1,1,1,1,4,5};
            if(blend==3&&!device.render_state(0xf,0))return false;
            if(!device.render_state(0x13,source[blend])||!device.render_state(0x14,destination[blend])||!device.render_state(0xab,operation[blend]))return false;
        }
    }
    const u8 filtering=u8((vm.get(0x1c)>>10)&1);
    if(!change(0xbc81a2,filtering,changed))return false;if(changed&&(!device.sampler_state(0,5,filtering?1:2)||!device.sampler_state(0,6,filtering?1:2)))return false;
    for(u32 i=0;i<2;++i){const u8 address=u8(i?(vm.get(0x18)>>30):(vm.get(0x1c)&3));if(!change(0xbc81a4+i,address,changed))return false;
        if(changed&&address<3){static constexpr u32 values[3]={1,3,2};if(!device.sampler_state(0,1+i,values[address]))return false;}
    }
    u32 calls;if(!memory.read_render_memory(p+0xc8,&calls,4))return false;++calls;return memory.write_render_memory(p+0xc8,&calls,4);
}
}
