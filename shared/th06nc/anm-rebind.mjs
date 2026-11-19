// Setter reset body 0x140001da0, followed by script publication and initial tick.
// Preserve fields the original setter does not clear, including position/binding.
export function rebindAnm(bank,id,state,options={}){
 if(state.byteLength!==288)throw Error('TH06nc ANM: rebind requires a complete VM view');
 const vm=bank.createVm(id,{...options,allowMissing:true}),v=new DataView(state.buffer,state.byteOffset,state.byteLength);
 const previousSprite=Number(v.getBigUint64(0x100,true));vm.boundBinding=previousSprite?bank.sprites.get(previousSprite-1):undefined;
 vm.state=state;vm.v=v;v.setUint16(0x38,id,true);
 for(const p of [0x2c,0x7c,0xac,0xa4,0x9c,0x84,0x70,0x68,0x5c,0x54,0x48,0x40,0x10c,0x114])v.setBigUint64(p,0n,true);
 v.setUint16(0x8c,0,true);v.setInt32(0xb8,0,true);
 for(const p of [0xe8,0xe4,0x78,0x64,0x50,0x3c])v.setFloat32(p,1,true);
 v.setUint32(0xec,0xffffffff,true);v.setUint32(0xc4,2,true);v.setInt32(0xb4,-999,true);
 vm.pointer(0xf0,vm.script?.offset??0);vm.pointer(0xf8,vm.script?.offset??0);
 if(vm.script)vm.tick();return vm;
}
