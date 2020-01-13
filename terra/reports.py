from django.core.exceptions import ObjectDoesNotExist
from django.db.models import (
    F,
    Q,
    Sum,
    Value,
    OuterRef,
    Subquery,
    DecimalField,
    ExpressionWrapper,
    IntegerField,
)
from django.db.models.functions import Coalesce, ExtractDay

from .models import TravelRequest, Employee, Funding, ActualExpense, EMPLOYEE_TYPES
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

    profdev_requested = (
        TravelRequest.objects.filter(
            traveler=OuterRef("pk"),
            administrative=False,
            departure_date__gte=start_date,
            return_date__lte=end_date,
        )
        .values("traveler__pk")
        .annotate(profdev_requested=Sum("funding__amount"))
        .values("profdev_requested")
    )

    profdev_spent = (
        TravelRequest.objects.filter(
            traveler=OuterRef("pk"),
            administrative=False
        )
        .values("traveler__pk")
        .annotate(profdev_spent=Sum("actualexpense__total", 
            filter=Q(actualexpense__date_paid__lte=end_date) & Q(actualexpense__date_paid__gte=start_date)
            ))
        .values("profdev_spent")
    )

    admin_requested = (
        TravelRequest.objects.filter(
            traveler=OuterRef("pk"),
            administrative=True,
            departure_date__gte=start_date,
            return_date__lte=end_date,
        )
        .values("traveler__pk")
        .annotate(admin_requested=Sum("funding__amount"))
        .values("admin_requested")
    )

    admin_spent = (
        TravelRequest.objects.filter(
            traveler=OuterRef("pk"),
            administrative=True
        )
        .values("traveler__pk")
        .annotate(admin_spent=Sum("actualexpense__total", 
            filter=Q(actualexpense__date_paid__lte=end_date) & Q(actualexpense__date_paid__gte=start_date)
            ))
        .values("admin_spent")
    )

    days_vacation = TravelRequest.objects.filter(
        traveler=OuterRef("pk"),
        departure_date__gte=start_date,
        return_date__lte=end_date,
    ).annotate(days_vacation=Sum("vacation__duration"))

    days_away = (
        TravelRequest.objects.filter(
            traveler=OuterRef("pk"),
            departure_date__gte=start_date,
            return_date__lte=end_date,
        )
        .values("traveler_id")
        .annotate(days_away=Sum("days_ooo"))
    )

    # final query

    rows = (
        Employee.objects.filter(pk__in=employee_ids)
        .annotate(
            profdev_requested=Coalesce(
                Subquery(profdev_requested, output_field=DecimalField()), Value(0)
            ),
            profdev_spent=Coalesce(
                Subquery(profdev_spent, output_field=DecimalField()), Value(0)
            ),
            admin_requested=Coalesce(
                Subquery(admin_requested, output_field=DecimalField()), Value(0)
            ),
            admin_spent=Coalesce(
                Subquery(admin_spent, output_field=DecimalField()), Value(0)
            ),
            days_vacation=Coalesce(
                Subquery(
                    days_vacation.values("days_vacation")[:1],
                    output_field=IntegerField(),
                ),
                Value(0),
            ),
            days_away=Coalesce(
                Subquery(
                    days_away.values("days_away")[:1], output_field=IntegerField()
                ),
                Value(0),
            ),
        )
        .values(
            "id",
            "profdev_requested",
            "profdev_spent",
            "admin_requested",
            "admin_spent",
            "days_vacation",
            "days_away",
        )
    )
    return rows


def merge_data(rows, data):
    for subunit in data["subunits"].values():
        for employee in subunit["employees"].values():
            try:
                employee.data = rows.get(id=employee.id)
                employee.data["admin_requested"]
                employee.data["profdev_requested"]
                employee.data["total_requested"] = (
                    employee.data["admin_requested"] + employee.data["profdev_requested"]
                )
                employee.data["total_spent"] = (
                    employee.data["admin_spent"] + employee.data["profdev_spent"]
                )
                employee.data["total_days_ooo"] = (
                    employee.data["days_away"] + employee.data["days_vacation"]
                )
            except ObjectDoesNotExist:
                employee.data = {
                    "admin_requested": 0,
                    "admin_spent": 0,
                    "days_away": 0,
                    "days_vacation": 0,
                    "profdev_requested": 0,
                    "profdev_spent": 0,
                    "total_requested": 0,
                    "total_days_ooo": 0,
                    "total_spent": 0,
                }
    return data


def unit_totals(employees):
    return {
        "profdev_requested": sum(e.data["profdev_requested"] for e in employees),
        "admin_requested": sum(e.data["admin_requested"] for e in employees),
        "total_requested": sum(e.data["total_requested"] for e in employees),
        "profdev_spent": sum(e.data["profdev_spent"] for e in employees),
        "admin_spent": sum(e.data["admin_spent"] for e in employees),
        "total_spent": sum(e.data["total_spent"] for e in employees),
        "days_vacation": sum(e.data["days_vacation"] for e in employees),
        "days_away": sum(e.data["days_away"] for e in employees),
        "total_days_ooo": sum(e.data["total_days_ooo"] for e in employees),
    }


def calculate_totals(data):
    data["unit_totals"] = {
        "admin_requested": 0,
        "admin_spent": 0,
        "days_away": 0,
        "days_vacation": 0,
        "profdev_requested": 0,
        "profdev_spent": 0,
        "total_requested": 0,
        "total_days_ooo": 0,
        "total_spent": 0,
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
    rows = Funding.objects.filter(
        fund=fund, treq__return_date__gte=start_date, treq__return_date__lte=end_date
    ).values(eid=F("treq__traveler"))
    rows2 = ActualExpense.objects.filter(
        fund=fund, treq__return_date__gte=start_date, treq__return_date__lte=end_date
    ).values(eid=F("treq__traveler"))
    return set([e["eid"] for e in rows.union(rows2)])


def get_individual_data_for_fund(employee_ids, fund, start_date=None, end_date=None):
    start_date, end_date = check_dates(start_date, end_date)

    # 4 subqueries plugged into the final query
    profdev_alloc = (
        TravelRequest.objects.filter(
            traveler=OuterRef("pk"),
            administrative=False,
            closed=False,
            departure_date__gte=start_date,
            return_date__lte=end_date,
        )
        .values("traveler__pk")
        .annotate(profdev_alloc=Sum("funding__amount", filter=Q(funding__fund=fund)))
        .values("profdev_alloc")
    )

    profdev_expend = (
        TravelRequest.objects.filter(
            traveler=OuterRef("pk"),
            administrative=False,
            closed=True,
            departure_date__gte=start_date,
            return_date__lte=end_date,
        )
        .values("traveler__pk")
        .annotate(
            profdev_expend=Sum(
                "actualexpense__total", filter=Q(actualexpense__fund=fund)
            )
        )
        .values("profdev_expend")
    )

    admin_alloc = (
        TravelRequest.objects.filter(
            traveler=OuterRef("pk"),
            administrative=True,
            closed=False,
            departure_date__gte=start_date,
            return_date__lte=end_date,
        )
        .values("traveler__pk")
        .annotate(admin_alloc=Sum("funding__amount"), filter=Q(funding__fund=fund))
        .values("admin_alloc")
    )

    admin_expend = (
        TravelRequest.objects.filter(
            traveler=OuterRef("pk"),
            administrative=True,
            closed=True,
            departure_date__gte=start_date,
            return_date__lte=end_date,
        )
        .values("traveler__pk")
        .annotate(
            admin_expend=Sum("actualexpense__total", filter=Q(actualexpense__fund=fund))
        )
        .values("admin_expend")
    )

    # final query
    rows = Employee.objects.filter(pk__in=employee_ids).annotate(
        profdev_alloc=Coalesce(
            Subquery(profdev_alloc, output_field=DecimalField()), Value(0)
        ),
        profdev_expend=Coalesce(
            Subquery(profdev_expend, output_field=DecimalField()), Value(0)
        ),
        admin_alloc=Coalesce(
            Subquery(admin_alloc, output_field=DecimalField()), Value(0)
        ),
        admin_expend=Coalesce(
            Subquery(admin_expend, output_field=DecimalField()), Value(0)
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


def get_type_and_employees():
    type_dict = {
        "University Librarian": [],
        "Executive": [],
        "Unit Head": [],
        "Librarian": [],
        "Sr. Exempt Staff": [],
        "Other": [],
    }
    employees = Employee.objects.order_by("unit")
    for employee in employees:
        if employee.get_type_display() in type_dict:
            type_dict[employee.get_type_display()].append(employee)

    return type_dict


def get_individual_data_type(employee_ids, start_date=None, end_date=None):

    # 4 subqueries plugged into the final query

    profdev_alloc = (
        TravelRequest.objects.filter(
            traveler=OuterRef("pk"),
            administrative=False,
            closed=False,
            departure_date__gte=start_date,
            return_date__lte=end_date,
        )
        .values("traveler__pk")
        .annotate(profdev_alloc=Sum("funding__amount"))
        .values("profdev_alloc")
    )

    profdev_expend = (
        TravelRequest.objects.filter(
            traveler=OuterRef("pk"),
            administrative=False,
            closed=True,
            departure_date__gte=start_date,
            return_date__lte=end_date,
        )
        .values("traveler__pk")
        .annotate(profdev_expend=Sum("actualexpense__total"))
        .values("profdev_expend")
    )

    admin_alloc = (
        TravelRequest.objects.filter(
            traveler=OuterRef("pk"),
            administrative=True,
            closed=False,
            departure_date__gte=start_date,
            return_date__lte=end_date,
        )
        .values("traveler__pk")
        .annotate(admin_alloc=Sum("funding__amount"))
        .values("admin_alloc")
    )

    admin_expend = (
        TravelRequest.objects.filter(
            traveler=OuterRef("pk"),
            administrative=True,
            closed=True,
            departure_date__gte=start_date,
            return_date__lte=end_date,
        )
        .values("traveler__pk")
        .annotate(admin_expend=Sum("actualexpense__total"))
        .values("admin_expend")
    )

    days_vacation = TravelRequest.objects.filter(
        traveler=OuterRef("pk"),
        departure_date__gte=start_date,
        return_date__lte=end_date,
    ).annotate(days_vacation=Sum("vacation__duration"))

    days_away = (
        TravelRequest.objects.filter(
            traveler=OuterRef("pk"),
            departure_date__gte=start_date,
            return_date__lte=end_date,
        )
        .values("traveler_id")
        .annotate(days_away=Sum("days_ooo"))
    )

    # final query
    rows = (
        Employee.objects.filter(pk__in=employee_ids)
        .annotate(
            profdev_alloc=Coalesce(
                Subquery(profdev_alloc, output_field=DecimalField()), Value(0)
            ),
            profdev_expend=Coalesce(
                Subquery(profdev_expend, output_field=DecimalField()), Value(0)
            ),
            admin_alloc=Coalesce(
                Subquery(admin_alloc, output_field=DecimalField()), Value(0)
            ),
            admin_expend=Coalesce(
                Subquery(admin_expend, output_field=DecimalField()), Value(0)
            ),
            days_vacation=Coalesce(
                Subquery(
                    days_vacation.values("days_vacation")[:1],
                    output_field=IntegerField(),
                ),
                Value(0),
            ),
            days_away=Coalesce(
                Subquery(
                    days_away.values("days_away")[:1], output_field=IntegerField()
                ),
                Value(0),
            ),
        )
        .values(
            "id",
            "profdev_alloc",
            "profdev_expend",
            "admin_alloc",
            "admin_expend",
            "days_vacation",
            "days_away",
        )
    )
    return rows


def merge_data_type(employee_ids, start_date, end_date):

    type_dict = get_type_and_employees()
    rows = get_individual_data_type(employee_ids, start_date, end_date)
    data = {
        "type": {
            "University Librarian": {"employees": [], "totals": {}},
            "Executive": {"employees": [], "totals": {}},
            "Unit Head": {"employees": [], "totals": {}},
            "Librarian": {"employees": [], "totals": {}},
            "Sr. Exempt Staff": {"employees": [], "totals": {}},
            "Other": {"employees": [], "totals": {}},
        },
        "all_type_total": {},
    }

    for employee_type in type_dict:
        for e in type_dict[employee_type]:
            try:
                employee = rows.get(id=e.id)
                employee["name"] = e.__str__()
                employee["unit"] = e.unit.__str__()
                employee["unit_manager"] = e.unit.manager.__str__()
                employee["admin_alloc"] += employee["admin_expend"]
                employee["profdev_alloc"] += employee["profdev_expend"]
                employee["total_alloc"] = (
                    employee["admin_alloc"] + employee["profdev_alloc"]
                )
                employee["total_expend"] = (
                    employee["admin_expend"] + employee["profdev_expend"]
                )
                employee["total_days_ooo"] = (
                    employee["days_away"] + employee["days_vacation"]
                )

            except ObjectDoesNotExist:
                employee = {
                    "admin_alloc": 0,
                    "admin_expend": 0,
                    "days_away": 0,
                    "days_vacation": 0,
                    "profdev_alloc": 0,
                    "profdev_expend": 0,
                    "total_alloc": 0,
                    "total_days_ooo": 0,
                    "total_expend": 0,
                }
            data["type"][employee_type]["employees"].append(employee)

    for employee_type in data["type"]:
        type_totals = {
            "admin_alloc": 0,
            "admin_expend": 0,
            "days_away": 0,
            "days_vacation": 0,
            "profdev_alloc": 0,
            "profdev_expend": 0,
            "total_alloc": 0,
            "total_days_ooo": 0,
            "total_expend": 0,
        }
        # add a totals dictionary for each employee type
        for employee in data["type"][employee_type]["employees"]:
            type_totals["admin_alloc"] += employee["admin_alloc"]
            type_totals["admin_expend"] += employee["admin_expend"]
            type_totals["days_away"] += employee["days_away"]
            type_totals["days_vacation"] += employee["days_vacation"]
            type_totals["profdev_alloc"] += employee["profdev_alloc"]
            type_totals["profdev_expend"] += employee["profdev_expend"]
            type_totals["total_alloc"] += employee["total_alloc"]
            type_totals["total_days_ooo"] += employee["total_days_ooo"]
            type_totals["total_expend"] += employee["total_expend"]
        data["type"][employee_type]["totals"] = type_totals

    complete_total = {
        "admin_alloc": 0,
        "admin_expend": 0,
        "days_away": 0,
        "days_vacation": 0,
        "profdev_alloc": 0,
        "profdev_expend": 0,
        "total_alloc": 0,
        "total_days_ooo": 0,
        "total_expend": 0,
    }

    for t in data["type"]:
        complete_total["admin_alloc"] += data["type"][t]["totals"]["admin_alloc"]
        complete_total["admin_expend"] += data["type"][t]["totals"]["admin_expend"]
        complete_total["days_away"] += data["type"][t]["totals"]["days_away"]
        complete_total["days_vacation"] += data["type"][t]["totals"]["days_vacation"]
        complete_total["profdev_alloc"] += data["type"][t]["totals"]["profdev_alloc"]
        complete_total["profdev_expend"] += data["type"][t]["totals"]["profdev_expend"]
        complete_total["total_alloc"] += data["type"][t]["totals"]["total_alloc"]
        complete_total["total_days_ooo"] += data["type"][t]["totals"]["total_days_ooo"]
        complete_total["total_expend"] += data["type"][t]["totals"]["total_expend"]
    data["all_type_total"] = complete_total

    return data


def get_individual_data_employee(employee_ids, start_date=None, end_date=None):
    start_date, end_date = check_dates(start_date, end_date)
    # 4 subqueries plugged into the final query

    total_estimatedexpense = (
        TravelRequest.objects.filter(
            traveler=OuterRef("pk"),
            departure_date__gte=start_date,
            return_date__lte=end_date,
        )
        .values("traveler__pk")
        .annotate(total_estimatedexpense=Sum("estimatedexpense__total"))
        .values("total_estimatedexpense")
    )

    profdev_alloc = (
        TravelRequest.objects.filter(
            traveler=OuterRef("pk"),
            administrative=False,
            closed=False,
            departure_date__gte=start_date,
            return_date__lte=end_date,
        )
        .values("traveler__pk")
        .annotate(profdev_alloc=Sum("funding__amount"))
        .values("profdev_alloc")
    )

    profdev_expend = (
        TravelRequest.objects.filter(
            traveler=OuterRef("pk"),
            administrative=False,
            closed=True,
            departure_date__gte=start_date,
            return_date__lte=end_date,
        )
        .values("traveler__pk")
        .annotate(profdev_expend=Sum("actualexpense__total"))
        .values("profdev_expend")
    )

    admin_alloc = (
        TravelRequest.objects.filter(
            traveler=OuterRef("pk"),
            administrative=True,
            closed=False,
            departure_date__gte=start_date,
            return_date__lte=end_date,
        )
        .values("traveler__pk")
        .annotate(admin_alloc=Sum("funding__amount"))
        .values("admin_alloc")
    )

    admin_expend = (
        TravelRequest.objects.filter(
            traveler=OuterRef("pk"),
            administrative=True,
            closed=True,
            departure_date__gte=start_date,
            return_date__lte=end_date,
        )
        .values("traveler__pk")
        .annotate(admin_expend=Sum("actualexpense__total"))
        .values("admin_expend")
    )

    days_vacation = TravelRequest.objects.filter(
        traveler=OuterRef("pk"),
        departure_date__gte=start_date,
        return_date__lte=end_date,
    ).annotate(days_vacation=Sum("vacation__duration"))

    days_away = (
        TravelRequest.objects.filter(
            traveler=OuterRef("pk"),
            departure_date__gte=start_date,
            return_date__lte=end_date,
        )
        .values("traveler_id")
        .annotate(days_away=Sum("days_ooo"))
    )

    # final query

    rows = (
        Employee.objects.filter(pk__in=employee_ids)
        .annotate(
            total_estimatedexpense=Coalesce(
                Subquery(total_estimatedexpense, output_field=DecimalField()), Value(0)
            ),
            profdev_alloc=Coalesce(
                Subquery(profdev_alloc, output_field=DecimalField()), Value(0)
            ),
            profdev_expend=Coalesce(
                Subquery(profdev_expend, output_field=DecimalField()), Value(0)
            ),
            admin_alloc=Coalesce(
                Subquery(admin_alloc, output_field=DecimalField()), Value(0)
            ),
            admin_expend=Coalesce(
                Subquery(admin_expend, output_field=DecimalField()), Value(0)
            ),
            days_vacation=Coalesce(
                Subquery(
                    days_vacation.values("days_vacation")[:1],
                    output_field=IntegerField(),
                ),
                Value(0),
            ),
            days_away=Coalesce(
                Subquery(
                    days_away.values("days_away")[:1], output_field=IntegerField()
                ),
                Value(0),
            ),
        )
        .values(
            "id",
            "total_estimatedexpense",
            "profdev_alloc",
            "profdev_expend",
            "admin_alloc",
            "admin_expend",
            "days_vacation",
            "days_away",
        )
    )
    return rows


def employee_total_report(employee_ids, start_date, end_date):
    employee_totals = {}
    rows = get_individual_data_employee(employee_ids, start_date, end_date)
    for e in employee_ids:
        try:
            employee = rows.get(id=e)
            employee["admin_alloc"] += employee["admin_expend"]
            employee["profdev_alloc"] += employee["profdev_expend"]
            employee["total_alloc"] = (
                employee["admin_alloc"] + employee["profdev_alloc"]
            )
            employee["total_expend"] = (
                employee["admin_expend"] + employee["profdev_expend"]
            )
            employee["total_days_ooo"] = (
                employee["days_away"] + employee["days_vacation"]
            )

        except ObjectDoesNotExist:
            employee = {
                "admin_alloc": 0,
                "admin_expend": 0,
                "days_away": 0,
                "days_vacation": 0,
                "total_estimatedexpense": 0,
                "profdev_alloc": 0,
                "profdev_expend": 0,
                "total_alloc": 0,
                "total_days_ooo": 0,
                "total_expend": 0,
            }
        employee_totals[e] = employee

    return employee_totals
