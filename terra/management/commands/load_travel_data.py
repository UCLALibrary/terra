from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from terra.models import (
    Activity,
    ActualExpense,
    Approval,
    Employee,
    Fund,
    FundAmount,
    TravelRequest,
    Unit,
)

import csv


def load_data(self, travel_file):
    """
    Loads historical data: Activities, Funds, TravelRequests.
    """
    self.stdout.write(f"Parsing {travel_file}")
    # Windows-derived CSV has leading BOM, so specify utf-8-sig, not utf-8
    with open(travel_file, encoding="utf-8-sig", newline="") as csvfile:
        reader = csv.DictReader(csvfile, dialect="excel")
        # Placeholder name until employee data is consistent
        fake_employee = _create_placeholder_employee(self)
        # Field names from CSV, for reference:
        for row in reader:
            # Get relevant data from CSV, with placeholders for now as needed
            employee_name = row["employee_name"]
            ucla_id = row["ucla_id"]
            purpose = row["purpose"]
            start_date = row["begin_travel_date"]
            end_date = row["end_travel_date"]
            workdays = row["workdays"]
            account = row["account"]
            cost_center = row["cc"]
            fund_part = row["fund"]
            fau_approver = row["fau_approver"]
            amount = row["amount"]

            self.stdout.write(f"\tProcessing row {reader.line_num}...")

            # Activity
            # Activities are not unique, so check for existence
            activity, created = Activity.objects.get_or_create(
                name=purpose, start=start_date, end=end_date
            )

            # Funds next
            # Funds are not unique, so check for existence
            fund, created = Fund.objects.get_or_create(
                account=account,
                cost_center=cost_center,
                fund=fund_part,
                manager=fake_employee,
            )

            # TravelRequest
            try:
                traveler = Employee.objects.get(uid__exact=ucla_id)
                treq = TravelRequest.objects.create(
                    traveler=traveler,
                    activity=activity,
                    departure_date=start_date,
                    return_date=end_date,
                    days_ooo=workdays,
                    closed=True,
                )
            except Employee.DoesNotExist:
                raise CommandError(f"Employee {employee_name} does not exist")

            # FundAmount
            fa = FundAmount.objects.create(
                treq=treq,
                fund=fund,
                amount=amount
            )

            # Approval
            approval = Approval.objects.create(
                timestamp=start_date,  # We don't have accurate data
                approver=fake_employee,  # Use fau_approver when data is fixed
                treq=treq,
                type="S",  # Can we be more accurate?
            )

            # ActualExpense
            expense = ActualExpense.objects.create(
                treq=treq,
                type="OTH",  # We only have aggregate data
                rate=1,  # Or blank?
                quantity=1,  # Or blank?
                total=amount,
                fund=fund,
            )


def _create_placeholder_employee(self):
    """
    Creates fake Employee for use as a placeholder until data cleanup is finished.
    """
    fake_user, created = User.objects.get_or_create(
        username="fakeuser",
        email="fakeuser@example.com",
        first_name="Fakey",
        last_name="McFakester",
    )
    fake_employee, created = Employee.objects.get_or_create(
        user=fake_user, unit=Unit.objects.get(name__exact="DIIT"), uid="000000000"
    )
    return fake_employee


class Command(BaseCommand):
    help = "Load historical travel data from CSV into database"

    def add_arguments(self, parser):
        parser.add_argument("travel_file")

    def handle(self, *args, **options):
        travel_file = options["travel_file"]
        load_data(self, travel_file)
