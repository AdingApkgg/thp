#include "BulletTransformCancel.hpp"
#include <map>
namespace th143 {
namespace {std::map<BulletMotionHost*,std::function<bool(BulletView,i32)>> bindings;}
bool start_bullet_transform_cancel(BulletView b,u32 row,const std::function<bool(BulletView,i32)>& cancel){if(!b.data||!cancel)return false;if(b.get(row+0x10)==1)b.put(0xc00,0xffffffff);return cancel(b,0);}
void bind_bullet_transform_cancel(BulletMotionHost& host,std::function<bool(BulletView,i32)> cancel){bindings[&host]=std::move(cancel);}
bool dispatch_bullet_transform_cancel(BulletView b,u32 row,BulletMotionHost& host){const auto at=bindings.find(&host);return at!=bindings.end()&&start_bullet_transform_cancel(b,row,at->second);}
}
