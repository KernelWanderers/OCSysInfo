import tensorflow as tf
from cpuinfo import get_cpu_info

devices = tf.config.list_physical_devices()
print(devices)


"""
Instance which extracts information about the system's CPU (SSSE3, SSE version, Codename, Generation, Model, etc.)
TODO: Refactor to use DeviceManager as parent instance.
"""
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

        print(self.model)

    def get_highest_sse(self):
        flags = self.info.get("flags")
        sse = list(set([flag.replace("_", ".") for flag in flags if "ssse" not in flag and "sse" in flag]))
        sse.sort(reverse=True)

        return sse[0].upper()

    def ssse_exists(self):
        flags = self.info.get("flags")
        return "ssse3" in flags

    def get_model_specs(self):
        return self.info.get("brand_raw")
