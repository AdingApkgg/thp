#include "th14-enemy-movement-fixture.cpp"
API(player_initialize) void player_initialize(const u32* words){std::memcpy(&environment.player_position,words,12);}
