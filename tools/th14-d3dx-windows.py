"""Execute the pinned x86 D3DX DLL for live vector inputs from a CPU oracle."""
from pathlib import Path
import hashlib,os,struct,subprocess
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_EAX,UC_X86_REG_EIP,UC_X86_REG_ESP
ROOT=Path(__file__).resolve().parents[1]
class WindowsVectors:
 def __init__(self,uc,entry,out):
  dll=Path('C:/Windows/SysWOW64/d3dx9_43.dll');self.dll_sha=hashlib.sha256(dll.read_bytes()).hexdigest();assert self.dll_sha=='0b28546be22c71834501f7d7185ede5d79742457331c7ee09efc14490dd64f5f'
  out.mkdir(parents=True,exist_ok=True);exe=out/'worker.exe';source=ROOT/'tools/th14-d3dx-normalize-worker.cs'
  subprocess.run(['C:/Windows/Microsoft.NET/Framework/v4.0.30319/csc.exe','-nologo','-platform:x86','-out:'+str(exe),str(source)],check=True,creationflags=subprocess.CREATE_NO_WINDOW)
  self.worker=subprocess.Popen([str(exe)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,encoding='ascii',creationflags=subprocess.CREATE_NO_WINDOW);self.calls=0;self.digest=hashlib.sha256();self.worker_sha=hashlib.sha256(exe.read_bytes()).hexdigest();uc.hook_add(UC_HOOK_CODE,self.normalize,begin=entry,end=entry)
 def normalize(self,u,address,size,user):
  sp=u.reg_read(UC_X86_REG_ESP);ret,out,source=struct.unpack('<3I',u.mem_read(sp,12));raw=bytes(u.mem_read(source,12));words=struct.unpack('<3I',raw)
  assert self.worker.poll()is None;self.worker.stdin.write(','.join(map(str,words))+'\n');self.worker.stdin.flush();values=list(map(int,self.worker.stdout.readline().strip().split(',')));assert len(values)==3
  result=struct.pack('<3I',*values);u.mem_write(out,result);self.digest.update(raw+result);self.calls+=1;u.reg_write(UC_X86_REG_EAX,out);u.reg_write(UC_X86_REG_ESP,sp+12);u.reg_write(UC_X86_REG_EIP,ret)
 def close(self):
  self.worker.stdin.close();self.worker.wait(timeout=5);assert self.worker.returncode==0,self.worker.stderr.read()
  return dict(backend='actual Windows x86 D3DX DLL service',dllSha256=self.dll_sha,workerSha256=self.worker_sha,calls=self.calls,inputOutputSha256=self.digest.hexdigest(),processor=os.environ.get('PROCESSOR_IDENTIFIER'))
