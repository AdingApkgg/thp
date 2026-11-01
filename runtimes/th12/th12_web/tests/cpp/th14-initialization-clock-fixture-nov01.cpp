// Only the explicitly observed initialization boundary advances host time.
#include "th14-vm-return-worker-fixture.cpp"
namespace {u32 init_callback=0,init_delivered=0,init_failed=0;u64 init_ready=0;
std::function<bool(const AnmVm&)> init_previous;}
API(observed_initialization_clock) u32 observed_initialization_clock(u32 callback,u64 ready){
 if(init_callback||!callback||!session.battle||ready<probe_clock_ns)return 0;
 init_callback=callback;init_ready=ready;init_previous=session.animations.before_initial_update;
 session.animations.before_initial_update=[](const AnmVm& vm){
  if(!init_delivered&&public_player_observations==init_callback&&vm.file_index==2&&vm.script_index==16&&vm.parent&&vm.parent->file_index==2&&vm.parent->script_index==17){
   if(probe_clock_ns>init_ready)init_failed=1;else probe_clock_ns=init_ready;
   ++init_delivered;
  }
  return !init_previous||init_previous(vm);
 };
 return 1;
}
API(observed_initialization_clock_state) u32 observed_initialization_clock_state(u32 field){return field?init_failed:init_delivered;}
