#include "ObjectDraw.hpp"
namespace th143 {
namespace {
float wrap_draw_angle(float angle){u32 count=0;while(angle>real(0x40490fdb)){angle-=real(0x40c90fdb);if(count++>32)break;}while(real(0xc0490fdb)>angle){angle+=real(0x40c90fdb);if(count++>32)break;}return angle;}
u32 draw_integer(float v){return v>=-2147483648.f&&v<2147483648.f?u32(i32(v)):0x80000000;}
}
bool draw_bullet_objects(BulletPool& pool,u32 root_flags,PlayerDrawHost& host){
    if(root_flags&4)return true;
    for(u32 list=0;list<6;++list){u32 token=pool.get(0x14+list*4),budget=BulletPool::count+1;
        while(token){if(!budget--||token<BulletPool::token_base||std::uint64_t(token)+BulletPool::stride>std::uint64_t(BulletPool::token_base)+pool.data.size())return false;
            auto s=AnmView{pool.data.data()+BulletPool::offset(token)};
            auto visual=[&](u32 at)->bool{auto vm=s.sub(at);std::memcpy(vm.data+0x3c,s.data+0xbc0,12);
                if(vm.get(0x1c)&0x40){vm.put(0x18,vm.get(0x18)|4);vm.put(0x50,word(wrap_draw_angle(s.floating(0xbdc)+real(0x3fc90fdb))));}
                if(s.get(0x20)&0x40){vm.put(0x18,vm.get(0x18)|8);vm.put(0x68,s.get(0x13bc));vm.put(0x6c,s.get(0x13bc));}
                return host.draw_player_visual(token+at,vm);
            };
            if((s.get(0x60c)&1)&&!visual(0x5f4))return false;if(!visual(0x28))return false;token=s.get(0xc14);
        }
    }return true;
}
bool draw_item_objects(ItemPool& pool,u32 root_flags,PlayerDrawHost& host){
    if(root_flags&4)return true;
    for(u32 i=0;i<ItemPool::count;++i){const u32 at=ItemPool::first+i*ItemPool::stride;auto s=AnmView{pool.data.data()+at};
        if(!s.get(0xbf4)||!(s.get(0x28)&1)||signed_word(s.get(0xc04))>0)continue;
        std::memcpy(s.data+0x4c,s.data+0xbac,12);std::memcpy(s.data+0x618,s.data+0xbac,12);
        if(-8.f>s.floating(0x50)){
            if(s.get(0x5f4)&1){const float distance=s.floating(0x61c)+8.f;s.put(0x61c,word(8.f));const float alpha=(distance*real(0x3d000000))*255.f;s.data[0xb13]=distance>=32.f?255:u8(draw_integer(alpha));
                if(!host.draw_player_visual(ItemPool::token(at+0x5dc),s.sub(0x5dc)))return false;}
            s.put(0xbfc,1);
        }else{if(!host.draw_player_visual(ItemPool::token(at+0x10),s.sub(0x10)))return false;s.put(0xbfc,0);}
    }return true;
}
}
