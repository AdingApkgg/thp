#pragma once
#include "Rng.hpp"
#include "Timer.hpp"
#include <vector>
namespace th11 {
// Native effect type 1: 4489e0/448a90, update callback 448720 at priority 14.
// The shared script RNG is intentional: replacing this with cosmetic random
// numbers changes subsequent ECL decisions and invalidates original replays.
struct ScreenShake {
    i32 duration=0,start=0,end=0;
    Timer timer;
    i32 ramp=0,hold=0,fall=0;bool phased=false;
    i32 update(Rng&,Vec2& offset,bool stopped=false) noexcept;
};
struct ScreenShakes {
    std::vector<ScreenShake> effects;
    Vec2 offset{};
    void start(i32 duration,i32 from,i32 to,const float* rate){
        ScreenShake effect{duration,from,to};effect.timer.set(0,rate);
        // 456b70 inserts before existing callbacks with the same priority.
        effects.insert(effects.begin(),effect);
    }
    void start_th14_hold(i32 amplitude,i32 ramp,i32 hold,i32 fall,const float* rate){
        ScreenShake effect;effect.start=amplitude;effect.ramp=ramp;effect.hold=hold;effect.fall=fall;effect.phased=true;effect.timer.set(0,rate);effects.insert(effects.begin(),effect);
    }
    void update(Rng& rng,bool stopped=false,Rng* visual=nullptr){
        for(auto it=effects.begin();it!=effects.end();)
            if(it->update(it->phased&&visual?*visual:rng,offset,stopped)==7)it=effects.erase(it);else ++it;
    }
};
}
