"""Finite vector controls through the actual installed x86 D3DX9_43 DLL."""
from pathlib import Path
import hashlib,json,os,random,struct,subprocess
ROOT=Path(__file__).resolve().parents[1]
def main():
 out=ROOT/'artifacts/th14/d3dx-normalize-check';out.mkdir(parents=True,exist_ok=True);dll=Path('C:/Windows/SysWOW64/d3dx9_43.dll');sha=lambda b:hashlib.sha256(b).hexdigest()
 assert sha(dll.read_bytes())=='0b28546be22c71834501f7d7185ede5d79742457331c7ee09efc14490dd64f5f'
 source=ROOT/'tools/th14-d3dx-normalize-worker.cs';exe=out/'worker.exe'
 subprocess.run(['C:/Windows/Microsoft.NET/Framework/v4.0.30319/csc.exe','-nologo','-platform:x86','-out:'+str(exe),str(source)],check=True,creationflags=subprocess.CREATE_NO_WINDOW)
 p=subprocess.Popen([str(exe)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,encoding='ascii',creationflags=subprocess.CREATE_NO_WINDOW)
 word=lambda f:struct.unpack('<I',struct.pack('<f',f))[0];r=random.Random(14);inputs=[]
 for v in [(0.,0.,0.),(-0.,0.,-0.),(0,300,600),(0,200,600),(0,1,0),(1,0,0),(1,1,1),(-30,300,600)]:inputs.append(list(map(word,v)))
 for power in (-100,-24,-23,-22,-10,0,10,50,60):
  for v in [(1,0,0),(0,1,0),(0,0,1),(1,-1,.125),(-.125,.375,1)]:inputs.append([word(x*2.**power)for x in v])
 for n in range(8192):
  power=r.randrange(-25,61);inputs.append([word(r.uniform(-1,1)*2.**power)for _ in range(3)])
 rows=[]
 for words in inputs:
  p.stdin.write(','.join(map(str,words))+'\n');p.stdin.flush();result=list(map(int,p.stdout.readline().strip().split(',')));assert len(result)==3;rows.append([words,result])
 p.stdin.close();p.wait(timeout=5);assert p.returncode==0,p.stderr.read()
 report=dict(dllSha256=sha(dll.read_bytes()),workerSourceSha256=sha(source.read_bytes()),workerSha256=sha(exe.read_bytes()),processor=os.environ.get('PROCESSOR_IDENTIFIER'),actualWindowsX86Dll=True,finiteInputsOnly=True,rows=rows)
 (out/'native.json').write_text(json.dumps(report,separators=(',',':'))+'\n');print(json.dumps(dict(cases=len(rows),dllSha256=report['dllSha256'])))
if __name__=='__main__':main()
