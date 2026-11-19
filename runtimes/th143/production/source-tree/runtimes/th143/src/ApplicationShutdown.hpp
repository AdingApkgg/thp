#pragma once
#include "AnmState.hpp"
#include <initializer_list>
namespace th143 {
struct ApplicationShutdownHost {
 virtual ~ApplicationShutdownHost()=default;
 virtual bool shutdown_read(u32 address,u32& value)=0;
 virtual bool shutdown_write(u32 address,u32 value)=0;
 // Entries8/32 are the COM Release/Unacquire vtable slots; others are original
 // function addresses or fixed import-slot identities. owner0 denotes cdecl.
 virtual bool shutdown_call(u32 entry,u32 owner,std::initializer_list<u32>,u32& result)=0;
};
// Complete443a00 body. The audio-drain service must eventually return zero.
// WinMain's subsequent scheduler/D3D/window teardown and CFG write are separate.
bool shutdown_application(u32 application,ApplicationShutdownHost&);
}
