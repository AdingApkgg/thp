#include "GameLaserKinds012Runtime.hpp"
namespace th143 {
GameLaserKinds012Runtime::GameLaserKinds012Runtime(GameOwnerRuntime& o,AnmResourceWorld& w,GameOwnerServices& a,SoundQueue& q,GameRenderRuntime& r,GameRenderDevice& d):owners(o),world(w),allocator(a),audio(q),render(r),device(d),kind0(o,w,a,q,r),kind1(o,w,a,q,r),contact_scratch(kind0.contact_scratch){
 kind0.rectangle_contact=[this](const std::array<float,3>& p,float l,float w,float a,bool f,i32& result){return rectangle_contact&&rectangle_contact(p,l,w,a,f,result);};
 kind0.graze_effect=[this](const std::array<float,3>& p){return graze_effect&&graze_effect(p);};
 kind0.item_effect=[this](const std::array<float,3>& p,i32 k){return item_effect&&item_effect(p,k);}; kind1.rectangle_contact=[this](const std::array<float,3>& p,float l,float w,float a,bool f,i32& result){return rectangle_contact&&rectangle_contact(p,l,w,a,f,result);};
 kind1.graze_effect=[this](const std::array<float,3>& p){return graze_effect&&graze_effect(p);};
 kind1.item_effect=[this](const std::array<float,3>& p,i32 k){return item_effect&&item_effect(p,k);};
 kind1.straight_spawn=[this](const u8* p,u32 n){return kind0.launch_laser(0,p,n);};
 kind1.boss_position=[this](std::array<float,3>& p,bool& present){return boss_position&&boss_position(p,present);};
}
AnmView GameLaserKinds012Runtime::beam(u32 p){for(auto& b:owners.storage)if(p==b.token&&b.bytes.size()>=0x14d0)return {b.bytes.data()};return {nullptr};}
bool GameLaserKinds012Runtime::read(u32 p,void* out,u32 n){const bool ok=owners.read(p,out,n)||world.read(p,out,n);if(!ok){diagnostic[0]=1;diagnostic[1]=p;diagnostic[2]=n;}return ok;}
bool GameLaserKinds012Runtime::write(u32 p,const void* in,u32 n){const bool ok=owners.write(p,in,n)||world.write(p,in,n);if(!ok){diagnostic[0]=2;diagnostic[1]=p;diagnostic[2]=n;}return ok;}
bool GameLaserKinds012Runtime::allocate(u32 n,u32& p,u8*& out){if(!allocator.allocate_game_storage(n,p)||!p)return false;owners.storage.push_back({p,std::vector<u8>(n,allocator.game_allocation_fill())});out=owners.storage.back().bytes.data();return true;}
bool GameLaserKinds012Runtime::script_bound(){if(world.pool){auto v=world.pool->view();v.put(0xc0,v.get(0xc0)+1);}return true;}
bool GameLaserKinds012Runtime::bullet_style(u32 p,i32& type,i32& color){auto v=beam(p);if(!v.data)return false;type=signed_word(v.get(0x5b8));color=signed_word(v.get(0x5bc));return true;}
AnmView GameLaserKinds012Runtime::laser_animation_template(u32 p,i32 script){auto* r=world.resource(p);return r&&script>=0&&u32(script)<r->templates.size()?AnmView{r->templates[u32(script)].data()}:AnmView{nullptr};}
bool GameLaserKinds012Runtime::laser_factory_initialize(u32 kind,u32 token,u32 p){auto v=beam(token);if(kind!=2||p!=0x7001f0ac||!v.data)return false;const bool ok=initialize_laser_kind2(v.data,0x14f0,token,parameters.data(),parameters.size(),AnmView{owners.lasers.data()}.get(0x5f4),*this);if(!ok){diagnostic[0]=3;diagnostic[1]=token;}return ok;}
bool GameLaserKinds012Runtime::launch_laser(u32 kind,const u8* p,u32 n){if(kind==0)return kind0.launch_laser(kind,p,n);if(kind==1)return kind1.launch_laser(kind,p,n);if(kind!=2||!p||n!=parameters.size())return false;std::memcpy(parameters.data(),p,n);u32 result;return create_laser(GameOwnerRuntime::laser_self,kind,0x7001f0ac,*this,result);}
bool GameLaserKinds012Runtime::laser_kind2_update_contact(u32 p,bool forced){auto v=beam(p);return v.data&&contact_laser_kind2(v,p,forced,kind2_contact_z_scratch,*this);}
bool GameLaserKinds012Runtime::laser_kind2_update_animation(u32,AnmView v){return anm_step(v,static_cast<LaserKind2Host&>(*this))!=-2;}
bool GameLaserKinds012Runtime::laser_player_position(std::array<float,3>& out){for(u32 i=0;i<3;++i)out[i]=owners.player.floating(0x5e0+i*4);return true;}
bool GameLaserKinds012Runtime::laser_player_cancel(u32 p,const std::array<float,3>& center,const std::array<float,3>& size,float angle,i32 kind,bool items){i32 result;return rectangle(p,center,size,angle,kind,items,result);}
bool GameLaserKinds012Runtime::laser_rectangle_visual(i32 script,const std::array<float,3>& p){u32 handle;return world.create_at(owners.bullets.get(0x9bf6cc),script,-1,p,handle);}
bool GameLaserKinds012Runtime::laser_rectangle_mask_allocate(u32 n,u32& p,u8*& out){if(mask_token||!allocator.allocate_game_storage(n,p)||!p)return false;owners.storage.push_back({p,std::vector<u8>(n?n:1,allocator.game_allocation_fill())});mask_token=p;out=owners.storage.back().bytes.data();return true;}
bool GameLaserKinds012Runtime::laser_rectangle_mask_release(u32 p){if(p!=mask_token||!p)return false;const bool ok=world.release_enemy_storage(p,true);mask_token=0;return ok;}
bool GameLaserKinds012Runtime::laser_draw_external(u32,AnmView v,u32 vertices,u32 count){return draw_anm_external_geometry(0x72000000,0x72000000,v,vertices,count,*this,device,device)!=-2;}
bool GameLaserKinds012Runtime::invoke(u32 p,u32 slot,bool has,u32 argument,i32& result){
 auto v=beam(p);if(!v.data)return false;if(v.get(0)==0x4c5ed8)return kind0.invoke(p,slot,has,argument,result);if(v.get(0)==0x4c5e70)return kind1.invoke(p,slot,has,argument,result);if(v.get(0)!=0x4c5da0)return false;
 diagnostic[3]=p;diagnostic[4]=slot;diagnostic[5]=v.get(0x594);diagnostic[6]=v.get(0x598);
 if(slot==0x10&&!has)return update_laser_kind2(v,p,*this,result);
 if(slot==0x14&&!has){result=0;return draw_laser_kind2(v,p,{world.viewport.second_origin[0],render.playfield_origin[1]},*this);}
 if(slot==0x18&&!has){result=0;return cleanup_laser_kind2(v,*this);}
 if(slot==0x34&&has){result=0;return laser_kind2_update_contact(p,argument!=0);}return false;
}
bool GameLaserKinds012Runtime::draw(u32 entry,u32 p){if(entry==0x43ae70)return kind0.draw(entry,p);if(entry==0x43d150)return kind1.draw(entry,p);if(entry!=0x440720)return false;i32 result;return invoke(p,0x14,false,0,result);}
bool GameLaserKinds012Runtime::rectangle(u32 p,const std::array<float,3>& center,const std::array<float,3>& size,float angle,i32 kind,bool items,i32& result){auto v=beam(p);if(!v.data)return false;if(v.get(0)==0x4c5ed8)return kind0.rectangle(p,center,size,angle,kind,items,result);if(v.get(0)==0x4c5e70)return kind1.rectangle(p,center,size,angle,kind,items,result);return v.get(0)==0x4c5da0&&cancel_laser_kind2_rectangle(v,p,center,size,angle,kind,items,*this,result);}
bool GameLaserKinds012Runtime::circle(u32 p,const std::array<float,3>& center,float radius,i32 kind,bool items,i32& result){auto v=beam(p);if(!v.data)return false;if(v.get(0)==0x4c5ed8)return kind0.circle(p,center,radius,kind,items,result);if(v.get(0)==0x4c5e70)return kind1.circle(p,center,radius,kind,items,result);return v.get(0)==0x4c5da0&&cancel_laser_kind2_circle(v,center,radius,kind,items,*this,result);}
bool GameLaserKinds012Runtime::full(u32 p,i32 kind,bool items,i32& result){auto v=beam(p);if(!v.data)return false;if(v.get(0)==0x4c5ed8)return kind0.full(p,kind,items,result);if(v.get(0)==0x4c5e70)return kind1.full(p,kind,items,result);return v.get(0)==0x4c5da0&&cancel_laser_kind2_full(v,kind,items,*this,result);}
bool GameLaserKinds012Runtime::release(u32 p){return beam(p).data&&allocator.release_game_storage(p);}
}
