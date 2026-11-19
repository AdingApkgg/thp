#include "BulletSpawnTransform.hpp"
#include <array>
#include <map>
namespace th143 {
namespace {
struct Services{BulletSpawnLaunch launch;BulletSpawnCancel cancel;};
std::map<BulletMotionHost*,Services> services;
float wrap(float angle){
 u32 count=0;while(angle>real(0x40490fdb)){angle-=real(0x40c90fdb);if(count++>32)break;}
 while(real(0xc0490fdb)>angle){angle+=real(0x40c90fdb);if(count++>32)break;}return angle;
}
}
bool start_bullet_spawn_transform(BulletView bullet,u32 row,const BulletSpawnLaunch& launch,const BulletSpawnCancel& cancel){
 if(!bullet.data||!launch)return false;
 std::array<u8,0x380> storage{};BulletView output{storage.data()};
 for(u32 i=0;i<3;++i)output.put(8+i*4,bullet.get(0xbc0+i*4));
 const auto half=[&](u32 at,u32 value){const u16 word=u16(value);std::memcpy(storage.data()+at,&word,2);};
 half(0x368,bullet.get(row+0x10));output.put(0x378,bullet.get(row+0x14));
 half(0x364,bullet.get(row+0x18));half(0x366,bullet.get(row+0x1c));
 output.put(0x374,0xffffffff);
 const float angle=bullet.floating(row);
 output.put(0x14,angle<=-998.f?bullet.get(0xbdc):word(wrap(angle)));
 output.put(0x18,bullet.get(row+4));
 output.put(0x1c,bullet.floating(row+8)<=-998.f?bullet.get(0xbd8):bullet.get(row+8));
 output.put(0x20,bullet.get(row+12));
 bullet.put(0xc20,bullet.get(0xc20)+1);
 output.put(0,bullet.get(row+0x3c));output.put(4,bullet.get(row+0x40));
 const u32 cancel_after=bullet.get(row+0x44);
 std::memcpy(storage.data()+0x28,bullet.data+0xc28,0x318);
 if(!launch(storage.data(),u32(storage.size())))return false;
 bullet.put(0xc20,bullet.get(0xc20)+1);
 if(cancel_after&&(!cancel||!cancel(bullet,0)))return false;
 return true;
}
void bind_bullet_spawn_transform(BulletMotionHost& host,BulletSpawnLaunch launch,BulletSpawnCancel cancel){
 if(launch||cancel)services[&host]={std::move(launch),std::move(cancel)};else services.erase(&host);
}
bool dispatch_bullet_spawn_transform(BulletView bullet,u32 row,BulletMotionHost& host){
 const auto found=services.find(&host);
 return found!=services.end()&&start_bullet_spawn_transform(bullet,row,found->second.launch,found->second.cancel);
}
}
