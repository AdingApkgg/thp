#pragma once
#include "AsciiFormat.hpp"
namespace th143 {
// Embedded MSVC precision2 rendering, including signed indefinite and Inf.
bool format_replay_slow_rate(std::string_view format,float value,std::string& out);
}
