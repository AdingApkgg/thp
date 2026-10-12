#include "th14-dialogue-portrait-geometry-fixture.cpp"
API(begin_panel_geometry) i32 begin_panel_geometry(i32 slot,float rate,float width,i32 immediate){
 portrait_renderer.invalidate();portrait_graphics.state={};portrait_graphics.handle=0;portrait_graphics.valid=true;portrait_graphics.quads.clear();portrait_graphics.materials.clear();portrait_renderer.viewport={0,0,640,480,0,1};portrait_renderer.offset={0,0};portrait_renderer.tint_enabled=false;
 if(!begin_family(slot,rate,immediate)||vms.size()!=4)return 0;
 for(u32 i=0;i<vms.size();++i)lifecycle_ids[i]=vms[i]->id;
 vms[1]->floats[0]=vms[3]->floats[0]=width;capture_lifecycle();capture_sprite();return 1;
}
