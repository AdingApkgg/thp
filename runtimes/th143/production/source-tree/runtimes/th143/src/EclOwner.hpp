#pragma once
#include "EclVm.hpp"

namespace th143 {
// TH143 489040 / 4896b0: secondary nodes are inserted immediately after root,
// while each update remembers its next node BEFORE executing that VM.
class EclOwner : public VmHost {
public:
    struct Node { Vm* value; Node* next = nullptr; Node* previous = nullptr; };
    Vm root;
    Vm* active = &root;
    Node threads{&root};
    // Secondary41d020 contexts preserve allocation bytes independently from
    // the actor's root VM. A session allocator can initialize those fields
    // before487240 copies arguments; zero-fill callers retain the default.
    using ThreadInitializer=bool(*)(Vm&,void*);
    ThreadInitializer prepare_thread=nullptr;
    void* thread_context=nullptr;

    explicit EclOwner(VmHost& services) : services_(services) {}
    ~EclOwner() override;
    EclOwner(const EclOwner&) = delete;
    EclOwner& operator=(const EclOwner&) = delete;
    i32 update(float elapsed);
    bool integer(i32 id, i32& v) override { return services_.integer(id, v); }
    bool floating(i32 id, float& v) override { return services_.floating(id, v); }
    u8* reference(i32 id, bool f) override { return services_.reference(id, f); }
    Instruction* find_subroutine(const char* name) override { return services_.find_subroutine(name); }
    i32 command(Vm& vm) override { return services_.command(vm); }
    bool spawn(Vm& source, i32 id, u32 skipped) override;
    Vm* thread(i32 id) override;
    void cancel_secondary() override;

private:
    VmHost& services_;
    void erase(Node*);
};
}
