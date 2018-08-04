import sys
import argparse

from dateutil.parser import parse as dateparser

from .api import TimesheetAPI


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
        args = parser.parse_args(sys.argv[2:])
        if args.start_date and args.end_date:
            date_kwargs = {
                'start_date': dateparser(args.start_date),
                'end_date': dateparser(args.end_date)
            }
        else:
            date_kwargs = {}
        api = TimesheetAPI()
        api.login(
            customer_id=args.customer_id,
            username=args.username,
            password=args.password)
        timesheet = api.get_timesheet(**date_kwargs)
        print(timesheet.json())


if __name__ == '__main__':
    TimesheetCLI()
