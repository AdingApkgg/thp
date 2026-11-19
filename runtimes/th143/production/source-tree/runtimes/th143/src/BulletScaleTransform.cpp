#include "BulletScaleTransform.hpp"
namespace th143 {
void start_bullet_scale_transform(BulletView b,u32 row,u32 rate){
 b.put(0xc04,b.get(0xc04)|0x400000);b.put(0x138c,b.get(row));b.put(0x1390,b.get(row+4));b.put(0x1394,0);b.put(0x1398,0);
 b.put(0x13b4,b.get(row+0x10));b.put(0x13b8,b.get(row+0x14));if(!(b.get(0x13b0)&1)){b.put(0x13ac,rate);b.put(0x13b0,b.get(0x13b0)|1);}
 b.put(0x13a0,0xffffffff);b.put(0x13a4,0);b.put(0x13a8,0);b.put(0x20,b.get(0x20)|0x40);b.put(0xc20,b.get(0xc20)+1);
}
bool update_bullet_scale_transform(BulletView b,AnmTimerHost& rates){
 if(!(b.get(0xc04)&0x400000))return true;float value;
 if(!scalar_interpolate({b.data+0x138c},rates,value))return false;b.put(0x13bc,word(value));
 if(!b.get(0x13b4)){b.put(0xc04,b.get(0xc04)&~0x400000u);if(value==1.f)b.put(0x20,b.get(0x20)&~0x40u);}return true;
}
}
