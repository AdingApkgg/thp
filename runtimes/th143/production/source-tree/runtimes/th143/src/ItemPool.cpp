#include "ItemPool.hpp"
#include <algorithm>

namespace th143 {
u32 ItemPool::get(u32 at)const{u32 value;std::memcpy(&value,data.data()+at,4);return value;}
void ItemPool::put(u32 at,u32 value){std::memcpy(data.data()+at,&value,4);}
void ItemPool::construct(){std::fill(data.begin(),data.end(),0);put(0,2);}
void ItemPool::build(u32 root,u32 begin,u32 n){
    for(u32 at=0;at<16;at+=4)put(root+at,0);
    for(u32 i=begin;i<begin+n;++i){
        const u32 at=first+i*stride,previous=get(root+4);
        put(at,token(root));put(at+4,0);put(at+8,0);put(at+12,0);
        if(previous){put(at+4,previous);put(offset(previous)+8,token(at));}
        if(get(root+12))put(root+12,token(at));
        put(root+4,token(at));put(at+8,token(root));
    }
}
void ItemPool::reset_storage(){
    std::fill(data.begin()+first,data.begin()+first+0xde21a0,0);
    put(0xde21d8,0);put(0xde21e0,0);put(0xde21e4,0);
    build(regular_free,0,regular_count);build(delayed_free,regular_count,count-regular_count);
}
bool ItemPool::spawn_delayed(i32 type,const std::array<float,3>& position,float angle,float speed,u32 rate,u32& result){
    if(type!=13&&type!=14)return false;
    result=get(delayed_free+4);if(!result)return true;
    const u32 at=offset(result);
    if(at<first||at>=first+count*stride||(at-first)%stride)return false;
    DirectionVector direction;if(!direction_vector(angle,speed,direction))return false;
    put(at+0xc08,get(0xde21e0));put(at+0xbf4,5);put(at+0xbf8,u32(type));put(at+0xbfc,u32(type));
    u32 wait=1;
    if(type==14){
        const i32 current=signed_word(get(0xde21dc)),counter=signed_word(get(0xde21d8));
        const i32 divisor=current>=1024?32:current>=512?16:current>=256?8:4;
        wait=u32(counter%divisor+(current>=1024?16:current>=512?8:current>=256?4:0));
    }
    put(at+0xc04,wait);
    for(u32 i=0;i<3;++i)put(at+0xbac+i*4,word(position[i]));
    put(at+0xbb8,word(direction.x));put(at+0xbbc,word(direction.y));put(at+0xbc0,0);
    if(!(get(at+0xbdc)&1)){put(at+0xbd8,rate);put(at+0xbdc,get(at+0xbdc)|1);}
    put(at+0xbcc,0xffffffff);put(at+0xbd0,0);put(at+0xbd4,0);
    put(at+0xbc4,word(speed));put(at+0xbc8,word(angle));put(at+0xba8,0);
    const u32 next=get(at+4),previous=get(at+8);
    if(next)put(offset(next)+8,previous);
    if(previous)put(offset(previous)+4,next);
    put(at+8,0);put(at+4,0);put(0xde21dc,get(0xde21dc)+1);return true;
}
bool ItemPool::release(u32 address){
    const u32 at=offset(address);if(at<first||at>=first+count*stride||(at-first)%stride)return false;
    const u32 root=get(at);
    if(root!=token(regular_free)&&root!=token(delayed_free))return false;
    const u32 head=get(offset(root)+4);
    put(at+0xbf4,0);
    if(head){put(at+4,head);put(offset(head)+8,address);}
    if(get(offset(root)+12))put(offset(root)+12,address);
    put(offset(root)+4,address);put(at+8,root);return true;
}
}
