#pragma once
#include "DevicePadButtonRead.hpp"
namespace th143 {
struct DeviceJoystickControlHost:DevicePadButtonReadHost {
 virtual bool joystick_memory_read(u32,void*,u32)=0;
};
//Full401b70 adds configured joystick controls to a preexisting keyboard mask.
//DirectInput valid bindings are signed-negative(disabled) or0..127; WinMM
//positive bindings use the x86 shift-count mask. Device counters are separate.
bool poll_device_joystick(u32 held,DeviceJoystickControlHost&,u32& result);
}
