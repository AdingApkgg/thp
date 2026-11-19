#include "RootLoad.hpp"
namespace th143 {
namespace {
struct Loader {
    RootState& root;u32 self;RootLoadHost& h;u32 budget;u32 result=0;
    bool read(u32 p,u32& value){if(p>=self&&std::uint64_t(p)+4<=std::uint64_t(self)+root.data.size()){value=root.view().get(p-self);return true;}return h.load_read(p,&value,4);}
    bool write(u32 p,u32 value){if(p>=self&&std::uint64_t(p)+4<=std::uint64_t(self)+root.data.size()){root.view().put(p-self,value);return true;}return h.load_write(p,&value,4);}
    bool mask(u32 p,u32 and_mask,u32 or_mask=0){u32 value;return read(p,value)&&write(p,(value&and_mask)|or_mask);}
    bool call(u32 entry,u32 owner=0,std::initializer_list<u32> args={}){return h.load_call(entry,owner,args,result);}
    bool indirect(u32 entry,u32 global){u32 owner;return read(global,owner)&&owner&&call(entry,owner);}
    bool increment(u32 p){u32 value;if(!read(p,value))return false;return signed_word(value)>=9999999||write(p,value+1);}
    bool enable(){for(u32 at:{8,12}){const u32 p=root.view().get(at);if(p&&!mask(p+4,0xffffffff,2))return false;}return true;}
    bool fail(i32& status){root.view().put(0x80,root.view().get(0x80)|8);if(!call(0x445110,0x4e47d0)||!write(0x4e516c,0)||!write(0x4e5168,1)||!enable())return false;status=-1;return true;}
    bool sleep(u32 ms){return budget--&&h.load_sleep(ms);}
    bool register_root(u32 entry,u32 priority,bool draw,u32 offset){
        if(!call(0x401830,0,{entry}))return false;const u32 token=result;if(!token||!mask(token+4,~2u)||!write(token+0x24,self)||!call(draw?0x401490:0x4013e0,0,{token,priority}))return false;
        root.view().put(offset,token);return true;
    }
};
u32 truncate(float value){return value>=-2147483648.f&&value<2147483648.f?u32(i32(value)):0x80000000;}
}
bool load_root(RootState& root,u32 self,RootLoadHost& host,i32& status,u32 wait_budget){
    Loader m{root,self,host,wait_budget};auto r=root.view();r.put(0x80,r.get(0x80)|4);
    if(!host.load_float_environment())return false;
    u32 manager,active,flags;
    if(!m.read(0x538de8,manager)||!manager||!m.read(manager+0x20,active))return false;
    while(signed_word(active)>=0){
        if(!m.read(0x4e4ef4,flags))return false;if(flags&0x180)return m.fail(status);
        if(!m.sleep(1)||!m.read(0x538de8,manager)||!manager||!m.read(manager+0x20,active))return false;
    }
    u32 background,global_root,save;
    if(!m.read(0x4e498c,background)||!background||!host.load_signal(background,2,true)||!m.read(0x4e6a5c,global_root)||!global_root||!m.read(0x4e6b9c,save)||!save||
       !m.write(0x4e40b0,word(1.f))||!m.mask(global_root+0x80,~0x4000u)||!m.write(0x4e47a8,0)||!m.write(0x4e47ac,0))return false;
    u32 mode,scene,primary,seed;
    if(!m.read(global_root+0x94,mode)||!m.read(0x4e479c,scene)||!m.read(0x4e4710,primary))return false;
    if(scene>=77||primary>=9)return false;
    if(!mode){
        const u32 record=save+scene*0x314;
        if(!m.write(record+0x14,scene)||!m.increment(record+0x44+primary*4)||!m.increment(record+0x6c)||!m.increment(save+0xed1c+primary*0x34)||!m.increment(save+0xef24)||
           !m.read(record+0x70,seed)||!m.write(0x4e4790,seed)||!m.write(0x4e4794,0))return false;
    }else if(!m.read(0x4e4790,seed))return false;
    u32 value,new_game;
    if(!m.read(save+0xed30+primary*0x34,value)||!m.write(0x4e4720,value)||!m.read(save+0xed34+primary*0x34,value)||!m.write(0x4e4724,value))return false;
    u8 alternate;if(!host.load_read(save+0xefad,&alternate,1)||!m.write(0x4e4728,alternate)||!m.write(0x4e474c,0)||!m.read(0x4e4ec8,new_game))return false;
    if(new_game){
        if(!m.write(0x4e4708,0)||!m.write(0x4e46f8,0)||!m.call(0x434190,0x4e46f0)||!m.write(0x4e475c,0))return false;
        u32 difficulty,first,second;
        if(!m.read(0x4e46fc,difficulty)||difficulty>=6||!m.read(0x4c5858+difficulty*4,first)||!m.read(0x4c5840+difficulty*4,second)||
           !m.write(0x4e4744,first*100)||!m.write(0x4e4748,second*100))return false;
        float amount=float(signed_word(first*100));amount/=100.f;amount*=100.f;
        if(!m.write(0x4e4740,truncate(amount))||!m.read(0x4c5828+difficulty*4,value)||!m.write(0x4e47c0,value)||!m.read(0x4e47b0,flags))return false;
        if(((flags>>5)&3)==2){u32 hud;if(!m.read(0x4e6a54,hud)||!m.write(0x4e4768,0))return false;if(hud){if(!m.read(0x4e476c,value)||!m.call(0x4319b0,0,{0,value}))return false;}}
        if(!m.call(0x44ca60))return false;if(!m.result)return m.fail(status);
        if(!m.call(0x450660))return false;if(!m.result)return m.fail(status);
        if(!m.read(0x4e4754,value))return false;
        if(signed_word(value)<0){if(!m.mask(0x4e47b0,~8u)||!m.write(0x4e4750,value))return false;}
        else{if(!m.read(0x4e4758,value)||!m.mask(0x4e47b0,~8u)||!m.write(0x4e4750,signed_word(value)>0?value:0))return false;}
    }else{
        if(!m.read(0x4e46f8,value))return false;if(value>seed)seed=value;if(!m.write(0x4e4790,seed))return false;
    }
    u32 descriptor;
    if(!m.register_root(0x433720,15,false,8)||!m.register_root(0x433730,2,true,12)||!m.read(0x4e6bac,descriptor)||!descriptor)return false;
    for(u32 i=0;i<23;++i){if(!m.read(0x4e49a4+i*4,value))return false;r.put(0x24+i*4,value);}
    if(!m.read(descriptor,value))return false;r.put(4,value);
    if(!m.read(0x4e47b0,flags))return false;
    if(!(flags&4)){
        if(!m.call(0x454740,r.get(0x94)))return false;if(!m.result)return m.fail(status);
        if(!m.read(0x4e6bac,descriptor)||!m.read(descriptor+4,value)||!m.call(0x40d550,value))return false;if(!m.result)return m.fail(status);
        for(u32 entry:{0x42d1b0,0x412880,0x434fc0,0x438dd0,0x447d20,0x45d4e0}){if(!m.call(entry))return false;if(!m.result)return m.fail(status);}
    }else{
        if(!m.call(0x4555f0)||!m.indirect(0x42c4e0,0x4e6a54)||!m.read(0x4e6bac,descriptor)||!m.read(descriptor+4,value)||!m.call(0x40d550,value))return false;
        if(!m.result)return m.fail(status);
    }
    if(!m.read(0x4e47b0,flags))return false;
    if(!(flags&0x11)){if(!m.read(0x4e6bac,descriptor)||!m.read(descriptor+8,value)||!m.call(0x41ec00,value))return false;if(!m.result)return m.fail(status);}
    else if(!m.call(0x432350,0,{0}))return false;
    if(!m.call(0x418880))return false;if(!m.result)return m.fail(status);
    if(!m.call(0x4112e0)||!m.call(0x436ba0))return false;
    u32 cheats,x,y;
    if(!m.read(0x4e6b68,cheats)||!cheats||!m.read(0x4c9fa4,x)||!m.read(0x4c9f84,y)||!m.write(cheats+0x484,x)||!m.write(cheats+0x488,y)||!m.write(cheats+0x48c,0)||!m.read(cheats+0x2b0,value))return false;
    if(value&&!m.call(0x438380,cheats))return false;
    if(!m.read(0x4e6a5c,global_root)||!m.read(global_root+0x94,mode)||!m.read(0x4e47b0,flags)||!m.read(0x4e479c,scene))return false;
    u32 cheat_mode=1;
    if(!mode&&!(flags&1)&&scene==35){u8 record;if(!m.read(0x4e6b9c,save)||!save||!host.load_read(save+0xf08a,&record,1))return false;if(!record)cheat_mode=3;}
    if(!m.call(0x436c30,0,{cheat_mode})||!m.read(0x4e47b0,flags)||!m.read(0x4e479c,scene))return false;
    if((flags&0x1000)&&(scene==2||scene==14||scene==28))flags&=~0x400u;
    if(!(flags&1)&&(!(flags&0x1000)||scene==2||scene==14||scene==28||scene==36)){
        if(!m.write(0x4e47b0,flags|0x200)||!m.read(0x4e6bac,descriptor)||!m.read(descriptor+12,value)||!m.call(0x444660,0,{scene,value}))return false;
    }else if(!m.write(0x4e47b0,flags&~0x200u))return false;
    u32 stage;
    if(!m.read(0x4e6a50,stage)||!stage)return false;for(u32 i=0;i<4;++i)if(!m.write(stage+0x24+i*4,0))return false;
    // 4087f0 timer reset preserves flags and an already-bound rate pointer.
    const u32 timer_flags=r.get(0x20);if(!(timer_flags&1)){r.put(0x1c,0x4e40b0);r.put(0x20,timer_flags|1);}
    r.put(0x14,0);r.put(0x18,0);r.put(0x10,0xffffffff);
    if(!m.read(0x53d6d8,value))return false;
    while(value){if(!m.sleep(16)||!m.read(0x53d6d8,value))return false;}
    u32 dirty,field;
    if(!m.read(0x4e47ac,field)||!m.read(0x4e47a4,dirty)||!m.write(0x4e47a4,0)||!m.write(0x4e47ac,dirty?0:field)||!m.call(0x444e00,0x4e47d0))return false;
    r.put(0x80,r.get(0x80)&~4u);
    if(!m.read(0x4e47b0,flags)||!m.write(0x4e516c,0)||!m.write(0x4e5168,1)||!m.write(0x538de4,0)||!m.write(0x4e6b78,0)||!m.write(0x4e47b0,(flags&0xffffefe8)|((flags&1)*2))||!m.write(0x4e6b74,0))return false;
    for(u32 p:{0x4e498c,0x4e4990,0x4e4994,0x4e4998})if(!m.indirect(0x418240,p))return false;
    if(!m.enable())return false;status=0;return true;
}
}
