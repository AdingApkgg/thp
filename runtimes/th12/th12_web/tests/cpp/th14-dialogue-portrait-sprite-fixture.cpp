#include "th14-dialogue-portrait-lifecycle-fixture.cpp"
static u32 sprite_state[16*38];
static void capture_sprite(){for(u32 i=0;i<vms.size();++i){auto* s=sprite_state+i*38;if(!lifecycle_alive[i]){for(u32 j=0;j<38;++j)s[j]=0;continue;}std::memcpy(s,state+i*22,22*sizeof(u32));auto& vm=*vms[i];s[22]=bits(vm.sprite_size.x);s[23]=bits(vm.sprite_size.y);for(u32 j=0;j<4;++j){s[24+j*2]=bits(vm.uv[j].x);s[25+j*2]=bits(vm.uv[j].y);}s[32]=bits(vm.sprite_matrix.m[0]);s[33]=bits(vm.sprite_matrix.m[5]);s[34]=bits(vm.uv_matrix.m[0]);s[35]=bits(vm.uv_matrix.m[5]);s[36]=bits(vm.transform_matrix.m[0]);s[37]=bits(vm.transform_matrix.m[5]);}}
API(begin_sprite) i32 begin_sprite(u32 resource_index,float rate,i32 immediate){if(!begin_lifecycle(resource_index,rate,immediate))return 0;capture_sprite();return 1;}
API(sprite_interrupt) void sprite_interrupt(i32 label){lifecycle_interrupt(label);capture_sprite();}
API(sprite_step) i32 sprite_step(){if(!lifecycle_step())return 0;capture_sprite();return 1;}
API(sprite_data) const u32* sprite_data(){return sprite_state;}
