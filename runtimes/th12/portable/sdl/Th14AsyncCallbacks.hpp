#pragma once
#include <emscripten.h>
#include <cstdint>
// Used only by TH14's GLES Application translation unit. Keep these exports
// distinct from the optional WebGPU host and its archive integration.
using Th14AsyncWork=void(*)(void*);
using Th14AsyncFrame=EM_BOOL(*)(double,void*);
EM_JS(void,th14_async_schedule,(Th14AsyncWork callback,void* data,int delay),{
    Module['th14AsyncRuntime'].schedule(callback,data,delay);
});
EM_JS(int,th14_async_request_frames,(Th14AsyncFrame callback,void* data),{
    return Module['th14AsyncRuntime'].startFrames(callback,data);
});
extern "C" {
EMSCRIPTEN_KEEPALIVE void th14_async_invoke(std::uint32_t callback,std::uint32_t data){reinterpret_cast<void(*)(void*)>(std::uintptr_t(callback))(reinterpret_cast<void*>(std::uintptr_t(data)));}
EMSCRIPTEN_KEEPALIVE int th14_async_frame(std::uint32_t callback,double time,std::uint32_t data){return reinterpret_cast<EM_BOOL(*)(double,void*)>(std::uintptr_t(callback))(time,reinterpret_cast<void*>(std::uintptr_t(data)));}
}
