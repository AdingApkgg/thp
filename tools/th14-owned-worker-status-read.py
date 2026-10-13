"""Nonblocking read of the resource-thread status in the explicitly owned test child."""
import argparse,ctypes as C,hashlib,json,struct
from ctypes import wintypes as W
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--snapshot',required=True);p.add_argument('--work-directory',required=True)
    a=p.parse_args();directory,work=[(ROOT/name).resolve() for name in (a.snapshot,a.work_directory)]
    assert all(path.is_relative_to(ROOT/'artifacts/th14') for path in (directory,work))
    manifest=json.loads((directory/'manifest.json').read_text());exe=work/'th14.exe'
    assert hashlib.sha256(exe.read_bytes()).hexdigest()==manifest['executableSha256']
    k=C.WinDLL('kernel32',use_last_error=True)
    def function(name,result,args):
        f=getattr(k,name);f.restype=result;f.argtypes=args;return f
    handle=C.c_void_p
    opened=function('OpenProcess',handle,[W.DWORD,W.BOOL,W.DWORD])(0x1050,False,manifest['pid'])
    if not opened:raise C.WinError(C.get_last_error())
    close=function('CloseHandle',W.BOOL,[handle]);duplicate=None
    try:
        path,length=C.create_unicode_buffer(32768),W.DWORD(32768)
        query=function('QueryFullProcessImageNameW',W.BOOL,[handle,W.DWORD,W.LPWSTR,C.POINTER(W.DWORD)])
        if not query(opened,0,path,C.byref(length)):raise C.WinError(C.get_last_error())
        assert Path(path.value).resolve()==exe,'PID no longer belongs to our exact private reference child'
        process_code=W.DWORD();get_process_code=function('GetExitCodeProcess',W.BOOL,[handle,C.POINTER(W.DWORD)])
        assert get_process_code(opened,C.byref(process_code)) and process_code.value==259
        data,received=C.create_string_buffer(28),C.c_size_t()
        read=function('ReadProcessMemory',W.BOOL,[handle,handle,handle,C.c_size_t,C.POINTER(C.c_size_t)])
        if not read(opened,0x4d98ec,data,28,C.byref(received)) or received.value!=28:raise C.WinError(C.get_last_error())
        words=struct.unpack('<7I',data.raw);assert words[1]
        duplicate=handle();current=function('GetCurrentProcess',handle,[])()
        copy=function('DuplicateHandle',W.BOOL,[handle,handle,handle,C.POINTER(handle),W.DWORD,W.BOOL,W.DWORD])
        if not copy(opened,words[1],current,C.byref(duplicate),0x100800,False,0):raise C.WinError(C.get_last_error())
        wait=function('WaitForSingleObject',W.DWORD,[handle,W.DWORD])(duplicate,0)
        code=W.DWORD();get_code=function('GetExitCodeThread',W.BOOL,[handle,C.POINTER(W.DWORD)])
        if not get_code(duplicate,C.byref(code)):raise C.WinError(C.get_last_error())
        assert wait in (0,0x102)
        result=dict(pid=manifest['pid'],exactOwnedExecutable=str(exe),owner='0x4d98ec',ownerWords=list(words),
                    zeroTimeoutWait=wait,nativeExitCode=code.value,threadSignaled=wait==0,
                    noGameOrThreadStateWrites=True,observerSha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                    scope='Only the already-created private reference child identified by manifest PID and exact image path is read. Duplicate its resource-thread handle for limited query and synchronize, query with timeout0, close only local duplicate/process handles. No attachment, suspension, UI input or scheduling/termination. This query is at the current game state, not retroactive proof of a different bootstrap handle.')
        (directory/'owned-worker-status-read-oct13.json').write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps(result))
    finally:
        if duplicate and duplicate.value:close(duplicate)
        close(opened)

if __name__=='__main__':main()
