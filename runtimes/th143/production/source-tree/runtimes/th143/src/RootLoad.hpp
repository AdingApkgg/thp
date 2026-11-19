#pragma once
#include "RootFrame.hpp"
#include <initializer_list>
namespace th143 {
struct RootLoadHost {
    virtual ~RootLoadHost()=default;
    virtual bool load_read(u32 token,void*,u32 bytes)=0;
    virtual bool load_write(u32 token,const void*,u32 bytes)=0;
    // Services preserve the used ECX/stack arguments; unused register/stack
    // garbage is canonicalized to zero. The application
    // adapter owns factories, resources, Scheduler, audio and presentation.
    virtual bool load_call(u32 entry,u32 owner,std::initializer_list<u32> args,u32& result)=0;
    virtual bool load_signal(u32 vm,i32 signal,bool immediate)=0;
    virtual bool load_sleep(u32 milliseconds)=0;
    virtual bool load_float_environment()=0;
};
// 432440/432a20. Native handled failure sets result=-1; missing host services
// return false. Sleep pumps the application's cooperative loading services.
bool load_root(RootState&,u32 self,RootLoadHost&,i32& result,u32 wait_budget=100000);
}
