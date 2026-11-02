#include "Rng.hpp"
#include "Th14WebGpuCallbacks.hpp"
#include <emscripten.h>
using namespace th11;
namespace {
u32 status[32]{},bits,phase,locking,fail,visual;
bool asynchronous;
EM_ASYNC_JS(void,wait_boundary,(),{await Module['rngBoundaryWait']();});
struct Context {Rng* target;Rng* nested;RngBoundaryScope* expected;bool paused=false;};
bool tick(void* owner,Rng& rng,RngBoundary point){
 auto& context=*static_cast<Context*>(owner);++status[2];
 if(&rng!=context.target||u32(point)!=phase||context.paused)return true;
 context.paused=true;++status[4];status[0]=1;
 status[22]=RngBoundaryScope::active->previous->running;
 status[23]=RngBoundaryScope::active==context.expected;
 if(asynchronous)wait_boundary();
 if(RngBoundaryScope::active!=context.expected)++status[1];
 // A nested VM using other RNGs remains observable; recursive use of the
 // currently observed RNG must be suppressed by the scope's reentry guard.
 context.nested->next32();rng.next16();
 return !fail;
}
void first(void*){
 volatile u32 guard[2048];for(u32 i=0;i<2048;++i)guard[i]=i^0x6147ac91u;
 Rng a{1234,0xbeef,13},b{4321,0xcafe,27},c{7890,0xabba,39},d{9876,0xf00d,41};
 Context context{visual?&b:&a,&c,nullptr};
 {
  RngBoundaryScope outer(a,b,&context,tick,locking);
  {
   RngBoundaryScope inner(c,d,nullptr,[](void*,Rng&,RngBoundary){++status[3];return true;});
   context.expected=&inner;
   status[5]=bits==16?context.target->next16():context.target->next32();
   d.next16();(visual?a:b).next32();status[15]=outer.failed;
  }
  status[24]=RngBoundaryScope::active==&outer;
 }
 for(u32 i=0;i<2048;++i)if(guard[i]!=(i^0x6147ac91u))++status[1];
 status[6]=a.seed;status[7]=a.calls;status[8]=b.seed;status[9]=b.calls;
 status[10]=c.seed;status[11]=c.calls;status[12]=d.seed;status[13]=d.calls;
 status[14]=RngBoundaryScope::active!=nullptr;status[16]=a.reserved;status[17]=2048;
 status[0]=2;
}
void second(void*){if(status[0]!=2||RngBoundaryScope::active)++status[1];status[0]=3;}
EM_BOOL frame(double,void*){if(status[0]!=3||RngBoundaryScope::active)++status[1];++status[21];status[0]=4;return EM_FALSE;}
void setup(u32 b,u32 p,u32 l,u32 f,u32 v){
 for(auto& word:status)word=0;bits=b;phase=p;locking=l;fail=f;visual=v;
 if(RngBoundaryScope::active)++status[1];
}
}
extern "C" {
EMSCRIPTEN_KEEPALIVE const u32* rng_async_status(){return status;}
EMSCRIPTEN_KEEPALIVE void th11_key(u32 scan,u32 down){if(status[0]!=2||RngBoundaryScope::active)++status[1];++status[18];status[19]=scan;status[20]=down;}
EMSCRIPTEN_KEEPALIVE void rng_reference(u32 b,u32 p,u32 l,u32 f,u32 v){setup(b,p,l,f,v);asynchronous=false;first(nullptr);th11_key(17,1);second(nullptr);frame(0,nullptr);}
EMSCRIPTEN_KEEPALIVE void rng_schedule(u32 b,u32 p,u32 l,u32 f,u32 v){
 setup(b,p,l,f,v);asynchronous=true;
 th14_webgpu_schedule(first,nullptr,0);th14_webgpu_schedule(second,nullptr,0);th14_webgpu_request_frames(frame,nullptr);
}
}
