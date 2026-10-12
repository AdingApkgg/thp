#include "th14-natural-input-fixture.cpp"
// Read-only post-clear lifecycle inspection. No forced completion export.
API(natural_ending_value) i32 natural_ending_value(u32 kind){
 if(kind==0)return session.ending?session.ending->index:-1;
 if(kind==1)return session.ending?session.ending->seen:-1;
 if(kind==2)return session.title?i32(session.title->screen):-1;
 if(kind==3)return session.ending?session.ending->active:0;
 if(kind==4)return session.scores.characters[session.state.character*2+session.state.subtype][0x7dc+session.state.difficulty*4];
 return -1;
}
