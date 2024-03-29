from decimal import Decimal
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import (
    F,
    Q,
    Sum,
    Value,
    OuterRef,
    Subquery,
    DecimalField,
    IntegerField,
)
from django.db.models.functions import Coalesce


from .models import TravelRequest, Employee, Funding, ActualExpense
from .utils import fiscal_year_bookends, profdev_spending_cap, profdev_days_cap


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
        TravelRequest.objects.filter(traveler=OuterRef("pk"), administrative=False)
        .values("traveler__pk")
        .annotate(
            profdev_spent=Sum(
                "actualexpense__total",
                filter=Q(actualexpense__date_paid__lte=end_date)
                & Q(actualexpense__date_paid__gte=start_date),
            )
        )
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
        TravelRequest.objects.filter(traveler=OuterRef("pk"), administrative=True)
        .values("traveler__pk")
        .annotate(
            admin_spent=Sum(
                "actualexpense__total",
                filter=Q(actualexpense__date_paid__lte=end_date)
                & Q(actualexpense__date_paid__gte=start_date),
            )
        )
        .values("admin_spent")
    )

    days_vacation = TravelRequest.objects.filter(
        traveler=OuterRef("pk"),
        departure_date__gte=start_date,
        return_date__lte=end_date,
    ).annotate(days_vacation=Sum("vacation__duration"))

    profdev_days_away = (
        TravelRequest.objects.filter(
            traveler=OuterRef("pk"),
            departure_date__gte=start_date,
            return_date__lte=end_date,
            administrative=False,
            canceled=False,
        )
        .values("traveler_id")
        .annotate(profdev_days_away=Sum("days_ooo"))
    )
    admin_days_away = (
        TravelRequest.objects.filter(
            traveler=OuterRef("pk"),
            departure_date__gte=start_date,
            return_date__lte=end_date,
            administrative=True,
            canceled=False,
        )
        .values("traveler_id")
        .annotate(admin_days_away=Sum("days_ooo"))
    )

    # final query

    rows = (
        Employee.objects.filter(pk__in=employee_ids)
        .annotate(
            profdev_requested=Coalesce(
                Subquery(profdev_requested, output_field=DecimalField()), Decimal(0)
            ),
            profdev_spent=Coalesce(
                Subquery(profdev_spent, output_field=DecimalField()), Decimal(0)
            ),
            admin_requested=Coalesce(
                Subquery(admin_requested, output_field=DecimalField()), Decimal(0)
            ),
            admin_spent=Coalesce(
                Subquery(admin_spent, output_field=DecimalField()), Decimal(0)
            ),
            days_vacation=Coalesce(
                Subquery(
                    days_vacation.values("days_vacation")[:1],
                    output_field=IntegerField(),
                ),
                Value(0),
            ),
            profdev_days_away=Coalesce(
                Subquery(
                    profdev_days_away.values("profdev_days_away")[:1],
                    output_field=IntegerField(),
                ),
                Value(0),
            ),
            admin_days_away=Coalesce(
                Subquery(
                    admin_days_away.values("admin_days_away")[:1],
                    output_field=IntegerField(),
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
            "profdev_days_away",
            "admin_days_away",
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
                    employee.data["admin_requested"]
                    + employee.data["profdev_requested"]
                )
                employee.data["total_spent"] = (
                    employee.data["admin_spent"] + employee.data["profdev_spent"]
                )
                employee.data["total_days_ooo"] = (
                    employee.data["profdev_days_away"]
                    + employee.data["admin_days_away"]
                )
            except ObjectDoesNotExist:
                employee.data = {
                    "admin_requested": 0,
                    "admin_spent": 0,
                    "admin_days_away": 0,
                    "profdev_days_away": 0,
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
        "profdev_days_away": sum(e.data["profdev_days_away"] for e in employees),
        "admin_days_away": sum(e.data["admin_days_away"] for e in employees),
        "total_days_ooo": sum(e.data["total_days_ooo"] for e in employees),
    }


def calculate_totals(data):
    data["unit_totals"] = {
        "admin_requested": 0,
        "admin_spent": 0,
        "admin_days_away": 0,
        "profdev_days_away": 0,
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
    rows = get_individual_data(
        [e.id for e in unit.all_employees()], start_date, end_date
    )
    data = merge_data(rows, data)
    return calculate_totals(data)


def get_treq_list(fund, start_date=None, end_date=None):
    start_date, end_date = check_dates(start_date, end_date)
    funding_rows = Funding.objects.filter(
        fund=fund, treq__departure_date__gte=start_date, treq__return_date__lte=end_date
    ).values(travel=F("treq"))

    actual_expense_rows = ActualExpense.objects.filter(
        fund=fund, date_paid__gte=start_date, date_paid__lte=end_date
    ).values(travel=F("treq"))
    treq_ids = set([e["travel"] for e in funding_rows.union(actual_expense_rows)])
    return treq_ids


def get_individual_data_for_treq(treq_ids, fund, start_date=None, end_date=None):
    start_date, end_date = check_dates(start_date, end_date)

    profdev_requested = (
        Funding.objects.filter(
            treq=OuterRef("pk"),
            fund=fund,
            treq__departure_date__gte=start_date,
            treq__return_date__lte=end_date,
            treq__administrative=False,
        )
        .values("treq__pk")
        .annotate(profdev_requested=Sum("amount", filter=Q(fund=fund)))
        .values("profdev_requested")
    )

    admin_requested = (
        Funding.objects.filter(
            treq=OuterRef("pk"),
            fund=fund,
            treq__departure_date__gte=start_date,
            treq__return_date__lte=end_date,
            treq__administrative=True,
        )
        .values("treq__pk")
        .annotate(admin_requested=Sum("amount", filter=Q(fund=fund)))
        .values("admin_requested")
    )

    profdev_spent = (
        ActualExpense.objects.filter(
            treq=OuterRef("pk"),
            date_paid__lte=end_date,
            date_paid__gte=start_date,
            fund=fund,
            treq__administrative=False,
        )
        .values("treq__pk")
        .annotate(profdev_spent=Sum("total", filter=Q(fund=fund)))
        .values("profdev_spent")
    )

    admin_spent = (
        ActualExpense.objects.filter(
            treq=OuterRef("pk"),
            date_paid__lte=end_date,
            date_paid__gte=start_date,
            fund=fund,
            treq__administrative=True,
        )
        .values("treq__pk")
        .annotate(admin_spent=Sum("total", filter=Q(fund=fund)))
        .values("admin_spent")
    )

    rows = TravelRequest.objects.filter(pk__in=treq_ids).annotate(
        profdev_requested=Coalesce(
            Subquery(
                profdev_requested.values("profdev_requested"),
                output_field=DecimalField(),
            ),
            Decimal(0),
        ),
        admin_requested=Coalesce(
            Subquery(
                admin_requested.values("admin_requested"), output_field=DecimalField()
            ),
            Decimal(0),
        ),
        profdev_spent=Coalesce(
            Subquery(
                profdev_spent.values("profdev_spent"), output_field=DecimalField()
            ),
            Decimal(0),
        ),
        admin_spent=Coalesce(
            Subquery(admin_spent.values("admin_spent"), output_field=DecimalField()),
            Decimal(0),
        ),
    )

    return rows


def get_fund_employee_list(fund, start_date=None, end_date=None):
    start_date, end_date = check_dates(start_date, end_date)
    rows = Funding.objects.filter(fund=fund).values(eid=F("treq__traveler"))
    rows2 = ActualExpense.objects.filter(fund=fund).values(eid=F("treq__traveler"))
    return set([e["eid"] for e in rows.union(rows2)])


def get_individual_data_for_fund(employee_ids, fund, start_date=None, end_date=None):
    start_date, end_date = check_dates(start_date, end_date)

    # 4 subqueries plugged into the final query
    profdev_requested = (
        TravelRequest.objects.filter(
            traveler=OuterRef("pk"),
            administrative=False,
            departure_date__gte=start_date,
            return_date__lte=end_date,
            funding__fund=fund,
        )
        .values("traveler__pk")
        .annotate(
            profdev_requested=Sum("funding__amount", filter=Q(funding__fund=fund))
        )
        .values("profdev_requested")
    )

    profdev_spent = (
        TravelRequest.objects.filter(
            traveler=OuterRef("pk"), administrative=False, actualexpense__fund=fund
        )
        .values("traveler__pk")
        .annotate(
            profdev_spent=Sum(
                "actualexpense__total",
                filter=Q(actualexpense__fund=fund)
                & Q(actualexpense__date_paid__lte=end_date)
                & Q(actualexpense__date_paid__gte=start_date),
            )
        )
        .values("profdev_spent")
    )

    admin_requested = (
        TravelRequest.objects.filter(
            traveler=OuterRef("pk"),
            administrative=True,
            departure_date__gte=start_date,
            return_date__lte=end_date,
            funding__fund=fund,
        )
        .values("traveler__pk")
        .annotate(admin_requested=Sum("funding__amount"), filter=Q(funding__fund=fund))
        .values("admin_requested")
    )

    admin_spent = (
        TravelRequest.objects.filter(
            traveler=OuterRef("pk"), administrative=True, actualexpense__fund=fund
        )
        .values("traveler__pk")
        .annotate(
            admin_spent=Sum(
                "actualexpense__total",
                filter=Q(actualexpense__fund=fund)
                & Q(actualexpense__date_paid__lte=end_date)
                & Q(actualexpense__date_paid__gte=start_date),
            )
        )
        .values("admin_spent")
    )

    # final query
    rows = Employee.objects.filter(pk__in=employee_ids).annotate(
        profdev_requested=Coalesce(
            Subquery(
                profdev_requested.values("profdev_requested"),
                output_field=DecimalField(),
            ),
            Decimal(0),
        ),
        profdev_spent=Coalesce(
            Subquery(
                profdev_spent.values("profdev_spent"), output_field=DecimalField()
            ),
            Decimal(0),
        ),
        admin_requested=Coalesce(
            Subquery(
                admin_requested.values("admin_requested"), output_field=DecimalField()
            ),
            Decimal(0),
        ),
        admin_spent=Coalesce(
            Subquery(admin_spent.values("admin_spent"), output_field=DecimalField()),
            Decimal(0),
        ),
    )
    return rows


def calculate_fund_totals(employees):
    totals = {
        "admin_requested": 0,
        "admin_spent": 0,
        "profdev_requested": 0,
        "profdev_spent": 0,
        "total_requested": 0,
        "total_spent": 0,
    }
    for e in employees:
        e.total_requested = e.profdev_requested + e.admin_requested
        e.total_spent = e.profdev_spent + e.admin_spent
        totals["profdev_requested"] += e.profdev_requested
        totals["profdev_spent"] += e.profdev_spent
        totals["admin_requested"] += e.admin_requested
        totals["admin_spent"] += e.admin_spent
    totals["total_requested"] = totals["admin_requested"] + totals["profdev_requested"]
    totals["total_spent"] = totals["admin_spent"] + totals["profdev_spent"]
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
        TravelRequest.objects.filter(traveler=OuterRef("pk"), administrative=False)
        .values("traveler__pk")
        .annotate(
            profdev_spent=Sum(
                "actualexpense__total",
                filter=Q(actualexpense__date_paid__lte=end_date)
                & Q(actualexpense__date_paid__gte=start_date),
            )
        )
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
        TravelRequest.objects.filter(traveler=OuterRef("pk"), administrative=True)
        .values("traveler__pk")
        .annotate(
            admin_spent=Sum(
                "actualexpense__total",
                filter=Q(actualexpense__date_paid__lte=end_date)
                & Q(actualexpense__date_paid__gte=start_date),
            )
        )
        .values("admin_spent")
    )

    days_vacation = TravelRequest.objects.filter(
        traveler=OuterRef("pk"),
        departure_date__gte=start_date,
        return_date__lte=end_date,
    ).annotate(days_vacation=Sum("vacation__duration"))

    profdev_days_away = (
        TravelRequest.objects.filter(
            traveler=OuterRef("pk"),
            departure_date__gte=start_date,
            return_date__lte=end_date,
            administrative=False,
            canceled=False,
        )
        .values("traveler_id")
        .annotate(profdev_days_away=Sum("days_ooo"))
    )
    admin_days_away = (
        TravelRequest.objects.filter(
            traveler=OuterRef("pk"),
            departure_date__gte=start_date,
            return_date__lte=end_date,
            administrative=True,
            canceled=False,
        )
        .values("traveler_id")
        .annotate(admin_days_away=Sum("days_ooo"))
    )
    # final query
    rows = (
        Employee.objects.filter(pk__in=employee_ids)
        .annotate(
            profdev_requested=Coalesce(
                Subquery(profdev_requested, output_field=DecimalField()), Decimal(0)
            ),
            profdev_spent=Coalesce(
                Subquery(profdev_spent, output_field=DecimalField()), Decimal(0)
            ),
            admin_requested=Coalesce(
                Subquery(admin_requested, output_field=DecimalField()), Decimal(0)
            ),
            admin_spent=Coalesce(
                Subquery(admin_spent, output_field=DecimalField()), Decimal(0)
            ),
            days_vacation=Coalesce(
                Subquery(
                    days_vacation.values("days_vacation")[:1],
                    output_field=IntegerField(),
                ),
                Value(0),
            ),
            profdev_days_away=Coalesce(
                Subquery(
                    profdev_days_away.values("profdev_days_away")[:1],
                    output_field=IntegerField(),
                ),
                Value(0),
            ),
            admin_days_away=Coalesce(
                Subquery(
                    admin_days_away.values("admin_days_away")[:1],
                    output_field=IntegerField(),
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
            "profdev_days_away",
            "admin_days_away",
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
                employee["admin_requested"]
                employee["profdev_requested"]
                employee["total_requested"] = (
                    employee["admin_requested"] + employee["profdev_requested"]
                )
                employee["total_spent"] = (
                    employee["admin_spent"] + employee["profdev_spent"]
                )
                employee["total_days_ooo"] = (
                    employee["profdev_days_away"] + employee["admin_days_away"]
                )

            except ObjectDoesNotExist:
                employee = {
                    "admin_requested": 0,
                    "admin_spent": 0,
                    "profdev_requested": 0,
                    "profdev_spent": 0,
                    "total_spent": 0,
                    "total_requested": 0,
                    "profdev_days_away": 0,
                    "admin_days_away": 0,
                    "days_vacation": 0,
                    "total_days_ooo": 0,
                }
            data["type"][employee_type]["employees"].append(employee)

    for employee_type in data["type"]:
        type_totals = {
            "admin_requested": 0,
            "admin_spent": 0,
            "admin_days_away": 0,
            "profdev_days_away": 0,
            "days_vacation": 0,
            "profdev_requested": 0,
            "profdev_spent": 0,
            "total_requested": 0,
            "total_days_ooo": 0,
            "total_spent": 0,
        }
        # add a totals dictionary for each employee type
        for employee in data["type"][employee_type]["employees"]:
            type_totals["admin_requested"] += employee["admin_requested"]
            type_totals["admin_spent"] += employee["admin_spent"]
            type_totals["profdev_days_away"] += employee["profdev_days_away"]
            type_totals["admin_days_away"] += employee["admin_days_away"]
            type_totals["days_vacation"] += employee["days_vacation"]
            type_totals["profdev_requested"] += employee["profdev_requested"]
            type_totals["profdev_spent"] += employee["profdev_spent"]
            type_totals["total_requested"] += employee["total_requested"]
            type_totals["total_days_ooo"] += employee["total_days_ooo"]
            type_totals["total_spent"] += employee["total_spent"]
        data["type"][employee_type]["totals"] = type_totals

    complete_total = {
        "admin_requested": 0,
        "admin_spent": 0,
        "profdev_days_away": 0,
        "admin_days_away": 0,
        "days_vacation": 0,
        "profdev_requested": 0,
        "profdev_spent": 0,
        "total_requested": 0,
        "total_days_ooo": 0,
        "total_spent": 0,
    }

    for t in data["type"]:
        complete_total["admin_requested"] += data["type"][t]["totals"][
            "admin_requested"
        ]
        complete_total["admin_spent"] += data["type"][t]["totals"]["admin_spent"]
        complete_total["profdev_days_away"] += data["type"][t]["totals"][
            "profdev_days_away"
        ]
        complete_total["admin_days_away"] += data["type"][t]["totals"][
            "admin_days_away"
        ]
        complete_total["days_vacation"] += data["type"][t]["totals"]["days_vacation"]
        complete_total["profdev_requested"] += data["type"][t]["totals"][
            "profdev_requested"
        ]
        complete_total["profdev_spent"] += data["type"][t]["totals"]["profdev_spent"]
        complete_total["total_requested"] += data["type"][t]["totals"][
            "total_requested"
        ]
        complete_total["total_days_ooo"] += data["type"][t]["totals"]["total_days_ooo"]
        complete_total["total_spent"] += data["type"][t]["totals"]["total_spent"]
    data["all_type_total"] = complete_total

    return data


def get_individual_data_employee(employee_ids, start_date=None, end_date=None):
    start_date, end_date = check_dates(start_date, end_date)

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
        TravelRequest.objects.filter(traveler=OuterRef("pk"), administrative=False)
        .values("traveler__pk")
        .annotate(
            profdev_spent=Sum(
                "actualexpense__total",
                filter=Q(actualexpense__date_paid__lte=end_date)
                & Q(actualexpense__date_paid__gte=start_date),
            )
        )
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
        TravelRequest.objects.filter(traveler=OuterRef("pk"), administrative=True)
        .values("traveler__pk")
        .annotate(
            admin_spent=Sum(
                "actualexpense__total",
                filter=Q(actualexpense__date_paid__lte=end_date)
                & Q(actualexpense__date_paid__gte=start_date),
            )
        )
        .values("admin_spent")
    )

    profdev_days_away = (
        TravelRequest.objects.filter(
            traveler=OuterRef("pk"),
            administrative=False,
            departure_date__gte=start_date,
            return_date__lte=end_date,
            canceled=False,
        )
        .values("traveler_id")
        .annotate(profdev_days_away=Sum("days_ooo"))
    )
    total_requested = (
        TravelRequest.objects.filter(
            traveler=OuterRef("pk"),
            departure_date__gte=start_date,
            return_date__lte=end_date,
        )
        .values("traveler__pk")
        .annotate(total_requested=Sum("funding__amount"))
        .values("total_requested")
    )

    total_spent = (
        TravelRequest.objects.filter(traveler=OuterRef("pk"))
        .values("traveler__pk")
        .annotate(
            total_spent=Sum(
                "actualexpense__total",
                filter=Q(actualexpense__date_paid__lte=end_date)
                & Q(actualexpense__date_paid__gte=start_date),
            )
        )
        .values("total_spent")
    )

    admin_days_away = (
        TravelRequest.objects.filter(
            traveler=OuterRef("pk"),
            departure_date__gte=start_date,
            return_date__lte=end_date,
            administrative=True,
            canceled=False,
        )
        .values("traveler_id")
        .annotate(admin_days_away=Sum("days_ooo"))
    )

    # final query

    rows = (
        Employee.objects.filter(pk__in=employee_ids)
        .annotate(
            profdev_requested=Coalesce(
                Subquery(profdev_requested, output_field=DecimalField()), Decimal(0)
            ),
            profdev_spent=Coalesce(
                Subquery(profdev_spent, output_field=DecimalField()), Decimal(0)
            ),
            admin_requested=Coalesce(
                Subquery(admin_requested, output_field=DecimalField()), Decimal(0)
            ),
            admin_spent=Coalesce(
                Subquery(admin_spent, output_field=DecimalField()), Decimal(0)
            ),
            profdev_days_away=Coalesce(
                Subquery(
                    profdev_days_away.values("profdev_days_away")[:1],
                    output_field=IntegerField(),
                ),
                Value(0),
            ),
            total_requested=Coalesce(
                Subquery(total_requested, output_field=DecimalField()), Decimal(0)
            ),
            total_spent=Coalesce(
                Subquery(total_spent, output_field=DecimalField()), Decimal(0)
            ),
            admin_days_away=Coalesce(
                Subquery(
                    admin_days_away.values("admin_days_away")[:1],
                    output_field=IntegerField(),
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
            "profdev_days_away",
            "total_requested",
            "total_spent",
            "admin_days_away",
        )
    )
    return rows


def employee_total_report(employee_ids, start_date, end_date):
    employee_totals = {}
    rows = get_individual_data_employee(employee_ids, start_date, end_date)

    for e in employee_ids:
        try:
            employee = rows.get(id=e)
            employee["total_requested"]
            employee["total_spent"]
            employee["total_days_away"] = (
                employee["profdev_days_away"] + employee["admin_days_away"]
            )
            employee["profdev_remaining"] = (
                profdev_spending_cap - employee["profdev_spent"]
            )
            employee["profdev_days_remaining"] = (
                profdev_days_cap - employee["profdev_days_away"]
            )

        except ObjectDoesNotExist:
            employee = {
                "profdev_requested": 0,
                "profdev_spent": 0,
                "admin_requested": 0,
                "admin_spent": 0,
                "total_requested": 0,
                "total_spent": 0,
                "admin_days_away": 0,
                "total_days_away": 0,
                "profdev_remaining": 0,
                "profdev_days_remaining": 0,
            }
        employee_totals[e] = employee

    return employee_totals


def get_individual_data_treq(treq_ids, start_date=None, end_date=None):
    actualexpenses_fy = (
        ActualExpense.objects.filter(treq=OuterRef("pk"))
        .values("treq_id")
        .annotate(
            actualexpenses_fy=Sum(
                "total",
                filter=Q(date_paid__lte=end_date) & Q(date_paid__gte=start_date),
            )
        )
        .values("actualexpenses_fy")
    )
    funding_fy = (
        Funding.objects.filter(treq=OuterRef("pk"))
        .values("treq_id")
        .annotate(
            funding_fy=Sum(
                "amount",
                filter=Q(treq__return_date__lte=end_date)
                & Q(treq__departure_date__gte=start_date),
            )
        )
        .values("funding_fy")
    )
    days_ooo_fy = (
        TravelRequest.objects.filter(id=OuterRef("pk"), canceled=False)
        .values("id")
        .annotate(
            days_ooo_fy=Sum(
                "days_ooo",
                filter=Q(return_date__lte=end_date) & Q(departure_date__gte=start_date),
            )
        )
        .values("days_ooo_fy")
    )

    rows = (
        TravelRequest.objects.filter(pk__in=treq_ids).annotate(
            actualexpenses_fy=Coalesce(
                Subquery(actualexpenses_fy, output_field=DecimalField()), Decimal(0)
            ),
            funding_fy=Coalesce(
                Subquery(funding_fy, output_field=DecimalField()), Decimal(0)
            ),
            days_ooo_fy=Coalesce(
                Subquery(days_ooo_fy, output_field=IntegerField()), Value(0)
            ),
        )
    ).values("id", "actualexpenses_fy", "funding_fy", "days_ooo_fy")

    return rows
