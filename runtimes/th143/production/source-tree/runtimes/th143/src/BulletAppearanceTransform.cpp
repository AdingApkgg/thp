#include "BulletAppearanceTransform.hpp"
#include <map>
namespace th143 {
namespace {std::map<BulletMotionHost*,std::function<bool(BulletView,u32)>> bindings;}
void bind_bullet_appearance_transform(BulletMotionHost& h,std::function<bool(BulletView,u32)> f){if(f)bindings[&h]=std::move(f);else bindings.erase(&h);}
bool dispatch_bullet_appearance_transform(BulletView b,u32 row,BulletMotionHost& h){const auto p=bindings.find(&h);return p!=bindings.end()&&p->second(b,row);}
bool change_bullet_appearance(BulletView b,u32 row,u32 token,u32 resource,BulletFactoryHost& host){
 const u32 type=b.get(row+0x10),raw_color=b.get(row+0x14),color=raw_color&0x7fff,definition=0x4daf60+type*0x114;if(type>=43)return false;b.put(0x13ec,(type&65535)|(color<<16));
 u32 radius,layer,script,secondary,cancel;if(!host.read(definition+0x104,&radius,4)||!host.read(definition+0x108,&layer,4)||!host.read(definition,&script,4)||!host.read(definition+0x110,&secondary,4)||!host.read(definition+0x10c,&cancel,4))return false;
 b.put(0xbe4,radius);b.put(0xbe0,radius);b.put(0x13e8,definition);b.put(0xc24,layer);AnmView main{b.data+0x28},extra{b.data+0x5f4};anm_reset(main,token+0x28);b.put(0x5d4,0x417dc0);b.put(0x5d8,token);
 if(!anm_bind_script(main,resource,signed_word(script),host))return false;b.put(0x20,b.get(0x20)|0x10);b.put(0x44,(b.get(0x44)&~0x40000u)|0x20000u);anm_reset(extra,token+0x5f4);b.put(0x60c,b.get(0x60c)&~1u);
 if(secondary){b.put(0x60c,b.get(0x60c)|1u);if(!anm_bind_script(extra,resource,signed_word(secondary),host))return false;b.put(0x610,(b.get(0x610)&~0x40000u)|0x20000u);}
 switch(cancel){case 0:b.put(0xc00,color*2+4);break;case 1:{u32 value;if(!host.read(0x4c4670+color*4,&value,4))return false;b.put(0xc00,value);break;}case 2:b.put(0xc00,0xffffffff);b.put(0x20,b.get(0x20)|0x10);break;case 3:b.put(0xc00,16);break;case 4:b.put(0xc00,6);break;case 5:b.put(0xc00,12);break;case 6:{u32 value;if(!host.read(definition+0x10+color*16,&value,4))return false;b.put(0xc00,value);b.put(0x20,b.get(0x20)|0x10);break;}case 7:case 8:case 9:case 10:b.put(0xc00,cancel==7?0xe8:cancel==8?0xeb:cancel==9?0xee:0xf7);b.put(0x20,b.get(0x20)|0x10);break;}
 return !(raw_color&0x8000)||host.interrupt(b,0,2);
}
}
