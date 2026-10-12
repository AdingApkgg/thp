#include "th14-gpu-raster-fixture.cpp"
#include "../../../portable/sdl/Shaders.hpp"
#include <string>
extern "C" EMSCRIPTEN_KEEPALIVE const float* gpu_alpha_boundaries(){return renderer?renderer->alpha_boundaries():nullptr;}
extern "C" EMSCRIPTEN_KEEPALIVE void gpu_alpha_texture(u32 low){
    if(!renderer)return;renderer->release(2);
    for(u32 i=0;i<16;++i)texture_pixels[i]=(low?i%4:(47+i*53)%256)<<24|((31+i*73)%256)<<16|((19+i*41)%256)<<8|((11+i*97)%256);
}
extern "C" EMSCRIPTEN_KEEPALIVE const u8* gpu_alpha_case(u32 operation,u32 compare,u32 reference){
    if(!renderer||operation>1||compare<1||compare>8||reference>255)return nullptr;
    auto& r=*renderer;r.state=State{};r.state.target=1;r.state.texture=2;
    r.state.viewport={0,0,32,32,0,1};r.state.layout=attributes(VertexLayout::ScreenColorUv);
    auto& p=r.pipeline();p.depthWrite=false;p.blend=false;p.alphaTest=true;
    p.alphaCompare=Compare(compare-1);p.alphaReference=reference;
    p.color.operation=ColorOperation::Multiply;
    p.alpha.operation=operation?ColorOperation::Multiply:ColorOperation::First;
    p.alpha.first=p.color.first={ArgumentSource::Texture};p.alpha.second=p.color.second={ArgumentSource::Diffuse};
    p.minFilter=p.magFilter=Filter::Linear;p.addressU=p.addressV=Address::Clamp;
    r.clear(1,0xff42678b,1,0);
    const Vertex v[]={{3.5f,4.5f,0,1,0xc8b56e29,-.25f,-.125f},{25.5f,4.5f,0,1,0x795ac4e8,1.25f,-.125f},
        {3.5f,26.5f,0,1,0xea28cf7b,-.25f,1.125f},{25.5f,26.5f,0,1,0x467c318e,1.25f,1.125f}};
    r.draw(Topology::Strip,2,v,sizeof(Vertex));r.read(1);return target_pixels;
}
// Diagnostic-only: use the production vertex source and last program's uniforms
// to read the combiner alpha as raw float bits before framebuffer conversion.
extern "C" EMSCRIPTEN_KEEPALIVE const u8* gpu_alpha_probe(u32 operation,u32 mode,float alpha){
    if(!gpu_alpha_case(operation,8,0))return nullptr;
    GLint old=0;glGetIntegerv(GL_CURRENT_PROGRAM,&old);
    // Zero screen depth remains visible with either clip-control convention;
    // the diagnostic has depth testing disabled, just like the source case.
    std::string vertex_text=vertexSource;const std::string z="position.z*2.0-1.0";
    vertex_text.replace(vertex_text.find(z),z.size(),"position.z");
    const GLuint vertex_shader=glCreateShader(GL_VERTEX_SHADER);const char* vertex_code=vertex_text.c_str();
    glShaderSource(vertex_shader,1,&vertex_code,nullptr);glCompileShader(vertex_shader);
    std::string text=fragmentSource;
    text.insert(text.find("precision highp float;")+22,"\nprecision highp int;\n");
    if(mode==7)text.insert(text.find("uniform float alphaRef;"),"uniform float alphaDiagnostic;\n");
    if(mode==3||mode==4){
        const std::string sample="texture(tex,vUV)";text.replace(text.find(sample),sample.size(),"precise_sample()");
        const std::string anchor="uniform sampler2D tex;";
        text.insert(text.find(anchor)+anchor.size(),R"GLSL(
vec4 precise_sample(){vec2 dimensions=vec2(textureSize(tex,0)),position=vUV*dimensions-.5,base=floor(position),weight=fract(position);
vec2 origin=(base+.5)/dimensions,step=1.0/dimensions;
return mix(mix(textureLod(tex,origin,0.0),textureLod(tex,origin+vec2(step.x,0.0),0.0),weight.x),mix(textureLod(tex,origin+vec2(0.0,step.y),0.0),textureLod(tex,origin+step,0.0),weight.x),weight.y);}
)GLSL");
    }
    const std::string anchor="outColor=c;";const auto at=text.find(anchor);if(at==std::string::npos)return nullptr;
    if(mode==0||mode==4)text.replace(at,anchor.size(),"uint n=floatBitsToUint(c.a);outColor=vec4(float(n&255u),float((n>>8)&255u),float((n>>16)&255u),float((n>>24)&255u))/255.0;");
    if(mode==7)text.replace(at,anchor.size(),"outColor=vec4(0.0,0.0,0.0,alphaDiagnostic);");
    const GLuint fs=glCreateShader(GL_FRAGMENT_SHADER);const char* source=text.c_str();glShaderSource(fs,1,&source,nullptr);glCompileShader(fs);
    GLint okay=0;glGetShaderiv(fs,GL_COMPILE_STATUS,&okay);if(!okay){glDeleteShader(fs);return nullptr;}
    const GLuint program=glCreateProgram();glAttachShader(program,vertex_shader);glAttachShader(program,fs);glLinkProgram(program);glDeleteShader(fs);glDeleteShader(vertex_shader);
    glGetProgramiv(program,GL_LINK_STATUS,&okay);if(!okay){glDeleteProgram(program);return nullptr;}glUseProgram(program);
    GLint uniforms=0;glGetProgramiv(GLuint(old),GL_ACTIVE_UNIFORMS,&uniforms);
    for(GLint i=0;i<uniforms;++i){char name[128];GLsizei len=0;GLint size=0;GLenum kind=0;glGetActiveUniform(GLuint(old),i,sizeof(name),&len,&size,&kind,name);
        const auto a=glGetUniformLocation(GLuint(old),name),b=glGetUniformLocation(program,name);if(a<0||b<0)continue;float v[16]{};GLint integer=0;
        if(kind==GL_BOOL||kind==GL_INT||kind==GL_SAMPLER_2D){glGetUniformiv(GLuint(old),a,&integer);glUniform1i(b,integer);}
        else {glGetUniformfv(GLuint(old),a,v);if(kind==GL_FLOAT_MAT4)glUniformMatrix4fv(b,1,false,v);else if(kind==GL_FLOAT_VEC4)glUniform4fv(b,1,v);else if(kind==GL_FLOAT_VEC3)glUniform3fv(b,1,v);else glUniform1f(b,v[0]);}
    }
    if(mode==7)glUniform1f(glGetUniformLocation(program,"alphaDiagnostic"),alpha);
    // Renderer::draw expanded the strip into six triangle-list vertices.
    glDrawArrays(GL_TRIANGLES,0,6);static u8 values[4096];glReadPixels(0,0,32,32,GL_RGBA,GL_UNSIGNED_BYTE,values);
    glUseProgram(GLuint(old));glDeleteProgram(program);return values;
}
