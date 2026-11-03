#include "Replay.hpp"
#include "ReplayRngRestoreTh14.hpp"
#include "GameEconomy.hpp"
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
namespace {
u32 observed[64]{};
struct Context {
    Rng& gameplay;Rng& script;ReplayStageState& entry;
    u32 choice,bits,target,main_result=0,main_calls=0,trace_count=0;
};
void checkpoint(void* opaque,ReplayRngRestorePointTh14 point,Rng&,Rng*){
    auto& c=*static_cast<Context*>(opaque);const u32 p=u32(point);
    const u32 words[]={p,c.gameplay.seed,c.gameplay.reserved,c.gameplay.calls,
        c.script.seed,c.script.reserved,c.script.calls,c.entry.seed};
    if(c.trace_count>=3)__builtin_trap();
    for(u32 i=0;i<8;++i)observed[10+c.trace_count*8+i]=words[i];
    ++c.trace_count;
    if(p==c.target){
        if(c.main_calls++)__builtin_trap();auto& rng=c.choice?c.script:c.gameplay;
        c.main_result=c.bits==16?rng.next16():rng.next32();
    }
}
}
API(restore_probe) u32 restore_probe(u32 mode,u32 game_seed,u32 script_seed,u32 seed,u32 game_calls,
    u32 script_calls,u32 choice,u32 bits,u32 locking,u32 target){
    if(mode>2||choice>1||(bits!=16&&bits!=32)||locking>1||target>4)return 0;
    for(auto& word:observed)word=0;
    Rng gameplay{u16(game_seed),0xabcd,game_calls},script{u16(script_seed),0xbeef,script_calls};
    ReplayStageState entry;entry.seed=seed;GameEconomy economy;
    Context context{gameplay,script,entry,choice,bits,target};
    {
        RngBoundaryScope reads(script,gameplay,nullptr,[](void*,Rng&,RngBoundary){return true;},locking!=0);
        ReplayRngRestoreScopeTh14 scope(gameplay,&context,checkpoint);
        if(mode!=2)entry.restore(economy,gameplay,mode==0,&script);
        else{
#if defined(TH14_RESTORE_OLD_RECORD_ORDER)
            entry.seed=gameplay.seed;
            ReplayRngRestoreScopeTh14::checkpoint(ReplayRngRestorePointTh14::StageSeedRecorded,gameplay,&script);
            gameplay.calls=0;
            ReplayRngRestoreScopeTh14::checkpoint(ReplayRngRestorePointTh14::GameplayCounterCleared,gameplay,&script);
            script.seed=u16(entry.seed);
            ReplayRngRestoreScopeTh14::checkpoint(ReplayRngRestorePointTh14::ScriptSeedStored,gameplay,&script);
#else
            th14_record_stage_rng(gameplay,script,entry.seed);
#endif
        }
    }
    if(ReplayRngRestoreScopeTh14::active||RngBoundaryScope::active)return 0;
    const u32 words[]={gameplay.seed,gameplay.reserved,gameplay.calls,script.seed,script.reserved,
        script.calls,entry.seed,context.main_result,context.main_calls,context.trace_count};
    for(u32 i=0;i<10;++i)observed[i]=words[i];
    return 1;
}
API(restore_value) u32 restore_value(u32 index){return index<64?observed[index]:~0u;}
