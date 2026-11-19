// Original music globals 509660..509690 and request flag c21c0c.
export function createMusicState(){return {handle:-1,playing:false,fading:false,fadeStart:0,fadeFrame:0,pendingValue:0,requestActive:false};}
export function stopMessageMusic(music,{stopMusic=null,releaseMusic=null}={}){
 if(music.handle!==-1){if(!stopMusic||!releaseMusic)throw Error('TH06nc music: stop/release transport service missing');stopMusic({handle:music.handle,mode:0});releaseMusic({handle:music.handle});music.handle=-1;music.playing=false;music.fading=false;}
 music.pendingValue=0;music.requestActive=false;
}
export function fadeMessageMusic(music){music.requestActive=false;if(music.playing){music.fading=true;music.fadeStart=240;music.fadeFrame=240;}}
