#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <d3d9.h>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <vector>
#include <float.h>
using CreateTexture=HRESULT(WINAPI*)(LPDIRECT3DDEVICE9,UINT,UINT,UINT,DWORD,D3DFORMAT,D3DPOOL,LPDIRECT3DTEXTURE9*);
using LoadMemory=HRESULT(WINAPI*)(LPDIRECT3DSURFACE9,const PALETTEENTRY*,const RECT*,const void*,D3DFORMAT,UINT,const PALETTEENTRY*,const RECT*,DWORD,D3DCOLOR);
using LoadSurface=HRESULT(WINAPI*)(LPDIRECT3DSURFACE9,const PALETTEENTRY*,const RECT*,LPDIRECT3DSURFACE9,const PALETTEENTRY*,const RECT*,DWORD,D3DCOLOR);
static void check(bool ok,const char* at){if(!ok){std::fprintf(stderr,"capture32 failure %s\n",at);std::exit(1);}}
static void write(FILE* f,const void* p,size_t n){check(std::fwrite(p,1,n,f)==n,"write");}
int main(int argc,char**argv){
 check(argc==3,"arguments");FILE*in=nullptr,*out=nullptr;check(!fopen_s(&in,argv[1],"rb")&&!fopen_s(&out,argv[2],"wb"),"files");
 unsigned cw=0;check(!_controlfp_s(&cw,_PC_53|_RC_NEAR,_MCW_PC|_MCW_RC),"FPU");
 auto lib=LoadLibraryW(L"C:\\Windows\\SysWOW64\\d3dx9_43.dll");check(lib,"original32 system D3DX");
 auto create=reinterpret_cast<CreateTexture>(GetProcAddress(lib,"D3DXCreateTexture"));auto memory=reinterpret_cast<LoadMemory>(GetProcAddress(lib,"D3DXLoadSurfaceFromMemory"));auto copy=reinterpret_cast<LoadSurface>(GetProcAddress(lib,"D3DXLoadSurfaceFromSurface"));check(create&&memory&&copy,"exports");
 char magic[8];unsigned count=0;check(std::fread(magic,1,8,in)==8&&!std::memcmp(magic,"TH14CAP\0",8),"magic");check(std::fread(&count,4,1,in)==1,"count");
 std::vector<unsigned char> pixels(640*480*4);check(std::fread(pixels.data(),1,pixels.size(),in)==pixels.size(),"source");
 auto window=CreateWindowExW(0,L"STATIC",L"TH14 deferred capture isolated HAL",0,0,0,640,480,nullptr,nullptr,nullptr,nullptr);check(window,"hidden window");
 auto d3d=Direct3DCreate9(32);check(d3d,"D3D9");D3DPRESENT_PARAMETERS pp{};pp.BackBufferWidth=640;pp.BackBufferHeight=480;pp.BackBufferFormat=D3DFMT_A8R8G8B8;pp.BackBufferCount=1;pp.SwapEffect=D3DSWAPEFFECT_DISCARD;pp.hDeviceWindow=window;pp.Windowed=TRUE;pp.PresentationInterval=D3DPRESENT_INTERVAL_IMMEDIATE;
 IDirect3DDevice9*device=nullptr;check(SUCCEEDED(d3d->CreateDevice(0,D3DDEVTYPE_HAL,window,D3DCREATE_HARDWARE_VERTEXPROCESSING,&pp,&device)),"hidden HAL device");
 unsigned post=0;check(!_controlfp_s(&post,0,0),"post-device FPU");write(out,&cw,4);write(out,&post,4);write(out,&count,4);
 IDirect3DSurface9*source=nullptr;check(SUCCEEDED(device->GetBackBuffer(0,0,D3DBACKBUFFER_TYPE_MONO,&source)),"GetBackBuffer");D3DSURFACE_DESC desc{};check(SUCCEEDED(source->GetDesc(&desc)),"source desc");write(out,&desc,sizeof desc);
 RECT entire{0,0,640,480};check(SUCCEEDED(memory(source,nullptr,&entire,pixels.data(),D3DFMT_A8R8G8B8,640*4,nullptr,&entire,1,0)),"initialize own backbuffer");
 IDirect3DSurface9*readback=nullptr;check(SUCCEEDED(device->CreateOffscreenPlainSurface(640,480,D3DFMT_A8R8G8B8,D3DPOOL_SYSTEMMEM,&readback,nullptr)),"source readback");check(SUCCEEDED(device->GetRenderTargetData(source,readback)),"readback source");D3DLOCKED_RECT lock{};check(SUCCEEDED(readback->LockRect(&lock,nullptr,D3DLOCK_READONLY)),"lock source");for(unsigned y=0;y<480;++y)write(out,static_cast<char*>(lock.pBits)+y*lock.Pitch,640*4);readback->UnlockRect();readback->Release();
 for(unsigned i=0;i<count;++i){
  unsigned a[9];check(std::fread(a,4,9,in)==9,"case");IDirect3DTexture9*texture=nullptr;check(SUCCEEDED(create(device,512,512,1,0,D3DFORMAT(a[0]),D3DPOOL_MANAGED,&texture)),"text dimensions CreateTexture");D3DSURFACE_DESC td{};check(SUCCEEDED(texture->GetLevelDesc(0,&td)),"target desc");unsigned bpp=td.Format==D3DFMT_R5G6B5?2:td.Format==D3DFMT_A8R8G8B8?4:0;check(bpp,"target format");
  check(SUCCEEDED(texture->LockRect(0,&lock,nullptr,0)),"initialize target");for(unsigned y=0;y<512;++y)for(unsigned x=0;x<512;++x){unsigned value=bpp==2?0x5a6b:0x917c3a5e;std::memcpy(static_cast<char*>(lock.pBits)+y*lock.Pitch+x*bpp,&value,bpp);}texture->UnlockRect(0);
  IDirect3DSurface9*target=nullptr;HRESULT surfaceResult=texture->GetSurfaceLevel(0,&target);check(SUCCEEDED(surfaceResult),"GetSurfaceLevel");RECT s{LONG(a[1]),LONG(a[2]),LONG(a[3]),LONG(a[4])},d{LONG(a[5]),LONG(a[6]),LONG(a[7]),LONG(a[8])};
  HRESULT copyResult=copy(target,nullptr,&d,source,nullptr,&s,2,0);HRESULT dirtyResult=copyResult==0?texture->AddDirtyRect(nullptr):HRESULT(0x7fffffff);target->Release();
  write(out,&surfaceResult,4);write(out,&copyResult,4);write(out,&dirtyResult,4);write(out,&td,sizeof td);
  check(SUCCEEDED(texture->LockRect(0,&lock,nullptr,D3DLOCK_READONLY)),"read pixels");for(unsigned y=0;y<512;++y)write(out,static_cast<char*>(lock.pBits)+y*lock.Pitch,512*bpp);texture->UnlockRect(0);texture->Release();
 }
 check(std::fgetc(in)==EOF,"input trailing");std::fclose(in);std::fclose(out);source->Release();device->Release();d3d->Release();DestroyWindow(window);FreeLibrary(lib);std::printf("PASS own hidden capture32 %u cases\n",count);
}
