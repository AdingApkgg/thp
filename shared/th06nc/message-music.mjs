import {createMusicState,stopMessageMusic} from './music-state.mjs';
// Music command 3f49d..3f6cc: title VM/text, transport request and
// optional extra-stage HUD restoration. Transport is owned by audio manager.
export function applyMessageMusic(state,index,{publishText,localization=null,musicTracks,playMusic,stopMusic,releaseMusic}={}){
 if(index<0){stopMessageMusic(state.environment.musicState??=createMusicState(),{stopMusic,releaseMusic});return;}const track=musicTracks?.[index];if(!track||!publishText||!playMusic)throw Error('TH06nc message: music metadata/text/audio service missing');
 state.rebind(0xa80,0x730);const {v}=state;v.setUint16(0xb88,0x1010,true);const key=track.titleKey;publishText({offset:0xa80,key,text:localization?.[key]??key,colors:[0xe0ffff,0,0x10101,0x40202]});playMusic({file:track.file});
 if(v.getUint8(0x716)){v.setUint8(0x716,0);state.vm(0x28e0).bindSprite(0x647);v.setUint16(0x296a,2,true);v.setUint16(0x50a,1,true);}
}
