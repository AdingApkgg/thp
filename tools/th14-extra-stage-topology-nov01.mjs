import assert from 'node:assert/strict';

// Extra starts at stage7. It never needs the stage2..6 handoff observations.
// Camera, HUD, combat, input, RNG and VM comparisons remain mandatory.
export function requireSingleExtra(raw,count,difficulty,initialStage){
  assert.equal(difficulty,4,'This comparison is exclusively for Extra');
  assert.equal(initialStage,7,'Extra must start at stage7');
  assert(Number.isSafeInteger(count)&&count>0);
  assert(raw.length>=count*128,'Truncated Extra state payload');
  for(let i=0;i<count;i++){
    assert.equal(raw.readUInt32LE(i*128+29*4),4,'Extra difficulty changed');
    assert.equal(raw.readUInt32LE(i*128+30*4),7,'Extra payload contains a stage transition');
  }
  return true;
}
