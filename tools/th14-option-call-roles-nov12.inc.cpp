// Link-only observation: all four real implementations remain the providers.
namespace option_call_roles {
thread_local u32 registry_role=0,vm_depth=0;
std::atomic<u32> count{0};
std::array<u32,8192*32> data{};
struct Scope {u32 old;explicit Scope(bool overlay):old(registry_role){registry_role=overlay?2:1;}~Scope(){registry_role=old;}};
}
extern "C" bool __real__ZN4th1110AnmManager6updateEb(AnmManager*,bool);
extern "C" bool __wrap__ZN4th1110AnmManager6updateEb(AnmManager* a,bool overlay){
 option_call_roles::Scope scope(overlay);return __real__ZN4th1110AnmManager6updateEb(a,overlay);
}
extern "C" bool __real__ZN4th1110AnmManager6updateEbRKNSt3__28functionIFbvEEE(AnmManager*,bool,const std::function<bool()>&);
extern "C" bool __wrap__ZN4th1110AnmManager6updateEbRKNSt3__28functionIFbvEEE(AnmManager* a,bool overlay,const std::function<bool()>& callback){
 option_call_roles::Scope scope(overlay);return __real__ZN4th1110AnmManager6updateEbRKNSt3__28functionIFbvEEE(a,overlay,callback);
}
extern "C" bool __real__ZN4th1110AnmManager6updateEbRKNSt3__28functionIFbRKNS_5AnmVmENS0_14VmBoundaryTh14EEEE(AnmManager*,bool,const AnmManager::VmBoundaryCallbackTh14&);
extern "C" bool __wrap__ZN4th1110AnmManager6updateEbRKNSt3__28functionIFbRKNS_5AnmVmENS0_14VmBoundaryTh14EEEE(AnmManager* a,bool overlay,const AnmManager::VmBoundaryCallbackTh14& callback){
 option_call_roles::Scope scope(overlay);return __real__ZN4th1110AnmManager6updateEbRKNSt3__28functionIFbRKNS_5AnmVmENS0_14VmBoundaryTh14EEEE(a,overlay,callback);
}
extern "C" int __real__ZN4th115AnmVm6updateERNS_14AnmEnvironmentE(AnmVm*,AnmEnvironment*);
extern "C" int __wrap__ZN4th115AnmVm6updateERNS_14AnmEnvironmentE(AnmVm* vm,AnmEnvironment* env){
 using namespace option_call_roles;
 const u32 cb=observer_published_callback.load(std::memory_order_acquire);
 const bool worker=StageCppWorkerScopeTh14::owns(game);
 const bool wanted=game&&cb<3&&vm->file_index==9&&vm->script_index==10;
 u32* row=nullptr;
 if(wanted){
  const u32 index=count.fetch_add(1,std::memory_order_relaxed);if(index>=8192)std::abort();
  row=data.data()+index*32;
  const auto* control=!worker&&env==&game->animations?game->animations.th14_control.get():nullptr;
  const u32 before[]={index+1,cb,registry_role,u32(worker),vm->id,u32(vm->file_index),u32(vm->script_index),
   u32(vm->age.previous),u32(vm->age.current),th14_title_observer::float_bits(vm->age.fractional),
   u32(vm->timer.previous),u32(vm->timer.current),th14_title_observer::float_bits(vm->timer.fractional),
   th14_title_observer::float_bits(vm->rotation.z),th14_title_observer::float_bits(vm->angular_velocity.z),
   u32(vm->pending_interrupt),control?u32(control->flags):~0u,u32(env==&game->animations)};
  std::copy(std::begin(before),std::end(before),row);row[26]=vm->flags;row[27]=vm->flags2;row[30]=vm_depth;row[31]=u32(uintptr_t(vm));
 }
 ++vm_depth;const int result=__real__ZN4th115AnmVm6updateERNS_14AnmEnvironmentE(vm,env);--vm_depth;
 if(row){const u32 after[]={u32(vm->age.previous),u32(vm->age.current),th14_title_observer::float_bits(vm->age.fractional),
  u32(vm->timer.previous),u32(vm->timer.current),th14_title_observer::float_bits(vm->timer.fractional),
  th14_title_observer::float_bits(vm->rotation.z),u32(result)};
  std::copy(std::begin(after),std::end(after),row+18);row[28]=vm->flags;row[29]=vm->flags2;}
 return result;
}
API(option_role_count) u32 option_role_count(){return option_call_roles::count.load(std::memory_order_acquire);}
API(option_role_data) const u32* option_role_data(){return option_call_roles::data.data();}
