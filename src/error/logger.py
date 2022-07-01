import logging
import os
from logging.handlers import RotatingFileHandler
from platform import system
from src.info import AppInfo

class Logger:
    """
    Instance responsible for properly handling,
    formatting and logging information about the
    application's state.
    """

    def __init__(self, path=AppInfo.root_dir):
        # Basic formats.
        self.format = "%(asctime)s | {} | %(levelname)s: %(message)s"
        self.date = "%m/%d/%Y %I:%M:%S %p"

        # Adding the base log handlers.
        self.handler = logging.getLogger()
        self.rotating = RotatingFileHandler(os.path.join(path, "ocsysinfo.log"), mode="a", maxBytes=2 ** 13)

        # Add the RotatingFileHandler to the default logger.
        self.handler.addHandler(self.rotating)
        self.rotating.setFormatter(
            logging.Formatter(
                self.format.format(os.path.basename(__file__)), datefmt=self.date
            )
        )

    def critical(self, message, file="UNKNOWN"):
        self.handler.setLevel(logging.CRITICAL)
        self.rotating.setFormatter(
            logging.Formatter(self.format.format(os.path.basename(file)))
        )
        self.handler.critical(message)

    def error(self, message, file="UNKNOWN"):
        self.handler.setLevel(logging.ERROR)
        self.rotating.setFormatter(
            logging.Formatter(self.format.format(os.path.basename(file)))
        )
        self.handler.error(message)

    def info(self, message, file="UNKNOWN"):
        self.handler.setLevel(logging.INFO)
        self.rotating.setFormatter(
            logging.Formatter(self.format.format(os.path.basename(file)))
        )
        self.handler.info(message)

    def warning(self, message, file="UNKNOWN"):
        self.handler.setLevel(logging.WARNING)
        self.rotating.setFormatter(
            logging.Formatter(self.format.format(os.path.basename(file)))
        )
        self.handler.warning(message)
