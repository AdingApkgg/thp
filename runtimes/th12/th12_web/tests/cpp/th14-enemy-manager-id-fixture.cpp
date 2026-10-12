#include "../../cpp/game/EnemyManager.hpp"
using namespace th11;
#define API(n) extern "C" __attribute__((export_name(#n)))
struct World:EnemyFrameWorld {void clear_shot_targets(Enemy*)override{}};
API(initial_id) u32 initial_id(){EclProgram program;EnemyEnvironment environment;EnemyCommandEnvironment commands;World world;EnemyManager manager(program,environment,commands,world);return manager.total_created;}
API(reset_id) u32 reset_id(u32 poison){EclProgram program;EnemyEnvironment environment;EnemyCommandEnvironment commands;World world;EnemyManager manager(program,environment,commands,world);manager.total_created=poison;if(!manager.reset(program)||manager.count||commands.manager!=&manager)return 0xffffffffu;return manager.total_created;}
