import{InteractivePersistentCpuSessionV122}from'./InteractivePersistentCpuSessionV122.mjs';
import{BrowserGlyphRasterV2}from'./BrowserGlyphRasterV2.mjs';
export class InteractivePersistentCpuSessionV123 extends InteractivePersistentCpuSessionV122{
 async initializeCpu(progress){this.browserGlyphRaster=new BrowserGlyphRasterV2();return super.initializeCpu(progress);}
}
