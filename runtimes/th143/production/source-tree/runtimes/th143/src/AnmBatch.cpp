#include "AnmBatch.hpp"
namespace th143 {
namespace {
bool read(AnmRenderMemory& m,u32 p,u32& value){return m.read_render_memory(p,&value,4);}
bool write(AnmRenderMemory& m,u32 p,u32 value){return m.write_render_memory(p,&value,4);}
}
bool initialize_anm_batches(u32 p,AnmRenderMemory& m){
    return write(m,p+0xbc8200,0)&&write(m,p+0xf48204,p+0xbc8204)&&write(m,p+0xf48208,p+0xbc8204)&&write(m,p+0xf4820c,0)&&write(m,p+0xfe8210,p+0xf48210)&&write(m,p+0xfe8214,p+0xf48210);
}
bool append_anm_quad(u32 p,const AnmQuad& quad,AnmRenderMemory& m,u32& result){
    u32 cursor,count;if(!read(m,p+0xf48204,cursor))return false;if(cursor+0xa8>=p+0xf48204){result=1;return true;}
    static constexpr u32 order[6]={0,1,2,1,2,3};
    for(u32 i=0;i<6;++i)if(!m.write_render_memory(cursor+i*28,quad.vertices[order[i]].data(),28))return false;
    if(!write(m,p+0xf48204,cursor+0xa8)||!read(m,p+0xbc8200,count)||!write(m,p+0xbc8200,count+1))return false;result=0;return true;
}
bool reserve_anm_quad(u32 p,AnmRenderMemory& m,u32& token){
    u32 cursor,count;if(!read(m,p+0xf48204,cursor))return false;if(cursor+0xa8>=p+0xf48204){token=0;return true;}
    if(!read(m,p+0xbc8200,count)||!write(m,p+0xbc8200,count+1)||!write(m,p+0xf48204,cursor+0xa8))return false;token=cursor;return true;
}
bool cancel_anm_quad(u32 p,AnmRenderMemory& m){u32 count,cursor;return read(m,p+0xbc8200,count)&&write(m,p+0xbc8200,count-1)&&read(m,p+0xf48204,cursor)&&write(m,p+0xf48204,cursor-0xa8);}
bool flush_anm_quads(u32 p,u32 current,AnmRenderMemory& m,AnmRenderDevice& device){
    u32 count;if(!read(m,p+0xbc8200,count))return false;if(!count)return true;
    u8 configured;if(!m.read_render_memory(current+0xbc81a3,&configured,1))return false;
    if(configured!=1){if(!device.texture_stage_state(0,4,4)||!device.texture_stage_state(0,1,4))return false;configured=1;if(!m.write_render_memory(current+0xbc81a3,&configured,1))return false;}
    if(!device.texture_stage_state(0,6,0)||!device.texture_stage_state(0,3,0)||!device.vertex_format(0x144))return false;
    u32 cursor;if(!read(m,p+0xf48208,cursor)||!read(m,p+0xbc8200,count)||count>0x1000000/0xa8)return false;
    std::vector<u8> vertices(count*0xa8);if(!m.read_render_memory(cursor,vertices.data(),vertices.size())||!device.draw_triangles(count*2,28,vertices.data(),vertices.size()))return false;
    u32 end,draws;if(!read(m,p+0xf48204,end)||!read(m,p+0xcc,draws)||!write(m,p+0xcc,draws+1)||!write(m,p+0xf48208,end)||!write(m,p+0xbc8200,0))return false;return true;
}
}
