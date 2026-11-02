/* Separate x86 helper: interleave noise allocations and enemy-sized blocks. */
typedef unsigned int U32;typedef void *PTR;
__declspec(dllimport) PTR __stdcall GetProcessHeap(void);
__declspec(dllimport) PTR __stdcall HeapAlloc(PTR,U32,U32);
__declspec(dllimport) int __stdcall HeapFree(PTR,U32,PTR);
__declspec(dllimport) U32 __stdcall HeapSize(PTR,U32,PTR);
__declspec(dllimport) PTR __stdcall GetStdHandle(U32);
__declspec(dllimport) int __stdcall WriteFile(PTR,const void *,U32,U32 *,PTR);
__declspec(dllimport) void __stdcall ExitProcess(U32);
#ifndef NOISE_BYTES
#error NOISE_BYTES is required
#endif
struct Result {U32 magic,noise_size,heap,count,noise[8],primary[8],replacement[4],sizes[20];};
static struct Result result;
void mainCRTStartup(void){
 PTR heap=GetProcessHeap();PTR primary[8];U32 wrote=0;result.magic=0x4d485054u;result.noise_size=NOISE_BYTES;result.heap=(U32)heap;result.count=8;if(!heap)ExitProcess(2);
 for(U32 i=0;i<8;i++){
  PTR noise=HeapAlloc(heap,0,NOISE_BYTES);if(!noise)ExitProcess(3);result.noise[i]=(U32)noise;result.sizes[i]=HeapSize(heap,0,noise);
  primary[i]=HeapAlloc(heap,0,0x530c);if(!primary[i])ExitProcess(4);result.primary[i]=(U32)primary[i];result.sizes[8+i]=HeapSize(heap,0,primary[i]);
 }
 for(U32 i=0;i<4;i++)if(!HeapFree(heap,0,primary[i*2+1]))ExitProcess(5);
 for(U32 i=0;i<4;i++){PTR next=HeapAlloc(heap,0,0x530c);if(!next)ExitProcess(6);result.replacement[i]=(U32)next;result.sizes[16+i]=HeapSize(heap,0,next);}
 if(!WriteFile(GetStdHandle((U32)-11),&result,sizeof result,&wrote,0)||wrote!=sizeof result)ExitProcess(7);ExitProcess(0);
}
