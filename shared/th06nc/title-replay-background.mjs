export const titleReplayBackgroundAsset=Object.freeze({archive:'th06TL.dat',file:'select00d.anm',slot:70,base:0x7da});
// Five-layer background initialized by 75810; draw 75a50 and title front tail.
export class TitleReplayBackground {
 constructor(bank,resource){bank.load(resource,0x7da,{slot:70});this.vms=Array.from({length:5},(_,i)=>{const vm=bank.createVm(0x7da+i);vm.tick();return vm;});}
 tick(){for(const vm of this.vms)vm.tick();}
 close(){for(const i of [2,4,3])this.vms[i].interrupt(2);}
 draw(draw){for(const [i,path]of [[0,'flat'],[2,'rotated'],[4,'rotated'],[3,'flat']])draw(this.vms[i],{snap:true,offset:0x15ab0+i*288,path});}
 drawFront(draw){draw(this.vms[1],{snap:true,offset:0x15bd0,path:'flat'});}
}
