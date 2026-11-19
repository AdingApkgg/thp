#pragma once
#include "GameOwnerRuntime.hpp"
#include "AnmResourceWorld.hpp"
namespace th143 {
//40b4e0 factory,40b0d0 constructor and40b160 initialization. The actual owner
// includes two final callback words beyond the earlier191f0-byte bootstrap.
class GameAsciiRuntime final:private SchedulerHost {
public:
    static constexpr u32 self=0x71000000,bytes=0x191f8;
    GameAsciiRuntime(GameFrameRuntime& f,AnmResourceWorld& w,GameOwnerServices& a):frames(f),world(w),storage(a){}
    std::array<u8,bytes> data{};u32 global_owner=0;
    AnmView view(){return {data.data()};}
    bool create(u8 font,u32& result);
    //4436c0 application hook and40b550 global delete wrapper.
    bool activate();
    bool destroy();
private:
    GameFrameRuntime& frames;AnmResourceWorld& world;GameOwnerServices& storage;
    bool invoke(u32,u32,u32&)override{return false;}
    bool release_callback(u32 p)override{return storage.release_game_storage(p);}
};
}
