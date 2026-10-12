#include "../../cpp/game/ScreenDeformation.hpp"
#include <memory>
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static AnmManager manager;static AnmResource resource;static std::unique_ptr<ScreenDeformation> mesh;
API(run) i32 run(u32 height){mesh.reset();manager.clear();resource={};resource.scripts.resize(60);const AnmInstruction commands[]={{2,8,0,0},{-1,8,0,0}};for(auto& s:resource.scripts){s.bytes.resize(16);std::memcpy(s.bytes.data(),commands,16);}mesh=std::make_unique<ScreenDeformation>(manager);return mesh->initialize(resource,17,height)?0:-1;}
static AnmVm* vm(u32 n){return manager.find(n?mesh->animations[n-1]:mesh->control_animation);}
API(value) u32 value(u32 n,u32 field){auto* v=vm(n);if(!v)return 0xffffffff;switch(field){case 0:return v->script_index;case 1:return v->layer;case 2:return manager.geometry_bytes(*v);case 3:return (v->th13_native_flags&~0x3e000007u)|(v->drawing_mode()<<25)|(v->flags&7u);case 4:return v->flags2;case 5:return u32(v->integers[0]);case 6:return v->reserved_418==u32(reinterpret_cast<uintptr_t>(mesh.get()));default:return v->th16_callbacks[field-7];}}
API(word) u32 word(u32 n,u32 i){u32 result;std::memcpy(&result,static_cast<u8*>(vm(n)->geometry)+i*4,4);return result;}
API(columns) u32 columns(){return mesh->columns;}
API(rows) u32 rows(){return mesh->rows;}

API(copy) i32 copy(){
 for(u32 i=0;i<mesh->vertices.size();++i)mesh->vertices[i]={{float(i)*.25f,-float(i)*.5f,float(i%3)},1.f+float(i%2)*.125f,0xff001000u+i,{float(i)/1024.f,-float(i)/256.f}};
 auto* control=vm(0);if(!control||!control->draw_callback)return -1;control->draw_callback(*control);return 0;
}
