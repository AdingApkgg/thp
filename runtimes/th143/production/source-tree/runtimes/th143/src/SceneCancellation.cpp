#include "SceneCancellation.hpp"
#include <algorithm>
namespace th143 {
bool SceneCancellation::bind_actors(const std::vector<Actor>& input){
    if(active)return false;
    for(u32 i=0;i<input.size();++i){const auto& a=input[i];
        if(!a.token||std::uint64_t(a.token)+0x53d8>0x100000000ull||!a.state||!a.script||a.state->get(0x41b8)!=a.token)return false;
        for(u32 j=0;j<i;++j)if(input[j].token==a.token||input[j].state==a.state)return false;
    }actors=input;return true;
}
SceneCancellation::Actor* SceneCancellation::actor(u32 token){for(auto& a:actors)if(a.token==token)return &a;return nullptr;}
void SceneCancellation::publish(){bullets.put(0x9bf6c8,active->cancelled);items.put(0xde21d8,active->item_counter);rng=active->gameplay_rng;}
void SceneCancellation::refresh(){active->cancelled=bullets.get(0x9bf6c8);active->item_counter=items.get(0xde21d8);active->gameplay_rng=rng;}
bool SceneCancellation::circle(const std::array<float,3>& p,float radius,i32 kind,bool delayed,u32 flags){
    if(active)return false;BulletCancelGlobals g{bullets.get(0x9bf6c8),items.get(0xde21d8),flags,rng};active=&g;
    const bool okay=cancel_bullets_circle(BulletPool::token_base,p,radius,kind,delayed,world.rate,g,world,*this);publish();active=nullptr;return okay;
}
bool SceneCancellation::single(u32 token,i32 kind,u32 flags){
    if(active)return false;BulletView b{nullptr};if(!cancel_bullet_view(token,b))return false;
    BulletCancelGlobals g{bullets.get(0x9bf6c8),items.get(0xde21d8),flags,rng};active=&g;
    const bool okay=cancel_bullet(b,kind,bullets.get(0x9bf6cc),world.rate,g,world,*this);publish();active=nullptr;return okay;
}
bool SceneCancellation::item(const std::array<float,3>& p,i32 kind,u32 flags){
    if(active)return false;BulletCancelGlobals g{bullets.get(0x9bf6c8),items.get(0xde21d8),flags,rng};active=&g;
    const bool okay=bullet_cancel_item(p,kind,g,*this);publish();active=nullptr;return okay;
}
bool SceneCancellation::cancel_read(u32 p,void* out,u32 n){if(p<BulletPool::token_base||std::uint64_t(p)+n>std::uint64_t(BulletPool::token_base)+bullets.data.size())return false;std::memcpy(out,bullets.data.data()+BulletPool::offset(p),n);return true;}
bool SceneCancellation::cancel_write(u32 p,const void* in,u32 n){if(p<BulletPool::token_base||std::uint64_t(p)+n>std::uint64_t(BulletPool::token_base)+bullets.data.size())return false;std::memcpy(bullets.data.data()+BulletPool::offset(p),in,n);return true;}
bool SceneCancellation::cancel_bullet_view(u32 token,BulletView& view){
    if(token<BulletPool::bullet(0)||token>=BulletPool::bullet(BulletPool::count)||(token-BulletPool::bullet(0))%BulletPool::stride)return false;
    view={bullets.data.data()+BulletPool::offset(token)};return true;
}
bool SceneCancellation::animation_signal_callback(u32 entry,AnmView vm,i32 signal){publish();const bool okay=services.animation_signal_callback(entry,vm,signal);refresh();return okay;}
bool SceneCancellation::cancel_sound(u32 id,float x){publish();const bool okay=services.death_sound(i32(id),x);refresh();return okay;}
bool SceneCancellation::cancel_item(i32 type,const std::array<float,3>& p,float angle,float speed){publish();u32 ignored;const bool okay=items.spawn_delayed(type,p,angle,speed,world.global_rate_token(),ignored);refresh();return okay;}
bool SceneCancellation::cancel_enemy_circle(const std::array<float,3>& p,float radius,i32 kind){return th143::cancel_enemy_circle(enemy_manager,p,radius,kind,*active,*this,*this);}
bool SceneCancellation::enemy_cancel_read(u32 p,void* out,u32 n){
    if((p&3)||(n&3))return false;auto* bytes=static_cast<u8*>(out);
    for(u32 at=0;at<n;at+=4){const u32 address=p+at;u32 value;bool found=false;
        if(address==enemy_manager+0xd0){value=actors.empty()?0:actors.front().token+0x157c;found=true;}
        else for(u32 i=0;i<actors.size();++i){auto& a=actors[i];
            if(address==a.token+0x157c){value=a.token;found=true;break;}
            if(address==a.token+0x1580){value=i+1<actors.size()?actors[i+1].token+0x157c:0;found=true;break;}
            if(address>=a.token+0x11f0&&std::uint64_t(address)+4<=std::uint64_t(a.token)+0x53d8){value=a.state->get(address-a.token-0x11f0);found=true;break;}
        }
        if(!found)return false;std::memcpy(bytes+at,&value,4);
    }return true;
}
bool SceneCancellation::enemy_cancel_write(u32 p,const void* in,u32 n){
    if((p&3)||(n&3))return false;const auto* bytes=static_cast<const u8*>(in);
    for(auto& a:actors)if(p>=a.token+0x11f0&&std::uint64_t(p)+n<=std::uint64_t(a.token)+0x53d8){
        for(u32 at=0;at<n;at+=4){u32 value;std::memcpy(&value,bytes+at,4);a.state->put(p-a.token-0x11f0+at,value);}return true;
    }return false;
}
bool SceneCancellation::enemy_cancel_death(u32 token,i32& result){
    auto* a=actor(token);if(!a)return false;publish();
    if(!services.begin_cancelled_actor(*a->state,*a->script)){refresh();return false;}
    const bool okay=th143::enemy_death(*a->state,*a->script,a->callback,world,items,rng,services,result);
    const bool restored=services.end_cancelled_actor();refresh();return okay&&restored;
}
}
