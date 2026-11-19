#include "EnemyAnimationRefresh.hpp"
namespace th143 {
i32 enemy_animation_refresh(AnmView actor,Vm& vm,VmHost& host,EnemyAnimationRefreshHost& visuals) {
 if(vm.instruction->opcode!=313)return -2;
 const i32 slot=vm.integer_argument(0,host);
 const std::int64_t address=0x124+std::int64_t(slot)*4;
 if(vm.failed||address<0||address+4>0x41b8)return -2;
 const u32 offset=u32(address);u32 handle=actor.get(offset);
 if(!visuals.refresh_retire(offset,handle))return -2;
 actor.put(offset,handle);
 const i32 selector=signed_word(actor.get(0x304));
 const i32 script=signed_word(actor.get(0x310)+5u),layer=signed_word(actor.get(0x31c)+7u);
 if(!visuals.refresh_create(selector,script,layer,handle))return -2;
 actor.put(offset,handle);AnmView image{nullptr};
 if(!visuals.refresh_find(offset,handle,image))return -2;
 actor.put(offset,handle);
 if(!slot) {
  if(!image.data)return -2;
  actor.put(0x3ffc,word(image.floating(0x84)*image.floating(0x64)));
  actor.put(0x4000,word(image.floating(0x80)*image.floating(0x60)));
 }
 if(actor.get(0x4100)&0x20) {
  if(!visuals.refresh_clear_flag2(offset,handle))return -2;
  actor.put(offset,handle);
 }
 return 0;
}
}
