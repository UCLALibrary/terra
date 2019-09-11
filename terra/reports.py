from django.db.models import F, Q, Sum, Value
from django.db.models.functions import Coalesce

from .models import TravelRequest, Employee
from .utils import fiscal_year_bookends


def get_flat_subunit(subunit):
    team = Employee.objects.raw(
        """
        WITH RECURSIVE team(id, parent_unit_id) AS (
                SELECT id, parent_unit_id
                FROM terra_unit
                WHERE id = %s
            UNION ALL
                SELECT u.id, u.parent_unit_id
                FROM team AS t, terra_unit AS u
                WHERE t.id = u.parent_unit_id
            )
        SELECT e.*, first_name, last_name, %s AS subunit_id, %s AS subunit_name  
        FROM terra_employee AS e, terra_unit AS u, auth_user AS user, team
        WHERE e.unit_id = team.id
        AND e.unit_id = u.id
        AND e.user_id = user.id""",
        params=[subunit.id, subunit.id, subunit.name],
    )
    return team


def get_employees(unit):
    employees = {e.id: e for e in unit.employee_set.all()}
    for id, employee in employees.items():
        employee.subunit_id = unit.id
        employee.subunit_name = unit.name
        employee.last_name = employee.user.last_name
        employee.first_name = employee.user.first_name
    for subunit in unit.subunits.all():
        employees.update({e.id: e for e in get_flat_subunit(subunit)})
    return employees


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


def build_output_data_structure(rows, employees):
    data = {
        "subunits": {},
        "unit_totals": {
            "admin_alloc": 0,
            "admin_expend": 0,
            "profdev_alloc": 0,
            "profdev_expend": 0,
            "total_alloc": 0,
            "total_expend": 0,
        },
    }
    # merge query data with employee data
    for row in rows:
        employee = employees[row["employee_id"]]
        employee.data = row
        if employee.subunit_id not in data["subunits"].keys():
            data["subunits"][employee.subunit_id] = {
                "name": employee.subunit_name,
                "staff": {},
                "subunit_totals": {},
            }
        data["subunits"][employee.subunit_id]["staff"][employee.id] = employee
        del employees[employee.id]
    # now deal with remaining (nontraveling) staff
    for employee in employees.values():
        employee.data = {
            "admin_alloc": 0,
            "admin_expend": 0,
            "profdev_alloc": 0,
            "profdev_expend": 0,
            "total_alloc": 0,
            "total_expend": 0,
        }
        if employee.subunit_id not in data["subunits"].keys():
            data["subunits"][employee.subunit_id] = {
                "name": employee.subunit_name,
                "staff": {},
                "subunit_totals": {},
            }
        data["subunits"][employee.subunit_id]["staff"][employee.id] = employee
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
    for subunit in data["subunits"].values():
        subunit["subunit_totals"] = unit_totals(subunit["staff"].values())
        for key, value in data["unit_totals"].items():
            data["unit_totals"][key] += subunit["subunit_totals"][key]
    return data


def unit_report(unit, start_date=None, end_date=None):
    employees = get_employees(unit)
    rows = get_individual_data(employees)
    data = build_output_data_structure(rows, employees)
    return calculate_totals(data)
