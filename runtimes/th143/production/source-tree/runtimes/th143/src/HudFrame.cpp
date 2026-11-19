#include "HudFrame.hpp"
#include "DirectionVector.hpp"
#include <cmath>
namespace th143 {
namespace {
struct Frame {
    AnmView o;AnmWorld& w;HudFrameHost& h;
    bool tick(u32 at){
        const u32 old=o.get(at+4),token=o.get(at+12);o.put(at,old);float rate=1;
        if(token&&!h.timer_rate(token,rate))return false;
        const bool unit=!token||(rate>real(0x3f7d70a4)&&rate<real(0x3f8147ae));const float value=o.floating(at+8)+(unit?1.f:rate);
        o.put(at+4,unit?old+1:value>=-2147483648.f&&value<2147483648.f?u32(i32(value)):0x80000000);o.put(at+8,word(value));return true;
    }
    bool owner(u32 global,AnmView& out){return h.hud_owner(global,out);}
    AnmView raw(u32 at){return w.state(o.get(at));}
    AnmView find(u32 at){auto vm=w.find(o.get(at));if(!vm.data){o.put(at,0);w.error=0xf2000000|at;}return vm;}
    bool signal(u32 at,i32 value,bool immediate=false){return signal_animation(w,o.get(at),value,immediate,&h);}
    bool single(AnmView v,i32 value,bool immediate=false){return signal_animation_vm(w,v,value,immediate,&h);}
    bool create(u32 at,i32 script){
        const u32 token=o.get(0x2ac);auto* r=w.resource(token);if(!r||script<0||u32(script)>=r->templates.size())return false;
        ++w.instances.resource_uses[token];u32 self;AnmView vm;if(!w.acquire_state(self,vm))return false;
        anm_copy_template(vm,self,{r->templates[script].data()},w.global_rate_token());vm.put(0x1c,vm.get(0x1c)|0x200);
        for(u32 off:{0x59c,0x5a0,0x5a4,0x50})vm.put(off,0);
        if(anm_step(vm,w)==-2){u16 opcode=0;w.read(vm.get(0x28),&opcode,2);w.error=(u32(script+1)<<16)|opcode;return false;}u32 handle;if(!w.instances.registry.insert(vm,self,false,false,handle))return false;o.put(at,handle);return true;
    }
    bool retire(u32 at){if(!w.mark_retirement(o.get(at)))return false;o.put(at,0);return true;}
    bool countdown(AnmView player,AnmView manager){
        u32 flags=o.get(0x180);
        if(!(flags&1)){if(player.data&&player.floating(0x5e4)>400.f&&player.floating(0x5e0)<-64.f)flags|=1;}
        else if(player.data&&(384.f>player.floating(0x5e4)||player.floating(0x5e0)>-64.f))flags&=~1u;
        o.put(0x180,flags);
        auto first=raw(0x98),second=raw(0x9c);if(!first.data||!second.data)return false;
        if(manager.data&&signed_word(o.get(0x1a0))>=0&&manager.get(0x5c)&&!(manager.get(0x9c)&1)&&!o.get(0x198)){
            first.put(0x18,first.get(0x18)|2);second.put(0x18,second.get(0x18)|2);
            AnmView extra;if(!owner(0x4e6a0c,extra)||!extra.data||!player.data)return false;const bool variant=extra.get(0x7c)&0x100;
            const u32 mode=(o.get(0x180)>>9)&3;
            if(mode==0){
                if((!variant&&128.f>player.floating(0x5e4))||(variant&&player.floating(0x5e4)>320.f)){
                    o.put(0x180,(o.get(0x180)&~0x400u)|0x200);
                    if(!single(first,5)||!single(second,5)||!signal(0x120,5))return false;
                }
            }else{
                if(mode==1){
                    if((!variant&&160.f>player.floating(0x5e4))||(variant&&player.floating(0x5e4)>288.f)){
                        if(!single(first,4)||!single(second,4)||!signal(0x120,4))return false;
                        o.put(0x180,o.get(0x180)&~0x600u);
                    }
                }else{
                    if(!single(first,4,true)||!single(second,4,true))return false;
                    o.put(0x180,o.get(0x180)&~0x600u);
                }
            }
            const i32 seconds=signed_word(o.get(0x1a0)),previous=signed_word(o.get(0x1a8));
            if(seconds<previous){if(seconds<5){if(!single(first,9)||!single(second,9)||!h.hud_sound(12))return false;}else if(seconds<10){if(!single(first,8)||!single(second,8)||!h.hud_sound(11))return false;}}
            else if(seconds>previous)if(!single(first,7)||!single(second,7))return false;
            if(seconds!=previous){
                if(first.get(0x30)&&!anm_bind_sprite(first,239+seconds/10,w))return false;
                if(second.get(0x30)&&!anm_bind_sprite(second,239+seconds%10,w))return false;
            }
            o.put(0x1a8,o.get(0x1a0));
        }else{
            first.put(0x18,first.get(0x18)&~2u);second.put(0x18,second.get(0x18)&~2u);o.put(0x180,(o.get(0x180)&~0x200u)|0x400);
        }return true;
    }
    bool bars(AnmView manager){
        if(!manager.data||(manager.get(0x9c)&1))return true;
        for(u32 i=0;i<2;++i){
            if(!owner(0x4e6a48,manager)||!manager.data)return false;
            const u32 base=i*0x54,token=manager.get(0x5c+i*4);
            if(!token){
                for(u32 at:{0x1ac,0x1bc,0x1c4,0x1cc,0x1d4})o.put(base+at,0);
                if(o.get(base+0x1f8)){for(u32 j=0;j<7;++j)if(!retire(base+0x1dc+j*4))return false;o.put(base+0x1f8,0);}
                if(!i&&!retire(0xdc))return false;continue;
            }
            AnmView boss;if(!h.hud_actor(token,boss)||!boss.data)return false;
            if(signed_word(boss.get(0x5208))>=100000||(boss.get(0x52f0)&0x31)||signed_word(boss.get(0x528c))>0||o.get(0x198)){
                if(o.get(base+0x1f8)){for(u32 j=0;j<7;++j)if(!retire(base+0x1dc+j*4))return false;o.put(base+0x1f8,0);}continue;
            }
            const u32 hp=boss.get(0x5208);o.put(base+0x1b4,hp);
            const float ratio=float(signed_word(hp))/float(signed_word(boss.get(0x520c)));o.put(base+0x1b0,word(ratio));
            float smooth=o.floating(base+0x1ac);if(ratio>smooth){smooth+=real(0x3ccccccd);o.put(base+0x1ac,word(smooth));}
            smooth=o.floating(base+0x1ac);if(smooth>ratio)o.put(base+0x1ac,word(ratio));
            if(!o.get(base+0x1f8)){
                const i32 scripts[7]={223,224,225,226,226,226,226};
                for(u32 j=0;j<7;++j)if(!create(base+0x1dc+j*4,scripts[j]))return false;o.put(base+0x1f8,1);
            }
            auto ring=find(base+0x1dc);if(!ring.data)return false;
            ring.put(0x48,word(o.floating(base+0x1ac)*real(0xc0c90fdb)));ring.put(0x18,ring.get(0x18)|4);
            const float x=boss.floating(0x1234)*2.f,y=boss.floating(0x1238)*2.f;const u32 z=boss.get(0x123c);
            for(u32 j=0;j<3;++j){auto vm=find(base+0x1dc+j*4);if(!vm.data)return false;vm.put(0x59c,word(x));vm.put(0x5a0,word(y));vm.put(0x5a4,z);}
            float accumulated_z=0;
            for(u32 j=0;j<4;++j){
                auto vm=find(base+0x1e8+j*4);if(!vm.data)return false;const float mark=o.floating(base+0x1bc+j*8);
                if(mark!=0&&mark<o.floating(base+0x1ac)){
                    vm.put(0x18,vm.get(0x18)|2);float angle=real(0xc0490fdb)-mark*real(0x40c90fdb);u32 counter=0;
                    while(angle>real(0x40490fdb)){angle-=real(0x40c90fdb);if(counter++>32)break;}
                    while(real(0xc0490fdb)>angle){angle+=real(0x40c90fdb);if(counter++>32)break;}
                    vm.put(0x50,word(angle));vm.put(0x18,vm.get(0x18)|4);DirectionVector v;if(!direction_vector(angle,1.f,v))return false;
                    //4b4f20 supplies sine,4b4d60 cosine; retain their separate
                    // float stores and the original zero-term arithmetic.
                    float marker_x=v.x*0.f-v.y*112.f;marker_x+=x;float marker_y=v.x*112.f+v.y*0.f;marker_y+=y;
                    accumulated_z=boss.floating(0x123c)+accumulated_z;vm.put(0x59c,word(marker_x));vm.put(0x5a0,word(marker_y));vm.put(0x5a4,word(accumulated_z));
                }else vm.put(0x18,vm.get(0x18)&~2u);
            }
            if(!owner(0x4e6a48,manager)||!manager.data||!h.hud_actor(manager.get(0x5c+i*4),boss)||!boss.data)return false;
            AnmView player;if(!owner(0x4e6b88,player)||!player.data)return false;
            const float dx=boss.floating(0x1234)-player.floating(0x5e0),dy=boss.floating(0x1238)-player.floating(0x5e4);const float distance=dx*dx+dy*dy;
            if(o.get(base+0x1fc)){if(!(distance<real(0x46100000))){for(u32 j=0;j<7;++j)if(!signal(base+0x1dc+j*4,2))return false;o.put(base+0x1fc,0);}}
            else if(real(0x45c80000)>distance){for(u32 j=0;j<7;++j)if(!signal(base+0x1dc+j*4,3))return false;o.put(base+0x1fc,1);}
        }return true;
    }
    bool icons(){
        for(u32 i=0;i<10;++i){const u32 at=0xe0+i*4;
            if(signed_word(i)<signed_word(o.get(0x15c))){if(!o.get(at)&&!create(at,i32(i)+58))return false;}
            else if(o.get(at)){if(!signal(at,1))return false;o.put(at,0);}
        }return true;
    }
    bool arrow(AnmView manager){
        if(!manager.data)return true;AnmView boss{nullptr};
        if(manager.get(0x5c)&&(!h.hud_actor(manager.get(0x5c),boss)||!boss.data))return false;
        if(boss.data&&!(boss.get(0x52f0)&0x21)){
            auto vm=find(0xa0);if(!vm.data)return false;vm.put(0x18,vm.get(0x18)|2);
            AnmView extra;if(!owner(0x4e6a0c,extra)||!extra.data)return false;
            const bool special=extra.get(0x7c)&1;const i32 count=signed_word(boss.get(0x5210));const u32 mode=(o.get(0x180)>>1)&3;
            if(mode==0){if(count<(special?2000:700)){if(!single(vm,7))return false;o.put(0x180,(o.get(0x180)&~4u)|2);}}
            else if(mode==1){if(count<(special?1000:400)){if(!single(vm,8))return false;o.put(0x180,(o.get(0x180)&~2u)|4);}}
            else if(mode==2){if(count<(special?400:200)){if(!single(vm,9))return false;o.put(0x180,o.get(0x180)|6);}}
            else if(count>(special?400:200)){if(!single(vm,10))return false;o.put(0x180,o.get(0x180)&~6u);}
            float x=boss.floating(0x1234)+128.f;x+=192.f;x*=2.f;vm.put(0x59c,word(x));vm.put(0x5a0,0x44700000);
            AnmView player;if(!owner(0x4e6b88,player)||!player.data)return false;
            const float distance=std::fabs(boss.floating(0x1234)-player.floating(0x5e0));
            u8 alpha=255;if(distance<64.f){float value=distance*191.f;value*=real(0x3c800000);const u32 converted=value>=-2147483648.f&&value<2147483648.f?u32(i32(value)):0x80000000;alpha=u8(converted+64);}
            vm.data[0x537]=alpha;const float position=boss.floating(0x1234);if(-192.f>position||position>192.f)vm.data[0x537]=0;
        }else{
            auto vm=w.find(o.get(0xa0));if(vm.data&&!w.flag(o.get(0xa0),false))return false;
        }return true;
    }
};
}
bool update_hud(AnmView owner,AnmWorld& world,HudFrameHost& host){
    auto failed=[&](u32 stage){if(!world.error)world.error=0xf1000000|stage;return false;};
    Frame f{owner,world,host};if((owner.get(0x180)&0x100)&&!f.tick(0x184))return failed(1);
    if(owner.get(0x11c)&&!world.find(owner.get(0x118)).data){owner.put(0x118,0);owner.put(0x11c,0);}
    AnmView player,manager;if(!f.owner(0x4e6b88,player)||!f.owner(0x4e6a48,manager))return failed(2);
    if(!f.countdown(player,manager))return failed(3);
    if(!f.bars(manager))return failed(4);
    if(!f.icons())return failed(5);
    if(!f.owner(0x4e6a48,manager)||!f.arrow(manager))return failed(6);
    return f.tick(0x124)||failed(7);
}
}
