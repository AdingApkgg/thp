import {Day1ClearCpuSession} from './Day1ClearCpuSession.mjs';
export class Day1NoticeCpuSession extends Day1ClearCpuSession {
 async cpuSnapshot(frame){const s=await super.cpuSnapshot(frame),c=this.runtime,owner=c.title_notice_owner()>>>0;s.noticeOwner=owner;s.noticeSha256=owner?await this.sha(this.bytes(c.game_boot_region(owner,0x1b8),0x1b8).slice()):null;return s;}
}
