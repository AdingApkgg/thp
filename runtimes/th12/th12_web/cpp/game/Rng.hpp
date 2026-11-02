#pragma once
#include "Types.hpp"
#include "PortTitle.hpp"
namespace th11 {
// TH11 1.00a: 0x458bc0 / 0x458c30. next32 packs pre-rotation words.
struct Rng;
enum class RngBoundary {BeforeRead,SeedRead,CounterCommitted,BeforeStore,SeedWritten};
// Scoped observer for the two animation RNGs. Rng's eight-byte layout stays
// unchanged; nested animation updates restore the previous observer.
struct RngBoundaryScope {
    using Callback=bool(*)(void*,Rng&,RngBoundary);
    Rng* script;Rng* visual;void* owner;Callback callback;
    RngBoundaryScope* previous;bool native_locking=true,running=false,failed=false;
    static inline RngBoundaryScope* active=nullptr;
    RngBoundaryScope(Rng& a,Rng& b,void* context,Callback fn,bool locking=true)noexcept:
        script(&a),visual(&b),owner(context),callback(fn),previous(active),native_locking(locking){active=this;}
    ~RngBoundaryScope(){active=previous;}
    RngBoundaryScope(const RngBoundaryScope&)=delete;
    RngBoundaryScope& operator=(const RngBoundaryScope&)=delete;
    static bool locking_enabled(const Rng& rng)noexcept{
        for(auto* scope=active;scope;scope=scope->previous)if(&rng==scope->script||&rng==scope->visual)return scope->native_locking;
        return true;
    }
    static void checkpoint(Rng& rng,RngBoundary point)noexcept{
        for(auto* scope=active;scope;scope=scope->previous){
            if(&rng!=scope->script&&&rng!=scope->visual)continue;
            if(scope->running||scope->failed)return;
            scope->running=true;
            scope->failed=!scope->callback(scope->owner,rng,point);
            scope->running=false;return;
        }
    }
};
struct Rng {
    u16 seed=0,reserved=0;u32 calls=0;
    using Boundary=RngBoundary;
    template<class F> u16 next16_with_boundary(F&& checkpoint,bool native_locking=false) noexcept {
        ++calls;checkpoint(Boundary::CounterCommitted);
        checkpoint(Boundary::BeforeRead);const u16 input=seed;checkpoint(Boundary::SeedRead);
        const u16 mixed=u16((input^0x9630u)-0x6553u);
        const u16 result=u16((mixed<<2)|(mixed>>14));
        checkpoint(Boundary::BeforeStore);seed=result;checkpoint(Boundary::SeedWritten);
        return native_locking?seed:result;
    }
    u16 next16() noexcept {if constexpr(kPortTitle==14)return next16_with_boundary([this](Boundary p){RngBoundaryScope::checkpoint(*this,p);},RngBoundaryScope::locking_enabled(*this));else {const u16 mixed=u16((seed^0x9630u)-0x6553u);seed=u16((mixed<<2)|(mixed>>14));++calls;return seed;}}
    template<class F> u32 next32_with_boundary(F&& checkpoint) noexcept {
        checkpoint(Boundary::BeforeRead);const u16 input=seed;checkpoint(Boundary::SeedRead);
        calls+=2;checkpoint(Boundary::CounterCommitted);
        const u16 high=u16((input^0x9630u)-0x6553u);
        const u16 middle=u16((high<<2)|(high>>14));
        const u16 low=u16((middle^0x9630u)-0x6553u);
        const u16 result=u16((low<<2)|(low>>14));
        checkpoint(Boundary::BeforeStore);seed=result;checkpoint(Boundary::SeedWritten);
        return (u32(high)<<16)|low;
    }
    u32 next32() noexcept {if constexpr(kPortTitle==14)return next32_with_boundary([this](Boundary p){RngBoundaryScope::checkpoint(*this,p);});else {const u16 high=u16((seed^0x9630u)-0x6553u);const u16 middle=u16((high<<2)|(high>>14));const u16 low=u16((middle^0x9630u)-0x6553u);seed=u16((low<<2)|(low>>14));calls+=2;return (u32(high)<<16)|low;}}
    u32 next_four() noexcept {const u16 lo=next16(),hi=next16();next16();next16();return (u32(hi)<<16)|lo;}
    float unit() noexcept {return float(double(next32())*0x1p-32);}
    float signed_unit() noexcept {
        // TH14 4034b0 rounds the unsigned conversion and the subtraction
        // separately in SSE. Combining them changes later random trajectories.
        if constexpr(kPortTitle==14||kPortTitle==16)return float(float(float(next32())*0x1p-31f)-1.f);
        return float(double(next32())*0x1p-31-1);
    }
};
static_assert(sizeof(Rng)==8);
}
