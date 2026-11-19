#pragma once
#include "EclOwner.hpp"
#include "EclVariableTweens.hpp"
namespace th143 {
//41d350 resets the root and its list header after secondary storage is freed.
void reset_external_ecl_root(EclOwner&,EclVariableTweens*,u32& secondary_counter);
}
