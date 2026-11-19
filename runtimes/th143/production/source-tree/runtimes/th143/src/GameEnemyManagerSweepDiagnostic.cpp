#include "GameEnemyManagerSweepRuntime.hpp"
namespace th143 {
namespace {u32 sweep_diagnostic[10]{};}
extern "C" __attribute__((export_name("day2_sweep_diagnostic"))) u32 day2_sweep_diagnostic(u32 i){return i<10?sweep_diagnostic[i]:0;}

GameEnemyManagerSweepRuntime::GameEnemyManagerSweepRuntime(GameEnemyRuntime& m,EnemyScripts& s,AnmWorld& w,ItemPool& i,Rng& r,SoundQueue& q):manager(m),scripts(s),world(w),items(i),random(r),audio(q){bind_enemy_manager_sweep(scripts,this);}
GameEnemyManagerSweepRuntime::~GameEnemyManagerSweepRuntime(){bind_enemy_manager_sweep(scripts,nullptr);}
bool GameEnemyManagerSweepRuntime::sweep(){for(auto& v:sweep_diagnostic)v=0;sweep_diagnostic[0]=manager.global_owner;sweep_diagnostic[1]=scripts.live.size();const bool ok=manager.global_owner&&sweep_enemy_manager(GameEnemyRuntime::self,*this);sweep_diagnostic[9]=ok;return ok;}
bool GameEnemyManagerSweepRuntime::memory(u32 p,void* data,u32 n,bool write){
    ++sweep_diagnostic[2];sweep_diagnostic[3]=p;sweep_diagnostic[4]=n;sweep_diagnostic[5]=write;if((p&3)||(n&3))return false;auto* bytes=static_cast<u8*>(data);
    if(p>=GameEnemyRuntime::self&&std::uint64_t(p)+n<=std::uint64_t(GameEnemyRuntime::self)+manager.data.size()){
        if(!write&&p==GameEnemyRuntime::self+0xd0&&n==4){const u32 head=scripts.live.empty()?0:scripts.live.front()->token+0x157c;std::memcpy(bytes,&head,4);return true;}
        if(write)std::memcpy(manager.data.data()+p-GameEnemyRuntime::self,bytes,n);else std::memcpy(bytes,manager.data.data()+p-GameEnemyRuntime::self,n);return true;
    }
    for(auto& a:scripts.storage)if(p>=a->token+0x11f0&&std::uint64_t(p)+n<=std::uint64_t(a->token)+0x53d8){for(u32 at=0;at<n;at+=4){u32 value;if(write){std::memcpy(&value,bytes+at,4);a->state.put(p-a->token-0x11f0+at,value);}else{value=a->state.get(p-a->token-0x11f0+at);std::memcpy(bytes+at,&value,4);}}return true;}return false;
}
bool GameEnemyManagerSweepRuntime::enemy_cancel_death(u32 token,i32& result){for(auto& a:scripts.storage)if(a->token==token){sweep_diagnostic[6]=token;struct Restore{EnemyScripts& s;EnemyScripts::Actor* active;~Restore(){s.active=active;}}restore{scripts,scripts.active};scripts.active=a.get();sweep_diagnostic[7]=1;return th143::enemy_death(a->state,a->owner,a->death_callback,world,items,random,*this,result);}return false;}
bool GameEnemyManagerSweepRuntime::death_resource(i32 slot,u32& token){sweep_diagnostic[8]=0x10000000|u32(slot);if(slot<0||slot>=6)return false;token=manager.view().get(0xa0+u32(slot)*4);return token!=0;}
bool GameEnemyManagerSweepRuntime::death_script_name(u32 token,const char*& name){sweep_diagnostic[8]=token;for(const auto& file:manager.program.files){const auto base=std::uintptr_t(file->bytes.data());if(token>=base&&std::uint64_t(token)<base+file->bytes.size()){const u32 at=u32(token-base);if(!std::memchr(file->bytes.data()+at,0,file->bytes.size()-at))return false;name=reinterpret_cast<const char*>(file->bytes.data()+at);return true;}}return false;}
}
