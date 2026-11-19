#include "PlayerShooting.hpp"
#include "DirectionVector.hpp"
#include <cmath>

namespace th143 {
namespace {
float wrap(float a){u32 n=0;while(a>real(0x40490fdb)){a-=real(0x40c90fdb);if(n++>32)break;}
    while(real(0xc0490fdb)>a){a+=real(0x40c90fdb);if(n++>32)break;}return a;}
u32 truncate(float a){return a>=-2147483648.f&&a<2147483648.f?u32(i32(a)):0x80000000u;}
void reset(PlayerState& p,u32 at,i32 value,PlayerShootingHost& host){
    if(!(p.get(at+16)&1)){p.put(at+12,host.global_rate_token());p.put(at+16,p.get(at+16)|1);}
    p.put(at,u32(value)-1);p.put(at+4,u32(value));p.put(at+8,word(float(value)));
}
bool tick(PlayerState& p,u32 at,PlayerShootingHost& host,bool cycle=false){
    const u32 pointer=p.get(at+12),old=p.get(at+4);float rate=1;if(pointer&&!host.timer_rate(pointer,rate))return false;
    const bool unit=!pointer||(rate>real(0x3f7d70a4)&&rate<real(0x3f8147ae));p.put(at,old);
    const float value=cycle?p.floating(at+8)-(unit?14.f:rate*14.f):p.floating(at+8)+(unit?1.f:rate);
    p.put(at+8,word(value));p.put(at+4,!cycle&&unit?old+1:truncate(value));return true;
}
bool velocity(PlayerState& p,u32 at,PlayerShootingHost& host){
    if(p.get(at+0x40)&15)return false;float rate;if(!host.timer_rate(host.global_rate_token(),rate))return false;
    DirectionVector v;if(!direction_vector(p.floating(at+0x1c),p.floating(at+0x18)*rate,v))return false;
    p.put(at+0x34,word(v.x));p.put(at+0x38,word(v.y));return true;
}
bool advance(PlayerState& p,u32 at,PlayerShootingHost& host){
    if(!velocity(p,at,host))return false;
    for(u32 i=0;i<3;++i){float value=p.floating(at+i*4)+p.floating(at+0x34+i*4);
        if(i<2)value=float(std::floor(double(value*100.f)))/100.f;p.put(at+i*4,word(value));}return true;
}
bool pointer_offset(const PlayerShootingConfig& c,u32 token,u32 bytes,u32& at){
    if(token<c.self||std::uint64_t(token)+bytes>std::uint64_t(c.self)+PlayerState::bytes)return false;at=token-c.self;return true;
}
bool region(PlayerState& p,u32 shot,PlayerShootingHost& host,u32& at){
    u32 cursor=p.get(0xde14);if(cursor>256)return false;
    for(u32 n=0;n<256;++n){if(cursor>=256)cursor=0;p.put(0xde14,cursor);at=0xde18+cursor*0xa4;
        if(!(p.get(at+0x10)&1)){
            p.put(at+0x10,(p.get(at+0x10)&~6u)|1);std::memset(p.data.data()+at+0x2c,0,0x44);
            for(u32 i=0;i<3;++i)p.put(at+0x2c+i*4,p.get(shot+0x54+i*4));
            p.put(at+0x24,p.get(shot+0xb0));p.put(at+0x28,p.get(shot+0xb4));p.put(at+0x1c,word(wrap(p.floating(shot+0x70))));p.put(at+0x20,0);
            reset(p,at+0x70,9999999,host);p.put(at+0x84,p.get(shot+0xac));p.put(at+0x88,0);p.put(at+0x8c,9999999);p.put(at+0x90,1);p.put(at+0x94,0);p.put(at+0xa0,0);return true;
        }p.put(0xde14,++cursor);
    }
    // The original returns the cursor pointer even on exhaustion, including
    // its one-past-bank pointer when the scan ends at index256.
    at=0xde18+cursor*0xa4;return at+0xa4<=PlayerState::bytes;
}
bool spawn(PlayerState& p,PlayerShotData& sht,u32 descriptor,u32 shot,i32 time,const PlayerShootingConfig& c,PlayerShootingHost& host,i32& result){
    if(descriptor<sht.token||std::uint64_t(descriptor)+0x58>std::uint64_t(sht.token)+sht.data.size())return false;
    const u32 d=descriptor-sht.token;auto byte=[&](u32 at){return i32(std::int8_t(sht.data[d+at]));};
    p.put(shot+0x98,1);p.put(shot+0xbc,descriptor);reset(p,shot+0x18,0,host);
    p.put(shot+0xac,u32(i32(std::int16_t(sht.get(d+2)))));p.put(shot+0xb0,sht.get(d+12));p.put(shot+0xb4,sht.get(d+16));
    p.put(shot+0x10,(p.get(shot+0x10)&~2u)|((p.get(0x18464)*2)&2));std::memset(p.data.data()+shot+0x54,0,0x44);
    const i32 option=byte(0x20),kind=byte(0x21);
    if(option){const i32 at=0xd664+option*0xe4;if(at<0||u32(at)+0x50>PlayerState::bytes)return false;
        p.put(shot+0x54,word(float(signed_word(p.get(u32(at))))*.0078125f));p.put(shot+0x58,word(float(signed_word(p.get(u32(at)+4)))*.0078125f));}
    else for(u32 i=0;i<3;++i)p.put(shot+0x54+i*4,p.get(0x5e0+i*4));
    if(kind==2||kind==3){if(!c.power_step||(c.power==i32(0x80000000u)&&c.power_step==-1))return false;
        const i32 at=kind==2?0x18300:0x182fc+option*4;if(at<0||u32(at)+4>PlayerState::bytes)return false;p.put(u32(at),u32(c.power/c.power_step));}
    p.put(shot+0x6c,sht.get(d+0x18));float angle=sht.floating(d+0x14);
    if(angle>=1000.f&&option)return false; // Random option dispersion needs its gameplay RNG service.
    if(angle>=995.f&&angle<1000.f&&option){const i32 at=0xd6b0+option*0xe4;if(at<0||u32(at)+4>PlayerState::bytes)return false;angle=p.floating(u32(at));}
    p.put(shot+0x70,word(wrap(angle)));if(!velocity(p,shot+0x54,host))return false;
    p.put(shot+0x54,word(p.floating(shot+0x54)+(sht.floating(d+4)-p.floating(shot+0x88))));
    p.put(shot+0x58,word(p.floating(shot+0x58)+(sht.floating(d+8)-p.floating(shot+0x8c))));
    const i32 script=i32(std::int16_t(sht.get(d+0x22)))+6;u32 handle;
    if(!host.create_shot_visual(p.get(0x10),script,handle))return false;p.put(shot+0x14,handle);auto vm=host.shot_visual(handle);if(!vm.data)return false;
    if(vm.get(0x1c)&0x40){vm.put(0x18,vm.get(0x18)|4);vm.put(0x50,sht.get(d+0x14));}
    u32 area;if(!region(p,shot,host,area))return false;p.put(shot+0xc0,c.self+area);p.put(area+0xa0,0x4518e0);p.put(area+0x8c,10000000);p.put(area+0x98,c.self+shot);p.put(shot+0x10,p.get(shot+0x10)|1);
    if(const u32 callback=sht.get(d+0x28)){i32 status;if(!host.shot_callback(callback,true,p,shot,time,status))return false;
        if(status){p.put(shot+0x98,0);if(!host.retire_shot_visual(p.get(shot+0x14)))return false;p.put(shot+0x14,0);p.put(area+0x10,p.get(area+0x10)&~1u);result=-1;return true;}}
    const i32 sound=std::int16_t(sht.get(d+0x24));if(sound>=0&&!host.shot_sound(sound,p.floating(shot+0x54)))return false;
    for(u32 i=0;i<3;++i)vm.put(0x59c+i*4,p.get(shot+0x54+i*4));result=0;return true;
}
bool emit(PlayerState& p,PlayerShotData& sht,i32 time,const PlayerShootingConfig& c,PlayerShootingHost& host){
    const u32 group=c.alternate&&c.equipment==7?(p.get(0x18464)?6:1):(p.get(0x18464)?5:0);u32 descriptor=sht.get(0xe0+group*4);
    for(u32 n=0;n<sht.data.size()/0x58+1;++n,descriptor+=0x58){
        if(descriptor<sht.token||std::uint64_t(descriptor)+4>std::uint64_t(sht.token)+sht.data.size())return false;const u32 d=descriptor-sht.token;
        const i32 period=std::int8_t(sht.data[d]);if(period<0)return true;if(!period)return false;
        if(time%period!=i32(std::int8_t(sht.data[d+1])))continue;
        const i32 kind=std::int8_t(sht.data[d+0x21]),option=std::int8_t(sht.data[d+0x20]);const i32 gate=kind==3?0x182fc+option*4:0x18300;
        if((kind==2||kind==3)&&(gate<0||u32(gate)+4>PlayerState::bytes||p.get(u32(gate))))continue;
        const u32 token=p.get(0xd6cc);if(!token)continue;u32 shot;if(!pointer_offset(c,token,0xd0,shot))return false;i32 status;
        if(!spawn(p,sht,descriptor,shot,time,c,host,status))return false;if(status)continue;
        const u32 previous=p.get(shot+4),next=p.get(shot+8);u32 at;
        if(previous){if(!pointer_offset(c,previous,12,at))return false;p.put(at+8,next);}if(next){if(!pointer_offset(c,next,8,at))return false;p.put(at+4,previous);}
        p.put(shot+4,0);p.put(shot+8,0);
    }return false;
}
}
bool player_shoot(PlayerState& p,PlayerShotData& sht,const PlayerShootingConfig& c,PlayerShootingHost& host){
    if(p.get(0x684)!=1){p.put(0xde0c,0);p.data[0xde10]=0;return true;}
    if(signed_word(p.get(0x182f0))<0){if(!(c.keys&1))return true;reset(p,0x182ec,0,host);}
    if(p.get(0x182f0)!=p.get(0x182ec)&&!emit(p,sht,signed_word(p.get(0x182f0)),c,host))return false;
    if(signed_word(p.get(0x182f0))>=14){if(c.keys&1)return tick(p,0x182ec,host,true);reset(p,0x182ec,-1,host);return true;}
    return tick(p,0x182ec,host);
}
bool player_update_shots(PlayerState& p,PlayerShotData& sht,const PlayerShootingConfig& c,PlayerShootingHost& host){
    auto recycle=[&](u32 shot){const u32 head=0xd6c8,old=p.get(head+4);u32 at;if(old){if(!pointer_offset(c,old,12,at))return false;p.put(shot+4,old);p.put(at+8,c.self+shot);}if(p.get(head+12))p.put(head+12,c.self+shot);p.put(head+4,c.self+shot);p.put(shot+8,c.self+head);return true;};
    for(u32 index=0;index<256;++index){const u32 shot=0x6c8+index*0xd0;if(!p.get(shot+0x98))continue;
        const u32 descriptor=p.get(shot+0xbc);if(descriptor<sht.token||std::uint64_t(descriptor)+0x58>std::uint64_t(sht.token)+sht.data.size())return false;const u32 d=descriptor-sht.token;bool retired=false;
        if(const u32 callback=sht.get(d+0x2c)){i32 result;if(!host.shot_callback(callback,false,p,shot,0,result))return false;if(result){if(!recycle(shot))return false;continue;}}
        if(!advance(p,shot+0x54,host))return false;auto vm=host.shot_visual(p.get(shot+0x14));
        const u32 kind=sht.data[d+0x21];
        if(!vm.data){p.put(shot+0x98,0);p.put(shot+0x14,0);retired=true;}
        else if(kind!=3&&signed_word(p.get(shot+0x1c))>=10){std::array<std::array<float,2>,4> vertices{};if(!host.shot_vertices(vm,vertices))return false;bool inside=false;
            const float x=float(c.viewport_origin[0]),y=float(c.viewport_origin[1]);for(const auto& v:vertices)if(v[0]>x&&v[0]<x+384.f&&v[1]>y&&v[1]<y+448.f)inside=true;
            if(!inside){if(kind==2)p.put(0x18300,0);if(!host.retire_shot_visual(p.get(shot+0x14)))return false;p.put(shot+0x14,0);p.put(shot+0x98,0);retired=true;}}
        if(retired){if(kind==5){p.put(0x18300,p.get(0x18300)-1);if(p.get(shot+0x10)&0x3c)p.put(0x18304,p.get(0x18304)-1);}
            if(const u32 token=p.get(shot+0xc0)){u32 area;if(!pointer_offset(c,token,0x14,area))return false;p.put(area+0x10,p.get(area+0x10)&~1u);}
            if(!recycle(shot))return false;continue;
        }
        if(const u32 token=p.get(shot+0xc0);token&&(p.get(shot+0x10)&1)){u32 area;if(!pointer_offset(c,token,0xa4,area))return false;
            for(u32 i=0;i<3;++i)p.put(area+0x2c+i*4,p.get(shot+0x54+i*4));p.put(area+0x1c,p.get(shot+0x70));p.put(area+0x24,p.get(shot+0xb0));p.put(area+0x28,p.get(shot+0xb4));p.put(area+0x84,p.get(shot+0xac));}
        for(u32 i=0;i<3;++i)vm.put(0x59c+i*4,p.get(shot+0x54+i*4));if(vm.get(0x1c)&0x40){vm.put(0x18,vm.get(0x18)|4);vm.put(0x50,p.get(shot+0x70));}
        if(!tick(p,shot+0x18,host))return false;
    }
    auto vm=host.shot_visual(p.get(0x182d8));if(!vm.data)p.put(0x182d8,0);else for(u32 i=0;i<3;++i)vm.put(0x59c+i*4,p.get(0x5e0+i*4));return true;
}
}
