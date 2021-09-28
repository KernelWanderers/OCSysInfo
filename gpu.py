import subprocess
import os
import xml.etree.ElementTree as ET


class GPU:
    def __init__(self):
        self.data = []
        self.get_gpu_info_win()
        print(self.data)

    def get_gpu_info_win(self):
        """Obtains system information from Windows's dxdiag command."""
        if not os.path.exists("dxdiag.xml"):
            print(
                "==== PLEASE WAIT PATIENTLY WHILE THE SCRIPT RETRIEVES DATA ABOUT THIS SYSTEM ====")
            subprocess.run(["dxdiag", "/x", "dxdiag.xml"], shell=True)
        tree = ET.parse("dxdiag.xml")
        gpu_list = (tree.find("./DisplayDevices"))
        for gpu in gpu_list:
            data = {}
            data['model'] = gpu.findtext("CardName")
            data['vram'] = gpu.findtext("DedicatedMemory")
            dev_key = gpu.findtext("DeviceKey")
            keys = []

            for i in range(len(dev_key)):
                if dev_key[i:][0:3].upper() == 'VEN' or dev_key[i:][0:3].upper() == 'DEV':
                    keys.append(self.get_ven_dev_win(i, dev_key))

            data['vendor'] = keys[0].split("_")[1]
            data['device'] = keys[1].split("_")[1]

            if not any(data.get("model") in x.get("model") for x in self.data):
                self.data.append(data)

    def get_ven_dev_win(self, i, list):
        text = ""
        for j in range(8):
            text += list[i+j]

        return text


g = GPU()
