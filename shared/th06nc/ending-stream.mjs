// Native 2b6e0: atoi on the current NUL token, then skip its terminator and
// every following NUL. Native memory beyond the allocation is not modeled.
export function readEndingInteger(bytes,offset){
 if(!(bytes instanceof Uint8Array)||!Number.isInteger(offset)||offset<0||offset>=bytes.length)throw Error('TH06nc ending: invalid cursor');
 let end=offset;while(end<bytes.length&&bytes[end]!==0)end++;if(end===bytes.length)throw Error('TH06nc ending: unterminated integer');
 let p=offset;while(p<end&&([9,10,11,12,13,32].includes(bytes[p])))p++;let sign=1n;if(bytes[p]===43||bytes[p]===45){if(bytes[p]===45)sign=-1n;p++;}let value=0n;while(p<end&&bytes[p]>=48&&bytes[p]<=57){value=value*10n+BigInt(bytes[p]-48);p++;}value*=sign;if(value>2147483647n)value=2147483647n;if(value< -2147483648n)value= -2147483648n;
 let next=end+1;while(next<bytes.length&&bytes[next]===0)next++;if(next===bytes.length)throw Error('TH06nc ending: cursor beyond stream');
 return {value:Number(value),next};
}
