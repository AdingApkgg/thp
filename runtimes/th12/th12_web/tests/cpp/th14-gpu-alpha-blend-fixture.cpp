#include "th14-gpu-raster-fixture.cpp"
extern "C" EMSCRIPTEN_KEEPALIVE const u8* gpu_alpha_blend_case(u32 source,u32 destination,u32 equation,u32 point,u32 low,u32 operation,u32 compare,u32 reference){
    if(!renderer||source<1||source>11||destination<1||destination>11||equation<1||equation>5||point>1||low>1||operation>1||compare<1||compare>8||reference>255)return nullptr;
    auto& r=*renderer;
    // Release the uploaded texture when its alpha range changes, including
    // transitions between repeated calls using the same renderer instance.
    static u32 previousLow=2;
    if(low!=previousLow){r.release(2);previousLow=low;for(u32 i=0;i<16;++i)texture_pixels[i]=(low?i%4:(47+i*53)%256)<<24|((31+i*73)%256)<<16|((19+i*41)%256)<<8|((11+i*97)%256);}
    r.state=State{};r.state.target=1;r.state.texture=2;
    r.state.viewport={0,0,32,32,0,1};r.state.layout=attributes(VertexLayout::ScreenColorUv);
    auto& p=r.pipeline();p.depthWrite=false;p.blend=true;p.alphaTest=true;
    p.sourceBlend=BlendFactor(source-1);p.destinationBlend=BlendFactor(destination-1);p.blendEquation=BlendEquation(equation-1);
    p.alphaCompare=Compare(compare-1);p.alphaReference=reference;
    p.color.operation=ColorOperation::Multiply;p.alpha.operation=operation?ColorOperation::Multiply:ColorOperation::First;
    p.alpha.first=p.color.first={ArgumentSource::Texture};p.alpha.second=p.color.second={ArgumentSource::Diffuse};
    p.minFilter=p.magFilter=point?Filter::Nearest:Filter::Linear;p.addressU=p.addressV=Address::Clamp;
    r.clear(1,0xff42678b,1,0);
    const Vertex v[]={{3.5f,4.5f,0,1,0xc8b56e29,-.25f,-.125f},{25.5f,4.5f,0,1,0x795ac4e8,1.25f,-.125f},
        {3.5f,26.5f,0,1,0xea28cf7b,-.25f,1.125f},{25.5f,26.5f,0,1,0x467c318e,1.25f,1.125f}};
    r.draw(Topology::Strip,2,v,sizeof(Vertex));r.read(1);return target_pixels;
}
