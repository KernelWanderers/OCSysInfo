import os
import dicttoxml
import logging
from src.managers.devicemanager import DeviceManager
from src.error.logger import Logger

def dump_xml(dm, dir, logger):
    data = None

    if not isinstance(dm, DeviceManager):
        raise TypeError("Parameter 'dm' is not of type 'DeviceManager'!")
    
    if not os.path.isdir(dir):
        raise ValueError("Parameter 'dir' is not a valid directory!")

    if not isinstance(logger, Logger):
        raise TypeError("Parameter 'logger' is not of type 'Logger'!")

    try:
        with open(os.path.join(dir, "info_dump.xml"), "wb") as xml:
            # Disables debug prints from `dicttoxml`
            dicttoxml.LOG.setLevel(logging.ERROR)
            xml.write(dicttoxml.dicttoxml(dm.info, root=True))
            xml.close()
            logger.info(
                f'Successfully dumped "info_dump.xml" into "{dir}"', __file__
            )
            
            data = f'Successfully dumped "info_dump.xml" into "{dir}"\n'
    except Exception as e:
        logger.error(
            f"Failed to dump to XML!\n\t^^^^^^^^^{str(e)}", __file__)

    return data