#pragma once
#include "GameEconomy.hpp"
namespace th11 {
#if PORT_TITLE == 14
bool th14_continue_economy(GameEconomy&,i32& continues)noexcept;
#endif
}
