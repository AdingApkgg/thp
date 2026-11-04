using System;
using System.Runtime.InteropServices;
public static class Th14PerspectiveD3dx {
 [DllImport(@"C:\Windows\SysWOW64\d3dx9_43.dll",CallingConvention=CallingConvention.StdCall)] static extern IntPtr D3DXMatrixLookAtLH([In,Out] float[] output,[In] float[] eye,[In] float[] target,[In] float[] up);
 [DllImport(@"C:\Windows\SysWOW64\d3dx9_43.dll",CallingConvention=CallingConvention.StdCall)] static extern IntPtr D3DXMatrixPerspectiveFovLH([In,Out] float[] output,float fov,float aspect,float nearPlane,float farPlane);
 [DllImport(@"C:\Windows\SysWOW64\d3dx9_43.dll",CallingConvention=CallingConvention.StdCall)] static extern IntPtr D3DXVec3Normalize([In,Out] float[] output,[In] float[] input);
 [DllImport("msvcrt.dll",CallingConvention=CallingConvention.Cdecl)] static extern uint _controlfp(uint value,uint mask);
 static float[] Part(float[] input,int start){return new float[]{input[start],input[start+1],input[start+2]};}
 public static void Main(){
  _controlfp(0,0x30300);string line;
  while((line=Console.ReadLine())!=null){
   if(line=="INFO"){Console.WriteLine("INFO,"+_controlfp(0,0));continue;}
   string[] words=line.Split(',');float[] input=new float[words.Length-1];
   for(int i=0;i<input.Length;i++)input[i]=BitConverter.ToSingle(BitConverter.GetBytes(uint.Parse(words[i+1])),0);
   float[] output=new float[words[0]=="N"?3:16];
   if(words[0]=="L"&&input.Length==9)D3DXMatrixLookAtLH(output,Part(input,0),Part(input,3),Part(input,6));
   else if(words[0]=="P"&&input.Length==4)D3DXMatrixPerspectiveFovLH(output,input[0],input[1],input[2],input[3]);
   else if(words[0]=="N"&&input.Length==3){D3DXVec3Normalize(input,input);output=input;}
   else throw new ArgumentException("Invalid D3DX component request");
   string[] result=new string[output.Length];for(int i=0;i<output.Length;i++)result[i]=BitConverter.ToUInt32(BitConverter.GetBytes(output[i]),0).ToString();
   Console.WriteLine(string.Join(",",result));
  }
 }
}
