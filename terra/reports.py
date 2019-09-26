from django.core.exceptions import ObjectDoesNotExist
from django.db.models import F, Q, Sum, Value, OuterRef, Subquery, DecimalField, ExpressionWrapper, IntegerField
from django.db.models.functions import Coalesce, ExtractDay

from .models import TravelRequest, Employee, Approval, ActualExpense
from .utils import fiscal_year_bookends


def check_dates(start_date, end_date):
    if start_date is None and end_date is None:
        start_date, end_date = fiscal_year_bookends()
    elif start_date is None or end_date is None:
        raise Exception("You must include a start and end date or leave both empty")
    elif end_date < start_date:
        raise Exception("Start date must come before end date")
    return start_date, end_date


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


def get_individual_data(employee_ids, start_date=None, end_date=None):
    start_date, end_date = check_dates(start_date, end_date)
    # 4 subqueries plugged into the final query

    profdev_alloc = TravelRequest.objects.filter(
        traveler=OuterRef("pk"),
        administrative=False,
        closed=False,
        departure_date__gte=start_date,
        return_date__lte=end_date,
    ).annotate(profdev_alloc=Sum("approval__amount"))

    profdev_expend = TravelRequest.objects.filter(
        traveler=OuterRef("pk"),
        administrative=False,
        closed=True,
        departure_date__gte=start_date,
        return_date__lte=end_date,
    ).annotate(profdev_expend=Sum("actualexpense__total"))

    admin_alloc = TravelRequest.objects.filter(
        traveler=OuterRef("pk"),
        administrative=True,
        closed=False,
        departure_date__gte=start_date,
        return_date__lte=end_date,
    ).annotate(admin_alloc=Sum("approval__amount"))

    admin_expend = TravelRequest.objects.filter(
        traveler=OuterRef("pk"),
        administrative=True,
        closed=True,
        departure_date__gte=start_date,
        return_date__lte=end_date,
    ).annotate(admin_expend=Sum("actualexpense__total"))

    # A new subquery for vacations.  Date math needs an Expresssion.
    duration = ExpressionWrapper(ExtractDay(F("vacation__end")) - ExtractDay(F("vacation__start")),output_field=IntegerField())
    vacation_days = TravelRequest.objects.filter(
        traveler=OuterRef("pk")
    ).annotate(vacation_days=Sum(duration))

    # TODO: Replace this platform-specific hack, maybe with custom db Func()
    MYSQL_TO_DAYS = 86400 * 1000000
    vacation_days = TravelRequest.objects.filter(
        traveler=OuterRef("pk")
    ).annotate(vacation_days=Sum(F("vacation__end")-F("vacation__start"), output_field=IntegerField()) / MYSQL_TO_DAYS)

    # final query
    rows = (
        Employee.objects.filter(pk__in=employee_ids)
        .annotate(
            profdev_alloc=Coalesce(
                Subquery(
                    profdev_alloc.values("profdev_alloc")[:1],
                    output_field=DecimalField(),
                ),
                Value(0),
            ),
            profdev_expend=Coalesce(
                Subquery(
                    profdev_expend.values("profdev_expend")[:1],
                    output_field=DecimalField(),
                ),
                Value(0),
            ),
            admin_alloc=Coalesce(
                Subquery(
                    admin_alloc.values("admin_alloc")[:1], output_field=DecimalField()
                ),
                Value(0),
            ),
            admin_expend=Coalesce(
                Subquery(
                    admin_expend.values("admin_expend")[:1], output_field=DecimalField()
                ),
                Value(0),
            ),
            vacation_days=Coalesce(
                Subquery(
                    vacation_days.values("vacation_days")[:1]
                ),
                Value(0),
            ),
        )
        .values("id", "profdev_alloc", "profdev_expend", "admin_alloc", "admin_expend", "vacation_days")
    )
    return rows


def merge_data(rows, data):
    for subunit in data["subunits"].values():
        for employee in subunit["employees"].values():
            try:
                employee.data = rows.get(id=employee.id)
                employee.data["admin_alloc"] += employee.data["admin_expend"]
                employee.data["profdev_alloc"] += employee.data["profdev_expend"]
                employee.data["total_alloc"] = (
                    employee.data["admin_alloc"] + employee.data["profdev_alloc"]
                )
                employee.data["total_expend"] = (
                    employee.data["admin_expend"] + employee.data["profdev_expend"]
                )
            except ObjectDoesNotExist:
                employee.data = {
                    "admin_alloc": 0,
                    "admin_expend": 0,
                    "profdev_alloc": 0,
                    "profdev_expend": 0,
                    "total_alloc": 0,
                    "total_expend": 0,
                    "vacation_days": 0,
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
        "vacation_days": sum(e.data["vacation_days"] for e in employees),
    }


def calculate_totals(data):
    data["unit_totals"] = {
        "admin_alloc": 0,
        "admin_expend": 0,
        "profdev_alloc": 0,
        "profdev_expend": 0,
        "total_alloc": 0,
        "total_expend": 0,
        "vacation_days": 0,
    }
    for subunit in data["subunits"].values():
        subunit["subunit_totals"] = unit_totals(subunit["employees"].values())
        for key in data["unit_totals"].keys():
            data["unit_totals"][key] += subunit["subunit_totals"][key]
    return data


def unit_report(unit, start_date=None, end_date=None):
    data = get_subunits_and_employees(unit)
    rows = get_individual_data([e.id for e in unit.all_employees()])
    data = merge_data(rows, data)
    return calculate_totals(data)


def get_fund_employee_list(fund, start_date=None, end_date=None):
    start_date, end_date = check_dates(start_date, end_date)
    rows = Approval.objects.filter(
        fund=fund, treq__return_date__gte=start_date, treq__return_date__lte=end_date
    ).values(eid=F("treq__traveler"))
    rows2 = ActualExpense.objects.filter(
        fund=fund, treq__return_date__gte=start_date, treq__return_date__lte=end_date
    ).values(eid=F("treq__traveler"))
    return set([e["eid"] for e in rows.union(rows2)])


def get_individual_data_for_fund(employee_ids, fund, start_date=None, end_date=None):
    start_date, end_date = check_dates(start_date, end_date)

    # 4 subqueries plugged into the final query
    profdev_alloc = TravelRequest.objects.filter(
        traveler=OuterRef("pk"),
        administrative=False,
        closed=False,
        departure_date__gte=start_date,
        return_date__lte=end_date,
    ).annotate(profdev_alloc=Sum("approval__amount", filter=Q(approval__fund=fund)))

    profdev_expend = TravelRequest.objects.filter(
        traveler=OuterRef("pk"),
        administrative=False,
        closed=True,
        departure_date__gte=start_date,
        return_date__lte=end_date,
    ).annotate(
        profdev_expend=Sum("actualexpense__total", filter=Q(actualexpense__fund=fund))
    )

    admin_alloc = TravelRequest.objects.filter(
        traveler=OuterRef("pk"),
        administrative=True,
        closed=False,
        departure_date__gte=start_date,
        return_date__lte=end_date,
    ).annotate(admin_alloc=Sum("approval__amount"), filter=Q(approval__fund=fund))

    admin_expend = TravelRequest.objects.filter(
        traveler=OuterRef("pk"),
        administrative=True,
        closed=True,
        departure_date__gte=start_date,
        return_date__lte=end_date,
    ).annotate(
        admin_expend=Sum("actualexpense__total", filter=Q(actualexpense__fund=fund))
    )

    # final query
    rows = Employee.objects.filter(pk__in=employee_ids).annotate(
        profdev_alloc=Coalesce(
            Subquery(
                profdev_alloc.values("profdev_alloc")[:1], output_field=DecimalField()
            ),
            Value(0),
        ),
        profdev_expend=Coalesce(
            Subquery(
                profdev_expend.values("profdev_expend")[:1], output_field=DecimalField()
            ),
            Value(0),
        ),
        admin_alloc=Coalesce(
            Subquery(
                admin_alloc.values("admin_alloc")[:1], output_field=DecimalField()
            ),
            Value(0),
        ),
        admin_expend=Coalesce(
            Subquery(
                admin_expend.values("admin_expend")[:1], output_field=DecimalField()
            ),
            Value(0),
        ),
    )
    return rows


def calculate_fund_totals(employees):
    totals = {
        "admin_alloc": 0,
        "admin_expend": 0,
        "profdev_alloc": 0,
        "profdev_expend": 0,
        "total_alloc": 0,
        "total_expend": 0,
    }
    for e in employees:
        e.profdev_alloc += e.profdev_expend
        e.admin_alloc += e.admin_expend
        e.total_alloc = e.profdev_alloc + e.admin_alloc
        e.total_expend = e.profdev_expend + e.admin_expend
        totals["profdev_alloc"] += e.profdev_alloc
        totals["profdev_expend"] += e.profdev_expend
        totals["admin_alloc"] += e.admin_alloc
        totals["admin_expend"] += e.admin_expend
    totals["total_alloc"] = totals["admin_alloc"] + totals["profdev_alloc"]
    totals["total_expend"] = totals["admin_expend"] + totals["profdev_expend"]
    return employees, totals


def fund_report(fund, start_date=None, end_date=None):
    eids = get_fund_employee_list(fund, start_date, end_date)
    employee_data = get_individual_data_for_fund(eids, fund, start_date, end_date)
    return calculate_fund_totals(employee_data)
