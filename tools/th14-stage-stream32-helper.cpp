#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <d3d9.h>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <vector>
#include <map>
#if !defined(_M_IX86)
#error Compile for x86.
#endif
static void check(bool ok,const char* why){if(!ok){std::fprintf(stderr,"stream32: %s\n",why);std::exit(1);}}
static DWORD word(FILE* f){DWORD v;check(std::fread(&v,4,1,f)==1,"read word");return v;}
static float real(DWORD v){float f;std::memcpy(&f,&v,4);return f;}
static std::vector<DWORD> block(FILE* f){DWORD n=word(f);check(n<10000000,"block bound");std::vector<DWORD>b(n);check(std::fread(b.data(),4,n,f)==n,"read block");return b;}
static unsigned short control(){unsigned short v;__asm { fnstcw v }return v;}
int main(int argc,char** argv){
 check(argc==4,"arguments");FILE *in=nullptr,*out=nullptr;check(fopen_s(&in,argv[1],"rb")==0&&in,"input");check(fopen_s(&out,argv[2],"wb")==0&&out,"output");
 char magic[8];check(std::fread(magic,1,8,in)==8&&!std::memcmp(magic,"TH14STRM",8),"magic");DWORD textureCount=word(in);check(textureCount==35,"texture count");
 HWND window=CreateWindowExW(0,L"STATIC",L"TH14 stream32 hidden HAL",0,0,0,640,480,nullptr,nullptr,nullptr,nullptr);check(window,"hidden window");
 auto d3d=Direct3DCreate9(D3D_SDK_VERSION);check(d3d,"D3D9");D3DADAPTER_IDENTIFIER9 adapter{};check(SUCCEEDED(d3d->GetAdapterIdentifier(0,0,&adapter)),"adapter");
 D3DPRESENT_PARAMETERS pp{};pp.BackBufferWidth=640;pp.BackBufferHeight=480;pp.BackBufferFormat=D3DFMT_A8R8G8B8;pp.BackBufferCount=1;pp.SwapEffect=D3DSWAPEFFECT_DISCARD;pp.hDeviceWindow=window;pp.Windowed=TRUE;pp.PresentationInterval=D3DPRESENT_INTERVAL_IMMEDIATE;
 IDirect3DDevice9* device=nullptr;check(SUCCEEDED(d3d->CreateDevice(0,D3DDEVTYPE_HAL,window,D3DCREATE_HARDWARE_VERTEXPROCESSING,&pp,&device)),"device");auto created=control();
 int precision=std::atoi(argv[3]);check(precision==24||precision==64,"precision");if(precision==64){__asm { fninit }}auto reset=control();
 IDirect3DSurface9 *rt=nullptr,*depth=nullptr,*readback=nullptr;
 check(SUCCEEDED(device->CreateRenderTarget(640,480,D3DFMT_A8R8G8B8,D3DMULTISAMPLE_NONE,0,FALSE,&rt,nullptr)),"render target");
 check(SUCCEEDED(device->CreateDepthStencilSurface(640,480,D3DFMT_D16,D3DMULTISAMPLE_NONE,0,TRUE,&depth,nullptr)),"depth");
 check(SUCCEEDED(device->CreateOffscreenPlainSurface(640,480,D3DFMT_A8R8G8B8,D3DPOOL_SYSTEMMEM,&readback,nullptr)),"readback");
 check(SUCCEEDED(device->SetRenderTarget(0,rt))&&SUCCEEDED(device->SetDepthStencilSurface(depth)),"targets");
 std::map<DWORD,IDirect3DTexture9*> textures;D3DLOCKED_RECT lock{};
 for(DWORD i=0;i<textureCount;i++){
  DWORD id=word(in),w=word(in),h=word(in),format=word(in),pitch=word(in),size=word(in);check(size==pitch*h&&size<32000000,"texture bounds");std::vector<unsigned char>b(size);check(std::fread(b.data(),1,size,in)==size,"texture pixels");
  IDirect3DTexture9* tex=nullptr;check(SUCCEEDED(device->CreateTexture(w,h,1,0,D3DFORMAT(format),D3DPOOL_MANAGED,&tex,nullptr)),"texture");textures[id]=tex;
  check(SUCCEEDED(tex->LockRect(0,&lock,nullptr,0)),"texture lock");for(DWORD y=0;y<h;y++)std::memcpy(static_cast<char*>(lock.pBits)+y*lock.Pitch,b.data()+y*pitch,pitch);check(SUCCEEDED(tex->UnlockRect(0)),"texture unlock");
 }
 DWORD frames=word(in);check(frames==21,"frame count");DWORD header[]{frames,created,reset,adapter.VendorId,adapter.DeviceId};check(std::fwrite(header,4,5,out)==5,"header");
 auto rs=[&](DWORD k,DWORD v){check(SUCCEEDED(device->SetRenderState(D3DRENDERSTATETYPE(k),v)),"render state");};
 auto ts=[&](DWORD stage,DWORD k,DWORD v){check(SUCCEEDED(device->SetTextureStageState(stage,D3DTEXTURESTAGESTATETYPE(k),v)),"texture stage");};
 auto ss=[&](DWORD stage,DWORD k,DWORD v){check(SUCCEEDED(device->SetSamplerState(stage,D3DSAMPLERSTATETYPE(k),v)),"sampler");};
 auto execute=[&](DWORD tag,const std::vector<DWORD>& b){
  switch(tag){
  case 1:check(b.size()==2,"RS size");rs(b[0],b[1]);break;
  case 2:check(b.size()==17,"matrix size");check(SUCCEEDED(device->SetTransform(D3DTRANSFORMSTATETYPE(b[0]),reinterpret_cast<const D3DMATRIX*>(b.data()+1))),"matrix");break;
  case 3:check(b.size()==6,"viewport size");check(SUCCEEDED(device->SetViewport(reinterpret_cast<const D3DVIEWPORT9*>(b.data()))),"viewport");break;
  case 4:check(b.size()==3,"sampler size");ss(b[0],b[1],b[2]);break;
  case 5:check(b.size()==2,"texture binding size");check(!b[1]||textures.count(b[1]),"texture handle");check(SUCCEEDED(device->SetTexture(b[0],b[1]?textures[b[1]]:nullptr)),"bind texture");break;
  case 6:check(b.size()==3,"stage size");ts(b[0],b[1],b[2]);break;
  case 7:check(b.size()==1,"FVF size");check(SUCCEEDED(device->SetFVF(b[0])),"FVF");break;
  case 8:check(b.size()>=3&&b[0]==5&&(b.size()-3)*4==(b[1]+2)*b[2],"draw size");check(SUCCEEDED(device->DrawPrimitiveUP(D3DPT_TRIANGLESTRIP,b[1],b.data()+3,b[2])),"draw");break;
  case 9:check(b.size()>=5&&b.size()==5+b[4]*4,"clear size");check(SUCCEEDED(device->Clear(b[4],b[4]?reinterpret_cast<const D3DRECT*>(b.data()+5):nullptr,b[0],b[1],real(b[2]),b[3])),"clear");break;
  default:check(false,"unknown command");
  }
 };
 for(DWORD i=0;i<frames;i++){
  DWORD stage=word(in),frame=word(in),initial=word(in),commands=word(in);
  const DWORD defaults[][2]{{7,1},{14,1},{15,1},{19,5},{20,6},{22,1},{23,8},{24,1},{25,7},{27,1},{28,1},{34,0xffa0a0a0},{35,0},{36,0x447a0000},{37,0x459c4000},{38,0x3f800000},{48,0},{137,0},{140,3},{161,0},{168,15},{171,1},{194,0},{206,0}};for(auto& s:defaults)rs(s[0],s[1]);
  const DWORD stages[][2]{{1,4},{2,2},{3,3},{4,4},{5,2},{6,3},{11,0},{24,2}};for(auto& s:stages)ts(0,s[0],s[1]);ts(1,1,1);
  const DWORD samplers[][2]{{1,1},{2,1},{5,2},{6,2},{7,0},{11,0}};for(auto& s:samplers)ss(0,s[0],s[1]);
  D3DVIEWPORT9 vp{0,0,640,480,0,1};check(SUCCEEDED(device->SetViewport(&vp))&&SUCCEEDED(device->Clear(0,nullptr,3,0xff42678b,1,0)),"frame initialization");
  for(DWORD j=0;j<initial;j++){auto tag=word(in);execute(tag,block(in));}
  check(SUCCEEDED(device->BeginScene()),"begin");
  for(DWORD j=0;j<commands;j++){auto tag=word(in);execute(tag,block(in));}
  check(SUCCEEDED(device->EndScene())&&SUCCEEDED(device->GetRenderTargetData(rt,readback)),"read");
  DWORD rowHeader[]{stage,frame,control()};check(std::fwrite(rowHeader,4,3,out)==3,"frame header");
  check(SUCCEEDED(readback->LockRect(&lock,nullptr,D3DLOCK_READONLY)),"read lock");for(int y=0;y<480;y++)check(std::fwrite(static_cast<char*>(lock.pBits)+y*lock.Pitch,1,640*4,out)==640*4,"pixels");check(SUCCEEDED(readback->UnlockRect()),"read unlock");
 }
 check(std::fgetc(in)==EOF,"trailing input");for(auto& entry:textures)entry.second->Release();readback->Release();depth->Release();rt->Release();device->Release();d3d->Release();DestroyWindow(window);std::fclose(in);std::fclose(out);std::printf("PASS stream32 %lu frames, FPCW %x -> %x\n",frames,created,reset);return 0;
}
