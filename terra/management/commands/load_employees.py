from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from terra.models import Employee, Unit

import csv

def create_employees(self, employee_file):
    """
    Does initial creation of Employees, and their underlying Users.
    """
    self.stdout.write(f'Parsing {employee_file}')
    # Windows-derived CSV has leading BOM, so specify utf-8-sig, not utf-8
    with open(employee_file, encoding='utf-8-sig', newline='') as csvfile:
        reader = csv.DictReader(csvfile, dialect='excel')
        # Field names from CSV, for reference:
        # ['department_code', 'employee_name', 'employee_id', 'ucla_id', 'email', job_code', 'job_code_desc', 'job_class_description', 'supervisor', 'department', 'aul_ul']
        for row in reader:
            # Get relevant data from CSV
            department = row['department']
            email = row['email']
            employee_name = row['employee_name']
            ucla_id = row['ucla_id']

            self.stdout.write(f'\tProcessing {employee_name}...')

            # Employees must have units; fetch from database
            unit = Unit.objects.get(name__exact=department)

            # Employees are based on Users, so create user first.
            # Use the email name as username for now, with unusable password.
            username = email.split('@')[0]
            user = User.objects.create_user(username, email)
            # Add first/last name to the user
            user.last_name, user.first_name = _split_name(employee_name)
            user.save()

            # Finally, create an Employee combining the above
            employee = Employee.objects.create(user=user, unit=unit, uid=ucla_id)

def add_supervisors(self, employee_file):
    """
    Adds supervisors to employees.
    """
    self.stdout.write(f'\nAdding supervisors...')
    with open(employee_file, encoding='utf-8-sig', newline='') as csvfile:
        reader = csv.DictReader(csvfile, dialect='excel')
        for row in reader:
            employee_name = row['employee_name']
            supervisor_name = row['supervisor']
            if supervisor_name:
                supervisor = find_employee_by_name(supervisor_name)
                employee = find_employee_by_name(employee_name)
                employee.supervisor = supervisor
                employee.save()
            else:
                self.stderr.write(f'\tNo supervisor found for {employee_name}')

def find_employee_by_name(employee_name):
    """
    Find Employee with the given name, using data from the employees csv file.
    """
    last_name, first_name = _split_name(employee_name)
    employee = Employee.objects.get(user=User.objects.get(last_name__exact=last_name, first_name__exact=first_name))
    return employee

def _split_name(employee_name):
    """
    Utility method for splitting 'Last, First' into 'Last' and 'First'.
    """
    last_name, first_name = [word.strip() for word in employee_name.split(',')]
    return (last_name, first_name)

class Command(BaseCommand):
    help = 'Load employees from CSV into database'

    def add_arguments(self, parser):
        parser.add_argument('employee_file')

    def handle(self, *args, **options):
        employee_file = options['employee_file']
        create_employees(self, employee_file)
        add_supervisors(self, employee_file)
