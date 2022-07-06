class DebuggerInst():
    def __init__(self):
        self.debug = None

    def log_dbg(self, contents = "\n"):
        if not self.debug:
            return

        print(contents)

    def toggle(self, value: bool):
        self.debug = value

Debugger = DebuggerInst()