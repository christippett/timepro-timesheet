from pkg_resources import get_distribution, DistributionNotFound

try:
    __version__ = get_distribution('timepro-timesheet').version
except DistributionNotFound:
    __version__ = 'unknown'  # package not installed
