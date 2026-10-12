#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <d3d9.h>
#include <cstdio>
#include <cstdlib>
#include <set>
#include <utility>
#include <vector>
#include <float.h>
static void check(bool ok,const char* label){if(!ok){std::fprintf(stderr,"weights32: %s\n",label);std::exit(1);}}
int main(int argc,char** argv){
 check(argc==3,"arguments");FILE *in=nullptr,*out=nullptr;check(!fopen_s(&in,argv[1],"rb")&&!fopen_s(&out,argv[2],"wb"),"files");
 char magic[8];unsigned count;check(std::fread(magic,1,8,in)==8&&!std::memcmp(magic,"TH14TEX\0",8)&&std::fread(&count,4,1,in)==1,"header");
 std::set<std::pair<unsigned,unsigned>> sizes;
 for(unsigned i=0;i<count;++i){unsigned a[19];check(std::fread(a,4,19,in)==19,"request");check(std::fseek(in,a[18],SEEK_CUR)==0,"skip");if(a[6]&&a[9]==0x30004){sizes.emplace(a[12],a[16]);sizes.emplace(a[13],a[17]);}}
 auto window=CreateWindowExW(0,L"STATIC",L"TH14 weights32",0,0,0,64,64,nullptr,nullptr,nullptr,nullptr);check(window!=nullptr,"window");auto d3d=Direct3DCreate9(D3D_SDK_VERSION);check(d3d!=nullptr,"D3D9");D3DPRESENT_PARAMETERS pp{};pp.BackBufferWidth=32;pp.BackBufferHeight=32;pp.BackBufferFormat=D3DFMT_A8R8G8B8;pp.BackBufferCount=1;pp.SwapEffect=D3DSWAPEFFECT_DISCARD;pp.hDeviceWindow=window;pp.Windowed=TRUE;IDirect3DDevice9* device=nullptr;check(SUCCEEDED(d3d->CreateDevice(0,D3DDEVTYPE_HAL,window,D3DCREATE_HARDWARE_VERTEXPROCESSING,&pp,&device)),"device");
 __asm { fninit }
 unsigned cw=0;_controlfp_s(&cw,0,0);auto dll=LoadLibraryW(L"d3dx9_43.dll");check(dll!=nullptr,"DLL");
 // Pinned DLL SHA is checked by the orchestration tool before this private routine.
 using Weights=void*(WINAPI*)(unsigned,unsigned,unsigned);using Free=void(__cdecl*)(void*);
 auto weights=reinterpret_cast<Weights>(reinterpret_cast<char*>(dll)+0xdc63b);auto release=reinterpret_cast<Free>(reinterpret_cast<char*>(dll)+0x1bf388);
 count=unsigned(sizes.size());check(std::fwrite(&cw,4,1,out)==1&&std::fwrite(&count,4,1,out)==1,"output");
 for(auto [source,destination]:sizes){void* data=weights(source,destination,0);check(data!=nullptr,"weights");unsigned bytes=*static_cast<unsigned*>(data);check(std::fwrite(&source,4,1,out)==1&&std::fwrite(&destination,4,1,out)==1&&std::fwrite(&bytes,4,1,out)==1&&std::fwrite(data,1,bytes,out)==bytes,"table");release(data);}
 std::fclose(in);std::fclose(out);device->Release();d3d->Release();DestroyWindow(window);FreeLibrary(dll);std::printf("PASS weights32 %u tables, post-device control %x\n",count,cw);return 0;
}
