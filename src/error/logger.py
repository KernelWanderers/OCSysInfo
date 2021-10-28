import logging
import os
from logging.handlers import RotatingFileHandler


class Logger:
    """
    Instance responsible for properly handling,
    formatting and logging information about the
    application's state.
    """

    def __init__(self):
        # Basic formats.
        self.format = '%(asctime)s | {} | %(levelname)s: %(message)s'.format(
            os.path.basename(__file__))
        self.date = '%m/%d/%Y %I:%M:%S %p'

        # Adding the base log handlers.
        self.handler = logging.getLogger()
        self.rotating = RotatingFileHandler(
            'ocsysinfo.log', mode='a', maxBytes=2**13)

        # Add the RotatingFileHandler to the default logger.
        self.handler.addHandler(self.rotating)
        self.rotating.setFormatter(
            logging.Formatter(self.format, datefmt=self.date))

    def critical(self, message):
        self.handler.setLevel(logging.CRITICAL)
        self.handler.critical(message)

    def error(self, message):
        self.handler.setLevel(logging.ERROR)
        self.handler.error(message)

    def info(self, message):
        self.handler.setLevel(logging.INFO)
        self.handler.info(message)

    def warning(self, message):
        self.handler.setLevel(logging.WARNING)
        self.handler.warning(message)
