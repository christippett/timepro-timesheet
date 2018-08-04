import argparse
from dateutil.parser import parse as dateparser

from .api import TimesheetAPI


def main():
    parser = argparse.ArgumentParser(
        prog='timepro',
        description='Programmatically get your timesheet from Intertec TimePro (timesheets.com.au.')
    parser.add_argument('--user', '-u', dest='username', nargs='?', help='Your username to log into TimePro')
    parser.add_argument('--password', '-p', dest='password', nargs='?', help='Your password to log into TimePro')
    parser.add_argument('--customer-id', '-id', dest='customer_id', nargs='?', help='Your company''s TimePro Customer ID')
    parser.add_argument('--start', dest='start_date', metavar='START_DATE', nargs='?', help='Start date of timesheet')
    parser.add_argument('--end', dest='end_date', metavar='END_DATE', nargs='?', help='End date of timesheet')
    args = parser.parse_args()
    if args.start_date and args.end_date:
        date_kwargs = {
            'start_date': dateparser(args.start_date),
            'end_date': dateparser(args.end_date)
        }
    else:
        date_kwargs = {}
    api = TimesheetAPI()
    api.login(
        username=args.username,
        password=args.password,
        customer_id=args.customer_id)
    timesheet = api.get_timesheet(**date_kwargs)
    return timesheet.json()
