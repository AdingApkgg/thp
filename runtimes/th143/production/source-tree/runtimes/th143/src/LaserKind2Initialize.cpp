#include "LaserKind2Initialize.hpp"
#include "LaserPathSegment.hpp"
#include "AnmInstance.hpp"
#include "DirectionVector.hpp"
namespace th143 {
namespace {
float wrap(float a){u32 count=0;while(a>real(0x40490fdb)){a-=real(0x40c90fdb);if(count++>32)break;}while(real(0xc0490fdb)>a){a+=real(0x40c90fdb);if(count++>32)break;}return a;}
u32 truncate(float a){return a>=-2147483648.f&&a<2147483648.f?u32(i32(a)):0x80000000;}
void timer(AnmView v,u32 at,u32 n,float fraction,u32 rate){if(!(v.get(at+16)&1)){v.put(at+12,rate);v.put(at+16,v.get(at+16)|1);}v.put(at,n-1);v.put(at+4,n);v.put(at+8,word(fraction));}
bool interrupt(AnmView v,LaserKind2Host& h){if(v.get(0x5c4))return false;v.put(0x4a0,2);return anm_step(v,h)!=-2;}
}
bool initialize_laser_kind2(u8* data,u32 bytes,u32 token,const u8* parameters,u32 parameter_bytes,u32 resource,LaserKind2Host& host){
 if(!data||bytes<0x14f0||!parameters||parameter_bytes<0x354)return false;std::memcpy(data+0x5c0,parameters,0x354);AnmView v{data};const i32 count=signed_word(v.get(0x5e0));if(count<1||count>4096)return false;v.put(0x5b8,v.get(0x5d8));v.put(0x5bc,v.get(0x5dc));v.put(0x10,2);v.put(0x14,2);
 AnmView main{data+0x914},secondary{data+0xee0};anm_reset(main,token+0x914);const u32 kind=v.get(0x5b8);if(kind!=1){main.put(0x5ac,0x4427b0);main.put(0x5b0,token);}if(!anm_bind_script(main,resource,kind==1?0x126:signed_word(kind+0x72),host)||!interrupt(main,host))return false;main.put(0x18,(main.get(0x18)&0xfffffe3fu)|0x20u);main.put(0x18,(main.get(0x18)&0xc31fffffu)|0x3000000u);main.put(0x1c,(main.get(0x1c)&~0x40000u)|0x20000u);
 auto source=host.laser_animation_template(resource,signed_word(v.get(0x5dc)+0x38));if(!source.data)return false;anm_copy_template(secondary,token+0xee0,source,host.global_rate_token());secondary.put(0x594,0);if(anm_step(secondary,host)==-2||!interrupt(secondary,host))return false;secondary.put(0x18,(secondary.get(0x18)&0xfffffe3fu)|0x20u);secondary.put(0x18,(secondary.get(0x18)&0xc3ffffffu)|0x2000000u);secondary.put(0x1c,(secondary.get(0x1c)&~0x40000u)|0x20000u);
 u32 vertices_token,points_token;u8 *vertices,*points;if(!host.laser_curve_allocate(u32(count)*56,true,vertices_token,vertices)||!host.laser_curve_allocate(u32(count)*32,true,points_token,points))return false;v.put(0x14b0,vertices_token);v.put(0x14ac,points_token);for(u32 i=0;i<3;++i)v.put(0x54+i*4,v.get(0x5c0+i*4));
 DirectionVector direction;if(v.floating(0x5e4)!=0.f){if(!direction_vector(v.floating(0x5cc),v.floating(0x5e4),direction))return false;v.put(0x54,word(v.floating(0x54)+direction.x));v.put(0x58,word(v.floating(0x58)+direction.y));v.put(0x5e4,0);for(u32 i=0;i<3;++i)v.put(0x5c0+i*4,v.get(0x54+i*4));}
 v.put(0x74,v.get(0x5d0));v.put(0x6c,v.get(0x5cc));v.put(0x78,v.get(0x5d4));if(!direction_vector(v.floating(0x5cc),v.floating(0x5d4),direction))return false;v.put(0x60,word(direction.x));v.put(0x64,word(direction.y));v.put(0x68,0);
 for(i32 i=0;i<count;++i){AnmView p{points+u32(i)*32};for(u32 j=0;j<3;++j){p.put(j*4,v.get(0x54+j*4));p.put(0xc+j*4,0);}p.put(0x18,v.get(0x5cc));p.put(0x1c,v.get(0x5d4));}
 const u32 rate=host.global_rate_token();const float age=v.floating(0x910);timer(v,0x40,truncate(age),age,rate);
 const u32 external=v.get(0x90c);if(external){std::array<u8,0x3c> node;if(!host.read(external,node.data(),node.size()))return false;std::memcpy(data+0x14b4,node.data(),node.size());u8* previous=data+0x14b4;for(u32 step=0;;++step){if(step>=4096)return false;const u32 next=AnmView{previous}.get(0);if(!next)break;std::array<u8,0x3c> input;if(!host.read(next,input.data(),input.size()))return false;u32 allocated;u8* storage;if(!host.laser_curve_allocate(0x3c,false,allocated,storage))return false;AnmView{previous}.put(0,allocated);std::memcpy(storage,input.data(),input.size());previous=storage;}v.put(0x90c,0);v.put(0x594,99);}
 else{v.put(0x14b4,0);v.put(0x14e4,v.get(0x78));v.put(0x14e0,word(wrap(v.floating(0x6c))));if(!direction_vector(v.floating(0x6c),1.f,direction))return false;v.put(0x14c8,word(direction.x));v.put(0x14cc,word(direction.y));v.put(0x14d0,0);v.put(0x14c4,0);v.put(0x14bc,0);v.put(0x14c0,0x497423f0);for(u32 i=0;i<3;++i)v.put(0x14d4+i*4,v.get(0x54+i*4));}
 for(u32 i=0;i<3;++i)AnmView{points}.put(0xc+i*4,v.get(0x60+i*4));
 for(i32 i=0;i<count;++i){const float time=v.floating(0x48)-float(i);u32 current=token+0x14b4;std::array<u8,0x3c> node;bool found=false;for(u32 depth=0;current;++depth){if(depth>=4096)return false;if(current==token+0x14b4)std::memcpy(node.data(),data+0x14b4,node.size());else if(!host.read(current,node.data(),node.size()))return false;AnmView n{node.data()};if(time>=n.floating(8)&&n.floating(0xc)>time){found=true;break;}current=n.get(0);}if(!found)continue;
  AnmView p{points+u32(i)*32};LaserPathPoint result{{p.floating(0),p.floating(4),p.floating(8)},p.floating(0x1c),p.floating(0x18)};bool okay;if(!i)okay=laser_path_point({node.data()},time,result);else{AnmView previous{points+u32(i-1)*32};LaserPathPoint before{{previous.floating(0),previous.floating(4),previous.floating(8)},previous.floating(0x1c),previous.floating(0x18)};okay=laser_path_previous({node.data()},before,time,result);}if(!okay)return false;for(u32 j=0;j<3;++j)p.put(j*4,word(result.position[j]));p.put(0x1c,word(result.speed));p.put(0x18,word(result.angle));
 }
 timer(v,0x5a0,30,30.f,rate);if(signed_word(v.get(0x904))>=0&&!host.laser_launch_sound(signed_word(v.get(0x904)),0.f))return false;timer(v,0x2c,0,0.f,rate);return true;
}
}
