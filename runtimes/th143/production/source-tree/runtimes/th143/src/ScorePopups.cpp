#include "ScorePopups.hpp"
namespace th143 {
u32 ScorePopups::get(u32 at)const{u32 value;std::memcpy(&value,data.data()+at,4);return value;}
void ScorePopups::put(u32 at,u32 value){std::memcpy(data.data()+at,&value,4);}
void ScorePopups::construct(){data.fill(0);put(0,2);}
bool ScorePopups::initialize(u32 resource,AnmVmHost& host){
    put(8,0x20000200);put(12,0x20000228);put(0x10,resource);
    AnmView vm{data.data()+0x18};anm_reset(vm,token+0x18);vm.put(0x30,resource);
    if(!anm_bind_sprite(vm,263,host))return false;
    vm.put(0x1c,(vm.get(0x1c)&0xffddffffu)|0x1c0000);return true;
}
bool ScorePopups::number(const std::array<float,3>& position,i32 value,u32 color,u32 rate){
    i32 cursor=signed_word(get(0x14));if(cursor>=25)cursor=0;if(cursor<0)return false;
    const u32 at=0x5e4+u32(cursor)*0x48;data[at+0x3c]=1;u32 digits=0;
    if(value<0)data[at+digits++]=10;
    else if(value==0)data[at+digits++]=0;
    else while(value){data[at+digits++]=u8(value%10);value/=10;}
    data[at+0x3d]=u8(digits);put(at+0x1c,color);
    if(!(get(at+0x30)&1)){put(at+0x2c,rate);put(at+0x30,get(at+0x30)|1);}
    put(at+0x20,0xffffffff);put(at+0x24,0);put(at+0x28,0);
    for(u32 i=0;i<3;++i)put(at+0xc+i*4,word(position[i]));put(at+0x18,word(2.f));put(0x14,u32(cursor+1));return true;
}
bool ScorePopups::update(AnmTimerHost& host){
    float global;if(!host.timer_rate(host.global_rate_token(),global))return false;
    for(u32 i=0;i<33;++i){
        const u32 at=0x5e4+i*0x48;if(!data[at+0x3c])continue;
        if(i<28){const float speed=real(get(at+0x18));put(at+0x10,word(real(get(at+0x10))-speed*global));put(at+0x18,word(speed*real(0x3f733333)));}
        const u32 token=get(at+0x2c),current=get(at+0x24);float rate=1;
        if(token&&!host.timer_rate(token,rate))return false;
        put(at+0x20,current);const bool unit=!token||(rate>real(0x3f7d70a4)&&rate<real(0x3f8147ae));
        const float elapsed=real(get(at+0x28))+(unit?1.f:rate);const u32 time=unit?current+1:elapsed>=-2147483648.f&&elapsed<2147483648.f?u32(i32(elapsed)):0x80000000;
        put(at+0x24,time);put(at+0x28,word(elapsed));
        if(signed_word(time)>60){
            if(i<28)data[at+0x3c]=0;
            else{const i32 alpha=i32(get(at+0x1c)>>24)-4;if(alpha<=0)data[at+0x3c]=0;else put(at+0x1c,(get(at+0x1c)&0xffffffu)|(u32(alpha)<<24));}
        }
    }return true;
}
}
