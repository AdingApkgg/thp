#pragma once
#include "GameOwnerRuntime.hpp"
#include "RootFactory.hpp"
#include "ApplicationTargets.hpp"
#include "GameAsciiRuntime.hpp"
namespace th143 {
struct CommonApplicationGlobals {u32 presentation=0;};
//443470/443200: common loading owner, ahead of the scene-specific Root.
class GameCommonRuntime final:private SchedulerHost {
public:
    static constexpr u32 self=0x6e03a000,bytes=0x610;
    GameCommonRuntime(GameFrameRuntime& f,GameOwnerServices& a,RootFactoryHost& h):frames(f),storage(a),platform(h){}
    std::array<u8,bytes> data{};u32 global_owner=0;
    AnmView view(){return {data.data()};}
    bool create(u32& result);
    bool update(AnmView application,ApplicationTargetGlobals&,CommonApplicationGlobals&,AnmRenderMemory&,ApplicationTargetServices&,GameAsciiRuntime&,u32& result);
private:
    GameFrameRuntime& frames;GameOwnerServices& storage;RootFactoryHost& platform;
    bool invoke(u32,u32,u32&)override{return false;}
    bool release_callback(u32 p)override{return storage.release_game_storage(p);}
};
}
