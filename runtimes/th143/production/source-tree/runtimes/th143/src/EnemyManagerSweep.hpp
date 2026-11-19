#pragma once
#include "EnemyCancel.hpp"
namespace th143 {
class EnemyScripts;
struct EnemyManagerSweepHost:EnemyCancelHost,AnmTimerHost {};
//421870: saved-next traversal, protected-actor filter, cleared drop block,
// unconditional retirement after death,and the manager's extra clock tick.
bool sweep_enemy_manager(u32 manager,EnemyManagerSweepHost&);
struct EnemyManagerSweepService {virtual ~EnemyManagerSweepService()=default;virtual bool sweep()=0;};
void bind_enemy_manager_sweep(EnemyScripts&,EnemyManagerSweepService*);
bool dispatch_enemy_manager_sweep(EnemyScripts&);
}
