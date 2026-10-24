using System;
using System.Runtime.InteropServices;
public static class Th14D3dxNormalizeWorker {
    [StructLayout(LayoutKind.Sequential)] public struct Vector3 { public float x,y,z; }
    [DllImport(@"C:\Windows\SysWOW64\d3dx9_43.dll", CallingConvention=CallingConvention.StdCall)]
    static extern IntPtr D3DXVec3Normalize(ref Vector3 output,ref Vector3 input);
    static float Real(string s) { return BitConverter.ToSingle(BitConverter.GetBytes(uint.Parse(s)),0); }
    static uint Word(float f) { return BitConverter.ToUInt32(BitConverter.GetBytes(f),0); }
    public static void Main() {
        string line;
        while((line=Console.ReadLine())!=null) {
            string[] words=line.Split(',');if(words.Length!=3)throw new ArgumentException("Expected three float words");
            Vector3 input=new Vector3{x=Real(words[0]),y=Real(words[1]),z=Real(words[2])},output=new Vector3();
            D3DXVec3Normalize(ref output,ref input);
            Console.WriteLine(Word(output.x)+","+Word(output.y)+","+Word(output.z));
        }
    }
}
