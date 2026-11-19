#pragma once
#include "AnmState.hpp"
#include <array>
namespace th143 {
struct DeviceInputState {
    static constexpr u32 bytes=0x248;
    std::array<u8,bytes> data{};
    AnmView view(){return {data.data()};}
};
struct DeviceInputHost {
    virtual ~DeviceInputHost()=default;
    // Both APIs return a complete declared256-byte keyboard buffer. The
    // Win32 BOOL is ignored by401fa0; DirectInput HRESULT failures reacquire.
    virtual bool keyboard_state(bool direct,std::array<u8,256>&,u32& status)=0;
    virtual bool acquire_keyboard(u32& status)=0;
    virtual bool missing_winmm_joystick(u32& error)=0;
};
void initialize_device_bindings(DeviceInputState&); //4072a0, preserves counters
void advance_device_buttons(DeviceInputState&); //407210
//401fa0 keyboard paths and401b70's failed WinMM query. A live joystick or the
// separate DirectInput joystick mode (config800) needs its actual typed host.
bool poll_device_keyboard(DeviceInputState&,bool enabled,u32 config,DeviceInputHost&,u32& held);
}
