const F=Math.fround;
export const scorePopupAssetPlan=()=>({archive:'th06IN.dat',file:'ascii.anm',slot:1,base:0});
// Numeric font VM initialized by 9790. This VM binds sprites without running
// scripts, and all popup digits share it, including the Power Up caption.
export function createScorePopupFont(anmBank){
 const vm=anmBank.createVm(0,{allowMissing:true});vm.state.fill(0);for(const p of [0xe8,0xe4,0x78,0x64,0x50,0x3c])vm.v.setFloat32(p,1,true);vm.v.setUint32(0xec,0xffffffff,true);vm.v.setUint32(0xc4,3,true);vm.v.setInt32(0xb4,-1,true);vm.bindSprite(0);vm.v.setFloat32(0xd0,F(.1),true);return vm;
}
// Full numeric popup draw 92a0. Sprite pointer changes directly, preserving UV
// matrix state; caption width is restored to 1/32 after its draw as in native.
export function drawScorePopups(pool,font,draw,{anmBank,worldOffset=[0,0]}={}){
 if(!anmBank)throw Error('TH06nc: score popup drawing needs ANM bank');const p=new DataView(pool.storage.buffer,pool.storage.byteOffset,pool.storage.byteLength),a=font.v;
 for(let slot=0;slot<515;slot++){
  const base=slot*40;if(!p.getUint8(base+0x1c))continue;const count=p.getUint8(base+0xc);a.setFloat32(0xc8,F(p.getFloat32(base+0x10,true)-F(count*4)),true);a.setUint32(0xcc,p.getUint32(base+0x14,true),true);a.setUint32(0xec,p.getUint32(base+8,true),true);
  for(let digit=count-1;digit>=0;digit--){
   const glyph=p.getUint8(base+0x1d+digit);font.pointer(0x100,glyph+1);font.boundBinding=anmBank.sprites.get(glyph);
   if(glyph>=10){a.setFloat32(0x3c,F(.1875),true);a.setFloat32(0x50,F(.03125),true);}
   const x=a.getFloat32(0xc8,true),y=a.getFloat32(0xcc,true);a.setFloat32(0xc8,F(x+F(worldOffset[0])),true);a.setFloat32(0xcc,F(y+F(worldOffset[1])),true);
   try{draw(font,{snap:true,space:'screen',part:'score-popup',slot,digit});}finally{a.setFloat32(0xc8,x,true);a.setFloat32(0xcc,y,true);}
   if(glyph>=10){a.setFloat32(0x3c,F(.03125),true);a.setFloat32(0x50,F(.03125),true);}a.setFloat32(0xc8,F(a.getFloat32(0xc8,true)+F(8)),true);
  }
 }
}
