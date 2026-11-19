#include "Scheduler.hpp"

namespace th143 {
AnmView Scheduler::at(u32 token){
    if(token>=self&&token<self+data.size())return {data.data()+token-self};
    auto i=records.upper_bound(token);if(i==records.begin())return {nullptr};--i;
    return token-i->first<i->second.size()?AnmView{i->second.data()+token-i->first}:AnmView{nullptr};
}
void Scheduler::construct(u8 fill){
    data.fill(fill);auto initialize=[&](u32 offset){auto s=at(self+offset);s.put(4,s.get(4)&~1u);s.put(0,0);s.put(8,0);s.put(12,0);s.put(16,0);s.put(20,self+offset);s.put(24,0);s.put(28,0);s.put(32,0);};
    initialize(0);initialize(40);at(self).put(0x54,0);records.clear();
}
bool Scheduler::create(u32 token,u32 entry,u8 fill){
    if(records.count(token)||token<self+data.size()&&std::uint64_t(token)+40>self)return false;
    auto& b=records[token];b.fill(fill);auto s=at(token);
    s.put(0,0);s.put(4,(s.get(4)&~1u)|1);s.put(8,entry);s.put(12,0);s.put(16,0);s.put(20,token);s.put(24,0);s.put(28,0);s.put(32,0);return true;
}
bool Scheduler::add(u32 token,i32 priority,bool draw,SchedulerHost& host,u32& result){
    auto r=at(token);if(!r.data)return false;result=0;
    if(r.get(12)){if(!host.invoke(r.get(12),r.get(36),result))return false;r.put(12,0);}
    u32 p=self+(draw?0x3c:0x14);r.put(0,u32(priority));
    while(at(p).get(4)){
        const u32 next=at(p).get(4),record=at(next).get(0);auto target=at(record);if(!target.data)return false;
        if(signed_word(target.get(0))>=priority)break;p=next;
    }
    const u32 next=at(p).get(4),node=token+20;auto n=at(node);
    if(next){n.put(4,next);at(next).put(8,node);}
    if(at(p).get(12))at(p).put(12,node);
    at(p).put(4,node);n.put(8,p);return true;
}
bool Scheduler::remove(u32 token,SchedulerHost& host){
    if(!token)return true;
    u32 found=0;
    for(u32 head:{self+0x14,self+0x3c}){
        for(u32 p=head;p;p=at(p).get(4)){auto n=at(p);if(!n.data)return false;if(n.get(0)==token){found=p;break;}}
        if(found)break;
    }
    if(!found)return true;
    auto s=at(self),n=at(found);if(s.get(0x50)==found)s.put(0x50,n.get(4));
    const u32 previous=n.get(8);if(!previous)return true;
    if(n.get(4))at(n.get(4)).put(8,previous);at(previous).put(4,n.get(4));n.put(4,0);n.put(8,0);
    auto r=at(token);r.put(8,0);
    if(r.get(4)&1){r.put(12,0);r.put(16,0);return host.release_callback(token);}return true;
}
bool Scheduler::dispatch(bool draw,SchedulerHost& host,i32& result,u32 budget){
    auto s=at(self);u32 count=0;u32 p=s.get(draw?0x40:0x18);
    while(p){
        if(!budget--)return false;auto n=at(p);if(!n.data)return false;s.put(0x50,n.get(4));const u32 token=n.get(0);auto r=at(token);if(!r.data)return false;
        if(r.get(8)){
            if(r.get(4)&2){
                if(!draw&&s.get(0x54)){if(r.get(16)){u32 ignored;if(!host.invoke(r.get(16),r.get(36),ignored))return false;}}
                else{
                    for(;;){
                        if(!budget--)return false;u32 code;if(!host.invoke(r.get(8),r.get(36),code))return false;
                        if(code==2&&(r.get(4)&2))continue;
                        if(code==0){if(!remove(token,host))return false;}
                        else if(code==3){result=1;return true;}
                        else if(code==4||(!draw&&code==8)){result=0;return true;}
                        else if(code==5){result=-1;return true;}
                        else if(!draw&&code==6){count=0;p=s.get(0x18);goto restart;}
                        else if(!draw&&code==7){if(r.get(16)){u32 ignored;if(!host.invoke(r.get(16),r.get(36),ignored))return false;}}
                        break;
                    }
                }
            }
            ++count;
        }
        p=s.get(0x50);
        restart:;
    }
    result=signed_word(count);return true;
}
}
