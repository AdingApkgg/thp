#include "StageDraw.hpp"
#include <cmath>
namespace th143 {
namespace {
bool state(StageDrawGlobals& g,StageDrawServices& host,u32 kind,u32 value){u32& current=kind==0x1c?g.depth_write:g.depth_test;
    if(current==value)return true;if(!host.flush_stage_camera_batch())return false;current=value;return host.set_stage_render_state(kind,value);
}
bool viewport(StageCamera& camera,StageDrawGlobals& g,StageDrawServices& host){if(!host.set_stage_viewport(camera.data.data()+0xe0))return false;g.camera_kind=3;return true;}
bool install(StageCamera& camera,StageDrawServices& host){if(host.has_animation_manager()&&!host.flush_stage_camera_batch())return false;
    if(!host.set_stage_camera_transform(2,camera.data.data()+0x60)||!host.set_stage_camera_transform(3,camera.data.data()+0xa0))return false;
    return !host.has_animation_manager()||host.set_stage_camera_origin(camera.view().get(0xfc),camera.view().get(0x100));
}
bool inline_animations(StageState& owner,u32 self,i32 layer,StageCamera& camera,StageDrawGlobals& g,StageDrawServices& host){auto s=owner.view();
    for(u32 i=0;i<8;++i){const u32 at=0x20c+i*AnmView::bytes;auto vm=s.sub(at);if(!vm.get(0x2c)||signed_word(s.get(0x306c+i*4))!=layer)continue;
        if(!layer){g.camera_token=0x4e4d84;if(!install(camera,host)||!viewport(camera,g,host)||!state(g,host,0x1c,0)||!host.flush_stage_camera_batch()||!state(g,host,0xe,0))return false;}
        if(vm.get(0x2c)&&!host.submit_stage_animation(self+at,vm))return false;
        if(!layer){if(!state(g,host,0xe,1))return false;g.camera_token=0x4e4d84;if(!prepare_stage_camera(camera,host)||!viewport(camera,g,host))return false;}
    }return true;
}
}
bool draw_stage_layer(StageState& owner,u32 self,i32 layer,StageCamera& camera,StageDrawGlobals& g,StageAnimationMemory& memory,StageDrawServices& host,u32 budget){
    auto s=owner.view();if(!inline_animations(owner,self,layer,camera,g,host)||!host.flush_stage_camera_batch()||!state(g,host,0x1c,1))return false;
    g.camera_token=0x4e4d84;if(!prepare_stage_camera(camera,host)||!viewport(camera,g,host)||!host.set_stage_sprite_mode(1))return false;
    u32 instance=s.get(0x18),steps=0;
    for(;;instance+=16){if(++steps>budget)return false;std::array<u8,16> raw;if(!memory.read_stage_animation_memory(instance,raw.data(),raw.size()))return false;AnmView item{raw.data()};std::int16_t object_index;std::memcpy(&object_index,raw.data(),2);if(object_index<0)break;
        u32 object;if(!memory.read_stage_animation_memory(s.get(0x14)+u32(object_index)*4,&object,4))return false;std::array<u8,28> object_header;if(!memory.read_stage_animation_memory(object,object_header.data(),object_header.size()))return false;
        if(i32(std::int8_t(object_header[2]))!=layer)continue;
        StageVector offset={item.floating(4),item.floating(8),item.floating(12)};const auto visible=stage_object_visibility({object_header.data()},offset,camera,s.floating(0x308c),g.origin_x,g.origin_y);
        u16 instance_flags;std::memcpy(&instance_flags,raw.data()+2,2);
        if(visible.culled){s.put(0x421c,s.get(0x421c)+1);instance_flags&=~u16(1);if(!memory.write_stage_animation_memory(instance+2,&instance_flags,2))return false;continue;}
        object_header[3]|=2;if(!memory.write_stage_animation_memory(object+3,object_header.data()+3,1))return false;
        for(u32 primitive=object+0x1c;;){if(++steps>budget)return false;std::array<u8,28> data;if(!memory.read_stage_animation_memory(primitive,data.data(),8))return false;std::int16_t kind,length,index;std::memcpy(&kind,data.data(),2);if(kind<0)break;std::memcpy(&length,data.data()+2,2);std::memcpy(&index,data.data()+6,2);if(length<8)return false;
            const u32 token=s.get(0x208)+u32(i32(index))*AnmView::bytes;auto vm=memory.stage_animation_storage(token);if(!vm.data)return false;
            if(!kind){if(!memory.read_stage_animation_memory(primitive,data.data(),data.size()))return false;AnmView p{data.data()};u32 flags=vm.get(0x18);
                if((flags&0x3e000000)>=0x08000000){for(u32 i=0;i<3;++i)vm.put(0x59c+i*4,word(p.floating(8+i*4)+offset[i]));
                    for(u32 i=0;i<2;++i){const float value=p.floating(0x14+i*4);if(value!=0||std::isnan(value)){u32 divisor;if(!memory.read_stage_animation_memory(vm.get(0x2c)+(i?0x34:0x38),&divisor,4))return false;flags|=8;vm.put(0x18,flags);vm.put(0x60+i*4,word(value/real(divisor)));}}
                }
                const u32 mode=(vm.get(0x18)>>25)&31;if(!state(g,host,0x1c,mode==8||mode==24)||!state(g,host,0xe,!(vm.get(0x18)&0x2000))||!host.submit_stage_animation(token,vm))return false;s.put(0x4220,s.get(0x4220)+1);
            }primitive+=u32(length);
        }instance_flags|=1;if(!memory.write_stage_animation_memory(instance+2,&instance_flags,2))return false;s.put(0x4218,s.get(0x4218)+1);
    }return state(g,host,0xe,0);
}
}
