import os
import plistlib
from src.managers.devicemanager import DeviceManager
from src.error.logger import Logger

def dump_plist(dm, dir, logger):
    data = None

    if not isinstance(dm, DeviceManager):
        raise TypeError("Parameter 'dm' is not of type 'DeviceManager'!")
    
    if not os.path.isdir(dir):
        raise ValueError("Parameter 'dir' is not a valid directory!")

    if not isinstance(logger, Logger):
        raise TypeError("Parameter 'logger' is not of type 'Logger'!")

    try:
        with open(os.path.join(dir, "info_dump.plist"), "wb") as plist:
            plistlib.dump(dm.info, plist, sort_keys=False)
            plist.close()
            logger.info(
                f'Successfully dumped info "info_dump.plist" into "{dir}"', __file__
            )

            data = f'Successfully dumped info "info_dump.plist" into "{dir}"\n'
    except Exception as e:
        logger.error(
            f"Failed to dump to Plist!\n\t^^^^^^^^^{str(e)}", __file__
        )

    return data