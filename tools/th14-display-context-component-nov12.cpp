#include "GameConfig.hpp"
#include "SceneCompositor.hpp"
#include <cstring>
using namespace th11;
using namespace touhou::graphics;
#define API(n) extern "C" __attribute__((export_name(#n)))
namespace {
struct Device final:ZunGraphics {
    PipelineState state{};
    PipelineState& pipeline()override{return state;}
    u32 texture(const AnmResource&,u32)override{return 1;}
    void bind_texture(u32)override{}
    void set_layout(VertexLayout)override{}
    void set_matrix(MatrixKind,const Matrix4&)override{}
    void triangles(u32,const void*,u32)override{std::abort();}
    void primitives(Topology,u32,const void*,u32)override{std::abort();}
    bool select_target(const AnmResource*,u32)override{return true;}
    bool clear_target(u32,const GraphicsViewport*,u32)override{return true;}
};
u32 words[3*37]{};
u32 bits(float x){u32 v;std::memcpy(&v,&x,4);return v;}
void snapshot(u32* out,AnmManager& manager,SceneCompositor& compositor){
    const auto& space=manager.render_space;
    *out++=bits(space.scale);*out++=bits(space.play_origin.x);*out++=bits(space.play_origin.y);
    *out++=bits(space.scaled_origin.x);*out++=bits(space.scaled_origin.y);
    for(const auto* camera:{&compositor.full_camera,&compositor.play_camera,&compositor.scaled_play_camera,&compositor.world_camera}){
        const auto& v=camera->viewport;
        for(u32 value:{v.x,v.y,v.width,v.height,bits(v.near_depth),bits(v.far_depth),camera->render_width,camera->render_height})*out++=value;
    }
}
}
API(output_ptr) u32 output_ptr(){return u32(words);}
API(run) u32 run(u32 mode,u32 has_resource){
    GameConfig config;config.bytes[0x1f]=u8(mode);
    AnmManager manager;manager.render_space.play_origin={-83,47};
    SceneCompositor compositor(manager);Device graphics;AnmRenderer renderer(graphics);AnmResource text;
    compositor.resource=has_resource?&text:nullptr;
    compositor.reset_cameras(true,config.render_width(),config.render_height());snapshot(words,manager,compositor);
    if(!compositor.draw(renderer,SceneDrawKind::Begin))return 0;snapshot(words+37,manager,compositor);
    compositor.reset_cameras(false,config.render_width(),config.render_height());snapshot(words+74,manager,compositor);
    return 111;
}
