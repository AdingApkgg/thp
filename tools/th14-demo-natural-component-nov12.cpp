#include "th14-demo-clock-component-nov12.cpp"
API(begin_natural) u32 begin_natural(u32 index,float rate){
 session.reset();session=std::make_unique<GameSession>(0,false);
 auto& s=*session;s.interactive=true;
 s.animations.th14_native_stack.configure(0x12345678);
 char name[24];std::snprintf(name,sizeof name,"demo%u.rpy",index);
 std::vector<u8> replay;
 if(index>=3||!source.read(name,replay)||!s.begin_replay(source,replay.data(),u32(replay.size()),0,true))return 0;
 s.animations.rate=rate;player_calls=0;
 s.battle->before_player_update=[](const GameBattle&){++player_calls;};
 return 1;
}
