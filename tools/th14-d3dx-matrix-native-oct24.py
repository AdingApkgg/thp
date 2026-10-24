"""Call the actual pinned Windows x86 D3DX matrix services without a device."""
from pathlib import Path
import argparse,hashlib,json,random,struct,subprocess
ROOT=Path(__file__).resolve().parents[1]
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--out',type=Path,default=ROOT/'artifacts/th14/bomb-animation-retirement-oct24/matrix-unit');args=parser.parse_args();home=args.out;home.mkdir(parents=True,exist_ok=True);sha=lambda b:hashlib.sha256(b).hexdigest()
 dll=Path('C:/Windows/SysWOW64/d3dx9_43.dll');assert sha(dll.read_bytes())=='0b28546be22c71834501f7d7185ede5d79742457331c7ee09efc14490dd64f5f';source=ROOT/'tools/th14-d3dx-matrix-worker.cs';exe=home/'worker.exe'
 subprocess.run(['C:/Windows/Microsoft.NET/Framework/v4.0.30319/csc.exe','-nologo','-platform:x86','-out:'+str(exe),str(source)],check=True,creationflags=subprocess.CREATE_NO_WINDOW)
 worker=subprocess.Popen([str(exe)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,encoding='ascii',creationflags=subprocess.CREATE_NO_WINDOW);rows=[];rng=random.Random(140024);bits=lambda x:struct.unpack('<I',struct.pack('<f',x))[0]
 try:
  worker.stdin.write('INFO\n');worker.stdin.flush();info=worker.stdout.readline().strip().split(',');assert info[0]=='INFO';dispatch=int(info[1]);assert dispatch==0x1ba245,hex(dispatch)
  for i in range(300):
   inputs=[('M',[bits(rng.uniform(-64,64))for _ in range(32)])]+[(axis,[bits(rng.uniform(-20,20))])for axis in 'XYZ']
   for op,words in inputs:
    worker.stdin.write(op+','+','.join(map(str,words))+'\n');worker.stdin.flush();line=worker.stdout.readline();assert line;output=list(map(int,line.strip().split(',')));assert len(output)==16;rows.append(dict(op=op,inputBits=words,outputBits=output,index=i))
 finally:worker.stdin.close();worker.wait(timeout=10)
 assert worker.returncode==0,worker.stderr.read()
 report=dict(actualWindowsX86D3dx=True,dllSha256=sha(dll.read_bytes()),multiplyDispatchRva=hex(dispatch),workerSourceSha256=sha(source.read_bytes()),workerSha256=sha(exe.read_bytes()),toolSha256=sha(Path(__file__).read_bytes()),rows=rows,audioPlayed=False,deviceCreated=False,originalGameProcessStarted=False,scope='Actual pinned Windows x86 D3DX9_43 CPU-selected SSE MatrixMultiply and RotationX/Y/Z,1200 deterministic independent finite inputs. The observed multiply dispatch is RVA1ba245: rows0/3 add product pairs and rows1/2 accumulate serially. This is a specific DLL/CPU environment, not all D3DX implementations, GPU pixels or full-game equality.',completeGame=False,nativeEquivalent=False)
 (home/'native.json').write_text(json.dumps(report,separators=(',',':'))+'\n');print(json.dumps(dict(nativeCases=len(rows),multiplyDispatchRva=hex(dispatch),actualWindowsX86D3dx=True)))
if __name__=='__main__':main()
