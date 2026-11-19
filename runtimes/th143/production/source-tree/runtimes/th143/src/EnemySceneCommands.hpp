#pragma once
#include "EnemyScripts.hpp"
namespace th143 {
struct EnemySceneCommandService {virtual ~EnemySceneCommandService()=default;virtual i32 scene_command(EnemyScripts&,Vm&)=0;virtual u8* scene_reference(EnemyScripts&,i32,bool){return nullptr;}};
void bind_enemy_scene_commands(EnemyScripts&,EnemySceneCommandService*);
i32 dispatch_enemy_scene_command(EnemyScripts&,Vm&);
VmHost& enemy_scene_vm_host(EnemyScripts&);
}
