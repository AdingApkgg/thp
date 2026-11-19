#include "AnmEffect0.hpp"
namespace th143 {
namespace {
bool bind(AnmView vm,u32 self,u32 resource,u32 script,AnmResourceWorld& world){auto* r=world.resource(resource);if(!r||script>=r->templates.size())return false;anm_copy_template(vm,self,{r->templates[script].data()},world.global_rate_token());vm.put(0x594,0);return anm_step(vm,static_cast<AnmWorld&>(world))!=-2;}
void position(u8* data){for(u32 i=0;i<4;++i){AnmView vm{data+i*AnmView::bytes};vm.put(0x59c,word(320.f));vm.put(0x5a0,word(240.f));vm.put(0x5a4,0);}}
}
bool initialize_anm_effect0(AnmView root,u8* data,u32 self,u32 resource,AnmResourceWorld& world){if(!root.data||!data)return false;std::memset(data,0,anm_effect0_bytes);root.put(0x5b4,self);root.put(0x24,0);for(u32 i=0;i<4;++i){auto vm=AnmView{data+i*AnmView::bytes};if(!bind(vm,self+i*AnmView::bytes,resource,3+i,world))return false;vm.put(0x59c,word(320.f));vm.put(0x5a0,word(240.f));vm.put(0x5a4,0);}AnmView{data}.put(0x1cfc,0);root.put(0x24,30);position(data);return bind({data+0x1730},self+0x1730,resource,11,world);}
i32 step_anm_effect0(u8* data,AnmVmHost& host){if(!data)return -2;u32 completed=0;for(u32 i=0;i<4;++i){AnmView vm{data+i*AnmView::bytes};if(anm_step(vm,host)==-2)return -2;if(!(vm.get(0x18)&1))++completed;}if(completed==4)return 1;if(anm_step({data+0x1730},host)==-2)return -2;AnmView extra{data};extra.put(0x1d00,extra.get(0x1d00)+1);return 0;}
bool signal_anm_effect0(AnmView root,u8* data,u32 self,u32 resource,i32 signal,AnmResourceWorld& world){if(!root.data||!data)return false;if(signal==1){for(u32 i=0;i<4;++i)if(!bind({data+i*AnmView::bytes},self+i*AnmView::bytes,resource,7+i,world))return false;}else if(signal>=7&&signal<=10){const u32 mode=u32(signal-7),layers[]={30,23,20,29};AnmView{data}.put(0x1cfc,mode);root.put(0x24,layers[mode]);position(data);}return true;}
}
