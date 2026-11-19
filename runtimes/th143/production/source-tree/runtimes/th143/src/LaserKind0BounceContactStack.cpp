#include "LaserKind0BounceContactStack.hpp"
namespace th143 {
bool bind_laser_kind0_bounce_contact_stack(const u8* p,u32 n,std::array<u32,2>& scratch){
 if(!p||n!=0x354)return false;auto v=AnmView{const_cast<u8*>(p)};scratch[0]=v.get(0x340);scratch[1]=v.get(0x334);return true;
}
}
