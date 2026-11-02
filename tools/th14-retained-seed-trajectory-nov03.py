"""Test whether retained seed words share an original RNG trajectory; no race order is inferred."""
from pathlib import Path
import hashlib,importlib,json,struct,sys
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32
from unicorn.x86_const import UC_X86_REG_ESP,UC_X86_REG_ECX,UC_X86_REG_EIP
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/frame-rng-scope-nov02/retained-stack-context';sys.path.insert(0,str(R/'tools'));sha=lambda b:hashlib.sha256(b).hexdigest()
image,*_=importlib.import_module('th-anm-handlers').handlers(14);assert sha(image.data)=='f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
m=Uc(UC_ARCH_X86,UC_MODE_32)
for _,address,size,raw,length in image.sections:
 first=address&~4095;m.mem_map(first,((address+size+4095)&~4095)-first);m.mem_write(address,image.data[raw:raw+length])
base,stack,rng=0x70000000,0x7000f000,0x4db508;m.mem_map(base,0x10000)
# This finite calculation disables original optional locking. Original RNG instructions are unchanged.
m.mem_write(0x4f5815,b'\0');m.mem_write(0x4f5812,b'\0');m.mem_write(rng,struct.pack('<HHI',18535,0,0));words=[]
for i in range(11):
 m.mem_write(stack,struct.pack('<I',base));m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,rng);m.emu_start(0x403310,base,count=500);assert m.reg_read(UC_X86_REG_EIP)==base
 seed,_,calls=struct.unpack('<HHI',bytes(m.mem_read(rng,8)));assert calls==2*(i+1);words.append(seed)
native_path=R/'artifacts/th14/reimu-controller-z-live-context-nov01/native/report.json';native=json.loads(native_path.read_bytes());event=next(x for x in native['transitionEvents'] if x['event']=='replay-seeds-restored-before-globals-copy' and x['stage']==3);at_event=struct.unpack_from('<H',bytes.fromhex(event['rngHex']))[0]
base_report=json.loads((R/'artifacts/th14/frame-rng-scope-nov02/counter-retained36826/model/report.json').read_bytes());exp=json.loads((R/'artifacts/th14/frame-rng-scope-nov02/retained-actor-experiment/model/report.json').read_bytes());assert event['restoredReplaySeed']==18535 and at_event==words[3]==10562 and exp['firstDifference']['portable']==words[6]==17185 and base_report['firstDifference']['native']==words[10]==40379
result={'passed':True,'originalNext32Executed':11,'trajectorySeeds':words,'restoredReplaySeed':18535,'globalSeedAtWorkerPostStoreEvent':at_event,'diagnosticPortableFirstDifferenceSeed':exp['firstDifference']['portable'],'originalPlayerFirstDifferenceSeed':base_report['firstDifference']['native'],'matchingStepCounts':{'eventSeed':4,'portableSeed':7,'originalPlayerSeed':11},'interpretation':'These numeric states fit one original RNG trajectory. The retained report did not observe every intervening seed write or their cross-thread total order; it does not prove that these were the actual calls or when they occurred.','actualHistoricalCallCountsOrThreadOrderProved':False,'nativeValuesProvidedToEngine':False,'productionChanged':False,'completeGame':False,'nativeEquivalent':False,'nativeReportSha256':sha(native_path.read_bytes()),'toolSha256':sha(Path(__file__).read_bytes())}
(H/'seed-trajectory.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='interpretation'}))
