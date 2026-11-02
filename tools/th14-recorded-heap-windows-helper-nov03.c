/* Isolated x86 Windows heap helper: inputs are sizes, flags and synthetic IDs. */
typedef unsigned int U32;typedef void *PTR;
__declspec(dllimport) PTR __stdcall GetProcessHeap(void);
__declspec(dllimport) PTR __stdcall HeapAlloc(PTR,U32,U32);
__declspec(dllimport) int __stdcall HeapFree(PTR,U32,PTR);
__declspec(dllimport) PTR __stdcall GetStdHandle(U32);
__declspec(dllimport) int __stdcall WriteFile(PTR,const void *,U32,U32 *,PTR);
__declspec(dllimport) void __stdcall ExitProcess(U32);
struct Action {U32 kind,id,size,flags;};
#include "heap-actions.h"
struct Result {U32 magic,count;U32 addresses[HEAP_ALLOCATION_COUNT];};
static struct Result result;static PTR live[HEAP_ALLOCATION_COUNT];
void mainCRTStartup(void){
 PTR heap=GetProcessHeap();U32 written=0;result.magic=0x54485048u;result.count=HEAP_ALLOCATION_COUNT;if(!heap)ExitProcess(2);
 for(U32 i=0;i<HEAP_ACTION_COUNT;i++){
  struct Action a=heap_actions[i];if(a.id>=HEAP_ALLOCATION_COUNT)ExitProcess(3);
  if(a.kind==1){if(live[a.id]||!a.size)ExitProcess(4);PTR p=HeapAlloc(heap,a.flags,a.size);if(!p)ExitProcess(5);live[a.id]=p;result.addresses[a.id]=(U32)p;}
  else if(a.kind==2){if(!live[a.id]||!HeapFree(heap,0,live[a.id]))ExitProcess(6);live[a.id]=0;}
  else ExitProcess(7);
 }
 if(!WriteFile(GetStdHandle((U32)-11),&result,sizeof result,&written,0)||written!=sizeof result)ExitProcess(8);ExitProcess(0);
}
