import os
from src.util.tree import tree
from src.managers.devicemanager import DeviceManager
from src.error.logger import Logger

def dump_txt(dm, dir, logger):
    data = None

    if not isinstance(dm, DeviceManager):
        raise TypeError("Parameter 'dm' is not of type 'DeviceManager'!")
    
    if not os.path.isdir(dir):
        raise ValueError("Parameter 'dir' is not a valid directory!")

    if not isinstance(logger, Logger):
        raise TypeError("Parameter 'logger' is not of type 'Logger'!")

    try:
        with open(
            os.path.join(dir, "info_dump.txt"), "w", encoding="utf-8"
        ) as file:
            for key in dm.info:
                file.write(tree(key, dm.info[key], color=False))
                file.write("\n")

            file.close()
            logger.info(
                f'Successfully dumped "info_dump.txt" into "{dir}"', __file__
            )

            data = f'Successfully dumped "info_dump.txt" into "{dir}"\n'
    except Exception as e:
        logger.error(
            f"Failed to dump to TXT!\n\t^^^^^^^^^{str(e)}", __file__)

    return data