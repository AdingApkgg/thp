// Read-only audit of production replay stores; does not advance time or RNG.
#include "th14-relative-rng-camera-order-fixture-nov04.cpp"
namespace {
u32 restore_audit[16][10]{},restore_audit_count=0;
std::unique_ptr<ReplayRngRestoreScopeTh14> restore_audit_scope;
}
API(restore_order_audit_install) u32 restore_order_audit_install(){
 if(restore_audit_scope||public_player_observations!=1)return 0;
 restore_audit_scope=std::make_unique<ReplayRngRestoreScopeTh14>(session.animations.visual_rng,nullptr,
  [](void*,ReplayRngRestorePointTh14 point,Rng& visual,Rng* script){
   if(restore_audit_count>=16)return;
   auto* row=restore_audit[restore_audit_count++];row[0]=session.state.stage;row[1]=public_player_observations;row[2]=u32(point);
   row[3]=script?script->seed:~0u;row[4]=script?script->calls:~0u;row[5]=visual.seed;row[6]=visual.calls;
   row[7]=u32(probe_clock_ns);row[8]=u32(probe_clock_ns>>32);row[9]=session.battle?session.battle->pending_stage:0;
  });
 return 1;
}
API(restore_order_audit_count) u32 restore_order_audit_count(){return restore_audit_count;}
API(restore_order_audit_word) u32 restore_order_audit_word(u32 row,u32 column){return row<restore_audit_count&&column<10?restore_audit[row][column]:~0u;}
