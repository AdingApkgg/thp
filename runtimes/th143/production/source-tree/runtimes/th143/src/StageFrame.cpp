#include "StageFrame.hpp"
#include "AnmRsqrtTable.hpp"
#include <cmath>

namespace th143 {
namespace {
bool normalize(const std::array<float,3>& input,std::array<float,3>& output){
    float length=input[0]*input[0];length+=input[1]*input[1];length+=input[2]*input[2];
    if(!std::isfinite(length))return false;if(length<real(0x28800000)){output={0,0,0};return true;}
    // Pinned reference-CPU D3DX RSQRTSS estimate, followed by its float
    // Newton refinement. The estimate table has a separate hardware gate.
    const u32 bits=word(length);const i32 power=i32(bits>>23)-127;
    const u32 index=((bits&0x7fffff)|((u32(power)&1)<<23))>>12;
    const i32 exponent=power<0?(power-1)/2:power/2;
    const float estimate=real((0x3f000000u+(u32(anm_rsqrt_estimates[index])<<11))-(u32(exponent)<<23));
    float refine=estimate*length;refine*=estimate;const float half=estimate*.5f;refine=3.f-refine;refine*=half;
    for(u32 i=0;i<3;++i)output[i]=input[i]*refine;return true;
}
}
i32 advance_stage_frame(StageState& state,u32 self,StageScriptGlobals& globals,StageAnimationMemory& memory,AnmVmHost& animations,StageFrameServices& services){
    auto s=state.view();const u32 flags=s.get(0x4224);
    if((flags&8)||((flags&4)&&signed_word(s.get(0x422c))>=60))return 1;
    for(u32 at:{0x4370,0x4374,0x4378,0x437c,0x4380})s.put(at,0);
    std::array<float,3> target,direction;for(u32 i=0;i<3;++i)target[i]=s.floating(0x42bc+i*4)+s.floating(0x4280+i*4);
    if(!normalize(target,direction))return -2;for(u32 i=0;i<3;++i)s.put(0x4298+i*4,word(direction[i]));s.put(0x3094,0x808080);
    if(!(flags&4)||signed_word(s.get(0x422c))<30){
        if(!advance_stage_animations(state,memory,animations)||!advance_stage_script(state,self,globals,memory,animations))return -2;
        if(s.get(0x3098)){float old;if(!services.set_stage_animation_rate(1.f,old))return -2;
            bool ok=true;for(u32 i=0;i<3&&ok;++i)ok=anm_step(s.sub(0x30b4+i*AnmView::bytes),animations)!=-2;
            float ignored;if(!services.set_stage_animation_rate(old,ignored)||!ok)return -2;
        }
    }s.put(0x3098,0);
    if(!memory.write_stage_animation_memory(0x4e4d84,state.data.data()+0x4274,0x12c))return -2;
    for(u32 i=0;i<8;++i)if(anm_step(s.sub(0x20c+i*AnmView::bytes),animations)==-2)return -2;
    if(s.get(0x4244)&&!services.update_stage_warp(state))return -2;
    s.put(0x4240,s.get(0x4240)+1);return 1;
}
}
