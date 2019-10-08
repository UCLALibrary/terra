from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from terra.models import Employee, Unit, EMPLOYEE_TYPES

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
            staff_type = row['staff_type']

            self.stdout.write(f'\tProcessing {employee_name}...')

            # User & Employee
            user = _get_user(employee_name, email)
            # Employees must have units; fetch from database
            unit = Unit.objects.get(name__exact=department)
            employee = _get_employee(user, ucla_id, unit, staff_type)


def _get_user(employee_name, email):
    # Employees are based on Users, so create user first.
    # Use the email name as username for now, with unusable password.
    username = email.split('@')[0]
    # Users might already exist, via small initial load
    user, created = User.objects.get_or_create(username=username, email=email)
    # Add first/last name to the user
    user.last_name, user.first_name = _split_name(employee_name)
    user.save()
    return user


def _get_employee(user, ucla_id, unit, staff_type):
    staff_type = _get_employee_type_key(staff_type)
    employee, created = Employee.objects.get_or_create(user=user, uid=ucla_id, unit=unit, type=staff_type)
    return employee

def _get_employee_type_key(value):
    # EMPLOYEE_TYPES is tuple of tuples; we need key matching value in 1.
    # Convert to dictionary, then keys/values to lists, and get by value.
    d = dict(EMPLOYEE_TYPES)
    return list(d.keys())[list(d.values()).index(value)]

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
                self.stdout.write(f"Adding {supervisor_name} to {employee_name}")
                supervisor = find_employee_by_name(self, supervisor_name)
                employee = find_employee_by_name(self, employee_name)
                employee.supervisor = supervisor
                employee.save()
            else:
                self.stderr.write(f'\tNo supervisor found for {employee_name}')

def find_employee_by_name(self, employee_name):
    """
    Find Employee with the given name, using data from the employees csv file.
    """
    last_name, first_name = _split_name(employee_name)
    try:
        employee = Employee.objects.get(user=User.objects.get(last_name__exact=last_name, first_name__exact=first_name))
        return employee
    except ObjectDoesNotExist:
        self.stderr.write(f"\tERROR: {employee_name} not found")

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
