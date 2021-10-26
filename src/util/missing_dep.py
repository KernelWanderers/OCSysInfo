from unittest import TestCase
from pkg_resources import require, DistributionNotFound
from subprocess import call
from sys import platform, executable
from pathlib import Path


if platform.lower() == "darwin":
    REQUIRED = Path(Path(__file__).parent).parent.with_name(
        "requirements-macOS.txt")
elif platform.lower() == "linux":
    REQUIRED = Path(Path(__file__).parent).parent.with_name(
        "requirements-Linux.txt")
elif platform.lower() == "windows":
    REQUIRED = Path(Path(__file__).parent).parent.with_name(
        "requirements-Windows.txt")
else:
    raise Exception(
        "Failed to locate requirements file. Maybe it was deleted?")


class Requirements(TestCase):
    """
    Instance, solely here to ensure that all necessary
    dependencies are installed.
    """

    def test_req(self):
        missing = []
        requirements = REQUIRED.open()

        for requirement in requirements:
            requirement = str(requirement)

            with self.subTest(requirement=requirement):
                try:
                    require(requirement)
                except DistributionNotFound:
                    missing.append(requirement.strip())

        return missing

    def install_reqs(self, missing):
        acceptable = {'y', 'n', 'yes', 'no'}
        answer = input(
            '\n\033[96mDo you wish to install the aforementioned missing packages? [y/n]:\033[0m '
        )

        if answer.lower() in acceptable:
            if 'y' in answer.lower():
                print('\n\n')
                for missed in missing:
                    self.req(missed, acceptable)

                print(
                    '\n\033[92mSuccessfully installed required dependencies!\033[0m'
                )
            else:
                print('Exited successfully.')
                exit(0)

    def req(self, requirement, acceptable, heading=''):
        if not heading:
            heading = '\033[4m\033[91mNOTE: This is not an optional package.'

        ans = input(
            f'{heading}\033[0m\033[96m\nAre you sure you want to install "{requirement}"? [y/n]:\033[0m '
        )

        if ans.lower() in acceptable:
            if 'y' in ans.lower():
                call(
                    [executable, '-m', 'pip', 'install', requirement]
                )
                print('\n\n')
            else:
                print('\n')

                extra = \
                    '\033[1m\033[91mThis package is not optional.\033[0m' + \
                    '\033[1m\033[91m You must install it.\033[0m'

                self.req(requirement, acceptable, heading=extra)
        else:
            invalid = '\n\033[1m\033[91mInvalid option. ' + \
                'Please use only "yes", "no", "y" or "n" to answer.'

            self.req(requirement, acceptable, heading=invalid)
