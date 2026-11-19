// Title gameplay request 4dbc4..4dc35. The settings belong to the new run;
// live stocks are copied by 3aa0f..3aa29, power by 3aa98..3aaa8.
// Music teardown and the remaining gameplay initializer are separate owners.
// Native new-run owner 3aa49..3aa71 publishes origin plus width/height.
export const gameplayPlayerBounds=Object.freeze([8,16,368,416]);
export function gameplayStartSettings({mode=0,practice=0,difficulty=1,lives=2,bombs=3}={}){
 mode&=255;practice&=255;
 const fixedStocks=(difficulty|0)===4||practice!==0;
 return {lifeProtection:mode!==0,practice,spellPractice:false,
  defaultLives:fixedStocks||mode!==0?2:lives&255,
  defaultBombs:fixedStocks?3:bombs&255,
  replayPlayback:false,gameState:2,playerPower:mode!==0?8:0,continueState:(difficulty|0)>=4?4:0};
}

// Difficulty-indexed table 3084e0, read at new-run 3aed7..3af10 and
// playback-stage 3b15d..3b171. Ordinary stage advance preserves the rank.
export function initialGameplayRank(difficulty){
 if(!Number.isInteger(difficulty)||difficulty<0||difficulty>4)throw Error('TH06nc: invalid gameplay difficulty');
 return [20,32,32,32,18][difficulty];
}
