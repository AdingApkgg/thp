#include "TrophyGridNavigation.hpp"
namespace th143 {
bool navigate_trophy_grid(AnmView t,AnmView save,u32 fresh,u32 repeated){
 if(!t.data||!save.data||t.get(0x30)!=70||t.get(0x28)>=70)return false;t.put(0x2c,t.get(0x28));MenuCursor cursor{t.sub(0x28)};i32 ignored;const u32 pressed=fresh|repeated;
 auto locked=[&](){return t.get(0x28)>=60&&!save.data[0xeff9+t.get(0x28)];};
 if(pressed&0x10){if(!cursor.move(-10,ignored))return false;if(locked()&&!cursor.move(-10,ignored))return false;}
 if(pressed&0x20){if(!cursor.move(10,ignored))return false;if(locked()&&!cursor.move(10,ignored))return false;}
 if(pressed&0x40){u32 budget=10;do{if(!budget--||!cursor.move(t.get(0x28)%10==0?9:-1,ignored))return false;}while(locked());}
 if(pressed&0x80){u32 budget=10;do{if(!budget--||!cursor.move(t.get(0x28)%10==9?-9:1,ignored))return false;}while(locked());}
 return true;
}
}
