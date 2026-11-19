#include "GameFrameTimingRuntime.hpp"
namespace th143 {
bool GameFrameTimingRuntime::create(u32& result){result=0;if(global_owner||!services.reserve_game_owner(self,data.size()))return false;data.fill(0);view().put(0,2);global_owner=self;u32 token;if(!services.allocate_game_storage(0x28,token)||!token||!scheduler.create(token,0x42bf70,services.game_allocation_fill()))return false;auto cb=scheduler.at(token);cb.put(4,cb.get(4)|2);cb.put(0x24,self);u32 value;if(!scheduler.add(token,72,true,*this,value))return false;view().put(12,token);result=self;return true;}
bool GameFrameTimingRuntime::destroy(){if(!global_owner)return true;if(!scheduler.remove(view().get(12),*this))return false;global_owner=0;return services.release_game_storage(self);}
}
