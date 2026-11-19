#include "LaserKind0Initialize.hpp"
#include "AnmInstance.hpp"
#include "DirectionVector.hpp"
namespace th143 {
namespace {
void timer(AnmView v,u32 at,u32 n,u32 rate){if(!(v.get(at+16)&1)){v.put(at+12,rate);v.put(at+16,v.get(at+16)|1);}v.put(at,n-1);v.put(at+4,n);v.put(at+8,word(float(signed_word(n))));}
bool interrupt(AnmView v,LaserKind0Host& host){if(v.get(0x5c4))return false;v.put(0x4a0,2);return anm_step(v,host)!=-2;}
}
bool initialize_laser_kind0(u8* data,u32 bytes,u32 token,const u8* parameters,u32 parameter_bytes,u32 resource,LaserKind0Host& host){
 if(!data||bytes<0x1a78||!parameters||parameter_bytes<0x354)return false;std::memcpy(data+0x5c0,parameters,0x354);AnmView v{data};v.put(0x5b8,v.get(0x5e4));v.put(0x5bc,v.get(0x5e8));v.put(0x10,2);v.put(0x14,0);
 AnmView main{data+0x914},secondary{data+0xee0},end{data+0x14ac};anm_reset(main,token+0x914);main.put(0x5ac,0x439930);main.put(0x5b0,token);u32 script;if(!host.read(0x4daf60+v.get(0x5b8)*0x114,&script,4)||!anm_bind_script(main,resource,signed_word(script),host)||!interrupt(main,host))return false;
 main.put(0x18,(main.get(0x18)&0xfffffe3fu)|0x20u);main.put(0x18,(main.get(0x18)&0xc31fffffu)|0x3000000u);main.put(0x1c,(main.get(0x1c)&~0x40000u)|0x20000u);
 auto source=host.laser_animation_template(resource,signed_word(v.get(0x5e8)+0x38));if(!source.data)return false;anm_copy_template(secondary,token+0xee0,source,host.global_rate_token());secondary.put(0x594,0);if(anm_step(secondary,host)==-2||!interrupt(secondary,host))return false;secondary.put(0x18,(secondary.get(0x18)&0xfffffe3fu)|0x20u);secondary.put(0x18,(secondary.get(0x18)&0xc3ffffffu)|0x2000000u);secondary.put(0x1c,(secondary.get(0x1c)&~0x40000u)|0x20000u);
 source=host.laser_animation_template(resource,signed_word(v.get(0x5e8)+0x52));if(!source.data)return false;anm_copy_template(end,token+0x14ac,source,host.global_rate_token());end.put(0x594,0);if(anm_step(end,host)==-2)return false;end.put(0x1c,(end.get(0x1c)&~0x40000u)|0x20000u);
 const u32 rate=host.global_rate_token();timer(v,0x5a0,30,rate);if(signed_word(v.get(0x90c))>=0&&!host.laser_launch_sound(signed_word(v.get(0x90c)),0.f))return false;timer(v,0x2c,0,rate);timer(v,0x40,0,rate);for(u32 i=0;i<3;++i)v.put(0x54+i*4,v.get(0x5c0+i*4));
 DirectionVector direction;if(v.floating(0x5ec)!=0.f){if(!direction_vector(v.floating(0x5cc),v.floating(0x5ec),direction))return false;v.put(0x54,word(direction.x+v.floating(0x54)));v.put(0x58,word(direction.y+v.floating(0x58)));}
 v.put(0x74,v.get(0x5dc));v.put(0x70,v.get(0x5d4));v.put(0x78,v.get(0x5e0));v.put(0x6c,v.get(0x5cc));v.put(0x7c,v.floating(0x5d4)>v.floating(0x5d0)?word(.01f):0);if(!direction_vector(v.floating(0x5cc),v.floating(0x5e0),direction))return false;v.put(0x60,word(direction.x));v.put(0x64,word(direction.y));return true;
}
}
