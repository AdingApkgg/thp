using System;
using System.Runtime.InteropServices;
public static class Th14MatrixWorker {
 [DllImport(@"C:\Windows\SysWOW64\d3dx9_43.dll",CallingConvention=CallingConvention.StdCall)]static extern IntPtr D3DXMatrixRotationX([Out] float[] output,float angle);
 [DllImport(@"C:\Windows\SysWOW64\d3dx9_43.dll",CallingConvention=CallingConvention.StdCall)]static extern IntPtr D3DXMatrixRotationY([Out] float[] output,float angle);
 [DllImport(@"C:\Windows\SysWOW64\d3dx9_43.dll",CallingConvention=CallingConvention.StdCall)]static extern IntPtr D3DXMatrixRotationZ([Out] float[] output,float angle);
 [DllImport(@"C:\Windows\SysWOW64\d3dx9_43.dll",CallingConvention=CallingConvention.StdCall)]static extern IntPtr D3DXMatrixMultiply([Out] float[] output,float[] a,float[] b);
 [DllImport("kernel32.dll",CharSet=CharSet.Ansi)]static extern IntPtr LoadLibrary(string name);
 [DllImport("kernel32.dll",CharSet=CharSet.Ansi)]static extern IntPtr GetProcAddress(IntPtr module,string name);
 public static void Main(){string line;while((line=Console.ReadLine())!=null){
  if(line=="INFO"){
   float[] a=new float[16],o=new float[16];D3DXMatrixMultiply(o,a,a);
   IntPtr module=LoadLibrary(@"C:\Windows\SysWOW64\d3dx9_43.dll"),entry=GetProcAddress(module,"D3DXMatrixMultiply");
   if(Marshal.ReadByte(entry)!=255||Marshal.ReadByte(entry,1)!=37)throw new Exception("Unexpected D3DX dispatch");
   IntPtr target=Marshal.ReadIntPtr(new IntPtr(Marshal.ReadInt32(entry,2)));Console.WriteLine("INFO,"+(target.ToInt32()-module.ToInt32()).ToString());continue;
  }
  string[] f=line.Split(',');float[] input=new float[f.Length-1];for(int i=0;i<input.Length;i++)input[i]=BitConverter.ToSingle(BitConverter.GetBytes(uint.Parse(f[i+1])),0);float[] output=new float[16];
  if(f[0]=="M"&&input.Length==32){float[] a=new float[16],b=new float[16];Array.Copy(input,0,a,0,16);Array.Copy(input,16,b,0,16);D3DXMatrixMultiply(output,a,b);}
  else if(input.Length==1){if(f[0]=="X")D3DXMatrixRotationX(output,input[0]);else if(f[0]=="Y")D3DXMatrixRotationY(output,input[0]);else if(f[0]=="Z")D3DXMatrixRotationZ(output,input[0]);else throw new ArgumentException("Unknown matrix operation");}
  else throw new ArgumentException("Invalid matrix input");
  string[] result=new string[16];for(int i=0;i<16;i++)result[i]=BitConverter.ToUInt32(BitConverter.GetBytes(output[i]),0).ToString();Console.WriteLine(String.Join(",",result));
 }}
}
