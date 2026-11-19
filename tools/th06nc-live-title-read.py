"""Read-only title resource observation in the isolated original process."""
import ctypes,json,struct,sys
from ctypes import wintypes
pid=int(sys.argv[1]);kernel=ctypes.WinDLL('kernel32',use_last_error=True);psapi=ctypes.WinDLL('psapi',use_last_error=True)
kernel.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD];kernel.OpenProcess.restype=wintypes.HANDLE
kernel.ReadProcessMemory.argtypes=[wintypes.HANDLE,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_size_t,ctypes.POINTER(ctypes.c_size_t)]
psapi.EnumProcessModules.argtypes=[wintypes.HANDLE,ctypes.c_void_p,wintypes.DWORD,ctypes.POINTER(wintypes.DWORD)]
psapi.GetModuleFileNameExW.argtypes=[wintypes.HANDLE,ctypes.c_void_p,wintypes.LPWSTR,wintypes.DWORD]
handle=kernel.OpenProcess(0x410,False,pid);assert handle
modules=(ctypes.c_void_p*1024)();needed=wintypes.DWORD();assert psapi.EnumProcessModules(handle,modules,ctypes.sizeof(modules),ctypes.byref(needed))
base=None
for module in modules[:needed.value//ctypes.sizeof(ctypes.c_void_p)]:
 name=ctypes.create_unicode_buffer(32768);psapi.GetModuleFileNameExW(handle,module,name,len(name))
 if name.value.lower().endswith('native-observation-20261119\\th06nc.exe'):base=module;break
assert base

def read(address,length):
 result=ctypes.create_string_buffer(length);count=ctypes.c_size_t();assert kernel.ReadProcessMemory(handle,address,result,length,ctypes.byref(count)),hex(address);assert count.value==length;return result.raw
u64=lambda p:struct.unpack('<Q',read(p,8))[0]
u32=lambda p:struct.unpack('<I',read(p,4))[0]
owner=base+0xc07240;manager=u64(base+0xa6e9b0);result={'base':hex(base),'titleState':u32(owner+0x168b0),'backgroundEnabled':read(owner+0x16830,1)[0],'configOptions':list(read(base+0xc21da4+16,10)),'environment':list(read(base+0xc21dfc,12)),'textureHandles':{str(i):struct.unpack('<ii',read(manager+0x20620+i*8,8))for i in [24,25,26,1326]},'resources':[],'vms':[]}
for slot in [0x18,0x19,0x1a]:
 asset=u64(manager+8+slot*8)
 if not asset:continue
 nameOffset=u32(asset+28);name=read(asset+nameOffset,100).split(b'\0')[0].decode('utf-8','replace');result['resources'].append({'slot':slot,'textureName':name,'width':u32(asset+12),'height':u32(asset+16)})
for offset in [0x15990,0x16170,0x16290,0x163b0,0x164d0,0x165f0]:
 vm=owner+offset;sprite=u64(vm+0x100);result['vms'].append({'offset':hex(offset),'scriptId':struct.unpack('<H',read(vm+0x38,2))[0],'color':hex(u32(vm+0xec)),'spriteIndex':(sprite-manager-0x608)//64 if sprite else None,'textureIndex':u32(sprite+0x24)if sprite else None})
print(json.dumps(result));kernel.CloseHandle.argtypes=[wintypes.HANDLE];kernel.CloseHandle(handle)
