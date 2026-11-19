#include "LaserKind1Initialize.hpp"
#include "AnmInstance.hpp"
#include "DirectionVector.hpp"
namespace th143 {
namespace {bool interrupt(AnmView v,LaserKind1Host& h){if(v.get(0x5c4))return false;v.put(0x4a0,2);return anm_step(v,h)!=-2;}}
bool initialize_laser_kind1(u8* data,u32 bytes,u32 token,const u8* parameters,u32 parameter_bytes,u32 resource,LaserKind1Host& host){
 if(!data||bytes<0x14d0||!parameters||parameter_bytes<0x374)return false;std::memcpy(data+0x5c0,parameters,0x374);AnmView v{data};v.put(0x5b8,v.get(0x610));v.put(0x5bc,v.get(0x614));v.put(0x10,3);v.put(0x14,1);
 AnmView main{data+0x938},secondary{data+0xf04};anm_reset(main,token+0x938);main.put(0x5ac,0x439930);main.put(0x5b0,token);u32 script;if(!host.read(0x4daf60+v.get(0x5b8)*0x114,&script,4)||!anm_bind_script(main,resource,signed_word(script),host)||!interrupt(main,host))return false;main.put(0x18,(main.get(0x18)&0xfffffe3fu)|0x20u);main.put(0x18,(main.get(0x18)&0xc31fffffu)|0x3000000u);main.put(0x1c,(main.get(0x1c)&~0x40000u)|0x20000u);
 auto source=host.laser_animation_template(resource,signed_word(v.get(0x614)+0x38));if(!source.data)return false;anm_copy_template(secondary,token+0xf04,source,host.global_rate_token());secondary.put(0x594,0);if(anm_step(secondary,host)==-2||!interrupt(secondary,host))return false;secondary.put(0x18,(secondary.get(0x18)&0xfffffe3fu)|0x20u);secondary.put(0x18,(secondary.get(0x18)&0xc3ffffffu)|0x2000000u);secondary.put(0x1c,(secondary.get(0x1c)&~0x40000u)|0x20000u);
 if(signed_word(v.get(0x600))>=0&&!host.laser_launch_sound(signed_word(v.get(0x600)),0.f))return false;for(u32 i=0;i<3;++i)v.put(0x54+i*4,v.get(0x5c0+i*4));if(v.floating(0x60c)!=0.f){DirectionVector d;if(!direction_vector(v.floating(0x5d8),v.floating(0x60c),d))return false;v.put(0x54,word(v.floating(0x54)+d.x));v.put(0x58,word(v.floating(0x58)+d.y));}
 v.put(0x70,v.get(0x5e4));v.put(0x78,v.get(0x5ec));v.put(0x6c,v.get(0x5d8));v.put(0x74,word(2.f));v.put(0x80,v.get(0x608));if(!(v.get(0x3c)&1)){v.put(0x38,host.global_rate_token());v.put(0x3c,v.get(0x3c)|1);}v.put(0x2c,0xffffffff);v.put(0x30,0);v.put(0x34,0);v.put(0x934,0);return true;
}
}
