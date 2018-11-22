from datetime import timedelta, date, datetime

from dateutil.parser import parse as dateparser


def generate_date_series(start_date, end_date):
    """
    Generate series of dates from start to end date
    """
    days_diff = (end_date - start_date).days
    return [start_date + timedelta(days=x) for x in range(0, days_diff + 1)]


def convert_keys_to_dates(data):
    converted_data = {}
    for k, d in data.items():
        key = k
        if not isinstance(key, date) and not isinstance(key, datetime):
            key = dateparser(key)
        converted_data[key] = d
    return converted_data


def convert_time_string_and_minutes_to_hours(time_string):
    colon_count = time_string.count(':')

    if colon_count < 1:
        return float(time_string)
    elif colon_count > 1:
        raise ValueError(
            'expected time_string to be in the format hh:mm or hh.h; got {}'.format(
                repr(time_string)
            )
        )

    hours, minutes = [float(x) for x in time_string.split(':')]

    return hours + (minutes / 60)
