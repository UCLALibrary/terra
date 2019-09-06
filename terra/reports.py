from django.db.models import F, Q, Sum, Value
from django.db.models.functions import Concat

from .models import TravelRequest
from .utils import fiscal_year_bookends


def subunit_lookup(uid, subunits):
    for subunit_name, staff in subunits.items():
        for employee in staff:
            if employee.uid == uid:
                return subunit_name


def unit_totals(data):
    return {
        "profdev_alloc": sum(
            x["profdev_alloc"] for x in data if x["profdev_alloc"] is not None
        ),
        "admin_alloc": sum(
            x["admin_alloc"] for x in data if x["admin_alloc"] is not None
        ),
        "total_alloc": sum(
            x["total_alloc"] for x in data if x["total_alloc"] is not None
        ),
        "profdev_expend": sum(
            x["profdev_expend"] for x in data if x["profdev_expend"] is not None
        ),
        "admin_expend": sum(
            x["admin_expend"] for x in data if x["admin_expend"] is not None
        ),
        "total_expend": sum(
            x["total_expend"] for x in data if x["total_expend"] is not None
        ),
    }


def unit_report(unit, start_date=None, end_date=None):
    if start_date is None and end_date is None:
        start_date, end_date = fiscal_year_bookends()
    elif start_date is None or end_date is None:
        raise Exception("You must include a start and end date or leave both empty")
    elif end_date < start_date:
        raise Exception("Start date must come before end date")
    subunits = unit.sub_teams()
    full_team = []
    for s in subunits:
        full_team.extend(subunits[s])
    staff_totals = (
        TravelRequest.objects.filter(
            traveler__in=full_team,
            departure_date__gte=start_date,
            return_date__lte=end_date,
            approval__type="F",
        )
        .values("traveler__uid")
        .annotate(
            admin_alloc=Sum("estimatedexpense__total", filter=Q(administrative=True))
        )
        .annotate(
            profdev_alloc=Sum("estimatedexpense__total", filter=Q(administrative=False))
        )
        .annotate(total_alloc=Sum("estimatedexpense__total"))
        .annotate(
            admin_expend=Sum("actualexpense__total", filter=Q(administrative=True))
        )
        .annotate(
            profdev_expend=Sum("actualexpense__total", filter=Q(administrative=False))
        )
        .annotate(total_expend=Sum("actualexpense__total"))
        .annotate(uid=F("traveler__uid"))
        .annotate(
            name=Concat(
                "traveler__user__first_name", Value(" "), "traveler__user__last_name"
            )
        )
    )
    subunits_data = {}
    for staff in staff_totals:
        subunit_name = subunit_lookup(staff["uid"], subunits)
        if subunit_name not in subunits_data.keys():
            subunits_data[subunit_name] = {"staff": [staff], "totals": None}
        else:
            subunits_data[subunit_name]["staff"].append(staff)
    for subunit_name, data in subunits_data.items():
        data["totals"] = unit_totals(data["staff"])
    output = {
        "subunits": subunits_data,
        "totals": unit_totals([s["totals"] for s in subunits_data.values()]),
    }
    return output
