// Node transport adapter for the actual browser endpoint and CPU module.
import {parentPort,workerData} from 'node:worker_threads';
import {resolve} from 'node:path';
import {pathToFileURL} from 'node:url';
const home=resolve(workerData.build),{default:createModule}=await import(pathToFileURL(resolve(home,'archive-decoder.mjs')));
const {createArchiveDecodeEndpoint}=await import(pathToFileURL(resolve(home,'Th14ArchiveDecodeEndpoint.mjs')));
let corrupt=workerData.fault==='decoded-sht-version';
if(workerData.fault&&!corrupt)throw new Error('Unsupported test-only fault');
const factory=async()=>{
    const module=await createModule();
    if(corrupt){
        const read=module._decoder_read,decode=new TextDecoder();
        module._decoder_read=(pointer,length)=>{
            const name=decode.decode(module.HEAPU8.subarray(pointer,pointer+length)),result=read(pointer,length);
            // Explicit malformed decoded input, before the unchanged production
            // SHT parser. Neither the DAT input nor production code is modified.
            if(corrupt&&result&&name.endsWith('.sht')){module.HEAPU8[result]=0;corrupt=false;}
            return result;
        };
    }
    return module;
};
const accept=createArchiveDecodeEndpoint(factory,(message,transfer=[])=>parentPort.postMessage(message,transfer));
parentPort.on('message',accept);
