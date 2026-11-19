#pragma once
#include "DeviceInput.hpp"
namespace th143 {
//Full402af0. Clears output before checking5390b0; Win32 alwaysreturns2,
//DirectInput alwaysreturns1 (alsoaftererror+Acquire),disabledreturns0.
bool capture_nickname_keyboard(std::array<u8,256>&,bool enabled,u32 config,DeviceInputHost&,u32& mode);
}
