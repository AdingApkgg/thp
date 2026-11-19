#pragma once
#include "DeviceInput.hpp"
#include "GameInputRuntime.hpp"
namespace th143 {
// The recording keyboard at4e1a64 is an overlapping bank of4e19d0.
// Copy at the dispatch boundary so Root startup and callback16 share writes;
// raw repeat counters in114..190 and longheld22c stay in the same bank.
inline void device_input_to_record(DeviceInputState& device,GameInputRuntime& input){std::memcpy(input.input.keyboard.data(),device.data.data()+0x94,input.input.keyboard.size());}
inline void record_input_to_device(GameInputRuntime& input,DeviceInputState& device){std::memcpy(device.data.data()+0x94,input.input.keyboard.data(),input.input.keyboard.size());}
}
