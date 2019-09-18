from django.core.exceptions import ObjectDoesNotExist
from django.db.models import F, Q, Sum, Value
from django.db.models.functions import Coalesce

from .models import TravelRequest, Employee
from .utils import fiscal_year_bookends


def get_subunits_and_employees(unit):
    data = {
        "subunits": {
            unit.id: {
                "subunit": unit,
                "employees": {e.id: e for e in unit.employee_set.all()},
            }
        }
    }
    for subunit in unit.subunits.all():
        data["subunits"][subunit.id] = {
            "subunit": subunit,
            "employees": {e.id: e for e in subunit.all_employees()},
        }
    return data


def get_individual_data(employees, start_date=None, end_date=None):
    if start_date is None and end_date is None:
        start_date, end_date = fiscal_year_bookends()
    elif start_date is None or end_date is None:
        raise Exception("You must include a start and end date or leave both empty")
    elif end_date < start_date:
        raise Exception("Start date must come before end date")
    rows = (
        TravelRequest.objects.filter(
            traveler__in=employees,
            departure_date__gte=start_date,
            return_date__lte=end_date,
            approval__type="F",
        )
        .values(employee_id=F("traveler__id"))
        .annotate(
            admin_alloc=Coalesce(
                Sum("estimatedexpense__total", filter=Q(administrative=True)), Value(0)
            )
        )
        .annotate(
            profdev_alloc=Coalesce(
                Sum("estimatedexpense__total", filter=Q(administrative=False)), Value(0)
            )
        )
        .annotate(total_alloc=Coalesce(Sum("estimatedexpense__total"), Value(0)))
        .annotate(
            admin_expend=Coalesce(
                Sum("actualexpense__total", filter=Q(administrative=True)), Value(0)
            )
        )
        .annotate(
            profdev_expend=Coalesce(
                Sum("actualexpense__total", filter=Q(administrative=False)), Value(0)
            )
        )
        .annotate(total_expend=Coalesce(Sum("actualexpense__total"), Value(0)))
    )
    return rows


def merge_data(rows, data):
    for subunit in data["subunits"].values():
        for employee in subunit["employees"].values():
            try:
                employee.data = rows.get(employee_id=employee.id)
            except ObjectDoesNotExist:
                employee.data = {
                    "admin_alloc": 0,
                    "admin_expend": 0,
                    "profdev_alloc": 0,
                    "profdev_expend": 0,
                    "total_alloc": 0,
                    "total_expend": 0,
                }
    return data


def unit_totals(employees):
    return {
        "profdev_alloc": sum(e.data["profdev_alloc"] for e in employees),
        "admin_alloc": sum(e.data["admin_alloc"] for e in employees),
        "total_alloc": sum(e.data["total_alloc"] for e in employees),
        "profdev_expend": sum(e.data["profdev_expend"] for e in employees),
        "admin_expend": sum(e.data["admin_expend"] for e in employees),
        "total_expend": sum(e.data["total_expend"] for e in employees),
    }


def calculate_totals(data):
    data["unit_totals"] = {
        "admin_alloc": 0,
        "admin_expend": 0,
        "profdev_alloc": 0,
        "profdev_expend": 0,
        "total_alloc": 0,
        "total_expend": 0,
    }
    for subunit in data["subunits"].values():
        subunit["subunit_totals"] = unit_totals(subunit["employees"].values())
        for key in data["unit_totals"].keys():
            data["unit_totals"][key] += subunit["subunit_totals"][key]
    return data


def unit_report(unit, start_date=None, end_date=None):
    data = get_subunits_and_employees(unit)
    rows = get_individual_data(unit.all_employees())
    data = merge_data(rows, data)
    return calculate_totals(data)
