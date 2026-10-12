#include "../../cpp/game/AnmManager.hpp"
#include "../../cpp/game/AnmOpcodes.hpp"
#include <cstdlib>
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static AnmVm nodes[3]{};static Vec3 result{};
static AnmManager manager;static AnmResource resource;static AnmVm* child=nullptr;
static i32 registry=-1;static u32 parent_id=0,child_id=0;
API(allocate) void* allocate(u32 n){return std::malloc(n);}
API(release) void release(void* p){std::free(p);}
API(position_case) void position_case(u32 depth,const float* vectors,const u32* flags){
    for(u32 i=0;i<3;++i){auto& vm=nodes[i];vm={};vm.initialize();vm.flags2=flags[i];vm.parent=i<depth?&nodes[i+1]:nullptr;std::memcpy(&vm.position,vectors+i*9,12);std::memcpy(&vm.script_position,vectors+i*9+3,12);std::memcpy(&vm.child_position,vectors+i*9+6,12);}
    result=nodes[0].render_position();
}
API(position_value) float position_value(u32 i){return i==0?result.x:i==1?result.y:result.z;}
API(spawn_case) i32 spawn_case(u32 opcode){
    manager.clear();resource={};resource.scripts.resize(2);
    auto append=[&](i16 op,const void* args,u32 size,i16 time=0){auto& b=resource.scripts[0].bytes;const auto at=b.size();b.resize(at+8+size);AnmInstruction header{op,u16(8+size),time,0};std::memcpy(b.data()+at,&header,8);if(size)std::memcpy(b.data()+at+8,args,size);};
    const Vec3 script{3,5,8},rotation{.25,.5,.75},position{12,21,34};const i32 slot=1;
    append(48,&script,12);append(49,&rotation,12);append(anm_canonical_opcode(opcode),&slot,4);append(2,nullptr,0);append(-1,nullptr,0);
    const AnmInstruction idle{0,8,32760,0},end{-1,8,32767,0};auto& b=resource.scripts[1].bytes;b.resize(16);std::memcpy(b.data(),&idle,8);std::memcpy(b.data()+8,&end,8);
    auto* parent=manager.create(resource,0,0,7,false,false,&position);if(!parent)return -1;
    parent_id=parent->id;child_id=parent_id-1;child=manager.find(child_id);if(!child)return -2;
    if(!manager.update(false))return -3;registry=child->timer.current==2?0:1;return 0;
}
API(spawn_word) u32 spawn_word(u32 field){return field==0?child->layer:field==1?child->parent==manager.find(parent_id):registry;}
API(spawn_real) float spawn_real(u32 field){const auto& p=field<3?child->position:field<6?child->child_position:child->rotation;return field%3==0?p.x:field%3==1?p.y:p.z;}
API(parent_move) float parent_move(){auto* parent=manager.find(parent_id);parent->position.x+=100;return child->render_position().x;}
API(parent_destroy) u32 parent_destroy(){manager.destroy(*manager.find(parent_id));manager.update(false);manager.update(true);return manager.find(child_id)!=nullptr;}
API(nested_retirement) i32 nested_retirement(){
    manager.clear();resource={};resource.scripts.resize(3);
    for(i32 i=0;i<3;++i){auto& bytes=resource.scripts[i].bytes;
        if(i<2){const AnmInstruction spawn{88,12,0,0};const i32 slot=i+1;bytes.resize(12);std::memcpy(bytes.data(),&spawn,8);std::memcpy(bytes.data()+8,&slot,4);}
        const AnmInstruction stop{2,8,0,0};const auto at=bytes.size();bytes.resize(at+8);std::memcpy(bytes.data()+at,&stop,8);
    }
    auto* root=manager.create(resource,0,0,7);if(!root)return -1;u32 count=0;
    for(auto* n=root->child.next;n;n=n->next)if(++count>3)return -2;
    if(count!=2||manager.active_count()!=3)return -3;
    manager.destroy(*root);
    // Reusing the parent slot before deferred deletion must not keep any old
    // descendants alive or corrupt the replacement's child chain.
    auto* replacement=manager.create(resource,0,0,7);if(!replacement)return -4;const u32 id=replacement->id;
    if(!manager.update(false)||manager.active_count()!=3)return -5;
    replacement=manager.find(id);count=0;for(auto* n=replacement->child.next;n;n=n->next)if(++count>3)return -6;
    return count==2?0:-7;
}
