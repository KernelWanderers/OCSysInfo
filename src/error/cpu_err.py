from sys import exit

def cpu_err(e):
    print("Something went wrong during 'CPU' discovery.")
    print(
        "This should not happen. Please open an issue at https://github.com/KernelWanderers/OCSysInfo/issues\n"
    )
    print(f"Error logs:\n\n{str(e)}")
    exit(1)
