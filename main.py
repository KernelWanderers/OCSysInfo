from cpuinfo import get_cpu_info


class CPU:
    """Instance for obtaining 'basic' information about the current system's CPU."""
    def __init__(self):
        self.url = "https://productapi.intel.com/intel-product-catalogue-service/reference"
        self.info = get_cpu_info()
        self.model = self.get_model_specs()
        self.sse = self.get_highest_sse()
        self.ssse = self.ssse_exists()
        self.does_macos_work = True
        self.initial_macos_support = ""
        self.final_macos_support = ""

    def get_highest_sse(self):
        flags = self.info.get("flags")
        sse = [flag for flag in flags if "_" not in flag and "ssse" not in flag and "sse" in flag]
        sse.sort(reverse=True)

        return sse[0].upper()

    def ssse_exists(self):
        flags = self.info.get("flags")
        return "ssse3" in flags

    def get_model_specs(self):
        return self.info.get("brand_raw")


cpu_class = CPU()
print(cpu_class.ssse_exists())
print(cpu_class.get_highest_sse())
print(cpu_class.get_model_specs())
