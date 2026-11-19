#include "PlayerFrame.hpp"
#include "DirectionVector.hpp"
#include <cmath>

namespace th143 {
namespace {
u32 truncate(float v){return v>=-2147483648.f&&v<2147483648.f?u32(i32(v)):0x80000000u;}
void reset(PlayerState& p,u32 at,i32 value,AnmTimerHost& host){
    if(!(p.get(at+16)&1)){p.put(at+12,host.global_rate_token());p.put(at+16,p.get(at+16)|1);}
    p.put(at,u32(value)-1);p.put(at+4,u32(value));p.put(at+8,word(float(value)));
}
bool tick(PlayerState& p,u32 at,bool decrement,AnmTimerHost& host){
    float rate=1;const u32 ptr=p.get(at+12);if(ptr&&!host.timer_rate(ptr,rate))return false;
    const bool unit=!ptr||(rate>real(0x3f7d70a4)&&rate<real(0x3f8147ae));
    const u32 old=p.get(at+4);p.put(at,old);
    const float value=decrement?p.floating(at+8)-(unit?1.f:rate):p.floating(at+8)+(unit?1.f:rate);
    p.put(at+8,word(value));p.put(at+4,!decrement&&unit?old+1:truncate(value));return true;
}
float wrap(float value){u32 n=0;while(value>real(0x40490fdb)){value-=real(0x40c90fdb);if(n++>32)break;}
    while(real(0xc0490fdb)>value){value+=real(0x40c90fdb);if(n++>32)break;}return value;}
std::array<float,3> position(PlayerState& p,u32 at=0x5e0){return {p.floating(at),p.floating(at+4),p.floating(at+8)};}
bool bank(PlayerState& p,u32 at,float rate,AnmTimerHost& host){
    if((p.get(at+0x6c)&15)!=0)return false;
    DirectionVector v;if(!direction_vector(p.floating(at+0x48),p.floating(at+0x44)*rate,v))return false;
    p.put(at+0x60,word(v.x));p.put(at+0x64,word(v.y));
    for(u32 i=0;i<3;++i){float value=p.floating(at+0x2c+i*4)+p.floating(at+0x60+i*4);
        if(i<2)value=std::floor(value*100.f)/100.f;p.put(at+0x2c+i*4,word(value));}
    p.put(at+0x14,word(p.floating(at+0x14)+p.floating(at+0x18)));
    p.put(at+0x1c,word(wrap(p.floating(at+0x1c)+p.floating(at+0x20))));p.put(at+0x94,0);
    if(!tick(p,at+0x70,true,host))return false;
    if(signed_word(p.get(at+0x74))<=0)p.put(at+0x10,p.get(at+0x10)&~1u);
    return true;
}
bool death(PlayerState& p,PlayerFrameGlobals& g,PlayerFrameHost& host){
    if(!host.effect(19,position(p)))return false;
    g.lives=signed_word(u32(g.lives)-1);if(g.lives>=0&&!host.lives_changed(g.lives,g.life_fragments))return false;
    p.put(0x684,2);reset(p,0x68c,0,host);reset(p,0x18468,180,host);
    if(!host.bind_player_visual(p,0))return false;
    for(u32 i=0;i<8;++i){const u32 at=0xd6ec+i*0xe4;p.put(at,0);
        if(!host.signal_visual(p.get(at+0xb0),1)||!host.signal_visual(p.get(at+0xb4),1))return false;}
    p.put(0x182e8,0);++g.deaths;g.death_flag=0;return true;
}
bool respawn_bank(PlayerState& p,AnmTimerHost& host){
    u32 cursor=p.get(0xde14);if(cursor>256)return false;
    for(u32 n=0;n<256;++n){if(cursor>=256)cursor=0;const u32 at=0xde18+cursor*0xa4;
        if(!(p.get(at+0x10)&1)){
            p.put(0xde14,cursor);p.put(at+0x10,(p.get(at+0x10)&~4u)|3);
            std::memset(p.data.data()+at+0x2c,0,0x44);
            for(u32 i=0;i<3;++i)p.put(at+0x2c+i*4,p.get(0x5e0+i*4));
            p.put(at+0x14,word(32.f));p.put(at+0x18,word(16.f));reset(p,at+0x70,30,host);
            p.put(at+0x84,150);p.put(at+0x88,0);p.put(at+0x8c,9999999);p.put(at+0x90,1);p.put(at+0x94,0);p.put(at+0xa0,0);return true;
        }p.put(0xde14,++cursor);
    }return true;
}
void mute(PlayerFrameGlobals& g,i32 id){for(u32 i=0;i<12;++i){if(g.sound_ids[i]<0||g.sound_ids[i]==id){g.sound_ids[i]=id;g.sound_parameters[i]=0xffffffff;return;}}}
}
i32 player_frame(PlayerState& p,PlayerFrameGlobals& g,PlayerFrameHost& host){
    if(!(g.input.elapsed>0))return 1;
    switch(p.get(0x684)){
    case 0:{
        const i32 time=signed_word(p.get(0x690));p.put(0x5f0,61440-u32(signed_word(p.get(0x690)*10240)/60));
        p.put(0x5e4,word(float(signed_word(p.get(0x5f0)))*.0078125f));
        for(u32 i=0;i<8;++i)p.put(0xd7c0+i*0xe4,1);
        for(u32 i=0;i<33;++i){p.put(0x1845c-i*8,p.get(0x5ec));p.put(0x18460-i*8,p.get(0x5f0));}
        if(time>=30){if(!host.cancel_circle(position(p),640.f,0)||!host.cancel_all_lasers(0,true))return -2;}
        else{const float radius=(float(time)*512.f)/30.f+64.f;
            if(!host.cancel_lasers(position(p,0x66c),radius,0,true)||!host.cancel_lasers(position(p,0x66c),radius*.25f,0,false))return -2;}
        if(time<60)break;p.put(0x684,1);reset(p,0x68c,0,host);
    }[[fallthrough]];
    case 1:if(!player_movement(p,g.input,host))return -2;break;
    case 4:if(signed_word(p.get(0x690))<12)break;if(!death(p,g,host))return -2;[[fallthrough]];
    case 2:
        if(signed_word(p.get(0x690))<30)break;
        if(g.lives<0){if(!host.game_over(g.game_mode==1))return -2;return 3;}
        p.put(0x684,0);g.input.elapsed=1;if(!host.set_frame_rate(1)||!respawn_bank(p,host))return -2;
        g.bombs=3;if(!host.bombs_changed(3,g.bomb_fragments))return -2;
        for(u32 i=0;i<3;++i)p.put(0x66c+i*4,p.get(0x5e0+i*4));
        p.put(0x5ec,0);p.put(0x5f0,61440);p.put(0x5e0,0);p.put(0x5e4,word(480.f));
        reset(p,0x18468,280,host);reset(p,0x68c,0,host);break;
    case 3:if(signed_word(p.get(0x690))==15&&!host.cancel_all_lasers(1,false))return -2;break;
    default:break;
    }
    p.put(0xd6dc,word(1.f));for(u32 i=0;i<3;++i)p.put(0xd6e0+i*4,word(g.wind[i]));
    for(u32 i=0;i<256;++i){const u32 at=0xde18+i*0xa4;if((p.get(at+0x10)&1)&&!bank(p,at,g.input.elapsed,host))return -2;}
    bool blink=false;
    if(signed_word(p.get(0x1846c))>0||(p.get(0x1847c)&0x20)){
        if(!tick(p,0x18468,true,host))return -2;
        blink=p.get(0x690)!=p.get(0x68c)&&signed_word(p.get(0x690))%3==0;
    }
    if(blink){p.put(0x2c,(p.get(0x2c)&~0x40000u)|0x20000);p.put(0x54c,0xff0000ff);}
    else p.put(0x2c,p.get(0x2c)&0xfff9ffff);
    if(!host.animate_player(p))return -2;
    const bool scaled=(p.get(0x1847c)&8)!=0;
    if(scaled){
        if(p.get(0x184a8)){float value;if(!scalar_interpolate({p.data.data()+0x18480},host,value))return -2;p.put(0x184b0,word(value));}
        const bool flash=p.get(0x184a8)&&signed_word(p.get(0x690))%3==0;
        p.put(0x74,flash?word(1.f):p.get(0x184b0));p.put(0x78,p.get(0x74));
    }else{p.put(0x74,word(1.f));p.put(0x78,word(1.f));}
    p.put(0x2c,p.get(0x2c)|8);
    const float scale=scaled?p.floating(0x184b0):1.f;
    for(u32 group=0;group<4;++group){const u32 out=group==0?0x630:group==1?0x18310:group==2?0x18328:0x18340;
        const u32 sizes=group==0?0x648:group==2?0x660:0x654;
        for(u32 i=0;i<3;++i){float half=p.floating(sizes+i*4);if(group==1)half*=.5f;half*=scale;
            p.put(out+i*4,word(p.floating(0x5e0+i*4)-half));p.put(out+12+i*4,word(p.floating(0x5e0+i*4)+half));}
    }
    if(!tick(p,0x68c,false,host)||!tick(p,0x6a0,false,host)||!tick(p,0x6b4,false,host))return -2;
    if(!g.message&&g.input.gameplay&&!(g.root_flags&0x4000)&&signed_word(p.get(0x6b8))>=20&&!(p.get(0x1847c)&0xa)){
        if(!host.shoot(p,g)||!host.update_shots(p))return -2;return 1;
    }
    reset(p,0x182ec,-1,host);p.put(0xde0c,0);p.data[0xde10]=0;reset(p,0x182c4,0,host);
    if(!host.retire_visual(p.get(0x182d8)))return -2;p.put(0x182d8,0);
    mute(g,30);mute(g,55);
    return host.update_shots(p)?1:-2;
}
}
