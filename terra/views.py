from django.views.generic.list import ListView
from django.views.generic.list import ListView
from django.views.generic import DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .models import TravelRequest, Unit
from .reports import unit_report

from django.shortcuts import render, render_to_response
from django.views.generic import CreateView
from django.views import View
from django.http import JsonResponse
import json
import pprint
from django.views.generic.list import BaseListView
from django.contrib.admin.views.autocomplete import AutocompleteJsonView as Base

from .models import TravelRequest


class UserDashboard(LoginRequiredMixin, ListView):

    model = TravelRequest
    context_object_name = "treqs"
    login_url = "/accounts/login/"
    redirect_field_name = "next"

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(traveler__user=self.request.user)

class UnitDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):

    model = Unit
    context_object_name = "unit"
    login_url = "/accounts/login/"
    redirect_field_name = "next"

    def test_func(self):
        if self.request.user.is_superuser:
            return True
        unit = self.get_object()
        return self.request.user.employee in unit.super_managers()

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["report"] = unit_report(self.object)
        return context


class UnitListView(LoginRequiredMixin, UserPassesTestMixin, ListView):

    model = Unit
    context_object_name = "units"
    login_url = "/accounts/login/"
    redirect_field_name = "next"

    def test_func(self):
        return (
            self.request.user.is_superuser
            or len(self.request.user.employee.managed_units.all()) > 0
        )

    def get_queryset(self):
        if self.request.user.is_superuser:
            return Unit.objects.filter(type="1")
        return Unit.objects.filter(manager=self.request.user.employee)

class AutocompleteJsonView(Base):
    """Overriding django admin's AutocompleteJsonView"""

    def get(self, request, *args, **kwargs):
        self.term = request.GET.get('term', '')
        self.paginator_class = self.model_admin.paginator
        self.object_list = self.get_queryset()
        context = self.get_context_data()
        return JsonResponse({
            'results': [
                {'id': str(obj.pk), 'text': str(obj)}
                for obj in context['object_list']
            ],
            'pagination': {'more': context['page_obj'].has_next()},
        })
        
class UnitManagerView(AutocompleteJsonView):
    def get_queryset(self):
        queryset = Employee.objects.all().order_by('name')
        return queryset