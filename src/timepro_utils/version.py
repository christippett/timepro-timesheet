from pkg_resources import get_distribution, DistributionNotFound


try:
    __version__ = get_distribution('timepro-utils').version
except DistributionNotFound:
    __version__ = 'unknown'  # package not installed
