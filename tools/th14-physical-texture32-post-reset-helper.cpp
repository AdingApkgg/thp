#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <d3d9.h>
#include <cstdio>
#include <cstdlib>
#include <vector>
#include <float.h>
using CreateTexture = HRESULT (WINAPI*)(LPDIRECT3DDEVICE9,UINT,UINT,UINT,DWORD,D3DFORMAT,D3DPOOL,LPDIRECT3DTEXTURE9*);
using LoadSurface = HRESULT (WINAPI*)(LPDIRECT3DSURFACE9,const PALETTEENTRY*,const RECT*,const void*,D3DFORMAT,UINT,const PALETTEENTRY*,const RECT*,DWORD,D3DCOLOR);
static void check(bool ok,const char* where){if(!ok){std::fprintf(stderr,"TH14 texture32 failure: %s\n",where);std::exit(1);}}
int main(int argc,char** argv){
 check(argc==4,"arguments");FILE* in=nullptr;FILE* out=nullptr;
 check(fopen_s(&in,argv[1],"rb")==0&&in,"input");check(fopen_s(&out,argv[2],"wb")==0&&out,"output");
 unsigned int cw=0;check(_controlfp_s(&cw,std::atoi(argv[3])==64?_PC_64:_PC_53,_MCW_PC|_MCW_RC)==0,"FPU control");
 auto library=LoadLibraryW(L"d3dx9_43.dll");check(library!=nullptr,"D3DX DLL");
 auto create=reinterpret_cast<CreateTexture>(GetProcAddress(library,"D3DXCreateTexture"));auto upload=reinterpret_cast<LoadSurface>(GetProcAddress(library,"D3DXLoadSurfaceFromMemory"));check(create&&upload,"D3DX exports");
 auto window=CreateWindowExW(0,L"STATIC",L"TH14 texture32 readback",0,0,0,64,64,nullptr,nullptr,nullptr,nullptr);check(window!=nullptr,"hidden window");
 auto d3d=Direct3DCreate9(D3D_SDK_VERSION);check(d3d!=nullptr,"D3D9");D3DPRESENT_PARAMETERS pp{};
 pp.BackBufferWidth=32;pp.BackBufferHeight=32;pp.BackBufferFormat=D3DFMT_A8R8G8B8;pp.BackBufferCount=1;pp.SwapEffect=D3DSWAPEFFECT_DISCARD;pp.hDeviceWindow=window;pp.Windowed=TRUE;pp.PresentationInterval=D3DPRESENT_INTERVAL_IMMEDIATE;
 IDirect3DDevice9* device=nullptr;check(SUCCEEDED(d3d->CreateDevice(0,D3DDEVTYPE_HAL,window,D3DCREATE_HARDWARE_VERTEXPROCESSING,&pp,&device)),"HAL device");
 char magic[8];unsigned count=0;check(std::fread(magic,1,8,in)==8&&!std::memcmp(magic,"TH14TEX\0",8),"magic");check(std::fread(&count,4,1,in)==1,"case count");
 if(std::atoi(argv[3])==64){__asm { fninit }}else{unsigned post_reset=0;check(_controlfp_s(&post_reset,_PC_53,_MCW_PC|_MCW_RC)==0,"post-device precision reset");}
 unsigned post_device_control=0;check(_controlfp_s(&post_device_control,0,0)==0,"post-device FPU control");
 check(std::fwrite(&cw,4,1,out)==1&&std::fwrite(&post_device_control,4,1,out)==1&&std::fwrite(&count,4,1,out)==1,"output header");
 for(unsigned i=0;i<count;++i){
  unsigned a[19];check(std::fread(a,4,19,in)==19,"request");std::vector<unsigned char> source(a[18]);check(std::fread(source.data(),1,source.size(),in)==source.size(),"source bytes");
  IDirect3DTexture9* texture=nullptr;check(SUCCEEDED(create(device,a[0],a[1],a[2],a[3],D3DFORMAT(a[4]),D3DPOOL(a[5]),&texture)),"CreateTexture");D3DSURFACE_DESC desc{};check(SUCCEEDED(texture->GetLevelDesc(0,&desc)),"GetLevelDesc");
  const unsigned format=unsigned(desc.Format);const unsigned bpp=format==20?3:format==21||format==22?4:format==28?1:format==23||format==25||format==26||format==29?2:0;check(bpp>0,"readback format");
  D3DLOCKED_RECT lock{};check(SUCCEEDED(texture->LockRect(0,&lock,nullptr,0)),"clear LockRect");for(unsigned y=0;y<desc.Height;++y)std::memset(static_cast<char*>(lock.pBits)+y*lock.Pitch,0,desc.Width*bpp);check(SUCCEEDED(texture->UnlockRect(0)),"clear UnlockRect");
  if(a[6]){IDirect3DSurface9* surface=nullptr;check(SUCCEEDED(texture->GetSurfaceLevel(0,&surface)),"GetSurfaceLevel");RECT s{LONG(a[10]),LONG(a[11]),LONG(a[12]),LONG(a[13])},d{LONG(a[14]),LONG(a[15]),LONG(a[16]),LONG(a[17])};check(SUCCEEDED(upload(surface,nullptr,&d,source.data(),D3DFORMAT(a[7]),a[8],nullptr,&s,a[9],0)),"LoadSurfaceFromMemory");surface->Release();}
  check(SUCCEEDED(texture->LockRect(0,&lock,nullptr,D3DLOCK_READONLY)),"read LockRect");const unsigned metadata[]={format,desc.Width,desc.Height,desc.Width*bpp,desc.Width*desc.Height*bpp};check(std::fwrite(metadata,4,5,out)==5,"metadata");for(unsigned y=0;y<desc.Height;++y)check(std::fwrite(static_cast<char*>(lock.pBits)+y*lock.Pitch,1,desc.Width*bpp,out)==desc.Width*bpp,"pixels");check(SUCCEEDED(texture->UnlockRect(0)),"read UnlockRect");texture->Release();
 }
 check(std::fgetc(in)==EOF,"trailing input");std::fclose(in);std::fclose(out);device->Release();d3d->Release();DestroyWindow(window);FreeLibrary(library);std::printf("PASS texture32 %u cases, control %x\n",count,cw);return 0;
}
