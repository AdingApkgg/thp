"""Separate native text inputs that are representable by actual FontDevice delivery.

Does not modify the historical scratch oracle or its reports.
"""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
source=(ROOT/'tools/th14-text-raster-native.py').read_text()
source=source.replace("output=ROOT/'artifacts/th14/text-raster-native'","output=ROOT/'artifacts/th14/font-device-raster-native'")
source=source.replace("outline=(0x654321,0,0x192633,0x778899,0x741999,0,0xffffff,0x5f12c4)[profile]","outline=0")
source=source.replace("spacing=(0,0,0,12,19,0,0,11)[profile]","spacing=(0,0,0,12,20,0,0,12)[profile]")
source=source.replace("'artifacts/th14/text-raster-native/'+name","'artifacts/th14/font-device-raster-native/'+name").replace("ROOT/'artifacts/th14/text-raster-native.json'","ROOT/'artifacts/th14/font-device-raster-native.json'")
(ROOT/'tools/th14-font-device-raster-native.py').write_text(source,encoding='utf8')
gpu=(ROOT/'tools/th14-gpu-text-native.py').read_text().replace("OUT=ROOT/'artifacts/th14/gpu-text'","OUT=ROOT/'artifacts/th14/font-device-gpu'").replace("ROOT/'artifacts/th14/text-raster-native.json'","ROOT/'artifacts/th14/font-device-raster-native.json'")
(ROOT/'tools/th14-font-device-gpu-native.py').write_text(gpu,encoding='utf8')
prepare=(ROOT/'tools/th14-gpu-text-prepare.py').read_text().replace("'artifacts/th14/gpu-text'","'artifacts/th14/font-device-gpu'").replace('th14-gpu-text-data.hpp','th14-font-device-gpu-data.hpp')
(ROOT/'tools/th14-font-device-gpu-data-prepare.py').write_text(prepare,encoding='utf8')
print('Prepared isolated native FontDevice delivery inputs and D3DX/GPU oracle')
