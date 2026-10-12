#include "../../cpp/game/AnmManager.hpp"
#include "../../cpp/game/AnmOpcodes.hpp"
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static AnmManager manager;static AnmResource resource;static AnmVm *parent,*child;alignas(4) static u8 code[64];static AnmInstruction idle{0,8,32760,0};
API(run) i32 run(u32 op,u32 refs,u32 inherited,u32 layer,u32 program){
    manager.clear();resource={};resource.scripts.resize(2);
    auto append=[&](u32 slot,i16 raw,const void* args,u32 bytes,u16 references=0){auto& b=resource.scripts[slot].bytes;const auto at=b.size();b.resize(at+8+bytes);const AnmInstruction h{raw==-1?i16(-1):i16(anm_canonical_opcode(raw)),u16(8+bytes),0,references};std::memcpy(b.data()+at,&h,8);if(bytes)std::memcpy(b.data()+at+8,args,bytes);};
    append(0,2,nullptr,0);append(0,-1,nullptr,0);append(1,304,&layer,4);
    if(program==2)append(1,509,nullptr,0);
    if(program){const float fixed[]={10.5,-11.25,12.75},referenced[]={10004,10005,10006};append(1,400,program==2?referenced:fixed,12,program==2?7:0);}
    append(1,2,nullptr,0);append(1,-1,nullptr,0);
    parent=manager.create(resource,0,2,27);if(!parent)return -1;parent->flags2=inherited<<25;parent->position={12,21,34};parent->script_position={3,5,8};parent->rotation={.25,.5,.75};
    const i32 ints[]={1,6,9,12};const float floats[]={.25,-.5,.75,1};std::memcpy(parent->integers,ints,sizeof ints);std::memcpy(parent->floats,floats,sizeof floats);parent->extra_integers[0]=17;parent->extra_integers[1]=-19;
    const u32 tail[]={0x11223344,0x55667788,0x80000000,0xffffffff,0x3f800000,256};std::memcpy(parent->th16_variable_tail,tail,sizeof tail);
    std::memset(code,0,sizeof code);auto* p=reinterpret_cast<AnmInstruction*>(code);p->opcode=anm_canonical_opcode(op);p->length=op==505||op==506?20:12;p->references=refs;const i32 script=refs?10000:1;std::memcpy(code+8,&script,4);
    if(op==505||op==506){const float xy[]={refs?10004.f:.25f,refs?10005.f:-.5f};std::memcpy(code+12,xy,8);}
    auto* next=reinterpret_cast<AnmInstruction*>(code+p->length);next->length=8;next->time=32760;parent->instruction=parent->script_begin=p;parent->timer.set(0,&manager.rate);
    const int status=parent->update(manager);child=manager.find(parent->id+1);return child?status:-2;
}
API(word) u32 word(u32 n){switch(n){case 0:return child->parent==parent;case 1:return child->layer;case 2:return bool(child->flags2&0x2000000);case 3:return parent->child.next==&child->child;case 4:return !child->instruction;case 5:return bool(child->flags&0x100);default:break;}
    if(n==22)return bool(child->flags2&0x400);if(n>=6&&n<10)return u32(child->integers[n-6]);u32 bits=0;if(n>=10&&n<14)std::memcpy(&bits,child->floats+n-10,4);else if(n>=14&&n<16)return u32(child->extra_integers[n-14]);else if(n>=16&&n<22)return child->th16_variable_tail[n-16];return bits;
}
API(real) float real(u32 i){const auto& p=i<3?child->position:i<6?child->script_position:i<9?child->child_position:child->rotation;return i%3==0?p.x:i%3==1?p.y:p.z;}
API(overlay_registry) i32 overlay_registry(){child->instruction=&idle;child->timer.set(0,&manager.rate);if(!manager.update(false))return -1;return child->timer.current==0;}

API(transform_parent) i32 transform_parent(){return child->th16_transform_parent==parent;}
