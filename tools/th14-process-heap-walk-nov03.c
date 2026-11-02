/* x86 helper: inspect only this process's heap, never the TH14 process. */
typedef unsigned int U32;typedef unsigned short U16;typedef unsigned char U8;typedef void *PTR;
__declspec(dllimport) PTR __stdcall GetProcessHeap(void);
__declspec(dllimport) PTR __stdcall HeapAlloc(PTR,U32,U32);
__declspec(dllimport) int __stdcall HeapFree(PTR,U32,PTR);
__declspec(dllimport) int __stdcall HeapLock(PTR);
__declspec(dllimport) int __stdcall HeapUnlock(PTR);
__declspec(dllimport) int __stdcall HeapWalk(PTR,void *);
__declspec(dllimport) U32 __stdcall GetLastError(void);
__declspec(dllimport) PTR __stdcall GetStdHandle(U32);
__declspec(dllimport) int __stdcall WriteFile(PTR,const void *,U32,U32 *,PTR);
__declspec(dllimport) void __stdcall ExitProcess(U32);
struct HeapEntry { PTR data;U32 size;U8 overhead,region;U16 flags;U32 details[4]; };
struct Entry { U32 address,size,overhead,flags; };
struct Result { U32 magic,heap,initial[8],replacement[4],counts[3];struct Entry rows[3][4096]; };
static struct Result result;
static void snapshot(PTR heap,U32 phase){
    struct HeapEntry entry;entry.data=0;
    if(!HeapLock(heap))ExitProcess(10);
    while(HeapWalk(heap,&entry)){
        U32 i=result.counts[phase];if(i==4096)ExitProcess(11);
        result.rows[phase][i].address=(U32)entry.data;result.rows[phase][i].size=entry.size;
        result.rows[phase][i].overhead=entry.overhead;result.rows[phase][i].flags=entry.flags;
        result.counts[phase]=i+1;
    }
    if(GetLastError()!=259)ExitProcess(12);
    if(!HeapUnlock(heap))ExitProcess(13);
}
void mainCRTStartup(void){
    PTR heap=GetProcessHeap();PTR p[8];U32 wrote=0;result.magic=0x57485054u;result.heap=(U32)heap;if(!heap)ExitProcess(2);
    for(U32 i=0;i<8;i++){p[i]=HeapAlloc(heap,0,0x530c);if(!p[i])ExitProcess(3);result.initial[i]=(U32)p[i];}
    snapshot(heap,0);
    for(U32 i=0;i<4;i++)if(!HeapFree(heap,0,p[i*2+1]))ExitProcess(4);
    snapshot(heap,1);
    for(U32 i=0;i<4;i++){PTR next=HeapAlloc(heap,0,0x530c);if(!next)ExitProcess(5);result.replacement[i]=(U32)next;}
    snapshot(heap,2);
    if(!WriteFile(GetStdHandle((U32)-11),&result,sizeof result,&wrote,0)||wrote!=sizeof result)ExitProcess(6);
    ExitProcess(0);
}
