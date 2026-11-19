// Native7bb80: cfg name is8 bytes; display sanitizes printable ASCII and
// pads the first NUL and remainder with spaces. Returned ninth byte is NUL.
export function readConfigName(config){
 if(config.length!==44)throw Error('TH06nc config: invalid raw span');
 const name=new Uint8Array(9);let ended=false;
 for(let i=0;i<8;i++){const c=config[32+i];ended||=c===0;name[i]=ended||c<32||c>126?32:c;}
 return name;
}
// Native7bc00 clears9 bytes, then strncpy(...,8). File allocation/queue is
// a platform service; caller persists the complete44-byte configuration.
export function writeConfigName(config,input=null){
 if(config.length!==44)throw Error('TH06nc config: invalid raw span');
 config.fill(0,32,41);if(input===null)return;
 for(let i=0;i<8&&i<input.length&&input[i]!==0;i++)config[32+i]=input[i];
}
