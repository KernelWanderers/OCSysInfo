import os

from src.info import AppInfo, clear_ansi


class DebuggerInst():
    def __init__(self):
        self.debug = None
        self.file  = os.path.join(
            AppInfo.root_dir,
            'ocsi_dbg_log.txt'
        )

    def log_dbg(self, contents = "\n"):
        if not self.debug:
            return
        
        if self.file:
            with open(self.file, 'a') as file:
                file.write(clear_ansi(contents) + "\n")
                file.close()

        print(contents)

    def toggle(self, value: bool):
        self.debug = value

Debugger = DebuggerInst()