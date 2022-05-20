import logging
import os
from logging.handlers import RotatingFileHandler
from src.info import root_dir

class Logger:
    """
    Instance responsible for properly handling,
    formatting and logging information about the
    application's state.
    """

    def __init__(self):
        # Basic formats.
        self.format = "%(asctime)s | {} | %(levelname)s: %(message)s"
        self.date = "%m/%d/%Y %I:%M:%S %p"

        # Adding the base log handlers.
        self.handler = logging.getLogger()
        self.rotating = RotatingFileHandler("ocsysinfo.log", mode="a", maxBytes=2 ** 13)

        # Add the RotatingFileHandler to the default logger.
        self.handler.addHandler(self.rotating)
        self.rotating.setFormatter(
            logging.Formatter(
                self.format.format(os.path.basename(__file__)), datefmt=self.date
            )
        )

    def handle_file(self, file="UNKNOWN"):
        if file == "UNKNOWN":
            return file

        if file == os.path.expanduser("~"):
            return file

        if "private" in file.lower().split('/')[:-1]:
            # Switch root directory to $HOME
            # in case it's an inaccessible directory.
            root_dir = os.path.expanduser("~")
            print(f"[IMPORTANT]: Switched default directory, for logging and dumps, to '{root_dir}'!")
            return root_dir

        return file

    def critical(self, message, file="UNKNOWN"):
        file = self.handle_file(file)

        self.handler.setLevel(logging.CRITICAL)
        self.rotating.setFormatter(
            logging.Formatter(self.format.format(os.path.basename(file)))
        )
        self.handler.critical(message)

    def error(self, message, file="UNKNOWN"):
        file = self.handle_file(file)

        self.handler.setLevel(logging.ERROR)
        self.rotating.setFormatter(
            logging.Formatter(self.format.format(os.path.basename(file)))
        )
        self.handler.error(message)

    def info(self, message, file="UNKNOWN"):
        file = self.handle_file(file)

        self.handler.setLevel(logging.INFO)
        self.rotating.setFormatter(
            logging.Formatter(self.format.format(os.path.basename(file)))
        )
        self.handler.info(message)

    def warning(self, message, file="UNKNOWN"):
        file = self.handle_file(file)

        self.handler.setLevel(logging.WARNING)
        self.rotating.setFormatter(
            logging.Formatter(self.format.format(os.path.basename(file)))
        )
        self.handler.warning(message)
