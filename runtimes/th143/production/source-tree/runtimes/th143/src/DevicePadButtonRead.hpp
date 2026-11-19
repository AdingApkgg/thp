#pragma once
#include "AnmState.hpp"
#include <array>
namespace th143 {
struct DevicePadButtonReadHost {
 virtual ~DevicePadButtonReadHost()=default;
 virtual bool pad_winmm_state(std::array<u8,52>& info,u32& status)=0;
 virtual bool pad_direct_poll(u32 device,u32& status)=0;
 virtual bool pad_direct_acquire(u32 device,u32& status)=0;
 // The platform supplies all272 bytes even for a failing HRESULT; native
 //copies button bytes regardless. Partially uninitialized API output is separate.
 virtual bool pad_direct_state(u32 device,std::array<u8,272>& state,u32& status)=0;
};
//401e70. WinMM32button mask orDirectInput128bytes; failedPoll reacquires up to
//401calls andreturnszeros without readingState inthatframe.
bool read_device_pad_buttons(std::array<u8,128>& buttons,u32 config,u32 device,DevicePadButtonReadHost&);
}
