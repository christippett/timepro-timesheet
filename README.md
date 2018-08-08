Intertec TimePro Utils
=============================================================

[![PyPI version](https://img.shields.io/pypi/v/timepro-timesheet.svg)](https://pypi.python.org/pypi/timepro-timesheet)
[![Build status](https://img.shields.io/travis/christippett/timepro-timesheet.svg)](https://travis-ci.org/christippett/timepro-timesheet)
[![Coverage](https://img.shields.io/coveralls/github/christippett/timepro-timesheet.svg)](https://coveralls.io/github/christippett/timepro-timesheet?branch=master)
[![Python versions](https://img.shields.io/pypi/pyversions/timepro-timesheet.svg)](https://pypi.python.org/pypi/timepro-timesheet)
[![Github license](https://img.shields.io/github/license/christippett/timepro-timesheet.svg)](https://github.com/christippett/timepro-timesheet)

Description
===========

Programmatically get and submit timesheet data to Intertec TimePro (timesheets.com.au)


Installation
============

Install with `pip`:

``` bash
pip install timepro-timesheet
```

Usage
=====

Command line
------------

**GET data**

Once installed, you can use the CLI to get your timesheet data as JSON.

``` bash
$ timepro get -c CUST -u john.doe -p password123
  {
    "2018-08-04": [
      {
        "customer_code": "EXAMPLE",
        "customer_description": "Example Company Pty Ltd",
        "project_code": "EX-123",
        "project_psid": "EX-123{:}1",
        "project_description": "EXAMPLE - EX-123 - SOW000 - Important Business Stuff - PO 123",
        "task_id": null,
        "task_description": null,
        "hours": 8
      }
    ]
  }
```

You can filter the timesheet period by specifying dates for `--start` and `--end`, or by using the `--this-week`, `--this-month`, `--last-week` or `--last-month` flags. By default, the current week's timesheet entries are returned.

**POST data**

Data can be submitted by reading from a JSON file.

``` bash
$ timepro post -c CUST -u john.doe -p password123 -f timesheet_entries.json
```

or

``` bash
$ cat timesheet_entries.json | timepro post -c CUST -u john.doe -p password123
```

Python
------

``` python
from timepro_timesheet.api import TimesheetAPI

# Log into timesheets.com.au via the TimesheetAPI class
api = TimesheetAPI()
api.login(customer_id='CUST', username='john.doe', password='password123')

# Get timesheet (defaults to current month)
timesheet = api.get_timesheet()

# Get timesheet for a given date
timesheet = api.get_timesheet(start_date=date(2018, 6, 1), end_date=date(2018, 6, 25))

# Output timesheet
timesheet.json()
timesheet.row_entries()
timesheet.date_entries()

```
