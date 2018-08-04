import re
import itertools
import json
from collections import OrderedDict
from datetime import timedelta

from dateutil.parser import parse as dateparser

from .utils import generate_date_series


class Timesheet:
    FORM_XPATH_INPUT_ROWS = '//input[@name="InputRows"]'
    FORM_XPATH_START_DATE = '//input[@name="StartDate"]'
    FORM_XPATH_END_DATE = '//input[@name="EndDate"]'
    FORM_XPATH_CUSTOMERS = '//*[contains(@name, "CustomerCode_")]'
    FORM_XPATH_PROJECTS = '//*[contains(@name, "Project_")]'
    FORM_XPATH_TASKS = '//*[contains(@name, "Task_")]'
    FORM_XPATH_TIMES = '//*[contains(@name, "FinishTime_")]'
    FORM_XPATH_DESCRIPTIONS = '//*[contains(@name, "Description_")]'
    TIMESHEET_FIELD_PATTERN = r'^(?P<entry_type>\w+)_(?P<row_id>\d+)_(?P<column_id>\d+)$'

    def __init__(self, staff_id, user_context_id, customer_options=None, project_options=None, task_options=None,
                 html=None, data=None):
        self.staff_id = staff_id
        self.user_context_id = user_context_id
        self._customer_options = customer_options or []
        self._project_options = project_options or []
        self._task_options = task_options or []
        self._form_data = {}
        self._html = html
        if html:
            self._form_data = self.extract_form_data_from_html(html)
        if data:
            self._form_data = self.extract_form_data_from_dict(data)

    def lookup_customer(self, customer):
        customers = [c for c in self._customer_options if c['customer_code'] == customer]
        return customers[0] if customers else {}

    def lookup_project(self, project):
        search_key = 'project_psid' if '{:}' in project else 'project_code'
        projects = []
        for p in self._project_options.copy():
            p.pop('task_count', None)  # exclude task_count when returning project details
            if p[search_key] == project:
                projects.append(p)
        return projects[0] if projects else {}

    def lookup_task(self, task):
        tasks = [t for t in self._task_options if t['task_id'] == task]
        return tasks[0] if tasks else {}

    def row_entries(self):
        """
        Construct dictionary of timesheet entries, with row numbers as keys.
        """
        entries = {}
        for k, v in self._form_data.items():
            m = re.match(self.TIMESHEET_FIELD_PATTERN, k)
            if not m:
                continue
            entry_type, row_id, column_id = m.groups()
            row_id, column_id = int(row_id), int(column_id)
            entry = entries.get(row_id, {})
            if entry_type == 'Customer':
                entry['customer'] = v
            elif entry_type == 'Project':
                entry['project'] = v
            elif entry_type == 'Task':
                entry['task'] = v
            elif entry_type == 'Description':
                entry['description'] = v
            elif entry_type == 'FinishTime':
                times = entry.get('times', [])
                hours = float(v) if v != '' else 0
                times.append((column_id, hours))
                entry['times'] = times
            entries[row_id] = entry
        # Process times into ordered (based on `column_id`) list of hours
        for k in entries.copy().keys():
            customer = entries[k].get('customer', '')
            project = entries[k].get('project', '')
            times = entries[k].get('times', [])
            if times:
                sorted_times = sorted(times, key=lambda t: t[0])
                times = [t[1] for t in sorted_times]
            # Remove rows with no data
            if (customer == '' and project == '') or sum(times) == 0:
                entries.pop(k)
                continue
            entries[k]['times'] = times
        return entries

    def count_entries(self):
        """
        Count number of timesheet entries. This should reconcile with the
        `InputRows` field from the form data.
        """
        return len(self.row_entries().keys())

    def form_data(self):
        """
        Output timesheet data in a format that can be POST'd to the
        timesheets.com.au servers.
        """
        data = self._form_data.copy()
        row_count = self.count_entries()
        for k in data.copy().keys():
            m = re.match(self.TIMESHEET_FIELD_PATTERN, k)
            if not m:
                continue
            entry_type, row_id, column_id = m.groups()
            if entry_type == 'FinishTime':
                # Some form elements not present in read-only timesheet,
                # we'll add these fields manually for completeness
                description_key = 'Description_{}_{}'.format(row_id, column_id)
                if description_key not in data:
                    data[description_key] = ''
                pbatch_key = 'PBatch_{}_{}'.format(row_id, column_id)
                if pbatch_key not in data:
                    data[pbatch_key] = ''
                sbatch_key = 'SBatch_{}_{}'.format(row_id, column_id)
                if sbatch_key not in data:
                    data[sbatch_key] = ''
        data.update({
            'UserContextID': self.user_context_id,
            'StaffID': self.staff_id,
            'InputRows': row_count,
            'Save': '  Save  ',
            'DataForm': 'Timesheet {}'.format(self.staff_id),
            'OptionsDisplayed': 'N',
            'OverrideAction': '',
            'DeletesPending': ''
        })
        return data

    def extract_form_data_from_dict(self, data):
        # Get unique customer/project/task entries, these will become our rows
        unique_entries = set()
        for _, entries in data.items():
            for e in entries:
                customer = e.get('customer_code')
                project = e.get('project_psid')
                task = e.get('task_id') or ''
                unique_entries.add('{}|{}|{}'.format(customer, project, task))

        # Use lambda to create default entry to avoid later referencing same object
        default_entry = lambda: dict(customer='', project='', task='', times=[])
        row_entries = dict((e, default_entry()) for e in unique_entries)

        # Generate range of dates from start to end date (to account for any missing dates in between)
        start_date = min(data.keys())
        end_date = max(data.keys())
        timesheet_dates = generate_date_series(start_date, end_date)

        # Populate row entry, sum hours across multiple days into single row value
        for dt in timesheet_dates:
            date_entries = data.get(dt, [])  # list of entries for the given date
            for key, entry in row_entries.items():
                # Sum all hours for a single date for the same customer/project/task
                hours = sum(
                    [e['hours'] for e in date_entries if '{}|{}|{}'.format(e.get('customer_code'), e.get('project_psid'), e.get('task_id') or '') == key]
                )
                entry['times'].append(hours)
                entry['customer'], entry['project'], entry['task'] = key.split('|')  # populate row keys

        # Replace key with row number
        row_entries = dict((i, v[1]) for i, v in enumerate(row_entries.items()))

        form_data = {}
        for row_id, entry in row_entries.items():
            f = '{}_{}_{}'  #
            form_data.update({
                f.format('CustomerCode', row_id, 0): entry.get('customer') or '',
                f.format('Project', row_id, 0): entry.get('project') or '',
                f.format('Task', row_id, 0): entry.get('task') or ''
            })
            for column_id, hour in enumerate(entry.get('times', [])):
                form_data.update({
                    f.format('FinishTime', row_id, column_id): hour
                })
        return form_data

    def extract_form_data_from_html(self, html):
        """
        Extract timesheet form data from HTML
        """
        form_input_rows = html.xpath(self.FORM_XPATH_INPUT_ROWS, first=True)
        input_rows = int(form_input_rows.attrs.get('value')) - 1 if form_input_rows else None
        data_elements = itertools.chain(
            html.xpath(self.FORM_XPATH_START_DATE)[:1],
            html.xpath(self.FORM_XPATH_END_DATE)[:1],
            html.xpath(self.FORM_XPATH_TIMES),
            html.xpath(self.FORM_XPATH_CUSTOMERS),
            html.xpath(self.FORM_XPATH_PROJECTS),
            html.xpath(self.FORM_XPATH_TASKS),
            html.xpath(self.FORM_XPATH_DESCRIPTIONS)
        )
        form_data = {}

        # Construct data dictionary
        for el in data_elements:
            name = el.attrs.get('name')
            # form elements can be a select element (drop down) if timesheet is not read-only
            if el.element.tag == 'select':
                option = el.xpath('//option[@selected]', first=True)
                value = option.attrs.get('value') if option else ''
            else:
                value = el.attrs.get('value')
            form_data[name] = value

        # Customer form elements aren't present in read-only timesheet, we need to lookup `customer_code` from project
        for k, v in form_data.copy().items():
            m = re.match(self.TIMESHEET_FIELD_PATTERN, k)
            if not m:
                continue
            entry_type, row_id, column_id = m.groups()
            if entry_type == 'Project':
                customer_key = 'Customer_{}_{}'.format(row_id, column_id)
                if customer_key not in form_data:
                    customer = self.lookup_project(v)
                    form_data[customer_key] = customer['customer_code'] if customer else ''
            elif entry_type == 'FinishTime':
                # Read-only timesheet can contain extra empty rows that do not need to be included
                if input_rows and int(row_id) > input_rows:
                    form_data.pop(k)
        return form_data

    def date_entries(self):
        """
        Construct dictionary of timesheet entries, with dates (`column_id` indexes) as keys.
        """
        form_data = self._form_data
        dates = {}
        for k, v in form_data.items():
            m = re.match(self.TIMESHEET_FIELD_PATTERN, k)
            if not m:
                continue
            entry_type, row_id, column_id = m.groups()

            # Only loop through FinishTime entries to assemble date entries
            if entry_type != 'FinishTime' or v == '0' or not v:
                continue
            row_id, column_id = int(row_id), int(column_id)
            date_entries = dates.get(column_id, [])

            # Lookup row details
            row_entry = self.row_entries().get(row_id)
            customer = self.lookup_customer(row_entry.get('customer'))
            project = self.lookup_project(row_entry.get('project'))
            task = self.lookup_task(row_entry.get('task'))
            entry = { 'hours': float(v) if v != '' else 0 }
            entry.update(customer)
            entry.update(project)
            entry.update(task)

            # Add entry under date
            date_entries.append(entry)
            dates[column_id] = date_entries

        # Generate range of dates from start to end date (to account for any missing dates in between)
        start_date = dateparser(form_data['StartDate'])
        end_date = dateparser(form_data['EndDate'])
        timesheet_dates = generate_date_series(start_date, end_date)

        # Match dates in timesheet period with ordinal index from `dates`
        d = {}
        for i, dt in enumerate(timesheet_dates):
            d[dt] = dates.get(i, [])
        return d

    def json(self):
        date_entries = self.date_entries()
        print(
            json.dumps(dict((k.strftime('%Y-%m-%d'), v) for k, v in date_entries.items()), indent=2)
        )
