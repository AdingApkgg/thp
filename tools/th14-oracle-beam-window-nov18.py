"""Run unchanged retail452700 on a captured40-word beam window.

Tests the declared native instruction/ANM/cookie boundary, not the original
caller stack history or full-game replay. Reports literal matches separately
from the explicit bounded-rule repair of nonfinite fallback geometry.
"""
from pathlib import Path
import sys,json,array,struct,hashlib,ctypes,math,importlib
import argparse
R=Path(__file__).resolve().parents[1];parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--capture',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();capture=args.capture.resolve();output=args.output.resolve();assert output.is_relative_to(R/'artifacts/th14') and not output.exists();sys.path.insert(0,str(R/'tools'))
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
source=(R/'tools/th14-oracle-live-beam-hits-nov14.py').read_text();setup=source[source.index('image, _, _ ='):source.index('results, types =')];exec(compile(setup,'declared-original-beam-boundaries','exec'),globals())
summary=json.loads((capture/'beam-window-summary.json').read_bytes());run=json.loads((capture/'report.json').read_bytes());assert summary['stride']==40 and summary['dropped']==0 and run['passed'] and run['retired'];p=capture/'beam-window.u32';assert p.stat().st_size==summary['count']*40*4;words=array.array('I');words.frombytes(p.read_bytes());inputs=[words[i:i+40]for i in range(0,len(words),40)];results=[]
for index,w in enumerate(inputs):
 for ptr,size in [(obj,0x100),(area,0x100),(vm,0x600),(player,0x19000)]:m.mem_write(ptr,bytes(size))
 m.mem_write(stack-0x3000,bytes(0x3100));side_effects.clear()
 for address,value in [(0x4db67c,player),(0x4d8f58,0x3f800000),(obj+0x14,71),(obj+0xc0,area),(obj+0x70,w[6]),(obj+0xb0,w[7]),(obj+0xa4,0),(obj+0xa8,1),(obj+0x18,w[2]),(obj+0x1c,w[1]),(area+0x24,w[8]),(area+0x28,w[9]),(area+0x84,w[19]),(player+0x184b4,w[21])]:put(address,value)
 for address,value in [(obj+0x54,w[4]),(obj+0x58,w[5]),(obj+0x5c,w[32]),(target,w[10]),(target+4,w[11]),(target+8,w[33]),(rect,w[15]),(rect+4,w[16]),(stack,end),(stack+4,rect if w[14]else 0),(stack+8,w[13]),(stack+12,w[12]),(stack-36,w[17])]:put(address,value)
 m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,obj);m.reg_write(UC_X86_REG_EDX,target);m.reg_write(UC_X86_REG_MXCSR,0x1f80);m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff);m.emu_start(0x452700,end,count=1000000);assert m.reg_read(UC_X86_REG_EIP)==end
 actual=[get(obj+0xb0),get(area+0x24),get(player+0x184b4),m.reg_read(UC_X86_REG_EAX)];expected=[w[23],w[24],w[30],w[25]];results.append({'index':index,'frame':w[0],'matched':actual==expected,'native':actual,'bounded':expected,'scratchHex':hex(w[17]),'hasRectangle':bool(w[14])})
diff=[r for r in results if not r['matched']]
flt=lambda b:struct.unpack('<f',struct.pack('<I',b))[0]
protected=[];unexplained=[]
for row in diff:
 w=inputs[row['index']];native=row['native'];bounded=row['bounded'];prior=flt(w[7]);expectedPrior=min(530.,max(0.,prior)) if math.isfinite(prior)else 0.
 known=(not math.isfinite(flt(native[0])) and not math.isfinite(flt(native[1])) and all(math.isfinite(flt(x)) for x in bounded[:2]) and flt(bounded[0])==flt(bounded[1])==expectedPrior and native[2:]==bounded[2:])
 (protected if known else unexplained).append(row)
proof={'auditCompleted':True,'declaredProtectionOnly':not unexplained,'cases':len(results),'exactMatches':len(results)-len(diff),'allNativeFieldsIdentical':not diff,'protectedDifferences':protected,'unexplainedDifferences':unexplained,'instructionBytesPatched':0,'originalNativeBeamBody':True,'anmAndCookieBoundaryControlled':True,'hitLastFrameDeclaredOne':True,'comparedFields':['beamLength','areaLength','ordinaryHitCounter','returnDamage'],'actualCallerStackValidated':False,'nativeValuesFedBack':False,'inputSha256':hashlib.sha256(p.read_bytes()).hexdigest(),'originalExeSha256':hashlib.sha256(image.data).hexdigest(),'toolSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'completeGame':False}
output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof));raise SystemExit(0 if proof['declaredProtectionOnly']else 1)
