#include "EmitterCursorDecrement.hpp"
namespace th143 {
bool decrement_emitter_cursor(AnmView s,i32 index){
 if(index<0||index>=16)return false;
 const u32 at=0x3e3c+u32(index)*4,value=s.get(at)-1u;
 s.put(at,value&0x80000000u?0:value);return true;
}
}
