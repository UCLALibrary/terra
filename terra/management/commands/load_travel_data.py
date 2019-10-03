from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from terra.models import (
    Activity,
    ActualExpense,
    Approval,
    Employee,
    EstimatedExpense,
    Fund,
    TravelRequest,
    Unit,
)

from datetime import datetime
import csv, pytz


def load_data(self, travel_file):
    """
    Loads historical data: everything except units.
    """
    # For now, we need a fake employee to use as fund manager.
    fund_manager = _create_placeholder_employee()
    unit_head = fund_manager
    self.stdout.write(f"Parsing {travel_file}")
    # Windows-derived CSV has leading BOM, so specify utf-8-sig, not utf-8
    with open(travel_file, encoding="utf-8-sig", newline="") as csvfile:
        reader = csv.DictReader(csvfile, dialect="excel")
        # Field names from CSV, for reference:
        # employee_name,employee_id,ucla_id,email,start_date,end_date,workdays,vac_days,t_and_e,purpose,department,unit_head,supervisor,aul,account,cc,fund,amount_approved,amount_paid
        for row in reader:
            # Get relevant data from CSV, with placeholders for now as needed
            employee_name = row["employee_name"]
            email = row["email"]
            ucla_id = row["ucla_id"]
            department = row["department"]
            purpose = row["purpose"]
            start_date = row["start_date"]
            end_date = row["end_date"]
            workdays = row["workdays"]
            account = row["account"]
            cost_center = row["cc"]
            fund_part = row["fund"]
            amount_approved = row["amount_approved"]
            amount_paid = row["amount_paid"]

            # Clean up bad input data
            start_date = _convert_MDY(start_date)
            end_date = _convert_MDY(end_date)
            if workdays == "":
                workdays = 0

            # Don't include CSV header rows in line number
            line_num = reader.line_num - 1
            self.stdout.write(f"\tProcessing row {line_num}...")

            # User & Employee
            user = _get_user(employee_name, email)
            # Employees must have units; fetch from database
            unit = Unit.objects.get(name__exact=department)
            employee = _get_employee(user, ucla_id, unit)

            # Activity
            activity = _get_activity(purpose, start_date, end_date)

            # Fund
            fund = _get_fund(account, cost_center, fund_part, fund_manager)

            # TravelRequest
            treq = _get_treq(employee, activity, start_date, end_date, workdays)

            # Approval/funding
            # start_date was changed from "naive" to "aware" above, to avoid warnings, but doesn't matter since Approval.approved_on is an automatic timestamp.....
            if amount_approved != "":
                approval = _get_funding_approval(start_date, unit_head, treq, fund, amount_approved)

            # Expenses: Create only if data present, not blank
            if amount_approved != "":
                est_expense = _get_estimated_expense(treq, amount_approved)
            if amount_paid != "":
                act_expense = _get_actual_expense(treq, amount_paid, fund)
            

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


def _get_employee(user, ucla_id, unit):
    employee, created = Employee.objects.get_or_create(user=user, uid=ucla_id, unit=unit)
    return employee

def _get_activity(purpose, start_date, end_date):
    activity, created = Activity.objects.get_or_create(
        name=purpose, start=start_date, end=end_date
    )
    return activity

def _get_fund(account, cost_center, fund_part, fund_manager):
    fund, created = Fund.objects.get_or_create(account=account, cost_center=cost_center, fund=fund_part, manager=fund_manager)
    return fund


def _get_treq(employee, activity, start_date, end_date, workdays):
    treq, created = TravelRequest.objects.get_or_create(traveler=employee, activity=activity, departure_date=start_date, return_date=end_date, days_ooo=workdays)
    return treq

def _get_funding_approval(approval_date, approved_by, treq, fund, amount_approved):
    approval, created = Approval.objects.get_or_create(approved_on=approval_date, approved_by=approved_by, treq=treq, fund=fund, amount=amount_approved)
    return approval

def _get_actual_expense(treq, amount, fund):
    # Create, without check for existing
    expense = ActualExpense.objects.create(treq=treq, total=amount, fund=fund, type="OTH", rate=1, quantity=1)
    return expense

def _get_estimated_expense(treq, amount):
    # Create, without check for existing
    expense = EstimatedExpense.objects.create(treq=treq, total=amount, type="OTH", rate=1, quantity=1)
    return expense



def _convert_MDY(MDY_string):
    """
    Utility method for converting naive m/d/y strings to aware datetimes.
    Forces time to noon, and applies America/LA time zone.
    """
    d = datetime.strptime(MDY_string + " 12", "%m/%d/%Y %H")
    tz = pytz.timezone("America/Los_Angeles")
    d = tz.localize(d)
    return d

def _split_name(employee_name):
    """
    Utility method for splitting 'Last, First' into 'Last' and 'First'.
    """
    last_name, first_name = [word.strip() for word in employee_name.split(',')]
    return (last_name, first_name)


def _create_placeholder_employee():
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
        user=fake_user, unit=Unit.objects.get(name__exact="Library Business Services"), uid="000000000"
    )
    return fake_employee


class Command(BaseCommand):
    help = "Load historical travel data from CSV into database"

    def add_arguments(self, parser):
        parser.add_argument("travel_file")

    def handle(self, *args, **options):
        travel_file = options["travel_file"]
        load_data(self, travel_file)
