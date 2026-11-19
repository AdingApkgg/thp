#pragma once
#include "GameOwnerRuntime.hpp"
#include "RootFactory.hpp"
namespace th143 {
//45f630/45ed30 cold title owner and its embedded45ef60 loader worker.
// Title worker execution, interactive pages and teardown are separate bodies.
class GameTitleRuntime {
public:
    static constexpr u32 self=0x6e040000,bytes=0xef78;
    GameTitleRuntime(GameOwnerServices& storage,RootFactoryHost& platform,u32& presentation):storage(storage),platform(platform),presentation(presentation){}
    std::array<u8,bytes> data{};u32 global_owner=0;
    AnmView view(){return {data.data()};}
    bool create(u32& result);
private:GameOwnerServices& storage;RootFactoryHost& platform;u32& presentation;
};
}
