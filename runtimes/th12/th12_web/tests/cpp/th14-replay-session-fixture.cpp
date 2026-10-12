#include "th14-session-fixture.cpp"
static std::vector<u8> original_replay,saved_replay;
API(begin_demo) i32 begin_demo(u32 index){
 if(index>=3)return 0;char name[20];std::snprintf(name,sizeof name,"demo%u.rpy",index);
 return source.read(name,original_replay)&&session.begin_replay(source,original_replay.data(),u32(original_replay.size()),0,true);
}
API(replay_observation) i32 replay_observation(u32 n){
 const auto& r=session.playback;const auto* stage=r.stage(session.state.stage);
 const u32 selection=replay_selection;u32 raw[4]{};
 if(r.decoded().size()>=selection+16)std::memcpy(raw,r.decoded().data()+selection,16);
 switch(n){case 0:return session.state.character;case 1:return session.state.subtype;case 2:return session.state.difficulty;
 case 3:return session.state.stage;case 4:return stage?stage->frames:0;case 5:return r.frame();
 case 6:case 7:case 8:case 9:return raw[n-6];
 case 10:return session.economy.lives;case 11:return session.economy.power;case 12:return session.economy.th14_bombs;
 case 13:return session.animations.script_rng.seed;case 14:return session.animations.script_rng.calls;
 case 15:return session.economy.score_units;case 16:return session.economy.graze;
 case 17:return session.battle&&session.battle->player?session.battle->player->motion.state.x:0;
 case 18:return session.battle&&session.battle->player?session.battle->player->motion.state.y:0;
 default:return 0;}
}
