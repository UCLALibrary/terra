from django.views.generic.list import ListView
from django.contrib.auth.mixins import LoginRequiredMixin

from .models import TravelRequest, Employee
from .utils import allocations_and_expenditures


class UserDashboard(LoginRequiredMixin, ListView):

    model = TravelRequest
    context_object_name = "treqs"
    login_url = "/accounts/login/"
    redirect_field_name = "next"

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(traveler__user=self.request.user)


class ManagerReports(LoginRequiredMixin, ListView):

    model = TravelRequest
    context_object_name = "treqs"
    login_url = "/accounts/login/"
    redirect_field_name = "next"

    def get_queryset(self):
        staff, mgrs = self.request.user.employee.full_team()
        return TravelRequest.objects.filter(traveler__in=staff)

    def get_context_data(self):
        context = super().get_context_data()
        context["treqs"] = [t for t in context["treqs"] if t.in_fiscal_year()]
        context["funded"] = [t for t in context["treqs"] if t.funded()]
        context["unfunded"] = [t for t in context["treqs"] if not t.funded()]
        context.update(allocations_and_expenditures(context["funded"]))
        return context
