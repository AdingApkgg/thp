"""Original mode8 nonzero rotation/order paths with real pinned x86 D3DX services."""
from pathlib import Path
import hashlib,json,subprocess
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/mode8-rotation-nov12';H.mkdir(exist_ok=False);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
base=R/'tools/th14-mode8-display-native-nov12.py';old=json.loads((R/'artifacts/th14/mode8-display-space-nov12/native.json').read_bytes());assert sha(base)==old['toolSha256']
P=R/'artifacts/th14/bomb-animation-retirement-oct24/matrix-unit';native=json.loads((P/'native.json').read_bytes());exe=P/'worker.exe';assert sha(exe)==native['workerSha256'] and sha(R/'tools/th14-d3dx-matrix-worker.cs')==native['workerSourceSha256'];assert sha(Path('C:/Windows/SysWOW64/d3dx9_43.dll'))==native['dllSha256']
worker=subprocess.Popen([str(exe)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,encoding='ascii',creationflags=subprocess.CREATE_NO_WINDOW)
calls=0
def rpc(op,words):
 global calls
 calls+=1;worker.stdin.write(op+','+','.join(map(str,words))+'\n');worker.stdin.flush();line=worker.stdout.readline();assert line,'D3DX worker returned EOF';values=list(map(int,line.strip().split(',')));assert len(values)==16;return values
worker.stdin.write('INFO\n');worker.stdin.flush();dispatch=worker.stdout.readline().strip();assert dispatch=='INFO,1811013',dispatch
code=base.read_text().replace('\r\n','\n');patches={
"R=Path(__file__).resolve().parents[1]":"R=Path(__file__).resolve().parents[3]",
"H=R/'artifacts/th14/mode8-display-space-nov12'":"H=R/'artifacts/th14/mode8-rotation-nov12'",
"assert not H.exists();H.mkdir()":"assert H.exists() and not (H/'native.json').exists()",
"UC_MODE_32\n":"UC_MODE_32,UC_HOOK_CODE\n",
"m.mem_map(B,0x100000);m.mem_write(0x4854a0,b'\\xc3')":"m.mem_map(B,0x100000)",
"put(at+0x1c,(resolution<<19)|(origin<<17))":"put(at+0x1c,(resolution<<19)|(origin<<17)|((0 if parent else order)<<2));floats(at+0x48,[-.25,.5,-.75] if parent else angles)",
"[(480,360),(640,480),(800,600),(801,623),(960,720),(1280,960)]":"[(640,480),(960,720),(1280,960)]",
"for res,origin,dirty,freeze,parent,sample in itertools.product(range(8),range(3),[0,4,8,12],[0,1],[0,1],[0,1]):":"for res,origin,dirty,freeze,parent,sample,order,angles in itertools.product([0,1,2,4],range(3),[4,8,12],[0],[0,1],[0],range(8),[(.125,-.375,.625),(-1.25,.75,-.5)]):",
"parent=parent,sample=sample))":"parent=parent,sample=sample,order=order,angles=angles))",
"allRotationsZero=True":"allRotationsZero=False,actualWindowsX86D3dxServices=True,declaredD3dxHostFpuEnvironment=True,originalGameFpuEnvironmentNotInherited=True",
}
for before,after in patches.items():assert code.count(before)==1,before;code=code.replace(before,after)
anchor='rows=[];inputs=bytearray();outputs=bytearray()'
bridge='''
def service(uc,pc,size,unused):
 sp=m.reg_read(UC_X86_REG_ESP);target=word(sp)
 if pc==0x4854a0:count=0
 else:
  op={B+0x100:'X',B+0x110:'Y',B+0x120:'Z',B+0x130:'M'}[pc];out=word(sp+4)
  if op=='M':values=list(struct.unpack('<32I',bytes(m.mem_read(word(sp+8),64))+bytes(m.mem_read(word(sp+12),64))));count=12
  else:values=[word(sp+8)];count=8
  m.mem_write(out,struct.pack('<16I',*rpc(op,values)));m.reg_write(UC_X86_REG_EAX,out)
 m.reg_write(UC_X86_REG_EIP,target);m.reg_write(UC_X86_REG_ESP,sp+4+count)
for slot,address in [(0x4b12d8,B+0x100),(0x4b12f8,B+0x110),(0x4b12cc,B+0x120),(0x4b12d4,B+0x130)]:
 put(slot,address);m.hook_add(UC_HOOK_CODE,service,begin=address,end=address)
m.hook_add(UC_HOOK_CODE,service,begin=0x4854a0,end=0x4854a0)
'''
assert code.count(anchor)==1;code=code.replace(anchor,bridge+'\n'+anchor)
derived=H/'native-derived.py';derived.write_text(code,encoding='utf8',newline='\n')
try:exec(compile(code,str(derived),'exec'),{'__file__':str(derived),'__name__':'__main__','rpc':rpc})
finally:
 worker.stdin.close();worker.wait(timeout=10)
 assert worker.returncode==0,worker.stderr.read()
report=dict(baseOracleSha256=sha(base),derivedOracleSha256=sha(derived),nativeMatrixWorkerSha256=sha(exe),nativeMatrixWorkerSourceSha256=sha(R/'tools/th14-d3dx-matrix-worker.cs'),dllSha256=native['dllSha256'],multiplyDispatch=dispatch,rpcCalls=calls,workerExited=True,workerExitCode=worker.returncode,originalGameRuns=0,gpuRuns=0,audibleOutput=False,completeGame=False,toolSha256=sha(Path(__file__)))
(H/'native-services.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
