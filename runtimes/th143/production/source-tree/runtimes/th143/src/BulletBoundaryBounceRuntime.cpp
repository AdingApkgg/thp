#include "BulletBoundaryBounceRuntime.hpp"
#include <map>
namespace th143 {
namespace {struct Binding{const BulletPool* pool;std::function<bool(i32)> sound;};std::map<BulletMotionHost*,Binding> bindings;}
void bind_bullet_boundary_bounce(BulletMotionHost& host,const BulletPool& pool,std::function<bool(i32)> sound){bindings[&host]={&pool,std::move(sound)};}
i32 dispatch_bullet_boundary_bounce(BulletView bullet,BulletMotionHost& host){const auto at=bindings.find(&host);if(at==bindings.end())return -2;const auto& binding=at->second;return update_bullet_boundary_bounce(bullet,real(binding.pool->get(0x64)),real(binding.pool->get(0x68)),binding.sound);}
}
