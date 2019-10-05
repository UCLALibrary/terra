from django.core.management.base import BaseCommand, CommandError
from terra.models import Unit

import csv

def create_units(self, unit_file):
    """
    Does initial creation of Units.
    """
    self.stdout.write(f'Parsing {unit_file}')
    # Windows-derived CSV has leading BOM, so specify utf-8-sig, not utf-8
    with open(unit_file, encoding='utf-8-sig', newline='') as csvfile:
        reader = csv.DictReader(csvfile, dialect='excel')
        for row in reader:
            unit_name = row["unit"]
            unit_type = row["unit_type"]
            unit_parent = row["parent"]
            self.stdout.write(f'Adding {unit_name}...')

            unit = Unit.objects.create(name=unit_name, type=unit_type)
            # These get read from CSV as strings...
            if int(unit_parent) > 0:
                unit.parent_unit = Unit.objects.get(pk=unit_parent)
                unit.save()


class Command(BaseCommand):
    help = 'Load units from CSV into database'

    def add_arguments(self, parser):
        parser.add_argument('unit_file')

    def handle(self, *args, **options):
        unit_file = options['unit_file']
        create_units(self, unit_file)
