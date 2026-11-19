#include "StagePresentation.hpp"
namespace th143 {
bool present_stage_background(StageState& owner,StageCamera& camera,StageDrawGlobals& g,StagePresentationServices& host,bool foreground){
    auto s=owner.view();const u32 flags=s.get(0x4224);if(flags&8)return true;if((flags&4)||signed_word(s.get(0x422c))>0)return false;
    auto state=[&](u32 kind,u32 value){u32& cached=kind==28?g.depth_write:g.depth_test;if(cached==value)return true;if(!host.flush_stage_camera_batch())return false;cached=value;return host.set_stage_render_state(kind,value);};
    auto raw=[&](u32 kind,u32 value){return host.flush_stage_camera_batch()&&host.set_stage_render_state(kind,value);};
    if(!host.flush_stage_camera_batch())return false;s.put(0x4370,camera.view().get(0xfc));s.put(0x4374,camera.view().get(0x100));std::memcpy(camera.data.data(),owner.data.data()+0x4274,300);g.camera_token=0x4e4d84;
    if(!prepare_stage_camera(camera,host)||!host.set_stage_viewport(camera.data.data()+0xe0))return false;g.camera_kind=3;
    if(foreground){if(!state(28,0)||!state(14,0)||!raw(23,8)||!host.draw_animation_layer(31)||!raw(23,4)||!host.draw_animation_layer(32))return false;}
    else if(!state(14,1))return false;
    if(!raw(23,4)||!raw(34,s.get(0x439c))||!raw(36,s.get(0x4384))||!raw(37,s.get(0x4388)))return false;
    if(!foreground){ApplicationClear clear;auto c=camera.view();clear.rectangle_count=1;clear.color=s.get(0x439c);clear.rectangle={i32(c.get(0xe0)),i32(c.get(0xe4)),i32(c.get(0xe0)+c.get(0xe8)),i32(c.get(0xe4)+c.get(0xec))};if(!host.clear_stage_viewport(clear))return false;
        if(s.data[0x3097]){if(!host.set_stage_tint(true,s.get(0x3094)))return false;s.data[0x3097]=0;}s.put(0x4218,0);s.put(0x421c,0);s.put(0x4220,0);
    }
    if(flags&1){if(foreground&&!state(14,0))return false;if(!state(28,1))return false;for(i32 i=foreground?8:0;i<(foreground?12:8);++i)if(!host.draw_background_layer(i))return false;if(!host.flush_stage_camera_batch())return false;if(!foreground&&s.get(0x3090))s.put(0x3090,s.get(0x3090)+1);}
    if(!host.set_stage_tint(false,0x80808080))return false;if(s.get(0x3098)&&!host.set_stage_tint(true,0xff404040))return false;
    if(!state(14,0)||!raw(23,8))return false;return !foreground||state(28,0);
}
}
