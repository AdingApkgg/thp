import {Day1NoticeCpuSession} from './Day1NoticeCpuSession.mjs';
export class CampaignCpuSession extends Day1NoticeCpuSession {
 async cpuSnapshot(frame){const s=await super.cpuSnapshot(frame);s.titlePhase=this.runtime.title_return_phase();s.previewWorkerDone=this.runtime.title_second_start_preview_done();return s;}
}
