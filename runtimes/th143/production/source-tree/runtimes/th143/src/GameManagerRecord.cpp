#include "GameManagerRecord.hpp"
namespace th143 {
void update_record_input(std::array<u8,0x1a0>& data){
    AnmView k{data.data()};u32 held=k.get(0x184),bit=1;
    k.put(0x18c,0);k.put(0x19c,0);
    for(u32 i=0;i<32;++i,held>>=1,bit<<=1){
        const u32 at=i*4;
        if(held&1){
            k.put(at,k.get(at)+1);k.put(0x100+at,k.get(0x100+at)+1);
            if(k.get(at)>=8)k.put(0x19c,k.get(0x19c)|bit);
            if(k.get(at)>=26){k.put(0x18c,k.get(0x18c)|bit);k.put(at,k.get(at)-8);}
        }else{k.put(at,0);k.put(0x100+at,0);}
    }
    held=k.get(0x184);const u32 changed=k.get(0x188)^held;
    k.put(0x190,changed&held);k.put(0x194,changed&~held);
}
bool record_game_manager_frame(GameManagerState& state,u32 self,GameManagerRecordGlobals& g,GameManagerSceneHost& host){
    if(!g.root_present||(g.root_flags&0x10)||g.dialog)return true;
    auto s=state.view();AnmView k{g.keyboard.data()};k.put(0x188,k.get(0x184));k.put(0x184,g.raw_keys&0xffff);
    update_record_input(g.keyboard);
    if((g.focus_flags&0x200)&&(k.get(0x184)&1)&&k.get(0x100)>=10)k.put(0x184,k.get(0x184)|8);
    const i32 frame=signed_word(s.get(0x6c));if(frame<0)return true;
    auto read=[&](u32 token,u32& value){return host.read_manager_memory(token,&value,4);};
    auto write=[&](u32 token,u32 value){return host.write_manager_memory(token,&value,4);};
    u32 block;if(!read(s.get(0x34),block))return false;
    if(frame%30==0){
        const float value=g.stage_value+.5f;
        const u32 converted=value>=256.f?255:value>=-2147483648.f&&value<2147483648.f?u32(i32(value))&255:0;
        u32 target;if(!read(block+0x18a0,target))return false;const u8 byte=u8(converted);
        if(!host.write_manager_memory(target,&byte,1)||!write(block+0x18a0,target+1))return false;
    }
    // 455810 rereads its write pointer before each individual word store.
    const u16 values[3]={u16(k.get(0x184)),u16(k.get(0x190)),u16(k.get(0x194))};
    for(u32 i=0;i<3;++i){u32 target;if(!read(block+0x1518,target)||!host.write_manager_memory(target+i*2,&values[i],2))return false;}
    u32 target;if(!read(block+0x1518,target)||!write(block+0x1518,target+6)||!read(block+0x1518,target))return false;
    if(signed_word(target-block)/6>=900){
        u32 next;if(!host.allocate_scene_history(GameManagerState::history_bytes,next)||!game_history_append(state,self,next,host))return false;
        s.put(0x34,next+0x18a4);
    }
    s.put(0x6c,s.get(0x6c)+1);return true;
}
i32 game_manager_replay_control(GameManagerState& state,bool root_present,u32 root_flags,u32 raw_keys){
    if(!root_present||(root_flags&4)||state.view().get(0x10)!=1||!(raw_keys&0x201))return 1;
    return signed_word(state.view().get(0x6c))%8?6:1;
}
}
