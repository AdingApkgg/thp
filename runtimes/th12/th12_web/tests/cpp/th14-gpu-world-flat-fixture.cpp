#include "th14-gpu-raster-fixture.cpp"
extern "C" EMSCRIPTEN_KEEPALIVE const u8* gpu_world_profile_case(u32 profile,u32 world,u32 view,u32 projection,u32 textureTransform,u32 fog,u32 range,u32 point){
    if(!renderer||profile>4||world>2||view>1||projection>1||textureTransform>1||fog>3||range>1||point>1)return nullptr;
    auto& r=*renderer;r.state=State{};r.state.target=1;r.state.texture=2;r.state.viewport={0,0,32,32,0,1};r.state.layout=attributes(VertexLayout::WorldColorUv);
    const float worlds[][16]={{1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1},{0,1,0,0,-1,0,0,0,0,0,1,0,.125f,-.125f,.5f,1},{.75f,0,0,0,0,1.25f,0,0,0,0,1,0,-.125f,.125f,.25f,1}};
    const float views[][16]={{1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1},{1,0,0,0,0,1,0,0,0,0,1,0,0,.125f,.5f,1}};
    const float projections[][16]={{1,0,0,0,0,1,0,0,0,0,1.f/9.9f,0,0,0,-.1f/9.9f,1},{1,0,0,0,0,1,0,0,0,0,10.f/9.9f,1,0,0,-1.f/9.9f,0}};
    const float texture[]={.75f,0,0,0,0,.5f,0,0,.125f,.25f,1,0,0,0,0,1};
    r.transform(MatrixKind::World,worlds[world]);r.transform(MatrixKind::View,views[view]);r.transform(MatrixKind::Projection,projections[projection]);r.transform(MatrixKind::Texture,texture);
    auto& p=r.pipeline();p.depthWrite=false;p.blend=false;p.alphaTest=true;p.alphaCompare=Compare::GreaterEqual;p.alphaReference=1;
    p.color.operation=p.alpha.operation=ColorOperation::Multiply;p.alpha.first=p.color.first={ArgumentSource::Texture};p.alpha.second=p.color.second={ArgumentSource::Diffuse};
    p.textureTransform=textureTransform;p.fog=fog!=0;p.fogMode=FogMode(fog);p.rangeFog=range;const float profiles[][3]={{.75f,2.5f,.6f},{0,1,.1f},{1,5,.5f},{2,3.25f,.9f},{.125f,10,1}};p.fogNear=profiles[profile][0];p.fogFar=profiles[profile][1];p.fogDensity=profiles[profile][2];p.fogColor=0xffa0b8d0;
    p.minFilter=p.magFilter=point?Filter::Nearest:Filter::Linear;p.addressU=p.addressV=Address::Repeat;
    r.clear(1,0xff42678b,1,0);
    struct WorldVertex{float x,y,z;u32 color;float u,v;};
    const WorldVertex v[]={{-.65f,.65f,1,0xc8b56e29,-.25f,-.125f},{.65f,.65f,1,0x795ac4e8,1.25f,-.125f},
        {-.65f,-.65f,1,0xea28cf7b,-.25f,1.125f},{.65f,-.65f,1,0x467c318e,1.25f,1.125f}};
    r.draw(Topology::Strip,2,v,sizeof(WorldVertex));r.read(1);return target_pixels;
}

