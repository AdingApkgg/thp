/* Standalone 32-bit Windows heap experiment. It does not launch the game. */
typedef unsigned int U32;
typedef void *PTR;
__declspec(dllimport) PTR __stdcall GetProcessHeap(void);
__declspec(dllimport) PTR __stdcall HeapAlloc(PTR,U32,U32);
__declspec(dllimport) int __stdcall HeapFree(PTR,U32,PTR);
__declspec(dllimport) U32 __stdcall HeapSize(PTR,U32,PTR);
__declspec(dllimport) PTR __stdcall GetStdHandle(U32);
__declspec(dllimport) int __stdcall WriteFile(PTR,const void *,U32,U32 *,PTR);
__declspec(dllimport) void __stdcall ExitProcess(U32);

struct Result { U32 magic,heap,initial[8],replacement[4],size[12],free_ok[4]; };
void mainCRTStartup(void){
    struct Result result;PTR heap=GetProcessHeap();U32 wrote=0;PTR p[8];
    result.magic=0x34485054u;result.heap=(U32)heap;
    if(!heap)ExitProcess(2);
    for(U32 i=0;i<8;i++){
        p[i]=HeapAlloc(heap,0,0x530c);if(!p[i])ExitProcess(3);
        result.initial[i]=(U32)p[i];result.size[i]=HeapSize(heap,0,p[i]);
    }
    for(U32 i=0;i<4;i++){
        result.free_ok[i]=HeapFree(heap,0,p[i*2+1]);if(!result.free_ok[i])ExitProcess(4);
    }
    for(U32 i=0;i<4;i++){
        PTR next=HeapAlloc(heap,0,0x530c);if(!next)ExitProcess(5);
        result.replacement[i]=(U32)next;result.size[8+i]=HeapSize(heap,0,next);
    }
    if(!WriteFile(GetStdHandle((U32)-11),&result,sizeof result,&wrote,0)||wrote!=sizeof result)ExitProcess(6);
    ExitProcess(0);
}
