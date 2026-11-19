#include "GameLaserKind1Runtime.hpp"
namespace th143 {
namespace {u32 laser_diagnostic[16]{};std::array<u8,0x374> laser_parameter_snapshot;}
extern "C" __attribute__((export_name("day10_laser1_diagnostic"))) u32 day10_laser1_diagnostic(u32 i){return i<16?laser_diagnostic[i]:0;}
extern "C" __attribute__((export_name("day10_laser1_parameter_data"))) const u8* day10_laser1_parameter_data(){return laser_parameter_snapshot.data();}

AnmView GameLaserKind1Runtime::beam(u32 token){for(auto& b:owners.storage)if(token==b.token&&b.bytes.size()>=0x14d0)return {b.bytes.data()};return {nullptr};}
bool GameLaserKind1Runtime::read(u32 p,void* out,u32 n){const bool ok=owners.read(p,out,n)||world.read(p,out,n);if(!ok){laser_diagnostic[0]=2;laser_diagnostic[1]=p;laser_diagnostic[2]=n;}return ok;}
bool GameLaserKind1Runtime::write(u32 p,const void* in,u32 n){const bool ok=owners.write(p,in,n)||world.write(p,in,n);if(!ok){laser_diagnostic[0]=3;laser_diagnostic[1]=p;laser_diagnostic[2]=n;}return ok;}
bool GameLaserKind1Runtime::script_bound(){if(world.pool){auto v=world.pool->view();v.put(0xc0,v.get(0xc0)+1);}return true;}
bool GameLaserKind1Runtime::bullet_style(u32 token,i32& type,i32& color){auto v=beam(token);if(!v.data)return false;type=signed_word(v.get(0x5b8));color=signed_word(v.get(0x5bc));return true;}
AnmView GameLaserKind1Runtime::laser_animation_template(u32 token,i32 script){auto* r=world.resource(token);return r&&script>=0&&u32(script)<r->templates.size()?AnmView{r->templates[u32(script)].data()}:AnmView{nullptr};}
bool GameLaserKind1Runtime::laser_factory_allocate(u32 n,u32& token,u8*& out){laser_diagnostic[3]=n;if(n!=0x14d0||!allocator.allocate_game_storage(n,token)){laser_diagnostic[0]=4;return false;}laser_diagnostic[4]=token;owners.storage.push_back({token,std::vector<u8>(n,allocator.game_allocation_fill())});out=owners.storage.back().bytes.data();return true;}
bool GameLaserKind1Runtime::laser_factory_initialize(u32 kind,u32 token,u32 pointer){auto v=beam(token);laser_diagnostic[5]=AnmView{owners.lasers.data()}.get(0x5f4);laser_diagnostic[6]=token;laser_diagnostic[7]=kind;laser_diagnostic[8]=pointer;return kind==1&&pointer==0x7001f0ac&&v.data&&initialize_laser_kind1(v.data,0x14d0,token,parameters.data(),parameters.size(),AnmView{owners.lasers.data()}.get(0x5f4),*this);}
bool GameLaserKind1Runtime::launch_laser(u32 kind,const u8* data,u32 n){for(auto& v:laser_diagnostic)v=0;laser_diagnostic[0]=1;laser_diagnostic[10]=kind;laser_diagnostic[11]=n;if(kind!=1||!data||n!=parameters.size())return false;std::memcpy(parameters.data(),data,n);laser_parameter_snapshot=parameters;u32 result;return create_laser(GameOwnerRuntime::laser_self,kind,0x7001f0ac,*this,result);}
bool GameLaserKind1Runtime::laser_player_position(std::array<float,3>& out){for(u32 i=0;i<3;++i)out[i]=owners.player.floating(0x5e0+i*4);return true;}
bool GameLaserKind1Runtime::laser_kind0_contact(u32 token,u32 argument){auto v=beam(token);return v.data&&contact_laser_kind1(v,token,argument!=0,contact_z_scratch,*this);}
bool GameLaserKind1Runtime::invoke(u32 token,u32 slot,bool has_argument,u32 argument,i32& result){auto v=beam(token);if(!v.data||v.get(0)!=0x4c5e70)return false;
 if(slot==0x10&&!has_argument){laser_diagnostic[12]=v.get(0x594);laser_diagnostic[13]=v.get(0x598);laser_diagnostic[14]=v.get(0x594)<18?v.get(0x5f4+v.get(0x594)*0x2c+0x20):0;laser_diagnostic[15]=0;LaserKind1UpdateServices services;services.boss_position=boss_position;services.contact=[this](u32 p,bool f){return laser_kind0_contact(p,u32(f));};return update_laser_kind1(v,token,*this,services,result);}
 if(slot==0x14&&!has_argument){result=0;return draw_laser_kind1(v,token,*this);}
 if(slot==0x18&&!has_argument){result=0;return true;} // Actual43d220 is xor eax,eax;ret.
 if(slot==0x34&&has_argument){result=0;return laser_kind0_contact(token,argument);}return false;
}
bool GameLaserKind1Runtime::draw(u32 entry,u32 token){if(entry!=0x43d150)return false;i32 result;return invoke(token,0x14,false,0,result);}
bool GameLaserKind1Runtime::release(u32 token){return beam(token).data&&allocator.release_game_storage(token);}
bool GameLaserKind1Runtime::laser_player_cancel(u32 token,const std::array<float,3>& p,const std::array<float,3>& size,float angle,i32 kind,bool items){auto v=beam(token);i32 result;return v.data&&cancel_laser_kind1_rectangle(v,p,size,angle,kind,items,*this,result);}
bool GameLaserKind1Runtime::laser_rectangle_visual(i32 script,const std::array<float,3>& p){u32 handle;return world.create_at(owners.bullets.get(0x9bf6cc),script,-1,p,handle);}
}

namespace th143 {bool GameLaserKind1Runtime::rectangle(u32 token,const std::array<float,3>& p,const std::array<float,3>& size,float angle,i32 kind,bool items,i32& result){auto v=beam(token);return v.data&&v.get(0)==0x4c5e70&&cancel_laser_kind1_rectangle(v,p,size,angle,kind,items,*this,result);}}

namespace th143 {
bool GameLaserKind1Runtime::circle(u32 token,const std::array<float,3>& p,float radius,i32 kind,bool items,i32& result){auto v=beam(token);return v.data&&v.get(0)==0x4c5e70&&cancel_laser_kind1_circle(v,p,radius,kind,items,*this,result);}
bool GameLaserKind1Runtime::full(u32 token,i32 kind,bool items,i32& result){auto v=beam(token);return v.data&&v.get(0)==0x4c5e70&&cancel_laser_kind1_full(v,kind,items,*this,result);}
}
