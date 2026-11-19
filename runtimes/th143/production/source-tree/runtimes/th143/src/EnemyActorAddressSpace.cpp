#include "EnemyActorAddressSpace.hpp"
#include <map>
namespace th143 {
namespace {std::map<EnemyScripts*,EnemyActorAddressSpace*> spaces;}
bool EnemyActorAddressSpace::allocate(u32& token){if(next<0x50010000||next>0xfffe0000)return false;token=next;next+=0x10000;++allocations;return true;}
void bind_enemy_actor_address_space(EnemyScripts& scripts,EnemyActorAddressSpace* space){if(space)spaces[&scripts]=space;else spaces.erase(&scripts);}
bool allocate_enemy_actor_address(EnemyScripts& scripts,u32 id,u32& token){auto at=spaces.find(&scripts);if(at!=spaces.end())return at->second->allocate(token);token=0x50000000+id*0x10000;return true;}
}
