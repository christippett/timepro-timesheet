import re
import itertools
import json
from collections import OrderedDict
from datetime import timedelta

from dateutil.parser import parse as dateparser


class Timesheet:
    FORM_XPATH_INPUT_ROWS = '//input[@name="InputRows"]'
    FORM_XPATH_START_DATE = '//input[@name="StartDate"]'
    FORM_XPATH_END_DATE = '//input[@name="EndDate"]'
    FORM_XPATH_CUSTOMERS = '//*[contains(@name, "CustomerCode_")]'
    FORM_XPATH_PROJECTS = '//*[contains(@name, "Project_")]'
    FORM_XPATH_TASKS = '//*[contains(@name, "Task_")]'
    FORM_XPATH_TIMES = '//*[contains(@name, "FinishTime_")]'
    TIMESHEET_FIELD_PATTERN = r'^(?P<entry_type>\w+)_(?P<row_id>\d+)_(?P<column_id>\d+)$'

    def __init__(self, customer_options, project_options, task_options, staff_id, user_context_id,
                 html=None, data=None):
        self.staff_id = staff_id
        self.user_context_id = user_context_id
        self._customer_options = customer_options
        self._project_options = project_options
        self._task_options = task_options
        self._form_data = {}
        self._html = html
        if html:
            self._form_data = self.extract_form_data_from_html(html)
        if data:
            self._data = data

    def lookup_customer(self, customer):
        customers = [c for c in self._customer_options if c['customer_code'] == customer]
        return customers[0] if customers else {}

    def lookup_project(self, project):
        search_key = 'project_psid' if '{:}' in project else 'project_code'
        projects = [p for p in self._project_options if p[search_key] == project]
        return projects[0] if project else {}

    def lookup_task(self, task):
        tasks = [t for t in self._task_options if t['task_id'] == task]
        return tasks[0] if tasks else {}

    def row_entries(self):
        """
        Construct dictionary of timesheet entries, with row numbers as keys.
        """
        entries = OrderedDict()
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
        for k, v in data.copy().items():
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
            html.xpath(self.FORM_XPATH_TASKS)
        )
        data = {}
        # Construct data dictionary
        for el in data_elements:
            name = el.attrs.get('name')
            if el.element.tag == 'select':
                option = el.xpath('//option[@selected]', first=True)
                value = option.attrs.get('value') if option else ''
            else:
                value = el.attrs.get('value')
            data[name] = value
        # Customer form elements not present in read-only timesheet,
        # we need to lookup `customer_code` from project
        for k, v in data.copy().items():
            m = re.match(self.TIMESHEET_FIELD_PATTERN, k)
            if not m:
                continue
            entry_type, row_id, column_id = m.groups()
            if entry_type == 'Project':
                customer_key = 'Customer_{}_{}'.format(row_id, column_id)
                customer = self.lookup_project(v)
                if customer_key not in data:
                    data[customer_key] = customer['customer_code'] if customer else ''
            elif entry_type == 'FinishTime':
                # Read-only timesheet includes extra empty rows that do not need to
                # be included
                if input_rows and int(row_id) > input_rows:
                    data.pop(k)
        return data

    def date_entries(self):
        """
        Construct dictionary of timesheet entries, with dates (`column_id` indexes) as keys.
        """
        form_data = self.form_data()
        date_entries = {}
        for k, v in form_data.items():
            m = re.match(self.TIMESHEET_FIELD_PATTERN, k)
            if not m:
                continue
            entry_type, row_id, column_id = m.groups()
            if entry_type != 'FinishTime' or v == '0' or not v:
                continue
            row_id, column_id = int(row_id), int(column_id)
            date = date_entries.get(column_id, [])
            row_entry = self.row_entries().get(row_id)
            customer = self.lookup_customer(row_entry.get('customer'))
            project = self.lookup_project(row_entry.get('project'))
            task = self.lookup_task(row_entry.get('task'))
            entry = {
                'customer_code': customer.get('customer_code'),
                'customer_description': customer.get('customer_description'),
                'project_code': project.get('project_code'),
                'project_psid': project.get('project_psid'),
                'project_description': project.get('project_description'),
                'task_id': task.get('task_id'),
                'task_description': task.get('task_description'),
                'hours': float(v) if v != '' else 0
            }
            date.append(entry)
            date_entries[column_id] = date

        # Generate range of dates from start to end date
        start_date = dateparser(form_data['StartDate'])
        end_date = dateparser(form_data['EndDate'])
        days_diff = (end_date - start_date).days
        timesheet_dates = [start_date + timedelta(days=x) for x in range(0, days_diff + 1)]

        # Match dates in timesheet period with ordinal index from `date_entries`
        d = {}
        for i, dt in enumerate(timesheet_dates):
            d[dt] = date_entries.get(i, [])
        return d

    def json(self):
        date_entries = self.date_entries()
        print(
            json.dumps(dict((k.strftime('%Y-%m-%d'), v) for k, v in date_entries.items()))
        )