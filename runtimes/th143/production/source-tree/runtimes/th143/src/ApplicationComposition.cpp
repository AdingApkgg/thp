#include "ApplicationComposition.hpp"
#include <cmath>
namespace th143 {
namespace {
i32 truncated(float value){if(!std::isfinite(value)||double(value)>=2147483648.||double(value)<-2147483648.)return i32(0x80000000u);return i32(value);}
}
bool compose_application(AnmView app,u32 self,u32 manager,ApplicationCompositionPass pass,
    ApplicationCompositionGlobals& globals,AnmRenderMemory& memory,AnmRenderDevice& render,
    ApplicationFrameDevice& device,ApplicationCompositionServices& host){
    if(!app.data)return false;
    const auto flush=[&](){return manager&&flush_anm_quads(manager,manager,memory,render);};
    const auto state=[&](u32 kind,u32 value){return host.composition_render_state(app.get(8),kind,value);};
    const auto marker=[&](u32 offset){const u32 value=0xffffffff;return memory.write_render_memory(app.get(offset)+0x534,&value,4);};
    if(pass!=ApplicationCompositionPass::Backbuffer&&!app.get(0x1ac))return true;
    if(pass==ApplicationCompositionPass::Backbuffer){
        ApplicationClear clear;clear.color=0xff000000;
        return flush()&&device.application_render_target(app.get(8),0,app.get(0x1b4))&&device.clear_application(app.get(8),clear);
    }
    if(pass==ApplicationCompositionPass::SecondaryTarget||pass==ApplicationCompositionPass::MainTarget||pass==ApplicationCompositionPass::InterfaceTarget){
        const u32 target=pass==ApplicationCompositionPass::MainTarget?0x1ac:0x1b0;
        if(!flush()||!device.application_render_target(app.get(8),0,app.get(target)))return false;
        const u32 viewport=pass==ApplicationCompositionPass::InterfaceTarget?0x43c:0x694;
        ApplicationClear clear;clear.rectangle_count=1;clear.flags=2;clear.color=app.get(0xa30);
        clear.rectangle={i32(app.get(viewport)),i32(app.get(viewport+4)),i32(app.get(viewport)+app.get(viewport+8)),i32(app.get(viewport+4)+app.get(viewport+12))};
        if(!device.clear_application(app.get(8),clear))return false;
        if(pass==ApplicationCompositionPass::InterfaceTarget){globals.logical_width=u32(truncated(globals.scale*384.f));globals.logical_height=u32(truncated(globals.scale*448.f));}
        return true;
    }
    if(pass==ApplicationCompositionPass::First&&globals.first_callback)return host.invoke_composition_callback(globals.first_callback);
    if(pass==ApplicationCompositionPass::Second&&globals.second_callback)return host.invoke_composition_callback(globals.second_callback);
    const bool fourth=pass==ApplicationCompositionPass::Fourth;
    if(!fourth&&!state(171,1))return false;
    if(!state(15,0))return false;
    if(!fourth&&app.get(0xa04)){if(!flush())return false;app.put(0xa04,0);if(!state(14,0))return false;}
    const bool primary=pass==ApplicationCompositionPass::First||pass==ApplicationCompositionPass::Second;
    if(primary){
        app.put(0x6e0,self+0x5b4);
        if(!flush()||!device.application_transform(app.get(8),2,app.data+0x614)||!device.application_transform(app.get(8),3,app.data+0x654))return false;
        const u32 x=app.get(0x6b0),y=app.get(0x6b4);
        if(!memory.write_render_memory(manager+0xd0,&x,4)||!memory.write_render_memory(manager+0xd4,&y,4)||!device.application_viewport(app.get(8),app.data+0x694))return false;
        app.put(0x6e4,3);
    }
    const u32 animation=pass==ApplicationCompositionPass::First?0x1bc:pass==ApplicationCompositionPass::Second?0x1c0:pass==ApplicationCompositionPass::Third?0x1c4:0x1c8;
    if(!host.draw_composition_animation(manager,app.get(animation)))return false;
    if(pass==ApplicationCompositionPass::Third){if(!flush()||!marker(animation))return false;}
    else {
        if(!marker(animation))return false;
        if(pass==ApplicationCompositionPass::First&&!host.draw_composition_layer(manager,33))return false;
        if(!flush())return false;
    }
    return state(15,1);
}
}
