from django.views.generic.list import ListView
from django.views.generic import DetailView
from django.contrib.auth.mixins import LoginRequiredMixin

from .models import TravelRequest, Unit
from .utils import allocations_and_expenditures


class UserDashboard(LoginRequiredMixin, ListView):

    model = TravelRequest
    context_object_name = "treqs"
    login_url = "/accounts/login/"
    redirect_field_name = "next"

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(traveler__user=self.request.user)


class UnitDetailView(LoginRequiredMixin, DetailView):

    model = Unit
    context_object_name = "unit"
    login_url = "/accounts/login/"
    redirect_field_name = "next"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["report"] = self.object.report()
        from pprint import pprint

        pprint(context)
        return context
