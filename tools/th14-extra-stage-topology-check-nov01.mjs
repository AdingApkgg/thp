import assert from 'node:assert/strict';
import{readFileSync,writeFileSync,existsSync}from'node:fs';
import{createHash}from'node:crypto';
import{requireSingleExtra}from'./th14-extra-stage-topology-nov01.mjs';
import{resolve,relative,isAbsolute}from'node:path';import{pathToFileURL}from'node:url';
const root=resolve(import.meta.dirname,'..');const at=process.argv.indexOf('--output');assert(at===2&&process.argv.length===4);const output=resolve(root,process.argv[3]);const scope=relative(resolve(root,'artifacts/th14'),output);assert(scope&&!scope.startsWith('..')&&!isAbsolute(scope));
const original=pathToFileURL(resolve(root,'artifacts/th14/retail-reimua-extra-full-hardware-oct24')+'/');
const raw=readFileSync(new URL('selected-state.u32',original));
assert.equal(raw.length,38403*128);
assert(requireSingleExtra(raw,38403,4,7));
let rejected=0;
for(const[frames,difficulty,stage,data]of[[38403,3,7,raw],[38403,4,1,raw],[0,4,7,raw],[38404,4,7,raw]]){
  assert.throws(()=>requireSingleExtra(data,frames,difficulty,stage));++rejected;
}
const changed=Buffer.from(raw);changed.writeUInt32LE(6,20000*128+30*4);
assert.throws(()=>requireSingleExtra(changed,38403,4,7));++rejected;
const missing=['world-camera.raw','hud-score.u32','combat-pool-index.json'].filter(name=>!existsSync(new URL(name,original)));
assert.equal(missing.length,3);
const report={oldExtraRowsActuallyChecked:38403,topologyOnlyPositiveChecks:1,malformedControlsRejected:rejected,oldPayloadSha256:createHash('sha256').update(raw).digest('hex'),missingMandatoryModernObservations:missing,oldRecordAcceptedAsCurrentCampaign:false,newNativeCampaignPending:false,completeGame:false,nativeEquivalent:false};
writeFileSync(output,JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(report));
