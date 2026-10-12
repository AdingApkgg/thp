// Diagnostic-only readback. Copies the current D16 renderbuffer into a texture;
// restores every GL state it changes so the production render path stays intact.
const gl=GL.currentContext.GLctx;
const saved={read:gl.getParameter(gl.READ_FRAMEBUFFER_BINDING),draw:gl.getParameter(gl.DRAW_FRAMEBUFFER_BINDING),program:gl.getParameter(gl.CURRENT_PROGRAM),vao:gl.getParameter(gl.VERTEX_ARRAY_BINDING),viewport:gl.getParameter(gl.VIEWPORT),active:gl.getParameter(gl.ACTIVE_TEXTURE),mask:gl.getParameter(gl.COLOR_WRITEMASK)};
const caps=[gl.BLEND,gl.DEPTH_TEST,gl.CULL_FACE,gl.SCISSOR_TEST,gl.DITHER],enabled=caps.map(k=>gl.isEnabled(k));
gl.activeTexture(gl.TEXTURE0);saved.texture=gl.getParameter(gl.TEXTURE_BINDING_2D);
let probe=Module.depthReadProbe;
if(!probe){
 const texture=(format,type)=>{const t=gl.createTexture();gl.bindTexture(gl.TEXTURE_2D,t);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,gl.NEAREST);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,gl.NEAREST);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_S,gl.CLAMP_TO_EDGE);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_T,gl.CLAMP_TO_EDGE);gl.texImage2D(gl.TEXTURE_2D,0,format,640,480,0,format===gl.DEPTH_COMPONENT16?gl.DEPTH_COMPONENT:gl.RGBA,type,null);return t;};
 const depth=texture(gl.DEPTH_COMPONENT16,gl.UNSIGNED_SHORT),color=texture(gl.RGBA8,gl.UNSIGNED_BYTE),copy=gl.createFramebuffer(),output=gl.createFramebuffer();
 gl.bindFramebuffer(gl.FRAMEBUFFER,copy);gl.framebufferTexture2D(gl.FRAMEBUFFER,gl.DEPTH_ATTACHMENT,gl.TEXTURE_2D,depth,0);gl.drawBuffers([gl.NONE]);gl.readBuffer(gl.NONE);if(gl.checkFramebufferStatus(gl.FRAMEBUFFER)!==gl.FRAMEBUFFER_COMPLETE)throw Error('Depth copy framebuffer');
 gl.bindFramebuffer(gl.FRAMEBUFFER,output);gl.framebufferTexture2D(gl.FRAMEBUFFER,gl.COLOR_ATTACHMENT0,gl.TEXTURE_2D,color,0);if(gl.checkFramebufferStatus(gl.FRAMEBUFFER)!==gl.FRAMEBUFFER_COMPLETE)throw Error('Depth encode framebuffer');
 const shader=(kind,source)=>{const s=gl.createShader(kind);gl.shaderSource(s,source);gl.compileShader(s);if(!gl.getShaderParameter(s,gl.COMPILE_STATUS))throw Error(gl.getShaderInfoLog(s));return s;};
 const vs=shader(gl.VERTEX_SHADER,'#version 300 es\nvoid main(){vec2 p=vec2((gl_VertexID<<1)&2,gl_VertexID&2);gl_Position=vec4(p*2.0-1.0,0.0,1.0);}'),fs=shader(gl.FRAGMENT_SHADER,'#version 300 es\nprecision highp float;precision highp int;uniform sampler2D depths;out vec4 c;void main(){uint z=uint(floor(texelFetch(depths,ivec2(gl_FragCoord.xy),0).r*65535.0+0.5));c=vec4(float(z&255u),float(z>>8),0.0,255.0)/255.0;}');
 const program=gl.createProgram();gl.attachShader(program,vs);gl.attachShader(program,fs);gl.linkProgram(program);if(!gl.getProgramParameter(program,gl.LINK_STATUS))throw Error(gl.getProgramInfoLog(program));gl.deleteShader(vs);gl.deleteShader(fs);
 probe=Module.depthReadProbe={depth,color,copy,output,program,vao:gl.createVertexArray()};
}
gl.bindFramebuffer(gl.READ_FRAMEBUFFER,saved.read);gl.bindFramebuffer(gl.DRAW_FRAMEBUFFER,probe.copy);gl.blitFramebuffer(0,0,640,480,0,0,640,480,gl.DEPTH_BUFFER_BIT,gl.NEAREST);
gl.bindFramebuffer(gl.FRAMEBUFFER,probe.output);gl.viewport(0,0,640,480);caps.forEach(k=>gl.disable(k));gl.colorMask(true,true,true,true);gl.useProgram(probe.program);gl.bindVertexArray(probe.vao);gl.bindTexture(gl.TEXTURE_2D,probe.depth);gl.uniform1i(gl.getUniformLocation(probe.program,'depths'),0);gl.drawArrays(gl.TRIANGLES,0,3);
const pixel=new Uint8Array(4);for(let i=0;i<count;i++){const x=HEAP32[(points>>2)+i*2],y=HEAP32[(points>>2)+i*2+1];gl.readPixels(x,y,1,1,gl.RGBA,gl.UNSIGNED_BYTE,pixel);HEAPU16[(out>>1)+i]=pixel[0]+pixel[1]*256;}
const error=gl.getError();
gl.bindTexture(gl.TEXTURE_2D,saved.texture);gl.activeTexture(saved.active);gl.bindFramebuffer(gl.READ_FRAMEBUFFER,saved.read);gl.bindFramebuffer(gl.DRAW_FRAMEBUFFER,saved.draw);gl.viewport(...saved.viewport);gl.useProgram(saved.program);gl.bindVertexArray(saved.vao);gl.colorMask(...saved.mask);caps.forEach((k,i)=>enabled[i]?gl.enable(k):gl.disable(k));
if(error!==gl.NO_ERROR)throw Error('Depth readback GL error '+error);
return 1;
