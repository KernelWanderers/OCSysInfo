import os
import json
from src.managers.devicemanager import DeviceManager
from src.error.logger import Logger

def dump_json(dm, dir, logger):
    data = None

    if not isinstance(dm, DeviceManager):
        raise TypeError("Parameter 'dm' is not of type 'DeviceManager'!")
    
    if not os.path.isdir(dir):
        raise ValueError("Parameter 'dir' is not a valid directory!")

    if not isinstance(logger, Logger):
        raise TypeError("Parameter 'logger' is not of type 'Logger'!")

    try:
        with open(os.path.join(dir, "info_dump.json"), "w") as _json:
            _json.write(json.dumps(
                dm.info, indent=4, sort_keys=False))
            _json.close()
            logger.info(
                f'Successfully dumped "info_dump.json" into "{dir}"', __file__
            )

            data = f'Successfully dumped "info_dump.json" into "{dir}"\n'
    except Exception as e:
        logger.error(
            f"Failed to dump to JSON!\n\t^^^^^^^^^{str(e)}", __file__)

    return data