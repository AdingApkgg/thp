"""Use the original TH14 replay decryptor/decompressor on ordinary-run witnesses."""
import hashlib,runpy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];parent=ROOT/'tools/th14-replay-native-decode.py';s=parent.read_text()
s=s.replace("directory=ROOT/'artifacts/th14/replay-writer-check'","directory=ROOT/'artifacts/th14/natural-input'").replace("directory.glob('*.rpy')","directory.glob('*/ordinary-input.rpy')")
s=s.replace("file=p.name,packed=packed", "file=str(p.relative_to(directory)),packed=packed")
s=s.replace('m.mem_map(base,0x400000)','m.mem_map(base,0x800000)').replace('base+0x100000','base+0x500000').replace('count=10000000','count=50000000')
s=s.replace('heap[0]=base+0x500000;m.mem_write(src',"assert src+packed<dst and dst+unpacked+32<base+0x500000;heap[0]=base+0x500000;m.mem_write(src")
s=s.replace('th14-replay-native-decode-verified.json','th14-natural-replay-native-decode-observed-oct12.json')
s=s.replace("report=dict(passed=True,", "report=dict(diagnosticEvidenceVerified=True,completeGame=False,nativeEquivalent=False,productionChanged=False,generatorSha256='"+hashlib.sha256(Path(__file__).read_bytes()).hexdigest()+"',parentSourceSha256='"+hashlib.sha256(parent.read_bytes()).hexdigest()+"',passed=True,")
out=ROOT/'tools/th14-natural-replay-decode-native.py';out.write_text(s);runpy.run_path(str(out),run_name='__main__')
