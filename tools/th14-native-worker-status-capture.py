"""Read actual completion status of the resource thread in our own retail child."""
import ctypes as C,hashlib,importlib,json,struct,sys
from ctypes import wintypes as W
from pathlib import Path

WARM=importlib.import_module('th14-native-stored-bootstrap-capture')
BOOT,CAPTURE,ROOT=WARM.BOOT,WARM.CAPTURE,WARM.ROOT

def main():
    output=(ROOT/sys.argv[sys.argv.index('--bootstrap-directory')+1]).resolve()
    assert output.is_relative_to(ROOT/'artifacts/th14')
    original_factory=C.WinDLL;state=dict(process=None,observed=False)
    def factory(name,*args,**kwargs):
        native=original_factory(name,*args,**kwargs)
        if name.lower()!='kernel32':return native
        native.GetCurrentProcess.restype=C.c_void_p;native.GetCurrentProcess.argtypes=[]
        native.DuplicateHandle.restype=W.BOOL;native.DuplicateHandle.argtypes=[C.c_void_p,C.c_void_p,C.c_void_p,C.POINTER(C.c_void_p),W.DWORD,W.BOOL,W.DWORD]
        native.GetExitCodeThread.restype=W.BOOL;native.GetExitCodeThread.argtypes=[C.c_void_p,C.POINTER(W.DWORD)]
        def created(arguments):
            info=C.cast(arguments[9],C.POINTER(CAPTURE.ProcessInfo)).contents
            state.update(process=info.process,pid=info.pid)
        def context_written(arguments):
            if state['observed'] or not state['process']:return
            context=C.string_at(arguments[1],716)
            if struct.unpack_from('<I',context,184)[0]!=CAPTURE.BP:return
            data,received=C.create_string_buffer(28),C.c_size_t()
            if not native.ReadProcessMemory(state['process'],0x4d98ec,data,28,C.byref(received)) or received.value!=28:raise C.WinError(C.get_last_error())
            words=struct.unpack('<7I',data.raw);assert words[1]
            duplicate,code=C.c_void_p(),W.DWORD()
            if not native.DuplicateHandle(state['process'],words[1],native.GetCurrentProcess(),C.byref(duplicate),0x100800,False,0):raise C.WinError(C.get_last_error())
            try:
                wait=native.WaitForSingleObject(duplicate,0)
                if not native.GetExitCodeThread(duplicate,C.byref(code)):raise C.WinError(C.get_last_error())
                assert wait in (0,0x102)
            finally:native.CloseHandle(duplicate)
            result=dict(pid=state['pid'],owner='0x4d98ec',ownerWords=list(words),
                        zeroTimeoutWait=wait,nativeExitCode=code.value,threadSignaled=wait==0,
                        noThreadStateWrites=True,privateOwnedChildOnly=True,
                        observerSha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                        scope='At the own hidden child first-Player debugger boundary, duplicate only its exact resource-thread handle for QUERY_LIMITED_INFORMATION|SYNCHRONIZE; query status with zero timeout and close only that duplicate. No attachment, input, thread scheduling/termination or game state changes by this observer. Existing warm case initialization remains separately declared.')
            (output/'original-worker-status-oct13.json').write_text(json.dumps(result,indent=2)+'\n')
            print(json.dumps(result),flush=True);state['observed']=True
        class Kernel:
            def __getattr__(self,attribute):return getattr(native,attribute)
        proxy=Kernel();proxy.CreateProcessW=BOOT.Function(native.CreateProcessW,created)
        proxy.Wow64SetThreadContext=BOOT.Function(native.Wow64SetThreadContext,context_written)
        return proxy
    C.WinDLL=factory
    try:WARM.main()
    finally:C.WinDLL=original_factory
    assert state['observed']

if __name__=='__main__':main()
