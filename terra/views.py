from django.shortcuts import render
from django.http import HttpResponse

from .models import (
    Unit,
    Employee,
    TravelRequest,
    Fund,
    Vacation,
    Activity,
    Approval,
    EstimatedExpense,
    ActualExpense,
)


def individual_dashboard(request):

    traveler_filter = TravelRequest.objects.filter(traveler__user=request.user)

    return render(
        request, "terra/individual_dashboard.html", {"filter_travel": traveler_filter}
    )
