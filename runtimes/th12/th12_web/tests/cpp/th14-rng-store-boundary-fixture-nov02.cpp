#include "Rng.hpp"
using namespace th11;
static u32 output[10];
struct Input {u32 restore,phase;};
extern "C" u32 rng_case(u32 bits,u32 seed,u32 restore,u32 calls,u32 phase,u32 locking){
 Rng rng{u16(seed),0xbeef,calls},visual{};Input input{restore,phase};
 RngBoundaryScope scope(rng,visual,&input,[](void* context,Rng& state,RngBoundary phase){
  auto& input=*static_cast<Input*>(context);if(u32(phase)!=input.phase)return true;
  output[4]=state.seed;output[5]=state.reserved;output[6]=state.calls;state.seed=u16(input.restore);
  output[7]=state.seed;output[8]=state.reserved;output[9]=state.calls;return true;
 },locking);
 output[0]=bits==16?rng.next16():rng.next32();output[1]=rng.seed;output[2]=rng.reserved;output[3]=rng.calls;
 return u32(reinterpret_cast<uintptr_t>(output));
}
extern "C" u32 rng_atomic_case(u32 bits,u32 seed,u32 calls){
 Rng rng{u16(seed),0xbeef,calls};
 output[0]=bits==16?rng.next16():rng.next32();output[1]=rng.seed;output[2]=rng.reserved;output[3]=rng.calls;
 return u32(reinterpret_cast<uintptr_t>(output));
}
extern "C" u32 scope_lifetime_case(){
 Rng a{1},b{2},c{3},d{4};u32 outer=0,inner=0;
 auto tick=[](void* p,Rng&,RngBoundary){++*static_cast<u32*>(p);return true;};
 {
  RngBoundaryScope first(a,b,&outer,tick);
  {RngBoundaryScope second(c,d,&inner,tick);a.next16();c.next32();}
  c.next16();a.next32();
 }
 a.next16();output[0]=outer;output[1]=inner;output[2]=RngBoundaryScope::active==nullptr;output[3]=sizeof(Rng);
 return u32(reinterpret_cast<uintptr_t>(output));
}
extern "C" u32 scope_failure_case(){
 Rng a{1},b{};u32 visits=0;
 {RngBoundaryScope scope(a,b,&visits,[](void* p,Rng&,RngBoundary phase){++*static_cast<u32*>(p);return phase!=RngBoundary::SeedRead;});
  a.next32();a.next16();output[0]=visits;output[1]=scope.failed;}
 output[2]=RngBoundaryScope::active==nullptr;
 return u32(reinterpret_cast<uintptr_t>(output));
}
extern "C" u32 scope_reentry_case(){
 Rng a{1},b{};u32 visits=0;
 {RngBoundaryScope scope(a,b,&visits,[](void* p,Rng& state,RngBoundary phase){++*static_cast<u32*>(p);if(phase==RngBoundary::BeforeStore)state.next16();return true;});a.next32();}
 output[0]=visits;output[1]=a.calls;output[2]=RngBoundaryScope::active==nullptr;
 return u32(reinterpret_cast<uintptr_t>(output));
}
