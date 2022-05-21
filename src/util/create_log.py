import os
from sys import exit


def create_log(create_dump=None):
    paths = [None, None]

    bundle_id = "OCSysInfo"
    lib_logs = os.path.join(
        os.path.expanduser("~"),
        "Library",
        "Logs"
    )
    lib_app = os.path.join(
        os.path.expanduser("~"),
        "Library",
        "Application Support"
    )

    if not bundle_id:
        bundle_id = "OCSysInfo"

    if not os.path.isdir(os.path.join(lib_logs, bundle_id)):
        print(
            f"Creating log directory in '{lib_logs}' called '{bundle_id}'...")

        try:
            os.mkdir(os.path.join(lib_logs, bundle_id))

            print(
                f"Successfully created log directory '{os.path.join(lib_logs, bundle_id)}'!")


        except Exception as e:
            print(
                f"Failed to create log directory '{os.path.join(lib_logs, bundle_id)}'!\n\t^^^^^^^{str(e)}")
            exit(1)

    if create_dump:
        if not os.path.isdir(os.path.join(lib_app, bundle_id)):
            print(
                f"Creating directory for app data in '{lib_app}' called '{bundle_id}'...")

            try:
                os.mkdir(os.path.join(lib_app, bundle_id))

                print(
                    f"Successfully created direcotry for app data '{os.path.join(lib_app, bundle_id)}'!")

            except Exception as e:
                print(
                    f"Failed to create directory for app data '{os.path.join(lib_app, bundle_id)}'!\n\t^^^^^^^{str(e)}")
                exit(1)

    paths[0] = os.path.join(
        lib_logs,
        bundle_id
    )
    
    paths[1] = os.path.join(
        lib_app,
        bundle_id
    )

    return paths
