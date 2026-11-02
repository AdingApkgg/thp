"""Validate bounded x86 MSVC exception-type diagnostics using synthetic memory."""
from pathlib import Path
import argparse,ast,hashlib,json,struct
R=Path(__file__).resolve().parents[1];obs=R/'tools/th14-native-terminal-exception-observer-nov03.py';base=R/'tools/th14-native-terminal-marker-observer-nov03.py';sha=lambda b:hashlib.sha256(b).hexdigest();source=obs.read_text(encoding='utf8');original=base.read_text(encoding='utf8');A=ast.parse(source);B=ast.parse(original)
def funcs(tree,name):return [ast.dump(x,include_attributes=False) for x in ast.walk(tree) if isinstance(x,ast.Call) and isinstance(x.func,ast.Attribute) and x.func.attr==name]
for name in ['WriteProcessMemory','SuspendThread','ResumeThread','Wow64SetThreadContext']:assert funcs(A,name)==funcs(B,name)
def func(tree,name):return next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name==name)
assert ast.dump(func(A,'install'),include_attributes=False)==ast.dump(func(B,'install'),include_attributes=False)
def handler(tree,pc):
 return next(x for x in ast.walk(tree) if isinstance(x,ast.If) and isinstance(x.test,ast.Compare) and isinstance(x.test.left,ast.Name) and x.test.left.id=='pc' and len(x.test.comparators)==1 and isinstance(x.test.comparators[0],ast.Constant) and x.test.comparators[0].value==pc)
for pc in [0x45521b,0x4552cd]:assert ast.dump(handler(A,pc),include_attributes=False)==ast.dump(handler(B,pc),include_attributes=False)
node=func(A,'msvc32_exception_type');program=compile(ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])),str(obs),'exec');words={0x100c:0x2000,0x2000:1,0x2004:0x3000,0x3004:0x4000};name=[b'.PAVSynthetic@@\0'+bytes(112)];reads=[]
def u32(addr):reads.append(('u32',addr));return words[addr]
def read(addr,size):reads.append(('read',addr,size));assert addr==0x4008 and size==128;return name[0][:size]
ns=dict(u32=u32,read=read);exec(program,ns);decode=ns['msvc32_exception_type'];positive=decode([0x19930520,0x9000,0x1000]);assert positive['attempted'] and positive['typeName']=='.PAVSynthetic@@' and positive['typeDescriptor']==0x4000 and positive['catchableTypeCount']==1 and positive['readOnly'] and not positive['providedToEngine']
assert not decode([1,2,3,4])['attempted'];negative=0
for kind in ['null-info','zero-count','large-count','missing-catchable','unterminated-name','non-ascii']:
 words.update({0x100c:0x2000,0x2000:1,0x2004:0x3000,0x3004:0x4000});name[0]=b'.PAVSynthetic@@\0'+bytes(112);params=[0x19930520,0x9000,0x1000]
 if kind=='null-info':params[2]=0
 if kind=='zero-count':words[0x2000]=0
 if kind=='large-count':words[0x2000]=129
 if kind=='missing-catchable':words[0x2004]=0
 if kind=='unterminated-name':name[0]=b'A'*128
 if kind=='non-ascii':name[0]=b'\xff\0'+bytes(126)
 out=decode(params);assert out['attempted'] and out['typeName'] is None and 'decodeError' in out and out['readOnly'];negative+=1
result=dict(verifiedSyntheticMsvc32ExceptionTypeCapture=True,positiveCases=1,negativeCases=negative,unexpectedParameterCountSkipped=True,originalMarkerInstallAndHandlersAstUnchanged=True,processWriteAndSuspendCallAstsUnchanged=True,syntheticOnly=True,liveExceptionTypeObserved=False,originalExceptionCauseProved=False,debugExceptionsStillBlockStrictGate=True,completeGame=False,nativeEquivalent=False,observerSha256=sha(obs.read_bytes()),markerObserverSha256=sha(base.read_bytes()),verifierSha256=sha(Path(__file__).read_bytes()))
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');p.add_argument('--output',type=Path,default=R/'artifacts/th14/replay-candidates-second-nov03/msvc32-exception-type-unit.json');a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(R/'artifacts/th14') or out.is_relative_to(R/'docs/porting');data=(json.dumps(result,indent=2)+'\n').encode()
if a.check:assert out.read_bytes()==data
else:out.write_bytes(data)
print(json.dumps(result))
