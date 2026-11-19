const F=Math.fround;
// Localization + getline feed the sixteen-row publication tail 59490..59598.
// Empty rows clear drawing bit1 while retaining the original crop/texture.
export function publishMusicRoomDescription(owner,key,{initial=false,localization={},publishText}={}){
 const text=key===null?'':localization[key]??key,lines=String(text).split('\n');if(lines.at(-1)==='')lines.pop();
 for(let i=0;i<16;i++){
  const offset=0x2b10+i*288,vm=initial?owner.sprite(offset,0x737+i):owner.vm(offset),v=vm.v,line=lines[i];
  if(line){v.setUint32(0xc4,v.getUint32(0xc4,true)|2,true);publishText(vm,{offset,text:line,colors:[0xffffff,0,0x10101,0x50505]});}
  else v.setUint32(0xc4,v.getUint32(0xc4,true)&~2,true);
  v.setFloat32(0xc8,96,true);v.setFloat32(0xcc,F(F(i*16)+F(305)),true);v.setFloat32(0xd0,0,true);v.setUint32(0xc4,(v.getUint32(0xc4,true)&~0x300)|0x400,true);
 }
}
