#include "alpha-fixture.cpp"
#include <cstdlib>
extern "C" void* allocated(u32 n){return std::malloc(n);}
extern "C" void released(void* p){std::free(p);}
extern "C" void gpu_close(){renderer.reset();}
extern "C" const u8* clear_case(u32 kind,u32 deferred,u32 dither){
    if(!renderer||kind>=16)return nullptr;
    auto& r=*renderer;
    r.state=State{};r.state.target=1;r.state.depth=3;
    r.state.viewport={0,0,32,32,0,1};r.state.layout=attributes(VertexLayout::ScreenColorUv);
    auto& p=r.pipeline();p.depthWrite=false;p.blend=false;p.alphaTest=false;p.dither=dither;
    p.color.operation=p.alpha.operation=ColorOperation::First;
    p.color.first=p.alpha.first={ArgumentSource::Diffuse};
    // Establish the dither state through an actual production draw.
    const Vertex tri[]={{1.5f,1.5f,.5f,1,0xff24be68,0,0},{30.5f,1.5f,.5f,1,0xff24be68,0,0},{1.5f,30.5f,.5f,1,0xff24be68,0,0}};
    r.clear(3,0xff42678b,1,0);r.draw(Topology::Triangles,1,tri,sizeof(Vertex));r.flush();
    const i32 whole[]{0,0,32,32},small[]{7,9,23,27},overlap[]{3,5,17,21};
    const u32 flag=deferred?8u:0u;
    r.clear(3|flag,0x7f28c47b,.25f,0,(kind&1)?small:whole,1);
    switch(kind/2){
    case 0:break; // Read resolves the pending color.
    case 1:r.clear(1,0xa41bd872,1,0,whole,1);break; // Complete overwrite.
    case 2:r.clear(1,0x3dca196f,1,0,overlap,1);break; // Partial overwrite.
    case 3:r.clear(1|flag,0x5d8b362a,1,0,overlap,1);break; // Two pending rectangles.
    case 4:
        r.pipeline().depthTest=true;r.pipeline().depthCompare=Compare::Less;
        r.draw(Topology::Triangles,1,tri,sizeof(Vertex));break; // Immediate depth must reject z=.5.
    case 5:{
        const i32 origin[]{0,0};
        r.state.target=4;r.clear(1,0xff150a81,1,0);r.copy(1,whole,4,origin);
        r.read(4);return second_pixels; // Copy source and destination resolve.
    }
    case 6:{
        r.state.target=4;r.state.depth=0;r.state.texture=1;r.clear(1,0xff931d41,1,0);
        r.pipeline().color.first=r.pipeline().alpha.first={ArgumentSource::Texture};
        const Vertex quad[]={{-.5f,-.5f,0,1,0xffffffff,0,0},{31.5f,-.5f,0,1,0xffffffff,1,0},{-.5f,31.5f,0,1,0xffffffff,0,1},{31.5f,31.5f,0,1,0xffffffff,1,1}};
        r.draw(Topology::Strip,2,quad,sizeof(Vertex));r.read(4);return second_pixels; // Texture sampling resolves.
    }
    case 7:r.present(1);break; // Presentation resolves before the blit.
    }
    r.read(1);return target_pixels;
}
