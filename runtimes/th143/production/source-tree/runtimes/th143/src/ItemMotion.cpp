#include "ItemMotion.hpp"
#include <cmath>

namespace th143 {
namespace {
bool inside(const std::array<float,4>& r,const std::array<float,3>& p){return !(r[0]>p[0]||r[1]>p[1]||p[0]>r[2]||p[1]>r[3]);}
bool heading(const ItemPlayer& player,const std::array<float,3>& p,float& angle){
    const float y=player.position[1]-p[1],x=player.position[0]-p[0];
    if(!std::isfinite(x)||!std::isfinite(y))return false;
    angle=x==0.f&&y==0.f?real(0x3fc90fdb):float(std::atan2(double(y),double(x)));return true;
}
}
bool item_manager_step(ItemPool& pool,const ItemPlayer& player,float elapsed,ItemMotionHost& host){
    pool.put(0xde21dc,0);pool.put(0xde21d4,0);
    for(u32 index=0;index<ItemPool::count;++index){
        const u32 at=ItemPool::first+index*ItemPool::stride;AnmView s{pool.data.data()+at};
        u32 state=s.get(0xbf4);if(!state)continue;
        if(state==5){
            s.put(0xc04,s.get(0xc04)-1);if(signed_word(s.get(0xc04))>=0)continue;
            s.put(0xbf4,2);
            if(!host.bind(s.sub(0x10),ItemPool::token(at+0x10),signed_word(s.get(0xbf8))))return false;
            s.put(0x10+0x594,0);
            if(!host.animate(s.sub(0x10)))return false;
            s.put(0x5f4,s.get(0x5f4)&~1u);s.put(0x604,0);continue;
        }
        if(state<1||state>4)return false;
        std::array<float,3> position;
        for(u32 i=0;i<3;++i)position[i]=s.floating(0xbac+i*4);
        const bool forced=player.attract_all||(player.state!=2&&player.state!=4&&player.position[1]<128.f);
        if((state==1||state==4)&&forced){state=3;s.put(0xbf4,3);s.put(0xc00,word(player.speed));}
        bool falling=state==1;
        if(falling){
            for(u32 i=0;i<3;++i){position[i]+=s.floating(0xbb8+i*4)*elapsed;s.put(0xbac+i*4,word(position[i]));}
            const float vy=s.floating(0xbbc)+elapsed*real(0x3cf5c28f);s.put(0xbbc,word(vy));
            if(vy>=0.f)s.put(0xbb8,0);if(vy>2.f)s.put(0xbbc,word(2.f));
            if(position[1]>472.f){if(!pool.release(ItemPool::token(at)))return false;continue;}
        }else if(state==2){
            for(u32 i=0;i<3;++i)position[i]+=s.floating(0xbb8+i*4)*elapsed;
            const float speed=s.floating(0xbc4)-elapsed*real(0x3cf5c28f);s.put(0xbc4,word(speed));
            DirectionVector v;if(!direction_vector(s.floating(0xbc8),speed,v))return false;
            s.put(0xbb8,word(v.x));s.put(0xbbc,word(v.y));s.put(0xbc0,0);
            for(u32 i=0;i<3;++i)s.put(0xbac+i*4,word(position[i]));
            if(speed<=0.f){state=3;s.put(0xbf4,3);s.put(0xc00,word(player.speed));}
            else{
                if(position[1]>472.f){if(!pool.release(ItemPool::token(at)))return false;continue;}
                if((s.get(0x28)&1)&&!host.animate(s.sub(0x10)))return false;
                if((s.get(0x5f4)&1)&&!host.animate(s.sub(0x5dc)))return false;
                if(s.get(0xba8))return false;continue;
            }
        }
        if(!falling){
        if(state==3)host.homing_type(signed_word(s.get(0xbf8)));
        float angle;if(!heading(player,position,angle))return false;
        DirectionVector v;if(!direction_vector(angle,s.floating(0xc00),v))return false;
        s.put(0xbb8,word(v.x));s.put(0xbbc,word(v.y));
        position[0]+=v.x*elapsed;position[1]+=v.y*elapsed;
        // The original homing path retains the previous Z velocity.
        position[2]+=s.floating(0xbc0)*elapsed;
        for(u32 i=0;i<3;++i)s.put(0xbac+i*4,word(position[i]));
        if(s.floating(0xc00)<12.f)s.put(0xc00,word(s.floating(0xc00)+real(0x3e4ccccd)));
        if(player.state==4){s.put(0xbf4,1);s.put(0xbb8,0);s.put(0xbbc,0);}
        }
        if(player.state!=2&&inside(player.collect,position)){
            if(!host.collect(signed_word(s.get(0xbf8)),position))return false;
            if(!host.retire_visual(s.get(0xba8),1))return false;
            if(!pool.release(ItemPool::token(at)))return false;
            continue;
        }
        if(player.state!=2&&s.get(0xbf4)!=3&&s.get(0xbf4)!=4&&inside(player.keys&8?player.focused_magnet:player.magnet,position)){
            const u32 type=s.get(0xbf8);if(type!=9&&type!=10&&type!=11){s.put(0xbf4,4);s.put(0xc00,word(player.speed/3.f));}
        }
        if((s.get(0x28)&1)&&!host.animate(s.sub(0x10)))return false;
        if((s.get(0x5f4)&1)&&!host.animate(s.sub(0x5dc)))return false;
        if(s.get(0xba8)&&!host.position_visual(s.get(0xba8),position))return false;
        const u32 current=s.get(0xbd0),token=s.get(0xbd8);float rate=1.f;
        if(token&&!host.timer_rate(token,rate))return false;
        s.put(0xbcc,current);
        const bool unit=!token||(rate>real(0x3f7d70a4)&&rate<real(0x3f8147ae));
        const float fraction=s.floating(0xbd4)+(unit?1.f:rate);
        if(!unit&&!(fraction>=-2147483648.f&&fraction<2147483648.f))return false;
        s.put(0xbd0,unit?current+1:u32(i32(fraction)));s.put(0xbd4,word(fraction));
        pool.put(0xde21d4,pool.get(0xde21d4)+1);
    }
    return true;
}
}
