#include "GameRootReplayReloadRuntime.hpp"
#include "GameRetainedPlayerFactory.hpp"
namespace th143 {
GameRootReplayReloadRuntime::GameRootReplayReloadRuntime(RootState& r,u32 p,GameManagerInitGlobals& g,SaveData& s,u32 sp,
    GameFrameRuntime& f,GameOwnerRuntime& o,GameStageRuntime& st,GameHudRuntime& h,
    GameMenuRuntime& m,GameEnemyRuntime& e,GameCheatRuntime& c,GameAuxRuntime& a,
    GameFrameTimingRuntime& t,AnmResourceWorld& w,GameOwnerServices& mem,RootLoadHost& io,GameRootReplayInputHost& replay)
    :root(r),self(p),state(g),save(s),save_token(sp),frames(f),owners(o),stage(st),hud(h),menu(m),enemies(e),cheat(c),auxiliary(a),timing(t),animations(w),storage(mem),platform(io),replay_input(replay){}
bool GameRootReplayReloadRuntime::load(i32& result,u32 budget){
    const bool retained=(state.game_flags&0x11)!=0;
    if(owners.created||stage.created||hud.globals.owner||menu.global_owner||cheat.global_owner)return false;
    if(retained){if(!enemies.global_owner||enemies.view().get(0xd0)||enemies.view().get(0xd8))return false;}
    else if(enemies.global_owner)return false;
    last_entry=last_address=0;return load_root(root,self,*this,result,budget);
}
bool GameRootReplayReloadRuntime::map(u32 p,void* data,u32 n,bool write){
    last_address=p;
    auto region=[&](u32 base,void* bytes,u32 size){
        if(p<base||std::uint64_t(p)+n>std::uint64_t(base)+size)return false;
        auto* at=static_cast<u8*>(bytes)+p-base;if(write)std::memcpy(at,data,n);else std::memcpy(data,at,n);return true;
    };
    if(region(self,root.data.data(),root.data.size())||region(0x4e46f0,state.game_state.data(),160)||
       region(save_token,save.data.data(),save.data.size())||region(0x4e49a4,state.root_snapshot.data(),92)||
       region(0x4e6b8c,&cached_shots,4)||region(0x4e47b0,&state.game_flags,4)||region(0x4e4ec8,&state.new_game,4)||region(0x4e479c,&state.scene,4)||
       region(GameFrameTimingRuntime::self,timing.data.data(),timing.data.size()))return true;
    if(hud.globals.owner&&region(GameHudRuntime::self,hud.data.data(),hud.data.size()))return true;
    if(cheat.global_owner&&region(GameCheatRuntime::self,cheat.data.data(),cheat.data.size()))return true;
    if(menu.global_owner&&region(GameMenuRuntime::self,menu.menu.data.data(),menu.menu.data.size()))return true;
    if(!write&&n==4){
        u32 value=0;bool found=true;
        switch(p){
        case 0x4e6a5c:value=self;break;case 0x4e6b9c:value=save_token;break;
        case 0x4e6a54:value=hud.globals.owner;break;case 0x4e6b84:value=menu.global_owner;break;
        case 0x4e6a48:value=enemies.global_owner;break;case 0x4e6b68:value=cheat.global_owner;break;
        case 0x4e6a50:value=timing.global_owner;break;case 0x4e6a40:value=auxiliary.effects_owner;break;
        case 0x4e6a0c:value=auxiliary.special_owner;break;
        default:found=false;
        }
        if(found){std::memcpy(data,&value,4);return true;}
    }
    if(write){if(owners.write(p,data,n)||stage.write(p,data,n)||auxiliary.write(p,data,n))return true;}
    else if(owners.read(p,data,n)||stage.read(p,data,n)||enemies.read(p,data,n)||auxiliary.read(p,data,n))return true;
    return write?platform.load_write(p,data,n):platform.load_read(p,data,n);
}
bool GameRootReplayReloadRuntime::name(u32 p,std::string& out){
    out.clear();for(u32 i=0;i<256;++i){u8 ch;if(!load_read(p+i,&ch,1))return false;if(!ch)return true;out.push_back(char(ch));}return false;
}
bool GameRootReplayReloadRuntime::load_call(u32 entry,u32 owner,std::initializer_list<u32> args,u32& result){
    last_entry=entry;result=0;
    switch(entry){
    case 0x434190:{
        if(owner!=0x4e46f0||args.size())return false;auto& g=state.game_state;
        g[19]=g[24]=0;g[26]=1;g[30]=3;
        // 434190 calls the HUD before clearing the old bomb-fragment value.
        if(hud.globals.owner&&!platform.load_call(0x4319b0,0,{g[30],g[31]},result))return false;
        for(u32 i:{31,28,29,32,33,34,35,39})g[i]=0;return true;
    }
    case 0x44ca60:
        if(args.size())return false;state.root_present=true;
        if(cached_shots)return create_player_with_retained_shots(owners,frames,animations,storage,cached_shots,state,result);
        return owners.create(entry,0,state,result);
    case 0x432350:{
        if(args.size()!=1||*args.begin()!=0||!enemies.global_owner)return false;
        auto e=enemies.view();if(!(e.get(0xc8)&1)){e.put(0xc8,e.get(0xc8)|1);e.put(0xc4,animations.global_rate_token());}
        e.put(0xb8,0xffffffff);e.put(0xbc,0);e.put(0xc0,0);e.put(0xd0,0);e.put(0xd4,0);return true;
    }
    case 0x450660:case 0x454740:case 0x412880:case 0x434fc0:case 0x438dd0:case 0x45d4e0:
        if(args.size())return false;
        state.root_present=true;if(entry==0x454740)std::memcpy(state.root_snapshot.data(),root.data.data()+0x24,92);
        if(entry==0x454740&&owner==1)return replay_input.create_root_replay_input(owner,state,result);
        return owners.create(entry,entry==0x454740?owner:0,state,result);
    case 0x401830:{
        if(args.size()!=1||!storage.allocate_game_storage(0x28,result)||!result)return false;
        return frames.scheduler.create(result,*args.begin(),storage.game_allocation_fill());
    }
    case 0x4013e0:case 0x401490:
        if(args.size()!=2)return false;
        return frames.scheduler.add(*args.begin(),signed_word(*(args.begin()+1)),entry==0x401490,*this,result);
    case 0x40d550:{std::string file;if(args.size()||!name(owner,file))return false;stage.loading.scene=state.scene;return stage.create(file,result);}
    case 0x42d1b0:{
        if(args.size())return false;u32 descriptor;if(!load_read(0x4e6bac,&descriptor,4))return false;hud.globals.scene.descriptor=descriptor;return hud.create(result);
    }
    case 0x447d20:{u32 width;return !args.size()&&load_read(0x53b0ec,&width,4)&&menu.create(width,result);}
    case 0x41ec00:{
        std::string file;if(args.size()||!name(owner,file))return false;
        u32 bullet=0,effect=auxiliary.effects_view().get(0x10);for(const auto& r:animations.resources)if(r.file==7)bullet=r.token;
        return enemies.create(file.c_str(),bullet,effect,result);
    }
    case 0x418880:return !args.size()&&auxiliary.create_special(result);
    case 0x4112e0:{u32 width;i32 status;if(args.size()||!load_read(0x53b0ec,&width,4)||!auxiliary.create_independent(width,status))return false;result=u32(status);return true;}
    case 0x436ba0:return !args.size()&&cheat.create(result);
    case 0x438380:return !args.size()&&owner==cheat.global_owner&&cheat.position();
    case 0x436c30:{
        if(args.size()!=1)return false;
        CheatSceneGlobals g{state.game_state[14],state.game_state[8],state.game_state[9],state.scene,menu.global_owner!=0,0,save.data[0xefac],save.data[0xf08a],{0,6,3,1,7,4,2,5,8}};
        return cheat.begin_scene(signed_word(*args.begin()),g);
    }
    // Application presentation, music queue, HUD visual arrays and background
    // VMs have typed platform ownership. Gameplay factory entries above never
    // escape to that service boundary.
    case 0x4319b0:case 0x444660:case 0x444e00:case 0x445110:case 0x418240:
        return platform.load_call(entry,owner,args,result);
    default:return false;
    }
}
}
