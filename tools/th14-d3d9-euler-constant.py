"""Read-only evidence for a literal in the tested Windows D3D9 runtime.

This proves a constructor writes the literal; it does not by itself prove that
every native fog draw uses that field or establish cross-device equivalence.
"""
import hashlib,json,struct
from pathlib import Path
import capstone
ROOT=Path(__file__).resolve().parent.parent
path=Path('C:/Windows/System32/d3d9.dll');raw=path.read_bytes()
sha=lambda b:hashlib.sha256(b).hexdigest()
literal=struct.pack('<f',2.71828)
positions=[i for i in range(len(raw)-3) if raw[i:i+4]==literal]
assert positions==[0x69b6d],positions
pe=struct.unpack_from('<I',raw,0x3c)[0];sections=struct.unpack_from('<H',raw,pe+6)[0];optional=struct.unpack_from('<H',raw,pe+20)[0]
base=struct.unpack_from('<Q',raw,pe+48)[0];offset=positions[0];section=None
for i in range(sections):
    p=pe+24+optional+i*40;vs,va,size,start=struct.unpack_from('<4I',raw,p+8)
    if start<=offset<start+size:section=(va,start);break
assert section
begin,end=0x69b4c,0x69be2;va,start=section
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_64)
instructions=[dict(address=hex(i.address),bytes=i.bytes.hex(),mnemonic=i.mnemonic,operands=i.op_str) for i in md.disasm(raw[begin:end],base+va+begin-start)]
assert any(i['bytes']=='c741184df82d40' and i['mnemonic']=='mov' for i in instructions)
report=dict(verifiedLiteral=True,completeGame=False,nativeEquivalent=False,path=str(path),sha256=sha(raw),literalWord='0x402df84d',literalFloat32=struct.unpack('<f',literal)[0],fileOffset=hex(offset),constructorBytesSha256=sha(raw[begin:end]),instructions=instructions,toolSha256=sha(Path(__file__).read_bytes()),limits='Read-only literal constructor evidence; use by the native fog shader is a hypothesis tested separately against actual HAL outputs. No native game draw-loop equivalence claim.')
destination=ROOT/'docs/porting/th14-d3d9-euler-constant-observed-oct11.json';destination.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
print('Verified literal 2.71828 in tested D3D9 constructor')
