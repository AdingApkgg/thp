#include "BulletSoundTransform.hpp"
#include <map>
namespace th143 {
namespace{std::map<BulletMotionHost*,BulletSpatialSound> sounds;}
bool start_bullet_sound_transform(BulletView bullet,u32 row,const BulletSpatialSound& sound){
 if(!sound||!sound(signed_word(bullet.get(row+0x10)),bullet.floating(0xbc0)))return false;
 bullet.put(0xc20,bullet.get(0xc20)+1);return true;
}
void bind_bullet_sound_transform(BulletMotionHost& host,BulletSpatialSound sound){
 if(sound)sounds[&host]=std::move(sound);else sounds.erase(&host);
}
bool dispatch_bullet_sound_transform(BulletView bullet,u32 row,BulletMotionHost& host){
 const auto found=sounds.find(&host);return found!=sounds.end()&&start_bullet_sound_transform(bullet,row,found->second);
}
}
