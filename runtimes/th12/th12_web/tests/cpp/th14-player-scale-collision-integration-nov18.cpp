#include "PlayerFrame.hpp"
#include <memory>
using namespace th11;
struct World final:PlayerFrameWorld {};
struct Fixture {
 ShtResource shots;AnmResource animations;AnmManager manager;GameEconomy economy;World world;
 PlayerFrame player{shots,animations,animations,manager,economy,world};
};
static std::unique_ptr<Fixture> fixture;
#define API(name) extern "C" __attribute__((export_name(#name)))
API(open_fixture) void open_fixture(){fixture=std::make_unique<Fixture>();}
API(close_fixture) void close_fixture(){fixture.reset();}
API(current_bounds) const u32* current_bounds(u32 flags,u32 factor){
 auto& p=fixture->player;p.th14_scale.flags=flags;p.th14_scale.factor=float_bits(factor);
 p.motion.state.position={12.25f,-80.5f,3.25f};p.state.hit_half={1,2,5};p.state.pickup_size={30,35,5};p.state.focused_half={50,59,5};
 p.update_bounds();static u32 out[24];const PlayerBounds values[]={p.state.hit,p.state.pickup,p.state.focused_attract,p.state.unfocused_attract};
 for(u32 i=0;i<4;i++){const float coords[]={values[i].minimum.x,values[i].minimum.y,values[i].minimum.z,values[i].maximum.x,values[i].maximum.y,values[i].maximum.z};for(u32 n=0;n<6;n++)out[i*6+n]=float_bits(coords[n]);}
 return out;
}
API(test) i32 test(i32 circle,float px,float py,float x,float y,float width,float height,float radius,float factor,i32 scaled,i32 state,i32 inv,i32 dialogue,i32 probe,i32 fault){
 auto& f=*fixture;auto& p=f.player;
 f.shots.header.hitbox=radius;p.motion.state.position={px,py,0};p.motion.state.flags=0;p.input.movement.bomb=false;
 p.state.hit={{px-.75f,py-1.25f,0},{px+.75f,py+1.25f,0}};
 p.th14_scale.flags=scaled?0x10u:0;p.th14_scale.factor=factor;p.state.life_state=state;p.state.invincibility.current=inv;
 // Exercise the actual live-player adapter; the old component fixture constructed this shape itself.
 auto shape=p.collision();shape.dialogue_active=dialogue!=0;
 if(fault==1)shape.radius=radius;
 if(fault==2&&scaled)shape.radius=shape.radius*factor*3.5999999046325684f;
 const auto r=circle?shape.circle({x,y},width,probe!=0):shape.rectangle({x,y},{width,height},probe!=0);
 return i32(r.kind)|(r.trigger_hit?0x100:0);
}
