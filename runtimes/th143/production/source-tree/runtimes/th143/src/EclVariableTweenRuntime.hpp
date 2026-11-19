#pragma once
#include "EclVariableTweens.hpp"
namespace th143 {
void campaign_tweens_reset(Vm&,u8);
void campaign_tweens_forget(const Vm&);
i32 campaign_tweens_command(Vm&,VmHost&);
bool campaign_tweens_advance(Vm&,VmHost&);
const EclVariableTweens* campaign_tweens_state(const Vm&);
bool campaign_vm_rate(float&);
}
