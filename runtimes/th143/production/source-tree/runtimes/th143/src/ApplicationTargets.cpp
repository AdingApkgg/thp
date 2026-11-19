#include "ApplicationTargets.hpp"
namespace th143 {
bool initialize_application_targets(AnmView app,ApplicationTargetGlobals& g,AnmRenderMemory& memory,ApplicationTargetServices& host){
    if(!app.data)return false;
    const auto read=[&](u32 p,u32& value){return memory.read_render_memory(p,&value,4);};
    const auto surface=[&](u32 resource,u32 entry,u32& out){u32 table,texture;return read(resource+0x124,table)&&read(table+entry*24,texture)&&host.target_surface(texture,out);};
    if(!app.get(0x1ac)){
        u32 token;
        if(!app.get(0x1b4)){token=app.get(0x1b4);if(!host.target_backbuffer(app.get(8),token))return false;app.put(0x1b4,token);}
        token=app.get(0x1ac);if(!surface(app.get(0x71c),1,token))return false;app.put(0x1ac,token);
        token=app.get(0x1b0);if(!surface(app.get(0x71c),2,token))return false;app.put(0x1b0,token);
        auto first=host.target_animation(app.get(0x1bc));if(!first.data)return false;
        if(!(first.get(0x18)&1)){
            const i32 offset=g.width==640?0:g.width==960?1:g.width==1280?2:-1;
            if(offset>=0)for(u32 i=0;i<4;++i){
                const u32 vm=app.get(0x1bc+i*4);const i32 script=std::array<i32,4>{52,65,55,68}[i]+offset;
                if(!host.copy_target_template(app.get(0x71c),script,vm))return false;
                auto state=host.target_animation(vm);if(!state.data)return false;state.put(0x594,0);
                if(!host.advance_target_animation(vm))return false;
            }
        }
        if(g.scale==1.5f){auto vm=host.target_animation(app.get(0x1c4));if(!vm.data)return false;vm.put(0x1c,vm.get(0x1c)&~0x400u);}
    }else std::memcpy(app.data+0x5b4,app.data+0x230,300);
    if(g.auxiliary){u32 resource,surface_token;
        if(!read(g.auxiliary+0x10,resource))return false;
        if(resource){if(!read(g.auxiliary+0x14,surface_token)||!surface(resource,0,surface_token)||!memory.write_render_memory(g.auxiliary+0x14,&surface_token,4))return false;}
    }
    return true;
}
bool release_application_targets(AnmView app,ApplicationTargetGlobals& g,AnmRenderMemory& memory,ApplicationTargetServices& host){
    if(!app.data)return false;
    for(u32 offset:{0x1acu,0x1b0u,0x1b4u}){const u32 token=app.get(offset);if(token){if(!host.release_target_surface(token))return false;app.put(offset,0);}}
    app.put(0x1ac,0);
    if(g.auxiliary){u32 token,flags;if(!memory.read_render_memory(g.auxiliary+0x14,&token,4))return false;
        if(token){if(!host.release_target_surface(token))return false;token=0;if(!memory.write_render_memory(g.auxiliary+0x14,&token,4))return false;}
        if(!memory.read_render_memory(g.auxiliary+0x18,&flags,4))return false;flags&=~4u;if(!memory.write_render_memory(g.auxiliary+0x18,&flags,4))return false;
    }return true;
}
}
