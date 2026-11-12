using System;
using System.Runtime.InteropServices;
public static class NormalizeWorker {
 [DllImport(@"C:\Windows\SysWOW64\d3dx9_43.dll",CallingConvention=CallingConvention.StdCall)]static extern IntPtr D3DXVec3Normalize([Out] float[] output,float[] input);
 public static void Main(){string line;while((line=Console.ReadLine())!=null){
  string[] f=line.Split(',');if(f.Length!=3)throw new ArgumentException("Expected three binary32 words");
  float[] input=new float[3],output=new float[3];
  for(int i=0;i<3;++i)input[i]=BitConverter.ToSingle(BitConverter.GetBytes(uint.Parse(f[i])),0);
  D3DXVec3Normalize(output,input);string[] r=new string[3];
  for(int i=0;i<3;++i)r[i]=BitConverter.ToUInt32(BitConverter.GetBytes(output[i]),0).ToString();
  Console.WriteLine(String.Join(",",r));
 }}
}
