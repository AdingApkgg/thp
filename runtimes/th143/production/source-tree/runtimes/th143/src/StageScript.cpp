#include "StageScript.hpp"
#include <cmath>
#include <vector>

namespace th143 {
namespace {
u32 truncate(float value){return value>=-2147483648.f&&value<2147483648.f?u32(i32(value)):0x80000000;}
void set_timer(AnmView t,u32 value,u32 rate){if(!(t.get(16)&1)){t.put(12,rate);t.put(16,t.get(16)|1);}t.put(0,value-1);t.put(4,value);t.put(8,word(float(signed_word(value))));}
bool advance(AnmView t,AnmTimerHost& host){const u32 pointer=t.get(12),current=t.get(4);float rate=1;if(pointer&&!host.timer_rate(pointer,rate))return false;
    const bool unit=!pointer||(rate>real(0x3f7d70a4)&&rate<real(0x3f8147ae));const float elapsed=t.floating(8)+(unit?1.f:rate);t.put(0,current);t.put(4,unit?current+1:truncate(elapsed));t.put(8,word(elapsed));return true;
}
void copy3(AnmView s,u32 to,u32 from){for(u32 i=0;i<3;++i)s.put(to+i*4,s.get(from+i*4));}
float wrap(float angle){u32 count=0;while(angle>real(0x40490fdb)){angle-=real(0x40c90fdb);if(count++>32)break;}while(angle<real(0xc0490fdb)){angle+=real(0x40c90fdb);if(count++>32)break;}return angle;}
bool shake(AnmView s,AnmTimerHost& host){
    if(!s.data[0x20]||s.data[0x20]>9)return true;if(s.data[0x20]!=1)return false;
    float phase=s.floating(0x2c)*real(0x40490fdb);phase*=2.f;phase*=.001953125f;phase=wrap(phase);
    const float first=float(std::sin(double(phase)));const float x=first*-20.f;const float second=float(std::sin(double(wrap(phase*2.f))));const float z=second*-10.f;
    s.put(0x42b0,word(x));s.put(0x42b8,word(z));s.put(0x428c,word(first*-.01f));s.put(0x42bc,word(x*-.5f));s.put(0x42c4,word(z*-.5f));
    if(!advance(s.sub(0x24),host))return false;if(signed_word(s.get(0x28))>=512)set_timer(s.sub(0x24),0,host.global_rate_token());return true;
}
}
bool advance_stage_script(StageState& state,u32 self,StageScriptGlobals& g,StageAnimationMemory& memory,AnmVmHost& animations,u32 budget){
    auto s=state.view();g.error_pc=g.error_opcode=0;bool tick=true;
    for(u32 executed=0;;++executed){const u32 pc=s.get(0x4c);u32 time;std::int16_t opcode,length;
        if(executed>=budget||!memory.read_stage_animation_memory(pc,&time,4)||!memory.read_stage_animation_memory(pc+4,&opcode,2)||!memory.read_stage_animation_memory(pc+6,&length,2))return false;
        if(signed_word(time)>signed_word(s.get(0x3c)))break;g.error_pc=pc;g.error_opcode=u32(opcode);
        if(opcode>=0&&opcode<=20)++g.executed[u32(opcode)];
        if(opcode==0){tick=false;break;}if(length<8||(length&3))return false;
        std::vector<u32> args(u32(length-8)/4);if(!args.empty()&&!memory.read_stage_animation_memory(pc+8,args.data(),u32(args.size())*4))return false;
        auto need=[&](u32 n){return args.size()>=n;};auto literal3=[&](u32 at,u32 first){for(u32 i=0;i<3;++i)s.put(at+i*4,args[first+i]);};
        auto curve=[&](u32 at,u32 current,bool hermite){copy3(s,at,current);s.put(at+0x50,args[0]);s.put(at+0x54,hermite?8:args[1]);
            if(hermite){literal3(at+0x18,2);literal3(at+12,5);literal3(at+0x24,8);}else literal3(at+12,2);set_timer(s.sub(at+0x3c),0,animations.global_rate_token());};
        switch(opcode){
        case 1:if(!need(2))return false;set_timer(s.sub(0x38),args[1],animations.global_rate_token());s.put(0x4c,s.get(0x1c)+args[0]);continue;
        case 2:if(!need(3))return false;copy3(s,0x4378,0x4274);literal3(0x4274,0);for(u32 i=0;i<3;++i)s.put(0x4378+i*4,word(s.floating(0x4274+i*4)-s.floating(0x4378+i*4)));break;
        case 3:if(!need(5))return false;curve(0xa8,0x4274,false);break;
        case 4:if(!need(3))return false;literal3(0x4280,0);break;
        case 5:if(!need(5))return false;curve(0x50,0x4280,false);break;
        case 6:if(!need(3))return false;literal3(0x428c,0);break;
        case 7:if(!need(1))return false;s.put(0x42c8,args[0]);break;
        case 8:if(!need(3))return false;s.put(0x439c,args[0]);for(u32 i=0;i<4;++i)s.put(0x438c+i*4,word(float(u8(args[0]>>(i*8)))));s.put(0x4384,args[1]);s.put(0x4388,args[2]);break;
        case 9:{if(!need(5))return false;std::array<u32,7> start,target;for(u32 i=0;i<7;++i)start[i]=s.get(0x4384+i*4);target[0]=args[3];target[1]=args[4];target[6]=args[2];for(u32 i=0;i<4;++i)target[i+2]=word(float(u8(args[2]>>(i*8))));stage_fog_begin(s.sub(0x158),start,target,args[0],args[1],animations.global_rate_token());break;}
        case 10:if(!need(11))return false;curve(0xa8,0x4274,true);break;
        case 11:if(!need(11))return false;curve(0x50,0x4280,true);break;
        case 12:if(!need(1))return false;s.data[0x20]=u8(args[0]);if(!s.data[0x20])for(u32 i=0;i<3;++i)s.put(0x42b0+i*4,0);set_timer(s.sub(0x24),0,animations.global_rate_token());break;
        case 13:if(!need(1))return false;g.render_option=args[0];break;
        case 14:{if(!need(3)||args[0]>=8)return false;auto vm=s.sub(0x20c+args[0]*AnmView::bytes);
            if(signed_word(args[1])>=0){auto source=memory.stage_animation_template(s.get(0x204),signed_word(args[1]));if(!source.data)return false;anm_copy_template(vm,self+0x20c+args[0]*AnmView::bytes,source,animations.global_rate_token());vm.put(0x594,0);if(anm_step(vm,animations)==-2)return false;}
            else vm.put(0x18,vm.get(0x18)&~1u);s.put(0x306c+args[0]*4,args[2]);break;}
        case 17:return false;
        case 18:if(!need(5))return false;curve(0x100,0x428c,false);break;
        case 19:{if(!need(1))return false;std::int16_t count;if(!memory.read_stage_animation_memory(s.get(0x10)+2,&count,2))return false;const u32 signal=args[0]+7;
            for(i32 i=0;i<count;++i){auto vm=memory.stage_animation_storage(s.get(0x208)+u32(i)*AnmView::bytes);if(!vm.data)return false;if(vm.get(0x5c4)){i32 result;if(!animations.callback(vm.get(0x5c4),vm,float(signed_word(signal)),result))return false;}vm.put(0x4a0,signal);}break;}
        case 20:if(!need(1))return false;s.put(0x308c,word(real(args[0])*real(args[0])));break;
        default:break;
        }s.put(0x4c,pc+u32(length));
    }
    if(tick&&!advance(s.sub(0x38),animations))return false;
    for(auto p:{std::array<u32,3>{0x50,0xa0,0x4280},{0xa8,0xf8,0x4274}})if(s.get(p[1])){std::array<u32,3> v;if(!anm_interpolate_vec3(s.sub(p[0]),animations,false,v))return false;for(u32 i=0;i<3;++i)s.put(p[2]+i*4,v[i]);}
    if(s.get(0x1f8)){std::array<u32,7> fog;if(!stage_fog_interpolate(s.sub(0x158),animations,fog))return false;for(u32 i=0;i<7;++i)s.put(0x4384+i*4,fog[i]);}
    if(s.get(0x150)){std::array<u32,3> v;if(!anm_interpolate_vec3(s.sub(0x100),animations,false,v))return false;for(u32 i=0;i<3;++i)s.put(0x428c+i*4,v[i]);}
    if(!shake(s,animations))return false;g.error_pc=g.error_opcode=0;return true;
}
}
