from datetime import timedelta


def generate_date_series(start_date, end_date):
    """
    Generate series of dates from start to end date
    """
    days_diff = (end_date - start_date).days
    return [start_date + timedelta(days=x) for x in range(0, days_diff + 1)]
