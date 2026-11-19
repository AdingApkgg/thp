#pragma once
#include "DeviceInput.hpp"
#include "DeviceJoystickControl.hpp"
namespace th143 {
struct DeviceInputV2Host:DeviceJoystickControlHost {
 virtual bool keyboard_state(bool direct,std::array<u8,256>&,u32& status)=0;
 virtual bool acquire_keyboard(u32& status)=0;
};
//401fa0 with successful401b70 joystick routes and exactly one407210 counter
//advance. Both keyboard layouts and disabled-keyboard joystick input apply.
bool poll_device_input_v2(DeviceInputState&,bool enabled,u32 config,DeviceInputV2Host&,u32& held);
}
