#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <d3d9.h>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <float.h>
#if !defined(_M_IX86)
#error This reference must be compiled for x86.
#endif
static void check(bool ok,const char* label){if(!ok){std::fprintf(stderr,"fog32: %s\n",label);std::exit(1);}}
struct Vertex{float x,y,z;DWORD color;float u,v;};
struct Request{D3DMATRIX world,view,projection,texture;DWORD fog,range,point,transform,color,start,end,density;};
static_assert(sizeof(void*)==4&&sizeof(Vertex)==24&&sizeof(Request)==288,"request ABI");
int main(int argc,char** argv){
 check(argc==4,"arguments");FILE *in=nullptr,*out=nullptr;
 check(fopen_s(&in,argv[1],"rb")==0&&in,"open requests");check(fopen_s(&out,argv[2],"wb")==0&&out,"open output");
 char magic[8];DWORD count=0,words[16];Vertex vertices[4];
 check(std::fread(magic,1,8,in)==8&&!std::memcmp(magic,"TH14FOG\0",8),"magic");check(std::fread(&count,4,1,in)==1,"count");check(std::fread(words,4,16,in)==16&&std::fread(vertices,sizeof(Vertex),4,in)==4,"common inputs");
 auto window=CreateWindowExW(0,L"STATIC",L"TH14 fog32 hidden reference",0,0,0,64,64,nullptr,nullptr,nullptr,nullptr);check(window!=nullptr,"hidden window");
 auto d3d=Direct3DCreate9(D3D_SDK_VERSION);check(d3d!=nullptr,"D3D9");D3DADAPTER_IDENTIFIER9 adapter{};check(SUCCEEDED(d3d->GetAdapterIdentifier(0,0,&adapter)),"adapter");
 D3DPRESENT_PARAMETERS pp{};pp.BackBufferWidth=pp.BackBufferHeight=32;pp.BackBufferFormat=D3DFMT_A8R8G8B8;pp.BackBufferCount=1;pp.SwapEffect=D3DSWAPEFFECT_DISCARD;pp.hDeviceWindow=window;pp.Windowed=TRUE;pp.PresentationInterval=D3DPRESENT_INTERVAL_IMMEDIATE;
 unsigned pre=0;check(_controlfp_s(&pre,_PC_53,_MCW_PC|_MCW_RC)==0,"pre control");
 IDirect3DDevice9* device=nullptr;check(SUCCEEDED(d3d->CreateDevice(0,D3DDEVTYPE_HAL,window,D3DCREATE_HARDWARE_VERTEXPROCESSING,&pp,&device)),"HAL hardware device");
 unsigned short afterCreate=0;__asm { fnstcw afterCreate }
 const int precision=std::atoi(argv[3]);check(precision==24||precision==53||precision==64,"precision");
 if(precision==64){__asm { fninit }}else if(precision==53){unsigned control=0;check(_controlfp_s(&control,_PC_53,_MCW_PC|_MCW_RC)==0,"post device precision");}
 unsigned short afterReset=0;__asm { fnstcw afterReset }
 DWORD header[]{count,afterCreate,afterReset,adapter.VendorId,adapter.DeviceId};check(std::fwrite(header,4,5,out)==5,"output header");
 IDirect3DSurface9 *rt=nullptr,*readback=nullptr;IDirect3DTexture9* texture=nullptr;
 check(SUCCEEDED(device->CreateRenderTarget(32,32,D3DFMT_A8R8G8B8,D3DMULTISAMPLE_NONE,0,FALSE,&rt,nullptr)),"target");check(SUCCEEDED(device->CreateOffscreenPlainSurface(32,32,D3DFMT_A8R8G8B8,D3DPOOL_SYSTEMMEM,&readback,nullptr)),"readback");check(SUCCEEDED(device->CreateTexture(4,4,1,0,D3DFMT_A8R8G8B8,D3DPOOL_MANAGED,&texture,nullptr)),"texture");
 D3DLOCKED_RECT lock{};check(SUCCEEDED(texture->LockRect(0,&lock,nullptr,0)),"texture lock");for(int y=0;y<4;++y)std::memcpy(static_cast<char*>(lock.pBits)+y*lock.Pitch,words+y*4,16);check(SUCCEEDED(texture->UnlockRect(0)),"texture unlock");
 check(SUCCEEDED(device->SetRenderTarget(0,rt))&&SUCCEEDED(device->SetDepthStencilSurface(nullptr)),"target bind");D3DVIEWPORT9 vp{0,0,32,32,0,1};check(SUCCEEDED(device->SetViewport(&vp)),"viewport");check(SUCCEEDED(device->SetFVF(0x142))&&SUCCEEDED(device->SetTexture(0,texture)),"input bind");
 auto rs=[&](DWORD k,DWORD v){check(SUCCEEDED(device->SetRenderState(D3DRENDERSTATETYPE(k),v)),"render state");};
 const DWORD states[][2]{{7,0},{14,0},{15,1},{22,1},{27,0},{28,0},{137,0},{161,0},{168,15},{194,0},{206,0}};for(const auto& s:states)rs(s[0],s[1]);
 auto stage=[&](DWORD k,DWORD v){check(SUCCEEDED(device->SetTextureStageState(0,D3DTEXTURESTAGESTATETYPE(k),v)),"stage state");};const DWORD stages[][2]{{1,4},{2,2},{3,0},{5,2},{6,0}};for(const auto& s:stages)stage(s[0],s[1]);check(SUCCEEDED(device->SetTextureStageState(1,D3DTSS_COLOROP,D3DTOP_DISABLE)),"disable second stage");
 auto sampler=[&](DWORD k,DWORD v){check(SUCCEEDED(device->SetSamplerState(0,D3DSAMPLERSTATETYPE(k),v)),"sampler");};const DWORD samplers[][2]{{1,1},{2,1},{5,2},{6,2},{11,0}};for(const auto& s:samplers)sampler(s[0],s[1]);
 for(DWORD i=0;i<count;++i){Request r{};check(std::fread(&r,sizeof(r),1,in)==1,"request");
  check(SUCCEEDED(device->SetTransform(D3DTS_WORLD,&r.world))&&SUCCEEDED(device->SetTransform(D3DTS_VIEW,&r.view))&&SUCCEEDED(device->SetTransform(D3DTS_PROJECTION,&r.projection))&&SUCCEEDED(device->SetTransform(D3DTS_TEXTURE0,&r.texture)),"transforms");
  stage(4,4);stage(24,r.transform?2:0);rs(25,7);rs(24,1);rs(28,r.fog!=0);rs(34,r.color);rs(35,0);rs(36,r.start);rs(37,r.end);rs(38,r.density);rs(48,r.range);rs(140,r.fog);sampler(5,r.point?1:2);sampler(6,r.point?1:2);
  check(SUCCEEDED(device->Clear(0,nullptr,D3DCLEAR_TARGET,0xff42678b,1,0))&&SUCCEEDED(device->BeginScene()),"begin frame");check(SUCCEEDED(device->DrawPrimitiveUP(D3DPT_TRIANGLESTRIP,2,vertices,sizeof(Vertex))),"draw");check(SUCCEEDED(device->EndScene())&&SUCCEEDED(device->GetRenderTargetData(rt,readback)),"read frame");
  check(SUCCEEDED(readback->LockRect(&lock,nullptr,D3DLOCK_READONLY)),"read lock");for(int y=0;y<32;++y)check(std::fwrite(static_cast<char*>(lock.pBits)+y*lock.Pitch,1,128,out)==128,"pixels");check(SUCCEEDED(readback->UnlockRect()),"read unlock");
 }
 check(std::fgetc(in)==EOF,"trailing input");std::fclose(in);std::fclose(out);texture->Release();readback->Release();rt->Release();device->Release();d3d->Release();DestroyWindow(window);std::printf("PASS fog32 %lu cases, raw control %x -> %x\n",count,afterCreate,afterReset);return 0;
}
