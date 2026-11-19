import {createScoreFile,decodeScoreFile,encodeScoreFile,scoreChunkTag} from './score-file.mjs';
import {loadHighScoreTables,serializeHighScoreTables,highScoreFields} from './score-tables.mjs';
// Persistence composition. HSCR uses the native table serializer; unrelated
// chunks retain their bytes until their complete owners are implemented.
// This is not the full native canonical serializer for CLRD/CATK/MUSC/etc.
export class ScoreSave {
 constructor(input=null){this.file=input?decodeScoreFile(input):createScoreFile();this.tables=loadHighScoreTables(this.file.records);}
 snapshot(){return encodeScoreFile({...this.file,records:[...this.file.records.filter(r=>scoreChunkTag(r)!=='HSCR'),...serializeHighScoreTables(this.tables)]});}
 highScore(mode,difficulty,profile){const first=this.tables.get(`${mode}/${difficulty}/${profile}`)?.[0];return first?highScoreFields(first).score:1000000n;}
 records(){return serializeHighScoreTables(this.tables).map(r=>{const x=highScoreFields(r);return {...x,score:String(x.score)};});}
}
