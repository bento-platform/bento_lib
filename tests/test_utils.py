import os
import re

from chord_lib.utils import get_own_version

from pathlib import Path
setup_path = os.path.join(Path(os.path.dirname(os.path.realpath(__file__))).parent, "setup.py")


def test_package_version():
    assert re.match(r"\d+\.\d+\.\d+", get_own_version(setup_path, "chord_lib")) is not None


def test_setup_path():
    assert re.match(r"\d+\.\d+\.\d+", get_own_version(setup_path, "does_not_exist")) is not None
