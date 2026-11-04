// Clock-only test host. No original state values or production source edits.
#include "th14-script-rng-register-audit-fixture-nov05.cpp"
namespace {
struct SupervisorResourceClock {
 u32 callback=0,scheduled=0,delivered=0,skipped=0,failed=0;
 u64 entry=0,pump=0;bool armed=false;
} supervisor_resource_clock;
}
extern "C" bool th14_observer_supervisor_resource_pump_clock(){
 auto& w=supervisor_resource_clock;
 if(!w.armed)return true;
 if(w.callback!=public_player_observations+1||probe_clock_ns>w.pump){++w.failed;return false;}
 probe_clock_ns=w.pump;w.armed=false;++w.delivered;return true;
}
API(observed_supervisor_resource_clock) u32 observed_supervisor_resource_clock(u32 callback,u64 entry,u64 pump){
 auto& w=supervisor_resource_clock;
 if(w.armed||w.failed||callback!=public_player_observations+1||entry>pump||entry<probe_clock_ns)return 0;
 w.callback=callback;w.entry=entry;w.pump=pump;w.armed=true;++w.scheduled;return 1;
}
API(supervisor_pump_menu_tick) u32 supervisor_pump_menu_tick(u64 now,u32 held){
 auto& w=supervisor_resource_clock;
 if(w.armed&&now!=w.entry){++w.failed;return 0;}
 const u32 result=rng_audit_menu_tick(now,held);
 // Ordinary frames have no pending loader and therefore do not enter the
 // instrumented loader-pump call site. They retain their ordinary behavior.
 if(w.armed){w.armed=false;++w.skipped;}
 return result&&!w.failed;
}
API(supervisor_resource_clock_meta) u32 supervisor_resource_clock_meta(u32 word){
 const auto& w=supervisor_resource_clock;
 const u32 values[]={w.scheduled,w.delivered,w.skipped,w.failed,u32(w.armed),w.callback};
 return word<6?values[word]:~0u;
}
