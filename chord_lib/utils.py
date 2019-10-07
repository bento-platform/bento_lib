import re

from pkg_resources import get_distribution, DistributionNotFound

__all__ = ["get_own_version"]


def get_own_version(setup_path, name):
    try:
        return get_distribution(name).version
    except DistributionNotFound:
        return [re.search(r"(\d+\.\d+\.\d+)", l).group(1) for l in open(setup_path, "r").readlines()
                if "    version" in l][0]
