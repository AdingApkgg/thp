#include "../../cpp/sdl/StageWorkerWaitTh14.hpp"
namespace { th11::sdl::StageWorkerWaitTh14 wait; }
#define API(name) extern "C" __attribute__((export_name(#name)))
API(begin_wait) unsigned long long begin_wait(unsigned initial){wait.begin(initial!=0);return wait.generation;}
API(dispatch_wait) unsigned dispatch_wait(unsigned long long token,unsigned long long now){return wait.start(token,now);}
API(wait_ready) unsigned wait_ready(unsigned long long now){return wait.ready(now);}
API(wait_remaining) unsigned long long wait_remaining(unsigned long long now){return wait.remaining(now);}
API(deliver_wait) unsigned deliver_wait(unsigned long long token,unsigned long long now){return wait.finish(token,now);}
API(cancel_wait) void cancel_wait(){wait.cancel();}
API(wait_owns) unsigned wait_owns(unsigned long long token){return wait.owns(token);}
