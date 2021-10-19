//
// Simple utility function to return
// the value of the EAX register after running
// the CPUID instruction.
// 
// NOTE: this only works on x86 architectures.
// CREDITS: https://github.com/Penagwin/asm-cpuid/blob/master/asm-cpuid.cc
//
// OCSysInfo does not attempt to claim ownership of this program.
// All the rights go to the rightful owners.
//
extern "C" int EAX()
{
    int n[5] = {};
    int i, val;

    for (i = 0; i < 5; i++)
    {
        __asm__("cpuid;"
                :"=a"(val)
                :"0"(i)
                :"%ebx", "%ecx", "%edx");
        
        n[i] = val;
    }

    return n[1];
}