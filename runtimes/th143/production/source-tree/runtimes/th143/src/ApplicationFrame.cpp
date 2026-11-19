#include "ApplicationFrame.hpp"
#include <cmath>
namespace th143 {
namespace {
i32 truncated(float value){if(!std::isfinite(value)||double(value)>=2147483648.||double(value)<-2147483648.)return i32(0x80000000u);return i32(value);}
}
bool begin_application_frame(AnmView app,u32 self,u32 manager,ApplicationFrameGlobals& g,AnmRenderMemory& memory,AnmRenderDevice& render,ApplicationFrameDevice& device){
    if(!app.data||!manager)return false;ApplicationClear clear;clear.color=g.clear_color;
    if(g.render_target){clear.color=0xffffffff;if(!device.clear_application(g.device,clear)||!device.application_render_target(g.device,0,g.render_target))return false;
        clear.rectangle_count=1;clear.color=g.clear_color;clear.rectangle={i32(g.stage_viewport[0]),i32(g.stage_viewport[1]),i32(g.stage_viewport[0]+g.stage_viewport[2]),i32(g.stage_viewport[1]+g.stage_viewport[3])};
        if(!device.clear_application(g.device,clear))return false;g.logical_width=384;g.logical_height=448;g.first_origin[0]=i32(g.width)/2;g.first_origin[1]=truncated(float(i32(g.height))-448.f)/2;
    }else if(!device.clear_application(g.device,clear))return false;
    auto put=[&](u32 offset,u32 value){return memory.write_render_memory(manager+offset,&value,4);};auto half=[&](u32 offset,u16 value){return memory.write_render_memory(manager+offset,&value,2);};
    if(!put(0xbc81a8,0)||!put(0xbc8198,0)||!half(0xbc819c,0xff0a)||!half(0xbc819f,0xffff)||!put(0xff75a8,0)||!put(0xff75a4,0x80808080)||!half(0xbc81a2,0xffff)||!put(0xd4,0)||!put(0xd0,0))return false;
    const u8 kind=255;if(!memory.write_render_memory(manager+0xbc819e,&kind,1))return false;app.put(0x6e0,self+0x488);
    if(!flush_anm_quads(manager,manager,memory,render)||!device.application_transform(g.device,2,app.data+0x4e8)||!device.application_transform(g.device,3,app.data+0x528)||!put(0xd0,app.get(0x584))||!put(0xd4,app.get(0x588)))return false;
    if(!device.application_viewport(app.get(8),app.data+0x568))return false;app.put(0x6e4,2);return true;
}
}
