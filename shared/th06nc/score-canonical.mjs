import {initializeScoreHeader} from './score-header.mjs';
import {serializeHighScoreTables} from './score-tables.mjs';
import {serializeScoreStatChunks} from './score-stat-chunks.mjs';
import {encodeScoreFile} from './score-file.mjs';
// Complete encoded output from explicit native writer inputs. Gameplay/global
// owners, dirty gating and filesystem lifecycle are supplied by the caller.
// GameSave uses this writer with its shared ScoreStats owner and live RNG.
export function encodeCanonicalScore({rng,tables,stats,marker=new Uint8Array(12),allocation}){
 if(!(marker instanceof Uint8Array)||marker.length!==12)throw Error('TH06nc score: invalid game marker');
 const header=initializeScoreHeader(rng,allocation),view=new DataView(marker.buffer,marker.byteOffset,marker.byteLength);
 view.setUint32(0,0x4b364854,true);view.setUint32(4,0xc000c,true);marker[8]=21;
 return encodeScoreFile({header,records:[marker,...serializeHighScoreTables(tables),...serializeScoreStatChunks(stats)]});
}
