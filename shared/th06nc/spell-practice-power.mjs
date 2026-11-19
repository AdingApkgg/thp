// Static initializer 1780..188a publishes nine ID/Power pairs. Gameplay's
// 3b018..3b0cb lookup uses a uint8 ID and defaults to full Power for other IDs.
const initialPowers=Object.freeze([32,32,64,64,64,64,64,64,64]);
export function spellPracticeStartingPower(id){return initialPowers[id&255]??128;}
