"""Combine source-read camera witnesses with relative script RNG restore order."""
from pathlib import Path
import argparse,hashlib,importlib.util,json
R=Path(__file__).resolve().parents[1];NAME='th14-compare-native-source-camera-rng-nov04.mjs'


def source():
 path=R/'tools/th14-prepare-source-read-camera-cursor-driver-nov04.py';spec=importlib.util.spec_from_file_location('parent_source',path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 text=m.source().decode().replace('\r\n','\n')
 def replace(old,new):
  nonlocal text
  assert text.count(old)==1,(old[:80],text.count(old));text=text.replace(old,new)
 replace("'vm-boundary-baseline']);","'vm-boundary-baseline','first-script-read-point']);")
 replace('let normalBoundary=null;', '''const firstScriptReadPoint=Number(options.get('first-script-read-point')??0);assert([0,1,2].includes(firstScriptReadPoint));
const firstScriptReadWindows=[],firstScriptReadSkipped=[];
const replayStoreEvents=stageEvents('replay-rng-store-events.jsonl');
for(let stage=2;stage<=maxStage;stage++){
 const stores=replayStoreEvents.filter(row=>row.stage===stage);
 assert.deepEqual(stores.map(row=>row.pc),[0x456115,0x456129,0x456133,0x456135]);
 const callback=stores[0].precedingPlayerCallbacks;assert(stores.every(row=>row.precedingPlayerCallbacks===callback));
 assert(callback>0&&callback<limit);
 const rng=stores.map(row=>{const bytes=Buffer.from(row.rngHex,'hex');return Array.from({length:4},(_,word)=>bytes.readUInt32LE(word*4));});
 const before=Array.from({length:32},(_,word)=>nativeRaw.readUInt32LE((callback-1)*128+word*4)),after=Array.from({length:32},(_,word)=>nativeRaw.readUInt32LE(callback*128+word*4));
 const delta=(after[22]-rng[2][1])>>>0;
 if(delta===0){firstScriptReadSkipped.push({stage,reason:'no completed script calls before next Player'});continue;}
 if(!rng.every(row=>row[1]===rng[0][1])||before[21]!==rng[0][0]||before[22]!==rng[0][1]||before[24]!==rng[0][3]){
  firstScriptReadSkipped.push({stage,reason:'first-read ordering cannot be inferred from these counters'});continue;
 }
 assert.equal(rng[0][3],rng[1][3]);assert.equal(rng[2][3],0);assert.deepEqual(rng[2],rng[3]);
 assert.equal(rng[1][0],rng[2][0]);assert(delta>0&&delta<10000);
 let seed=rng[2][0];for(let i=0;i<delta;i++){const mixed=((seed^0x9630)-0x6553)&65535;seed=((mixed<<2)|(mixed>>>14))&65535;}
 assert.equal(seed,after[21]);
 const previousNs=Number(times.readBigUInt64LE((callback-1)*8)),nextNs=Number(times.readBigUInt64LE(callback*8));
 const pumps=resourceEvents.filter(row=>row.event==='main-resource-pump'&&previousNs<row.hostMonotonicNs&&row.hostMonotonicNs<stores[0].hostMonotonicNs);
 assert(pumps.length);const pumpNs=pumps.at(-1).hostMonotonicNs,readyNs=stores[2].hostMonotonicNs;
 assert(previousNs<pumpNs&&pumpNs<readyNs&&readyNs<nextNs);
 assert.equal(phaseInputs.find(row=>row.stage===stage&&row.phase==='Initialize').readyNs,readyNs);
 if(firstScriptReadPoint<2)assert.equal(c.observed_first_script_read_window(stage,callback,baseNow+BigInt(pumpNs)-playerOrigin,baseNow+BigInt(readyNs)-playerOrigin,firstScriptReadPoint),1);
 firstScriptReadWindows.push({stage,callback,pumpNs,readyNs,completedScriptCallsAfterRestore:delta,nativeScriptCallsAtRestore:rng[2][1],nativeVisualCallsBeforeClear:rng[0][3],originalVmIdentityIsInput:false,originalRngValuesProvidedToEngine:false});
}
let normalBoundary=null;''')
 replace('report.sourceReadWindows=sourceReadWindows;', '''report.firstScriptReadPoint=firstScriptReadPoint;report.firstScriptReadWindows=firstScriptReadWindows;report.firstScriptReadSkipped=firstScriptReadSkipped;
report.firstScriptReadStates=firstScriptReadWindows.map(window=>({stage:window.stage,words:Array.from({length:12},(_,field)=>c.first_script_read_window_word(window.stage,field)>>>0)}));
for(const row of report.firstScriptReadStates){assert.equal(row.words[2],firstScriptReadPoint<2?1:0);assert.equal(row.words[3],0);}
report.sourceReadWindows=sourceReadWindows;''')
 return text.replace('\n','\r\n').encode()


if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');a=p.parse_args();raw=source();target=R/'tools'/NAME
 if a.check:assert target.read_bytes()==raw
 else:assert not target.exists();target.write_bytes(raw)
 print(json.dumps(dict(path=NAME,sha256=hashlib.sha256(raw).hexdigest(),originalVmIdentityIsInput=False,productionCoreChanged=False)))
