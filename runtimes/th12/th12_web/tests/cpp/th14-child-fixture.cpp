#include "../../cpp/game/AnmManager.hpp"
#include "../../cpp/game/AnmOpcodes.hpp"
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static AnmManager manager;
static AnmResource resource;
static AnmVm *parent,*child;
alignas(4) static u8 code[64];
static AnmInstruction idle{0,8,30000,0};
API(run) i32 run(u32 op,u32 refs,u32 inherited,u32 program){
    manager.clear();resource={};resource.scripts.resize(2);
    auto append=[&](u32 slot,i16 raw,const void* args,u32 bytes,u16 references=0){
        auto& b=resource.scripts[slot].bytes;const auto at=b.size();b.resize(at+8+bytes);
        const AnmInstruction h{raw==-1?i16(-1):i16(anm_canonical_opcode(raw)),u16(8+bytes),0,references};
        std::memcpy(b.data()+at,&h,8);if(bytes)std::memcpy(b.data()+at+8,args,bytes);
    };
    append(0,2,nullptr,0);append(0,-1,nullptr,0);
    if(program)append(1,509,nullptr,0);
    if(program==2){const float args[]={10004,10005,10006};append(1,400,args,12,7);}
    append(1,2,nullptr,0);append(1,-1,nullptr,0);
    parent=manager.create(resource,0,0,7);if(!parent)return -1;
    parent->flags2=inherited<<24;parent->position={12,21,34};parent->script_position={3,5,8};parent->rotation={.25f,.5f,.75f};
    const i32 ints[]={1,6,9,12};const float floats[]={.25f,-.5f,.75f,1};
    std::memcpy(parent->integers,ints,sizeof(ints));std::memcpy(parent->floats,floats,sizeof(floats));
    parent->extra_floats={5.5f,-6.25f,7.75f};parent->extra_integers[0]=17;parent->extra_integers[1]=-19;
    parent->random_scale={1.25f,3.5f};parent->random_bound=256;
    std::memset(code,0,sizeof(code));auto* cmd=reinterpret_cast<AnmInstruction*>(code);
    const u32 count=op==505||op==506?3:1;cmd->opcode=anm_canonical_opcode(op);cmd->length=8+count*4;cmd->references=refs;
    const i32 script=refs?10000:1;std::memcpy(code+8,&script,4);
    if(count==3){const float xy[]={refs?10004.f:.25f,refs?10005.f:-.5f};std::memcpy(code+12,xy,8);}
    auto* next=reinterpret_cast<AnmInstruction*>(code+cmd->length);next->length=8;next->time=30000;
    parent->instruction=parent->script_begin=cmd;parent->timer.set(0,&manager.rate);
    const i32 status=parent->update(manager);child=manager.find(parent->id+1);return child?status:-2;
}
API(word) u32 word(u32 i){
    if(i==0)return child->parent==parent;if(i==1)return child->layer;if(i==2)return (child->flags2&0x1000000)!=0;
    if(i==3)return parent->child.next==&child->child;if(i==4)return child->instruction==nullptr;
    if(i>=5&&i<21){
        const void* values[]={child->integers,child->integers+1,child->integers+2,child->integers+3,child->floats,child->floats+1,child->floats+2,child->floats+3,
            &child->extra_floats.x,&child->extra_floats.y,&child->extra_floats.z,child->extra_integers,child->extra_integers+1,
            &child->random_scale.x,&child->random_scale.y,&child->random_bound};
        u32 value;std::memcpy(&value,values[i-5],4);return value;
    }return 0;
}
API(real) float real(u32 i){const auto& p=i<3?child->position:i<6?child->script_position:i<9?child->child_position:child->rotation;return i%3==0?p.x:i%3==1?p.y:p.z;}
API(overlay_registry) i32 overlay_registry(){
    child->instruction=&idle;child->timer.set(0,&manager.rate);if(!manager.update(false))return -1;
    return child->timer.current==0;
}
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
    auto* replacement=manager.create(resource,0,0,7);if(!replacement)return -4;const u32 id=replacement->id;
    if(!manager.update(false)||manager.active_count()!=3)return -5;
    replacement=manager.find(id);count=0;for(auto* n=replacement->child.next;n;n=n->next)if(++count>3)return -6;
    return count==2?0:-7;
}
