from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from terra.models import Employee, Unit

import csv


def add_unit_heads(self, unit_file):
    """
    Does initial creation of Units.
    """
    self.stdout.write(f"Parsing {unit_file}")
    # Windows-derived CSV has leading BOM, so specify utf-8-sig, not utf-8
    with open(unit_file, encoding="utf-8-sig", newline="") as csvfile:
        reader = csv.DictReader(csvfile, dialect="excel")
        for row in reader:
            unit_name = row["unit"]
            unit_head = row["unit_head"]
            unit = Unit.objects.get(name__exact=unit_name)
            manager = find_employee_by_name(self, unit_head)
            unit.manager = manager
            unit.save()


def find_employee_by_name(self, employee_name):
    """
    Find Employee with the given name, using data from the employees csv file.
    """
    last_name, first_name = _split_name(employee_name)
    try:
        employee = Employee.objects.get(
            user=User.objects.get(
                last_name__exact=last_name, first_name__exact=first_name
            )
        )
        return employee
    except ObjectDoesNotExist:
        self.stderr.write(f"\tERROR: {employee_name} not found")


def _split_name(employee_name):
    """
    Utility method for splitting 'Last, First' into 'Last' and 'First'.
    """
    last_name, first_name = [word.strip() for word in employee_name.split(",")]
    return (last_name, first_name)


class Command(BaseCommand):
    help = "Add unit heads from CSV to units in database."

    def add_arguments(self, parser):
        parser.add_argument("unit_file")

    def handle(self, *args, **options):
        unit_file = options["unit_file"]
        add_unit_heads(self, unit_file)
