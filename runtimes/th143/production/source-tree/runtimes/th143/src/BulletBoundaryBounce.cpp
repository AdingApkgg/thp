#include "BulletBoundaryBounce.hpp"
#include "DirectionVector.hpp"
namespace th143 {
namespace {
float wrap(float angle){u32 count=0;while(angle>real(0x40490fdb)){angle-=real(0x40c90fdb);if(count++>32)break;}while(real(0xc0490fdb)>angle){angle+=real(0x40c90fdb);if(count++>32)break;}return angle;}
float negative(float value){return real(word(value)^0x80000000u);}
}
void start_bullet_boundary_bounce(BulletView b,u32 row){
    b.put(0xc04,b.get(0xc04)|0x40);b.put(0x1074,b.get(row));
    b.put(0x107c,b.get(row+0x14)&0x20?b.get(row+4):0x43c00000);
    b.put(0x1080,b.get(row+0x14)&0x20?b.get(row+8):0x43e00000);
    b.put(0x1098,b.get(row+0x10));b.put(0x1094,0);b.put(0x10a0,b.get(row+0x14));
}
i32 update_bullet_boundary_bounce(BulletView b,float manager_width,float manager_height,const std::function<bool(i32)>& sound){
    const float outer_width=manager_width>0.f?manager_width:b.floating(0x107c);
    const float outer_height=manager_width>0.f?manager_height:b.floating(0x1080);
    const float x=b.floating(0xbc0),y=b.floating(0xbc4);
    if(!(outer_width*-.5f>=x+0.f||x-0.f>=outer_width*.5f||224.f-outer_height*.5f>=y+0.f||y-0.f>=outer_height*.5f+224.f))return 0;
    const float width=manager_width>0.f?manager_width:b.floating(0x107c),height=manager_height>0.f?manager_height:b.floating(0x1080);
    const u32 flags=b.get(0x10a0);bool bounced=false;
    const auto vertical=[&](bool bottom){const float position=b.floating(0xbc4),edge=bottom?height*.5f+224.f:224.f-height*.5f;
        if(bottom?!(position>=edge):!(edge>position))return;
        bounced=true;if(flags&0x10)return;
        b.put(0xbdc,word(wrap(negative(b.floating(0xbdc)))));
        b.put(0xbc4,word(bottom?(height+448.f)-position:(448.f-height)-position));
    };
    const auto horizontal=[&](bool right){const float position=b.floating(0xbc0),edge=width*(right?.5f:-.5f);
        if(right?!(position>=edge):!(edge>position))return;
        bounced=true;if(flags&0x10)return;
        float angle=negative(b.floating(0xbdc))-real(0x40490fdb);angle=wrap(angle);angle+=0.f;angle=wrap(angle);angle=wrap(angle);
        b.put(0xbdc,word(angle));b.put(0xbc0,word((right?width:negative(width))-position));
    };
    if(flags&1)vertical(false);if(flags&2)vertical(true);if(flags&8)horizontal(true);if(flags&4)horizontal(false);
    if(b.floating(0x1074)>-990.f)b.put(0xbd8,b.get(0x1074));
    DirectionVector velocity;if(!direction_vector(b.floating(0xbdc),b.floating(0xbd8),velocity))return -2;
    b.put(0xbcc,word(velocity.x));b.put(0xbd0,word(velocity.y));
    if(bounced){b.put(0x1094,b.get(0x1094)+1);if(signed_word(b.get(0xc1c))>=0&&!sound(signed_word(b.get(0xc1c))))return -2;}
    if(signed_word(b.get(0x1094))>=signed_word(b.get(0x1098))){b.put(0xc04,b.get(0xc04)&~0x40u);return 1;}
    return 0;
}
}
