#include "StageActivation.hpp"

namespace th143 {
bool activate_stage(StageState& state,StageAnimationMemory& memory,AnmVmHost& animations){
    auto s=state.view();
    for(u32 offset:{8,12,0x4268}){u32 flags;const u32 p=s.get(offset)+4;
        if(!memory.read_stage_animation_memory(p,&flags,4))return false;flags|=2;if(!memory.write_stage_animation_memory(p,&flags,4))return false;
    }
    std::int16_t objects;if(!memory.read_stage_animation_memory(s.get(0x10),&objects,2))return false;
    u32 index=0;
    for(i32 i=0;i<objects;++i){u32 object;if(!memory.read_stage_animation_memory(s.get(0x14)+u32(i)*4,&object,4))return false;
        const u8 enabled=1;if(!memory.write_stage_animation_memory(object+3,&enabled,1))return false;
        u32 primitive=object+0x1c;
        for(u32 budget=0;budget<32768;++budget){std::int16_t kind,length,script;
            if(!memory.read_stage_animation_memory(primitive,&kind,2))return false;if(kind<0)break;
            if(!memory.read_stage_animation_memory(primitive+2,&length,2)||!memory.read_stage_animation_memory(primitive+4,&script,2)||length<8||index>=32768)return false;
            const u32 self=s.get(0x208)+index*AnmView::bytes;auto vm=memory.stage_animation_storage(self),source=memory.stage_animation_template(s.get(0x204),script);
            if(!vm.data||!source.data)return false;anm_copy_template(vm,self,source,animations.global_rate_token());vm.put(0x594,0);
            if(anm_step(vm,animations)==-2)return false;
            const u16 animation=u16(index);if(!memory.write_stage_animation_memory(primitive+6,&animation,2))return false;
            primitive+=u32(length);++index;if(budget==32767)return false;
        }
    }s.put(0x4c,s.get(0x1c));return true;
}
bool advance_stage_animations(StageState& state,StageAnimationMemory& memory,AnmVmHost& animations){
    auto s=state.view();std::int16_t objects;
    if(!memory.read_stage_animation_memory(s.get(0x10),&objects,2))return false;
    for(i32 i=0;i<objects;++i){u32 object;u8 flags;
        if(!memory.read_stage_animation_memory(s.get(0x14)+u32(i)*4,&object,4)||!memory.read_stage_animation_memory(object+3,&flags,1))return false;
        if(!(flags&1))continue;u32 live=0,primitive=object+0x1c;
        for(u32 budget=0;budget<32768;++budget){std::int16_t kind,length,index;
            if(!memory.read_stage_animation_memory(primitive,&kind,2))return false;if(kind<0)break;
            if(!memory.read_stage_animation_memory(primitive+2,&length,2)||!memory.read_stage_animation_memory(primitive+6,&index,2)||length<8||index<0)return false;
            auto vm=memory.stage_animation_storage(s.get(0x208)+u32(index)*AnmView::bytes);if(!vm.data||anm_step(vm,animations)==-2)return false;
            if(vm.get(0x28))++live;primitive+=u32(length);if(budget==32767)return false;
        }
        if(!live){flags&=~1u;if(!memory.write_stage_animation_memory(object+3,&flags,1))return false;}
    }return true;
}
}
