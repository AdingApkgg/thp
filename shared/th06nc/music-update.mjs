// Global owner tick 79c84..79d26, before scene input/update.
export function advanceMusicFade(music,{volume=10,setVolume,muteMusic,stopMusic,releaseMusic}={}){
 if(music.handle===-1||!music.fading)return;
 // Existing state names follow the message-command fixture: fadeStart is
 // address 509660 (the countdown), fadeFrame is 509664 (the divisor).
 music.fadeStart=(music.fadeStart-1)|0;
 if(music.fadeStart<=0){
  if(!stopMusic||!releaseMusic)throw Error('TH06nc music: fade transport missing');
  music.fading=false;stopMusic({handle:music.handle,mode:0});releaseMusic({handle:music.handle});music.handle=-1;music.playing=false;music.pendingValue=0;return;
 }
 if(!(volume&255)){if(!muteMusic)throw Error('TH06nc music: mute transport missing');muteMusic({handle:music.handle,value:0});return;}
 if(!setVolume||!music.fadeFrame)throw Error('TH06nc music: invalid fade transport/duration');
 setVolume({handle:music.handle,value:2300+(volume&255)*300+Math.trunc(Math.imul(music.fadeStart,5000)/music.fadeFrame)});
}
