import os
from sys import exit


def create_log(create_dump=True):
    from platform import system

    if system().lower() == "darwin":
        return create_log_osx(create_dump)
    elif system().lower() == "windows":
        return create_log_win(create_dump)
    elif system().lower() == "linux":
        return create_log_linux(create_dump)
    else:
        raise OSError(
            "Unknown OS/kernel type – this is not supposed to happen.")


def create_log_osx(create_dump=True):
    paths = ["", ""]

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
    else:
        paths[0] = os.path.join(
            lib_logs,
            bundle_id
        )

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
        else:
            paths[1] = os.path.join(
                lib_app,
                bundle_id
            )

    return paths


def create_log_win(create_dump=True):
    paths = ["", ""]

    app_id = "OCSysInfo"
    appdata_local = os.getenv("LOCALAPPDATA")
    ocsi_path = os.path.join(appdata_local, app_id)

    if not os.path.isdir(ocsi_path):
        try:
            print(f"Creating '{app_id}' entry in %LOCALAPPDATA%...")
            os.mkdir(ocsi_path)
            print(f"Successfully created parent entry in %LOCALAPPDATA%!")
        except Exception as e:
            print(
                f"Failed to create '{app_id}' entry in %LOCALAPPDATA%!\n\t^^^^^^^{str(e)}"
            )
            exit(1)

    if not os.path.isdir(os.path.join(ocsi_path, "Logs")):
        try:
            print(f"Creating 'Logs' entry in '%LOCALAPPDATA%\\{app_id}'...")
            os.mkdir(os.path.join(ocsi_path, "Logs"))
            print(
                f"Successfully created 'Logs' entry in '%LOCALAPPDATA%\\{app_id}'!")
        except Exception as e:
            print(
                f"Failed to create 'Logs' entry in '%LOCALAPPDATA%\\{app_id}'!\n\t^^^^^^^{str(e)}"
            )
            exit(1)
    else:
        paths[0] = os.path.join(
            ocsi_path,
            "Logs"
        )

    if not os.path.isdir(os.path.join(ocsi_path, "Data")):
        try:
            print(f"Creating 'Data' entry in '%LOCALAPPDATA%\\{app_id}'...")
            os.mkdir(os.path.join(ocsi_path, "Data"))
            print(
                f"Successfully created 'Data' entry in '%LOCALAPPDATA%\\{app_id}'!")
        except Exception as e:
            print(
                f"Failed to create 'Data' entry in '%LOCALAPPDATA%\\{app_id}'!\n\t^^^^^^^{str(e)}"
            )
            exit(1)
    else:
        paths[1] = os.path.join(
            ocsi_path,
            "Data"
        )

    return paths


def create_log_linux(create_dump=True):
    paths = ["", ""]

    # Conform to naming convention
    app_id = ".ocsysinfo"
    home = os.path.expanduser("~")
    path = os.path.join(home, app_id)
    logs = os.path.join(path, "logs")
    data = os.path.join(path, "data")

    if not os.path.isdir(path):
        os.mkdir(path)

    if not os.path.isdir(logs):
        try:
            print(f"Creating '{app_id}/logs' entry in {home}...")
            os.mkdir(logs)
            print(
                f"Successfully created '/logs' entry at {path}!")
        except Exception as e:
            print(
                f"Failed to create '/logs' entry in {path}!\n\t^^^^^^^{str(e)}"
            )
            exit(1)
    else:
        paths[0] = logs

    if not os.path.isdir(data):
        try:
            print(f"Creating '{app_id}/data' entry in {home}...")
            os.mkdir(data)
            print(f"Successfully created '/data' entry at {path}!")
        except Exception as e:
            print(
                f"Failed to create '/data' entry in {path}!\n\t^^^^^^^{str(e)}"
            )
            exit(1)
    else:
        paths[1] = data

    return paths