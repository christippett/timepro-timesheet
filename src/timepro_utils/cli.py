import sys
import argparse
from datetime import date

from dateutil.parser import parse as dateparser
from dateutil.relativedelta import relativedelta, MO, FR

# from .api import TimesheetAPI


TODAY = date.today()


class TimesheetCLI:

    def __init__(self):
        parser = argparse.ArgumentParser(
            description='Programmatically get your timesheet from Intertec TimePro (timesheets.com.au.')
        parser.add_argument('command', help='Action to run')
        # parse only common arguments, the rest will be parsed per subcommand
        args = parser.parse_args(sys.argv[1:2])
        if not hasattr(self, args.command):
            print('Invalid command')
            parser.print_help()
            exit(1)
        # use dispatch pattern to invoke method with same name
        getattr(self, args.command)()

    def _create_parser(self, description):
        parser = argparse.ArgumentParser(description=description)
        login_parameters = parser.add_argument_group('required arguments')
        login_parameters.add_argument('-c', '--customer', dest='customer_id', required=True, help="Employer's TimePro Customer ID")
        login_parameters.add_argument('-u', '--user', dest='username', required=True, help='Your username to log into TimePro')
        login_parameters.add_argument('-p', '--password', dest='password', required=True, help='Your password to log into TimePro')
        return parser

    def get(self):
        parser = self._create_parser(
            description='Get timesheet data from Intertec TimePro')
        get_parameters = parser.add_argument_group('filter options')
        get_parameters.add_argument('--start', dest='start_date', metavar='START_DATE', help='Start date of timesheet period')
        get_parameters.add_argument('--end', dest='end_date', metavar='END_DATE', help='End date of timesheet period')
        get_parameters.add_argument('--week', dest='get_week', action='store_true', help="Get current week's timesheet")
        get_parameters.add_argument('--month', dest='get_month', action='store_true', help="Get current month's timesheet")
        args = parser.parse_args(sys.argv[2:])
        if args.start_date and args.end_date:
            start_date = dateparser(args.start_date)
            end_date = dateparser(args.end_date)
        elif args.get_month:
            start_date = TODAY + relativedelta(day=1)
            end_date = TODAY + relativedelta(day=31)
        elif args.get_week:
            start_date = TODAY + relativedelta(weekday=MO(-1))
            end_date = TODAY + relativedelta(weekday=FR)
        else:
            # default to get this week's timesheet (excl. previous month)
            start_date = max([
                TODAY + relativedelta(day=1),
                TODAY + relativedelta(weekday=MO(-1))
            ])
            end_date = TODAY + relativedelta(weekday=FR)
        date_kwargs = dict(start_date=start_date, end_date=end_date)
        # api = TimesheetAPI()
        # api.login(
        #     customer_id=args.customer_id,
        #     username=args.username,
        #     password=args.password)
        # timesheet = api.get_timesheet(**date_kwargs)
        # print(timesheet.json())


if __name__ == '__main__':
    TimesheetCLI()
