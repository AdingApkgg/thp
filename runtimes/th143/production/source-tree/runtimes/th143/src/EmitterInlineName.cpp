#include "EmitterInlineName.hpp"
namespace th143 {
bool set_emitter_inline_name(AnmView s,i32 emitter,i32 row,u32 name){
 if(emitter<0||emitter>=16||row<0||row>=18)return false;
 s.put(0x68c+u32(emitter)*0x380+u32(row)*0x2c,name);return true;
}
}
