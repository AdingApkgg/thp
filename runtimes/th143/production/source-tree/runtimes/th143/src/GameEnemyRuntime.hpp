#pragma once
#include "GameOwnerRuntime.hpp"
#include "EclProgram.hpp"
namespace th143 {
struct GameEnemyServices {
    virtual ~GameEnemyServices()=default;
    virtual bool read_enemy_file(const char*,std::vector<u8>&)=0;
    virtual bool release_enemy_storage(u32 token,bool array)=0;
};
// 41ec00/41e6a0 cold factory and 41daf0/489880/41e860 resource ownership.
// Uses the session Scheduler. Actor creation/update/reset/destruction are
// separate from this cold resource lifecycle and must be bound by the session.
class GameEnemyRuntime final:private SchedulerHost {
public:
    static constexpr u32 self=0x6b003000;
    GameEnemyRuntime(Scheduler& s,GameOwnerServices& a,GameEnemyServices& f,std::array<u8,256>* shared_filename=nullptr):scheduler(s),services(a),files(f),shared_scratch(shared_filename){}
    std::array<u8,0xe8> data{};
    std::array<u8,0x1098> loader{};
    std::array<u8,256> scratch{};
    EclProgram program;
    struct Storage{u32 token;std::vector<u8> bytes;};
    std::vector<Storage> storage;
    std::vector<u32> file_tokens;
    u32 global_owner=0,loader_token=0;
    bool failed=false;
    AnmView view(){return {data.data()};}
    bool create(const char* filename,u32 bullet_resource,u32 effect_resource,u32& result);
    bool activate();
    bool load(const char* filename);
    u32 find(const char* name)const;
    bool read(u32 token,void*,u32 bytes);
private:
    Scheduler& scheduler;GameOwnerServices& services;GameEnemyServices& files;
    std::array<u8,256>* shared_scratch;
    bool allocate(u32 bytes,u32& token);
    bool attach(u32 token,const std::vector<u8>& raw);
    bool callback(u32 entry,i32 priority,bool draw,u32& token);
    bool invoke(u32,u32,u32&)override{return false;}
    bool release_callback(u32 token)override{return services.release_game_storage(token);}
};
}
