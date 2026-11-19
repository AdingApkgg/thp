#include "EnemyDrops.hpp"
namespace th143 {
namespace {
float wrap(float angle){u32 count=0;while(angle>real(0x40490fdb)){angle-=real(0x40c90fdb);if(count++>32)break;}while(real(0xc0490fdb)>angle){angle+=real(0x40c90fdb);if(count++>32)break;}return angle;}
}
bool enemy_drops(AnmView d,const std::array<float,3>& position,Rng& rng,ItemPool& pool,u32 rate){
    float angle=rng.signed_unit()*real(0x40490fdb);
    for(u32 type=1;type<=14;++type){const i32 count=signed_word(d.get(type*4));
        for(i32 i=0;i<count;++i){
            DirectionVector horizontal,vertical;
            if(!direction_vector(angle,d.floating(0x40),horizontal)||!direction_vector(angle,d.floating(0x44),vertical))return false;
            const float scale=rng.unit()*.5f+.5f;
            const std::array<float,3> drop{position[0]+horizontal.x*scale,position[1]+vertical.y*scale,position[2]+0.f};
            pool.put(0xde21d8,pool.get(0xde21d8)+1);
            if(type>=13){u32 token;if(!pool.spawn_delayed(i32(type),drop,real(0xbfc90fdb),real(0x3fe66666),rate,token))return false;}
            const float next=(rng.signed_unit()*real(0x40490fdb))*.25f+(angle+real(0x3fc90fdb));angle=wrap(next);
        }
    }
    std::memset(d.data+4,0,0x3c);return true;
}
}
