#pragma once
#include "EclOwner.hpp"
#include "EclProgram.hpp"
#include "ActorControls.hpp"
#include "ActorVisuals.hpp"
#include "EnemyMovement.hpp"
#include "EnemyActorRuntime.hpp"
#include <list>
#include <map>

namespace th143 {
struct EnemyVisual {
    u32 handle = 0, flags = 0, flags2 = 0;
    float width = 0, height = 0, scale_x = 1, scale_y = 1;
};
struct EnemyScriptServices {
    virtual ~EnemyScriptServices() = default;
    //41ee00 leaves the root VM stack/flags high bits from its allocation.
    // Sessions that own that allocation initialize the preserved bytes here,
    // before any initial ECL instruction executes. Existing zero-fill callers
    // need no extra service.
    virtual bool prepare_actor(EclOwner&){return true;}
    virtual bool create_visual(i32 file, i32 script, i32 layer, EnemyVisual&) = 0;
    virtual bool visual(u32 handle, EnemyVisual&) = 0;
    virtual bool rotate_visual(u32 handle, float angle) = 0;
    virtual bool retire_visual(u32 handle) = 0;
    virtual bool flag_visual(u32 handle, bool enabled) { return false; }
    virtual bool position_visual(u32 handle, const std::array<float,3>& position) { return false; }
    virtual Rng* gameplay_rng(){return nullptr;}
    virtual bool aim_position(float& x,float& y){return false;}
    virtual bool change_visual(u32 previous,i32 script,i32 layer,EnemyVisual&){return false;}
    virtual bool sound(i32 id, float x) = 0;
    virtual bool message_select(i32 id) = 0;
    virtual bool hud_value(i32 value) = 0;
    virtual bool message_active() const = 0;
    virtual bool root_special() const = 0;
    virtual u32 game_flags() const = 0;
    virtual void command(u32 actor_id, const Vm&) {}
};
// Actor/script ownership and command composition. Graphics and UI are typed
// world services. Unimplemented commands/moving interpolation reject rather
// than silently consuming native script instructions.
class EnemyScripts : public VmHost, public EnemySpawner {
public:
    struct Actor {
        ActorState state;
        EclOwner owner;
        u32 token;
        u32 death_callback=0;
        bool retired=false;
        std::string name;
        Actor(VmHost& host, u32 t, const char* n) : owner(host), token(t), name(n) {}
    };
    EclProgram& program;
    EnemyScriptServices& services;
    EmitterSink& emitters;
    ActorControlWorld controls;
    AnmHandles animations;
    std::list<Actor*> live;
    std::vector<std::unique_ptr<Actor>> storage;
    std::map<u32, std::unique_ptr<AnmNode>> visual_nodes;
    Actor* active = nullptr;
    EnemyActorRuntime* combat = nullptr;
    u32 next_id = 1, last_id = 0, difficulty = 0;
    u32 rate_token = 0x4e40b0;
    u32 signal_flags=0,signal_count=0; // Original globals4e6a28/4e6a2c.
    i32 frame = -1, error_opcode = -1;
    bool failed = false;

    EnemyScripts(EclProgram& p, EnemyScriptServices& s, EmitterSink& e) : program(p), services(s), emitters(e) {}
    bool spawn_enemy(const char*, const EnemySpawn&) override;
    bool update(float elapsed);
    bool integer(i32 id, i32& value) override;
    bool floating(i32 id,float& value) override;
    Instruction* find_subroutine(const char* name) override { return program.find(name); }
    i32 command(Vm&) override;
private:
    bool tick(Actor&, float,i32* result=nullptr);
    bool retire(Actor&);
    bool position(ActorState&, bool before,float elapsed=1.f);
    bool timer(ActorState&, u32 at, float elapsed, bool decrement = false);
    bool animation_command(Vm&);
    bool position_visuals(ActorState&);
    bool change_visual(ActorState&);
};
}
