#include "GameManagerScene.hpp"

namespace th143 {
bool begin_game_manager_scene(GameManagerState& state,u32 self,PlayerState& player,
                              GameManagerSceneGlobals& g,GameManagerSceneHost& host){
    auto s=state.view();AnmView p{player.data.data()};
    for(u32 at:{8,0x70,12})if(u32 callback=s.get(at)){
        u32 flags;
        if(!host.read_manager_memory(callback+4,&flags,4))return false;
        flags|=2;
        if(!host.write_manager_memory(callback+4,&flags,4))return false;
    }
    std::memset(g.keyboard.data(),0,0x80);
    std::memset(g.keyboard.data()+0x100,0,0x80);
    AnmView keys{g.keyboard.data()};
    for(u32 at:{0x180,0x184,0x188,0x18c,0x190,0x194,0x19c})keys.put(at,0);
    if(s.get(0x10)==0){
        const u32 checkpoint=s.get(0x20);u32 block;
        if(!game_history_clear(state,self,host)||
           !host.allocate_scene_history(GameManagerState::history_bytes,block)||
           !game_history_append(state,self,block,host))return false;
        s.put(0x34,block+0x18a4);
        if(!g.new_game&&!host.write_manager_memory(checkpoint+0x14,g.game_state.data(),0xa0))return false;
        const std::array<u32,2> position{p.get(0x5ec),p.get(0x5f0)};
        if(!host.write_manager_memory(checkpoint+12,position.data(),8))return false;
        s.put(0x6c,0);s.put(0x74,g.scene);
        const u32 value=p.get(0x18464);
        if(!host.write_manager_memory(s.get(0x20)+0xb4,&value,4))return false;
    }else if(s.get(0x10)==1){
        const u32 checkpoint=s.get(0x4c);s.put(0x74,g.scene);
        std::array<u32,2> position;
        if(!host.read_manager_memory(checkpoint+12,position.data(),8))return false;
        p.put(0x5ec,position[0]);p.put(0x5f0,position[1]);
        // CVTDQ2PS followed by a separate float multiply, as in453f40.
        p.put(0x5e0,word(float(i32(position[0]))*(1.0f/128.0f)));
        p.put(0x5e4,word(float(i32(position[1]))*(1.0f/128.0f)));
        for(u32 i=0;i<8;++i)p.put(0xd7c0+i*0xe4,1);
        u32 value;if(!host.read_manager_memory(checkpoint+0xb4,&value,4))return false;
        p.put(0x18464,value);
        if(g.scene==3)s.put(0x14,1);
        s.put(0x40,s.get(0x3c));s.put(0x48,s.get(0x44));s.put(0x50,0);
        for(u32 i=0;i<33;++i){p.put(0x1845c-i*8,p.get(0x5ec));p.put(0x18460-i*8,p.get(0x5f0));}
    }
    s.put(0x6c,0);return true;
}
}

