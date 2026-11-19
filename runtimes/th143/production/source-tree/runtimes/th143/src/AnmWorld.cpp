#include "AnmWorld.hpp"
#include "AnmGeometry.hpp"

namespace th143 {
bool AnmWorld::enable_pool(AnmPoolGlobals& globals,AnmPoolHost& services){
    if(pool||!states.empty()||!resources.empty())return false;
    pool_services=&services;pool=std::make_unique<AnmPool>();if(!pool->construct(globals,*this))return false;
    instances.registry.owner=pool->view();
    for(u32 i=0;i<AnmPool::count;++i){const u32 token=pool->self+AnmPool::first+i*AnmPool::stride;auto vm=pool->at(token);
        state_indices[token]=states.size();state_tokens.push_back(token);states.push_back(std::make_unique<StateStorage>(vm.data));instances.registry.pool.push_back(vm);
    }return true;
}
bool AnmWorld::register_pool_callback(u32 entry,i32 priority,bool draw,u32 owner){return pool_services&&pool_services->register_pool_callback(entry,priority,draw,owner);}
bool AnmWorld::set_pool_vertex_format(u32 value){return pool_services&&pool_services->set_pool_vertex_format(value);}
bool AnmWorld::allocate_pool_fallback(u32& token,AnmView& vm){
    token=0x62000000+external_count++*0x2000;auto owned=std::make_unique<StateStorage>();vm={owned->data()};
    state_indices[token]=states.size();state_tokens.push_back(token);states.push_back(std::move(owned));return true;
}
bool AnmWorld::acquire_state(u32& token,AnmView& vm){
    if(pool){if(!pool->allocate(token,vm,*this))return false;}
    else{if(!allocate_pool_fallback(token,vm))return false;anm_construct(vm);anm_reset(vm,token);vm.put(0x544,8191);}
    allocations.push_back(token);return true;
}
AnmView AnmWorld::state(u32 token){auto i=state_indices.find(token);return i==state_indices.end()?AnmView{nullptr}:AnmView{states[i->second]->data()};}
AnmWorld::Resource* AnmWorld::resource(u32 token) {
    for(auto& r:resources)if(r.token==token)return &r;return nullptr;
}
bool AnmWorld::read(u32 token,void* out,u32 n) {
    auto state=state_indices.upper_bound(token);
    if(state!=state_indices.begin()){
        --state;if(std::uint64_t(token)+n<=std::uint64_t(state->first)+AnmView::bytes){std::memcpy(out,states[state->second]->data()+token-state->first,n);return true;}
    }
    for(auto& r:regions)if(token>=r.token&&std::uint64_t(token)+n<=std::uint64_t(r.token)+r.bytes.size()){
        std::memcpy(out,r.bytes.data()+token-r.token,n);return true;
    }return false;
}
bool AnmWorld::write(u32 token,const void* in,u32 n) {
    for(auto& r:regions)if(token>=r.token&&std::uint64_t(token)+n<=std::uint64_t(r.token)+r.bytes.size()){
        std::memcpy(r.bytes.data()+token-r.token,in,n);return true;
    }return false;
}
bool AnmWorld::timer_rate(u32 token,float& out) {
    if(token!=global_rate_token())return false;out=rate;return true;
}
bool AnmWorld::sprite(u32 token,i32 index,u32& out,std::array<u32,17>& d) {
    auto* r=resource(token);if(!r||index<0||u32(index)>=r->count)return false;
    out=r->table+u32(index)*72;return read(out,d.data(),68);
}
bool AnmWorld::fallback_sprite(u32& token,i32& index) {
    for(auto& r:resources)if(r.file==2){token=r.token;index=262;return true;}return false;
}
bool AnmWorld::script(u32 token,i32 index,u32& out,u16& file,bool& ready) {
    auto* r=resource(token);if(!r||index<0||u32(index)>=r->scripts.size())return false;
    out=r->scripts[index];file=u16(r->file);ready=true;return true;
}
bool AnmWorld::build(u32 token) {
    auto* r=resource(token);if(!r)return false;r->templates.resize(r->scripts.size());
    if(pool){if(r->file>=30)return false;pool->view().put(0xbc7b0c+r->file*4,token);}
    for(u32 i=0;i<r->scripts.size();++i)if(!anm_template({r->templates[i].data()},r->template_token+i*AnmView::bytes,token,i,*this)){error=i;return false;}
    return true;
}
bool AnmWorld::create(u32 token,i32 script,i32 layer,u32& handle,bool prepend) {
    auto* r=resource(token);if(!r||script<0||u32(script)>=r->templates.size())return false;
    u32 self;AnmView vm;if(!acquire_state(self,vm))return false;
    return instances.create(token,vm,self,{r->templates[script].data()},layer,*this,handle,false,prepend);
}
bool AnmWorld::begin_frame(float elapsed) {
    // Original483830 resets the frame visit count before ordinary483740.
    // Nonempty secondary lists require their interpreter/draw path first.
    if(instances.registry.secondary_head)return false;
    rate=elapsed;manager.visited=0;return true;
}
bool AnmWorld::create_effect(i32 script,const std::array<float,3>& position,u32& handle){return create_at(effect_resource,script,-1,position,handle);}
bool AnmWorld::cancel_bullet(u32 token,i32 script,const std::array<float,3>& position,const std::array<float,3>& target){
    u32 handle;if(!create_at(token,script,-1,position,handle))return false;auto vm=find(handle);if(!vm.data)return false;
    vm.put(0xec,30);vm.put(0xf0,6);
    for(u32 i=0;i<3;++i){vm.put(0x9c+i*4,0);vm.put(0xa8+i*4,word(target[i]));vm.put(0xb4+i*4,0);vm.put(0xc0+i*4,0);}
    if(!(vm.get(0xe8)&1)){vm.put(0xe4,global_rate_token());vm.put(0xe8,vm.get(0xe8)|1);}
    vm.put(0xd8,0xffffffff);vm.put(0xdc,0);vm.put(0xe0,0);return true;
}
bool AnmWorld::create_at(u32 token,i32 script,i32 layer,const std::array<float,3>& position,u32& handle){
    auto* r=resource(token);if(!r||script<0||u32(script)>=r->templates.size())return false;
    u32 self;AnmView vm;if(!acquire_state(self,vm))return false;
    ++instances.resource_uses[token];
    anm_copy_template(vm,self,{r->templates[script].data()},global_rate_token());
    vm.put(0x1c,vm.get(0x1c)|0x200);
    if(layer>=0){vm.put(0x24,u32(layer));if(layer<=23)vm.put(0x1c,(vm.get(0x1c)&~0x40000u)|0x20000);}
    for(u32 i=0;i<3;++i)vm.put(0x59c+i*4,word(position[i]));vm.put(0x50,0);
    if(anm_step(vm,*this)==-2){u16 opcode=0;read(vm.get(0x28),&opcode,2);error=opcode;return false;}
    return instances.registry.insert(vm,self,false,false,handle);
}
bool AnmWorld::update() {const bool okay=manager.update(instances.registry,*this,*this);if(pool){auto p=pool->view();p.put(0xd8,manager.visited);for(u32 i=0;i<35;++i)p.put(0xfe8228+i*0x5cc+0x590,manager.draws[i]);}return okay;}
bool AnmWorld::parent_slowdown(u32 parent,float& out) {
    for(u32 depth=0;depth<1024;++depth){
        const AnmView vm=state(parent);if(!vm.data)return false;
        if(!vm.get(0x594)||(vm.get(0x1c)&0x8000)){out=vm.floating(0x598);return true;}parent=vm.get(0x594);
    }return false;
}
bool AnmWorld::child(AnmView parent,i32 script,u32 flags){
    auto* r=resource(parent.get(0x30));if(!r||script<0||u32(script)>=r->templates.size())return false;
    u32 self;AnmView vm;if(!acquire_state(self,vm))return false;u32 handle;
    const bool okay=instances.child(r->token,vm,self,{r->templates[script].data()},parent,parent.get(0x570),flags,*this,handle);last_child_token=self;return okay;
}
bool AnmWorld::detached_child(AnmView parent,i32 script){
    auto* r=resource(parent.get(0x30));if(!r||script<0||u32(script)>=r->templates.size())return false;
    u32 self;AnmView vm;if(!acquire_state(self,vm))return false;++instances.resource_uses[r->token];
    anm_copy_template(vm,self,{r->templates[script].data()},global_rate_token());
    vm.put(0x1c,((vm.get(0x1c)|0x200)&~0x1000000u)|(parent.get(0x1c)&0x1000000));vm.put(0x24,parent.get(0x24));
    for(u32 i=0;i<3;++i){vm.put(0x59c+i*4,parent.get(0x59c+i*4));vm.put(0x48+i*4,parent.get(0x48+i*4));vm.put(0x4ec+i*4,parent.get(0x3c+i*4));}
    if(anm_step(vm,*this)==-2){u16 opcode=0;read(vm.get(0x28),&opcode,2);error=opcode;return false;}
    u32 handle;const bool okay=instances.registry.insert(vm,self,false,false,handle);last_child_token=self;return okay;
}
AnmView AnmWorld::parameter_child(AnmView parent,i32 script,bool detached){
    if(!(detached?detached_child(parent,script):child(parent,script,0)))return {nullptr};return state(last_child_token);
}
bool AnmWorld::allocate_geometry(u32 bytes,u32& token){
    if(bytes>0x10000||geometry_buffers.size()>=512)return false;
    token=0x64000000+u32(geometry_buffers.size())*0x10000;
    geometry_buffers.push_back({token,std::vector<u8>(bytes)});return true;
}
AnmView AnmWorld::transform_parent(u32 token){
    return state(token);
}
bool AnmWorld::update_geometry(AnmView vm){
    AnmGeometryContext c;c.viewport_scale=viewport.scale;
    const u32 mode=(vm.get(0x18)>>25)&31;
    if(mode<24&&!anm_position(vm,viewport,*this,c.position))return false;
    if(mode<24&&vm.get(0x594)&&!(vm.get(0x1c)&0x8000)){
        auto parent=transform_parent(vm.get(0x594));if(!parent.data)return false;
        c.parent_scale={parent.floating(0x60),parent.floating(0x64)};
    }
    for(auto& b:geometry_buffers)if(b.token==vm.get(0x5b4))return anm_geometry(vm,b.bytes,c);
    return false;
}
bool AnmWorld::slowdown(AnmView vm,float& out) {
    if(vm.get(0x594)&&!(vm.get(0x1c)&0x8000))return parent_slowdown(vm.get(0x594),out);
    out=vm.floating(0x598);return true;
}
bool AnmWorld::effect(AnmView vm,i32 type) {
    if(type!=7){error=u32(type);return false;}
    auto extra=std::make_unique<Extra>();extra->token=0x66000000+extras.size()*0x2000;
    anm_effect7_initialize(vm,extra->data.data(),extra->token,global_rate_token());extras.push_back(std::move(extra));return true;
}
bool AnmWorld::callback(u32 entry,AnmView vm,float elapsed,i32& result) {
    Extra* data=nullptr;for(auto& p:extras)if(p->token==vm.get(0x5b4)){data=p.get();break;}
    if(!data){error=entry;return false;}
    const float previous=rate;rate=elapsed;bool okay=true;
    if(entry==0x407670){result=anm_effect7_step(vm,data->data.data(),*this);okay=result!=-2;}
    else if(entry==0x4081f0){result=0;okay=anm_effect7_cancel(data->data.data(),*this);}
    else if(entry==0x4081e0)result=0;
    else okay=false;
    rate=previous;if(!okay)error=entry;return okay;
}
bool AnmWorld::propagate(u32 handle,u32 offset,u32 mask,bool enabled) {
    auto vm=find(handle);if(!vm.data)return true;
    auto apply=[&](AnmView v){v.put(offset,enabled?v.get(offset)|mask:v.get(offset)&~mask);};apply(vm);
    if(vm.get(0x588))return true;
    u32 child=vm.get(0x584),budget=0;
    while(child){
        auto at=instances.registry.nodes.find(child-0x580);if(at==instances.registry.nodes.end()||++budget>instances.registry.nodes.size())return false;
        apply(at->second);child=at->second.get(0x584);
    }return true;
}
bool AnmWorld::flag(u32 handle,bool enabled){return propagate(handle,0x18,2,enabled);}
bool AnmWorld::mark_retirement(u32 handle){return propagate(handle,0x1c,0x20,true);}
bool AnmWorld::release_buffer(u32 token){releases.insert(releases.end(),{1,token});return true;}
bool AnmWorld::prepare_instance_release(u32 token,AnmView vm){return !pool||!pool->owns(token)||pool->return_slot(token,vm);}
bool AnmWorld::release_instance(u32 token){if(!pool||!pool->owns(token))releases.insert(releases.end(),{2,token});return true;}
}
