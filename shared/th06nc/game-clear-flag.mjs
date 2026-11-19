// Global 4f27b3 is shared by the message task gate and result clear marker.
export function bindGameClearFlag(environment){
 Object.defineProperty(environment,'cleared',{enumerable:true,configurable:true,get(){return Boolean(this.messageTaskSuspended);},set(value){this.messageTaskSuspended=Boolean(value);}});
 return environment;
}
// Ending initializer 2c914, before archive/script loading and CLRD updates.
export function markEndingGameClear(environment){environment.messageTaskSuspended=true;}
