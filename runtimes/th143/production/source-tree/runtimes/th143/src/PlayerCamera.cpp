#include "PlayerCamera.hpp"
#include <cmath>
namespace th143 {
namespace {
void reset(AnmView v,u32 at,u32 value,PlayerCameraHost& h){const u32 f=v.get(at+16);if(!(f&1)){v.put(at+12,h.global_rate_token());v.put(at+16,f|1);}v.put(at,value-1);v.put(at+4,value);v.put(at+8,word(float(signed_word(value))));}
bool tick(AnmView v,PlayerCameraHost& h){const u32 token=v.get(0x10),old=v.get(8);v.put(4,old);float r=1;if(token&&!h.timer_rate(token,r))return false;const bool unit=!token||(r>real(0x3f7d70a4)&&r<real(0x3f8147ae));const float value=v.floating(12)+(unit?1.f:r);v.put(12,word(value));v.put(8,unit?old+1:value>=-2147483648.f&&value<2147483648.f?u32(i32(value)):0x80000000);return true;}
AnmView resolve(AnmWorld& w,AnmView option,u32 at){auto vm=w.find(option.get(at));if(!vm.data)option.put(at,0);return vm;}
}
bool update_player_camera(AnmView option,AnmView equipment,PlayerState* player,AnmView cheat,PlayerCameraGlobals& g,AnmWorld& world,PlayerCameraHost& host){
    bool manager=false,actor=false;std::array<float,3> target;if(!host.camera_enemy(manager,actor,target))return false;if(!manager)return true;if(!player)return false;auto& p=*player;
    float angle=real(0xbfc90fdb);if(actor){const u32 at=p.get(0x1847c)&0x100?0x184b4:0x5e0;const float x=target[0]-p.floating(at),y=target[1]-p.floating(at+4);angle=x==0.f&&y==0.f?real(0x3fc90fdb):float(std::atan2(double(y),double(x)));}
    auto ui=[&](i32 child,i32 signal){return signal_cheat_child(cheat,cheat.get(0x2b8),child,signal,world);};
    auto death=[&](){return equipment.get(0x1c)&&g.secondary==3&&p.get(0x684)==4;};
    if(!option.get(0x1c)){
        const float sine=float(std::sin(double(angle))),cosine=float(std::cos(double(angle)));
        option.put(0x54,word(p.floating(0x5e0)+(cosine*64.f-sine*0.f)));option.put(0x58,word(p.floating(0x5e4)+(sine*64.f+cosine*0.f)));option.put(0x5c,0);
        auto vm=world.find(option.get(0x24));if(vm.data){vm.put(0x18,vm.get(0x18)|4);vm.put(0x50,word(angle));}vm=world.find(option.get(0x24));if(vm.data)for(u32 i=0;i<3;++i)vm.put(0x59c+i*4,option.get(0x54+i*4));
        if(signed_word(option.get(0x18))>0&&option.get(8)==option.get(0x44)){if(!signal_animation(world,option.get(0x24),2)||!ui(11,60))return false;}
        bool busy=false;if(equipment.get(0x14)&&!host.bomb_option_busy(equipment.get(0x14),busy))return false;
        if(!busy&&(p.get(0x684)==1||death())&&signed_word(option.get(0x18))>0&&(g.fresh&2)&&signed_word(option.get(8))>=signed_word(option.get(0x44))){
            if(!ui(11,6)||!ui(7,6))return false;if(equipment.get(0x1c)&&!host.bomb_alternate_release())return false;
            if(death()){p.put(0x684,1);u32 ignored;if(!world.create_at(p.get(0x10),22,-1,{p.floating(0x5e0),p.floating(0x5e4),p.floating(0x5e8)},ignored)||!ui(12,6)||!ui(8,6))return false;}
            equipment.put(0x18,equipment.get(0x18)+1);p.put(0x1847c,p.get(0x1847c)|0x12);option.put(0x1c,1);
            if(!host.bomb_sound(80,option.floating(0x54)))return false;reset(option,4,0,host);u32 handle;if(!world.create_at(p.get(0x10),9,-1,{0,0,0},handle))return false;option.put(0x28,handle);
            vm=resolve(world,option,0x28);if(!vm.data)return false;vm.put(0x240,option.get(0x40));vm.put(0x244,0);vm.put(0x204,vm.get(0x60));vm.put(0x208,vm.get(0x64));vm.put(0x20c,0x3e4ccccd);vm.put(0x210,0x3e4ccccd);reset(vm,0x22c,0,host);
            vm=resolve(world,option,0x24);if(!vm.data)return false;vm.put(0x18,vm.get(0x18)|8);vm.put(0x68,option.get(0x50));vm.put(0x6c,option.get(0x50));if(!ui(11,59))return false;
        }
    }
    if(option.get(0x1c)==1){
        if(!host.camera_rate(.25f))return false;const u32 k=g.held;const u32 d=(k&0x50)==0x50?5:(k&0x60)==0x60?7:(k&0x90)==0x90?6:(k&0xa0)==0xa0?8:(k&0x20)?2:(k&0x10)?1:(k&0x40)?3:(k>>5)&4;
        static constexpr float directions[9][2]={{0,0},{0,-1},{0,1},{-1,0},{1,0},{-1,-1},{1,-1},{-1,1},{1,1}};const float speed=d>=5?real(0x3f350781):1.f;
        option.put(0x54,word(option.floating(0x54)+speed*directions[d][0]));option.put(0x58,word(speed*directions[d][1]+option.floating(0x58)));
        for(u32 at:{0x24,0x28}){auto vm=world.find(option.get(at));if(vm.data)for(u32 i=0;i<3;++i)vm.put(0x59c+i*4,option.get(0x54+i*4));}
        if(p.get(0x684)!=1||(g.released&2)||signed_word(option.get(8))>=signed_word(option.get(0x40))){
            if(!host.bomb_stop_sound(80)||!host.bomb_sound(79,option.floating(0x54))||!host.camera_rate(real(0x3a83126f)))return false;option.put(0x1c,2);reset(option,4,0,host);option.put(0x20,0);
            if(!signal_animation(world,option.get(0x24),3,true)||!signal_animation(world,option.get(0x28),1))return false;
            u32 token;AnmView surface{nullptr};std::array<float,2> texture;if(!host.camera_surface(token,surface,texture)||!surface.data)return false;option.put(0x60,token);
            const float width=option.floating(0x50)*60.f,height=option.floating(0x50)*80.f,halfwidth=width*-.5f,halfheight=height*-.5f;
            const float sine=float(std::sin(double(angle))),cosine=float(std::cos(double(angle)));
            const std::array<float,4> xs{halfwidth,width*.5f,halfwidth,width*.5f},ys{halfheight,halfheight,height*.5f,height*.5f};
            for(u32 i=0;i<4;++i){float x=cosine*xs[i]-sine*ys[i];float y=sine*xs[i]+cosine*ys[i];x+=option.floating(0x54);y+=option.floating(0x58);x+=320.f;y+=16.f;x*=g.viewport_scale;y*=g.viewport_scale;x/=texture[0];y/=texture[1];surface.put(0x3b8+i*8,word(x));surface.put(0x3bc+i*8,word(y));}
        }
    }else if(option.get(0x1c)==2){
        option.put(0x20,option.get(0x20)+1);if(!host.camera_rate(real(0x3a83126f)))return false;
        if(option.get(0x20)==1){
            const i32 index=signed_word(option.get(0x48));AnmView surface{nullptr};std::array<float,2> texture;if(!host.camera_surface_view(option.get(0x60),surface,texture)||!surface.data)return false;
            const std::array<float,3> initial{(float(index%2)*60.f)*g.viewport_scale+320.f,(float(index/2)*80.f)*g.viewport_scale+0.f,0.f};for(u32 i=0;i<3;++i)surface.put(0x59c+i*4,word(initial[i]));
            if(!host.camera_request_capture())return false;i32 script=-1;if(g.screen_width==640)script=index*3+1;else if(g.screen_width==960)script=index*3+28;else if(g.screen_width==1280)script=index*3+55;
            if(script>=0){u32 handle;if(index<0||index>7||!host.camera_photo(script,handle))return false;option.put(0x2c+u32(index)*4,handle);}
            const float random=world.animation_rng.signed_unit();const std::array<float,3> start{(option.floating(0x54)+320.f)*g.viewport_scale,(option.floating(0x58)+16.f)*g.viewport_scale,0};
            const std::array<float,3> destination{(random*12.f+64.f)*g.viewport_scale,g.viewport_scale*(416.f-float(index)*50.f),0};
            auto photo=resolve(world,option,0x2c+u32(index)*4);if(!photo.data)return false;photo.put(0xec,60);photo.put(0xf0,4);
            for(u32 i=0;i<3;++i){photo.put(0xb4+i*4,0);photo.put(0xc0+i*4,0);photo.put(0x9c+i*4,word(start[i]));photo.put(0xa8+i*4,word(destination[i]));}reset(photo,0xd8,0,host);
            option.put(0x48,option.get(0x48)+1);option.put(0x18,option.get(0x18)-1);if(!option.get(0x18)&&!signal_animation(world,option.get(0x24),5))return false;
        }
        if(option.get(0x20)==2){
            if(!host.camera_rate(real(0x3a83126f)))return false;const std::array<float,3> size{option.floating(0x50)*60.f,option.floating(0x50)*80.f,0};
            if(!host.camera_bullets(option.sub(0x54),size,angle)||!host.camera_lasers(option.sub(0x54),size,angle))return false;p.put(0x1847c,p.get(0x1847c)&~0x12u);auto vm=resolve(world,option,0x24);if(!vm.data)return false;vm.put(0x18,vm.get(0x18)|8);vm.put(0x68,option.get(0x4c));vm.put(0x6c,option.get(0x4c));
        }
        if(option.get(0x20)==30){if(!host.camera_rate(1.f))return false;option.put(0x1c,0);reset(option,4,0,host);}
    }
    return tick(option,host);
}
}
