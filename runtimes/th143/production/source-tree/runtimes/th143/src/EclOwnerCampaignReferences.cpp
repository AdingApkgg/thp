#include "EclVariableTweenRuntime.hpp"
#include "EclThreadLifetime.hpp"
#include "EclOwnerShooting.hpp"

namespace th143 {
namespace {
struct CampaignReferenceHost final:VmHost {
 EclOwner& owner;VmHost& services;
 CampaignReferenceHost(EclOwner& o,VmHost& s):owner(o),services(s){}
 bool integer(i32 id,i32& value)override{return owner.integer(id,value);}
 bool floating(i32 id,float& value)override{return owner.floating(id,value);}
 u8* reference(i32 id,bool floating)override{return services.reference(id,floating);}
 Instruction* find_subroutine(const char* name)override{return owner.find_subroutine(name);}
 i32 command(Vm& vm)override{return owner.command(vm);}
 bool spawn(Vm& source,i32 id,u32 skipped)override{return owner.spawn(source,id,skipped);}
 Vm* thread(i32 id)override{return owner.thread(id);}
 void cancel_secondary()override{owner.cancel_secondary();}
};
}

EclOwner::~EclOwner() { campaign_tweens_forget(root); while (threads.next) erase(threads.next);bind_ecl_thread_release(*this,{}); }
void EclOwner::erase(Node* node) {
    if (node->next) node->next->previous = node->previous;
    if (node->previous) node->previous->next = node->next;
    campaign_tweens_forget(*node->value);
    release_ecl_thread_storage(*this,*node->value);
    delete node->value;
    delete node;
}
bool EclOwner::spawn(Vm& source, i32 id, u32 skipped) {
    auto* vm = new Vm;
    if(prepare_thread&&!prepare_thread(*vm,thread_context)){delete vm;return false;}
    auto* node = new Node{vm, threads.next, &threads};
    vm->thread_id = id;
    vm->difficulty = active->difficulty;
    if (node->next) node->next->previous = node;
    threads.next = node;
    Vm* previous = active;
    const i32 result = vm->call(source, *this, skipped);
    active = previous;
    return result == 0;
}
Vm* EclOwner::thread(i32 id) {
    for (Node* node = &threads; node; node = node->next)
        if (node->value->thread_id == id) return node->value;
    return nullptr;
}
void EclOwner::cancel_secondary() {
    for (Node* node = threads.next; node; node = node->next) node->value->instruction = nullptr;
}
i32 EclOwner::update(float elapsed) {
    CampaignReferenceHost reference_host(*this,services_);
    for (Node* node = &threads; node;) {
        Node* next = node->next;
        active = node->value;
        const i32 result = active->update(elapsed, reference_host);
        if (result == -2) return -2;
        if (result) {
            if (node == &threads) return -1;
            erase(node);
        }
        node = next;
    }
    active = &root;
    return 0;
}
}
