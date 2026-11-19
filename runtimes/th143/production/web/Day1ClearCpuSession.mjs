import {CompleteNaturalClearCpuSession} from './CompleteNaturalClearCpuSession.mjs';
export class Day1ClearCpuSession extends CompleteNaturalClearCpuSession {
 async initialize(progress){await super.initialize(progress);const c=this.runtime;if(typeof c.title_second_start_frame!=='function')throw Error('Title return runtime missing');this.runtime={...c,title_long_frame:c.title_second_start_frame};const t=BigInt(this.build.previewFileTime);c.title_clear_preview_time(Number(t&0xffffffffn),Number(t>>32n));}
 async cpuSnapshot(frame){const snapshot=await super.cpuSnapshot(frame);if(this.runtime.title_return_phase()||this.runtime.title_second_start_phase())snapshot.titleSha256=await this.sha(this.bytes(this.runtime.game_boot_region(0x6e040000,0xef78),0xef78).slice());return snapshot;}
}
