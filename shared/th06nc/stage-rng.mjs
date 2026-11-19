// Stage initializer 3b171..3b189: snapshot seed, then reset the draw count.
// The replay loader may subsequently replace the seed with its stage header.
export function initializeStageRng(environment){
 environment.replaySeed=environment.rng.seed&65535;environment.rng.count=0;
}
