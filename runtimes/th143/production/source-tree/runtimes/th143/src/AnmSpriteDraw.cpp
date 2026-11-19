#include "AnmSpriteDraw.hpp"
#include "AnmMeshDraw.hpp"
#include "AnmBillboard.hpp"
#include "AnmStripDraw.hpp"
#include "AnmRectDraw.hpp"
namespace th143 {
i32 draw_anm_sprite(u32 manager,u32 current,AnmView vm,AnmView camera,AnmQuad& scratch,const AnmViewport& viewport,u32& depth_test,AnmRenderMemory& memory,AnmSpriteDevice& device,AnmSpriteDrawHost& host,u32 rounding){
    if(!vm.data)return -2;if(vm.get(0x5bc)&&!host.draw_callback(vm.get(0x5bc),vm))return -2;
    const u32 flags=vm.get(0x18);if(!(flags&1)||!(flags&2)||(vm.get(0x1c)&0x20))return -1;
    // 444990 uses the current manager and shares the stage depth-test global.
    if(depth_test){if(!flush_anm_quads(current,current,memory,device))return -2;depth_test=0;if(!device.render_state(0xe,0))return -2;}
    const u32 mode=(vm.get(0x18)>>25)&31;if(mode==10||mode==23||mode>25)return 0;
    if(mode<=8&&!vm.data[0x537]&&!vm.data[0x53b])return -1;
    if(mode==24||mode==25){auto* mesh=host.mesh_device();auto* upload=host.primitive_device();return mesh&&upload?draw_anm_strip(manager,current,vm,vm.get(0x5b4),vm.get(0x4ac)*2,viewport,depth_test,memory,device,*mesh,*upload):-2;}
    if(mode==16||mode==20||mode==21||mode==22){auto* upload=host.primitive_device();return upload?draw_anm_rect_sprite(manager,current,vm,viewport,depth_test,memory,device,*upload,host):-2;}
    if(mode==8){auto* mesh=host.mesh_device();return mesh?draw_anm_mesh(manager,current,vm,viewport,depth_test,memory,device,*mesh,host):-2;}
    if(mode==4||mode==6)return draw_anm_billboard(manager,current,vm,camera,scratch,mode==6,host.physical_width(),host.physical_height(),memory,device);
    if(mode>3)return -2;
    const bool built=(mode==1||mode==3)?anm_rotated_quad_position(vm,viewport,host,scratch):anm_quad_position(vm,viewport,host,scratch);
    if(!built||!submit_anm_quad(manager,current,vm,camera,scratch,mode==0?1:0,memory,device,rounding))return -2;return 0;
}
}
