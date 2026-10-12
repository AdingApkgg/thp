#include "title-session-probe-fixture.cpp"
API(begin_season) i32 begin_season(u32 character,u32 season){
 if(season>=5||!session.begin(source,1,character,0,1))return 0;
 auto& player=*session.battle->player;session.economy.th16_subseason=season;
 player.th16_season_shots=&session.resources.core.season_shots[season];player.th16_season_animation=&session.resources.core.season_players[season];
 return player.rebuild_th16_options();
}
API(upgrade) i32 upgrade(i32 power,i32 energy){session.economy.power=power;session.economy.th16_season.count=energy;return session.battle->power_changed()&&session.battle->hud.update_season_th16();}
API(option_count) i32 option_count(u32 season){const auto& motion=session.battle->player->motion;return season?motion.th16_season_count:motion.state.option_count;}
API(option_valid) i32 option_valid(u32 n){const auto& player=*session.battle->player;const auto& motion=player.motion;const auto& option=motion.options[n];auto* vm=session.animations.find(option.animation);
 if(!option.state)return -1;if(!vm)return 0;
 const auto* resource=n<4?&session.resources.core.players[session.state.character]:player.th16_season_animation;
 return vm->resource==resource&&vm->file_index==(n<4?9:30)&&std::isfinite(vm->position.x)&&std::isfinite(vm->position.y);
}
API(body_word) u32 body_word(u32 n){const auto& vm=session.battle->player->motion.body;return n==0?vm.flags2:n==1?float_bits(vm.position.x):float_bits(vm.position.y);}
API(shots_count) u32 shots_count(u32 season){u32 count=0;auto& manager=session.battle->player->shots;for(u32 n=0;n<256;++n){const auto& shot=manager.at(n);if(shot.state&&bool(shot.th16.packed&0xf0000)==bool(season))++count;}return count;}
API(shots_valid) i32 shots_valid(){auto& manager=session.battle->player->shots;for(u32 n=0;n<256;++n){const auto& state=manager.at(n);if(!state.state)continue;const auto& shot=state.th16;auto* vm=session.animations.find(shot.animation);if(!state.spec)return 0;if(!vm)continue;const bool season=shot.packed&0xf0000;const auto* resource=season?session.battle->player->th16_season_animation:&session.resources.core.players[session.state.character];if(vm->resource!=resource||vm->file_index!=(season?30:9)||!std::isfinite(vm->position.x)||!std::isfinite(vm->position.y))return 0;}return 1;}
API(shots_stale) u32 shots_stale(){u32 count=0;auto& manager=session.battle->player->shots;for(u32 n=0;n<256;++n){const auto& shot=manager.at(n);if(shot.state&&!session.animations.find(shot.th16.animation))++count;}return count;}
API(bullet_diagnostic) i32 bullet_diagnostic(u32 n){auto& manager=session.battle->bullets;if(n==0)return manager.last_error;auto* bullet=manager.first_th16();if(!bullet)return -1;if(n==1)return bullet->transform_index;if(n==2)return bullet->sprite;if(n==3)return bullet->color;return n<22?bullet->th16_transforms[n-4].opcode:-1;}
