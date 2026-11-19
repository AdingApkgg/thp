import {advancePlayerOptions} from './player-options.mjs';
import {acceptPlayerFireInput,firePlayerShots} from './player-fire.mjs';
import {advancePlayerShots} from './player-shot-update.mjs';
import {advancePlayerBomb} from './player-bomb.mjs';
// Player owner update. Bomb callbacks use the same owner before life/motion.
export function tickPlayer(player,input,{previousInput=0,messageField=-1,bounds,freeze=false,...services}={}){
 if(freeze)return;
 const {v,environment={},anms}=player;
 for(let i=0;i<32;i++)v.setInt32(0x180+i*12,0,true);for(let i=0;i<16;i++)v.setInt32(0x7754+i*16,0,true);
 advancePlayerBomb(player,input,{previousInput,messageField,...services});
 player.advanceLife(services);
 if(player.state!==1&&player.state!==2){player.move(input,{bounds});advancePlayerOptions(player.bytes,{power:environment.playerPower??0});acceptPlayerFireInput(player,input,{messageField});}
 anms.get(0x78c8).tick();advancePlayerShots(player);
 if(v.getUint8(0x79f8)!==0){anms.get(0x9f38).tick();anms.get(0xa058).tick();}
 firePlayerShots(player,services);
}
