/* Separate x86 helper process per declared free order; no original game. */
typedef unsigned int U32;typedef void *PTR;
__declspec(dllimport) PTR __stdcall GetProcessHeap(void);
__declspec(dllimport) PTR __stdcall HeapAlloc(PTR,U32,U32);
__declspec(dllimport) int __stdcall HeapFree(PTR,U32,PTR);
__declspec(dllimport) U32 __stdcall HeapSize(PTR,U32,PTR);
__declspec(dllimport) PTR __stdcall GetStdHandle(U32);
__declspec(dllimport) int __stdcall WriteFile(PTR,const void *,U32,U32 *,PTR);
__declspec(dllimport) void __stdcall ExitProcess(U32);
#ifndef CASE_ID
#error CASE_ID is required
#endif
#if CASE_ID == 0
static const U32 count=4, order[8]={1,3,5,7,0,0,0,0};
#elif CASE_ID == 1
static const U32 count=4, order[8]={0,2,4,6,0,0,0,0};
#elif CASE_ID == 2
static const U32 count=4, order[8]={7,5,3,1,0,0,0,0};
#elif CASE_ID == 3
static const U32 count=4, order[8]={2,3,4,5,0,0,0,0};
#elif CASE_ID == 4
static const U32 count=8, order[8]={0,1,2,3,4,5,6,7};
#else
#error Unknown CASE_ID
#endif
struct Result {U32 magic,case_id,heap,count,initial[8],replacement[8],freed_order[8],sizes[16],free_ok[8];};
static struct Result result;
void mainCRTStartup(void){
 PTR heap=GetProcessHeap();PTR p[8];U32 wrote=0;result.magic=0x53485054u;result.case_id=CASE_ID;result.heap=(U32)heap;result.count=count;if(!heap)ExitProcess(2);
 for(U32 i=0;i<8;i++){p[i]=HeapAlloc(heap,0,0x530c);if(!p[i])ExitProcess(3);result.initial[i]=(U32)p[i];result.sizes[i]=HeapSize(heap,0,p[i]);result.freed_order[i]=0xffffffffu;}
 for(U32 i=0;i<count;i++){result.freed_order[i]=order[i];result.free_ok[i]=HeapFree(heap,0,p[order[i]]);if(!result.free_ok[i])ExitProcess(4);}
 for(U32 i=0;i<count;i++){PTR next=HeapAlloc(heap,0,0x530c);if(!next)ExitProcess(5);result.replacement[i]=(U32)next;result.sizes[8+i]=HeapSize(heap,0,next);}
 if(!WriteFile(GetStdHandle((U32)-11),&result,sizeof result,&wrote,0)||wrote!=sizeof result)ExitProcess(6);ExitProcess(0);
}
