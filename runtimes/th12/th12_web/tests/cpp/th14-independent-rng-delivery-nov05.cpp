// An independent producer supplies only readiness/acknowledgements. The real
// production job obtains synthetic input here and performs every RNG store.
// This is a component experiment, not ordinary Application integration.
#include "ReplayRngRestoreTh14.hpp"
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
extern "C" __attribute__((import_module("delivery"),import_name("ready"))) u32 host_ready(u32);
extern "C" __attribute__((import_module("delivery"),import_name("commit"))) void host_commit(u32);
extern "C" __attribute__((import_module("delivery"),import_name("now"))) double host_now();
namespace {
u32 result[64]{};
struct Context {
    Rng game{0x1011,0xabcd,19},script{0x5e23,0xbeef,23};
    u32 entry=0x6d31,iterations=0,boundary=~0u,input=0,commits=0;
    u32 call_seed=0,call_count=0;
    ReplayRngRestoreJobTh14 job;
    ReplayRngRestoreResultTh14 progress=ReplayRngRestoreResultTh14::Waiting;
    bool invalid=false;
    static u32 index(ReplayRngRestorePointTh14 p){
        using P=ReplayRngRestorePointTh14;
        return p==P::GameplaySeedStored?0:p==P::ScriptSeedStored?1:p==P::GameplayCounterCleared?2:~0u;
    }
    void advance(){
        if(progress==ReplayRngRestoreResultTh14::Failed||job.complete())return;
        progress=job.playback(game,&script,entry,false,[](ReplayRngRestorePointTh14 p){
            const auto code=host_ready(index(p));
            return code==0?ReplayRngRestoreResultTh14::Waiting:code==1?ReplayRngRestoreResultTh14::Ready:ReplayRngRestoreResultTh14::Failed;
        });
    }
    void committed(ReplayRngRestorePointTh14 p){
        const auto at=index(p);
        if(at!=commits||commits>=3){invalid=true;return;}
        const u32 words[]={at,boundary,iterations,input,game.seed,game.calls,script.seed,script.calls,job.stores()};
        for(u32 i=0;i<9;++i)result[16+commits*16+i]=words[i];
        ++commits;host_commit(at);
    }
};
}
API(delivery_run) u32 delivery_run(u32 maximum_ms){
    for(auto& word:result)word=0;
    if(maximum_ms<1||maximum_ms>3000)return 0;
    Context c;const double start=host_now();u32 value=0;
    {
        ReplayRngRestoreScopeTh14 scope(c.game,&c,[](void* p,ReplayRngRestorePointTh14 point,Rng&,Rng*){
            static_cast<Context*>(p)->committed(point);
        });
        // A single synchronous Wasm call remains active throughout this loop.
        // No recorded callback number, VM identity, native clock, seed, or
        // desired result is supplied by the producer.
        while(!c.job.complete()&&c.progress!=ReplayRngRestoreResultTh14::Failed&&host_now()-start<maximum_ms){
            c.call_seed=c.script.seed;c.call_count=c.script.calls;
            const auto first_commit=c.commits;
            value=c.script.next32_with_boundary([&](RngBoundary p){
                c.boundary=u32(p);
                if(p==RngBoundary::SeedRead)c.input=c.script.seed;
                c.advance();
            });
            for(u32 row=first_commit;row<c.commits;++row){
                const u32 words[]={value,c.script.seed,c.script.calls,c.call_seed,c.call_count,1,c.input};
                for(u32 i=0;i<7;++i)result[16+row*16+9+i]=words[i];
            }
            ++c.iterations;
        }
    }
    const u32 words[]={c.job.complete()?1u:0u,c.job.stores(),c.commits,c.iterations,
        u32(c.progress),c.invalid?1u:0u,c.game.seed,c.game.calls,c.script.seed,c.script.calls,
        c.entry,value,u32((host_now()-start)*1000),ReplayRngRestoreScopeTh14::active?1u:0u};
    for(u32 i=0;i<14;++i)result[i]=words[i];
    return c.invalid||ReplayRngRestoreScopeTh14::active?0:1;
}
API(delivery_value) u32 delivery_value(u32 index){return index<64?result[index]:~0u;}
