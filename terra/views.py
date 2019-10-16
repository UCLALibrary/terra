from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views.generic.list import ListView
from django.views.generic import DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required

from .models import TravelRequest, Unit, Fund, Employee
from .reports import unit_report, fund_report
from .utils import current_fiscal_year_object, current_fiscal_year


@login_required
def home(request):
    return HttpResponseRedirect(
        reverse("employee_detail", kwargs={"pk": request.user.employee.pk})
    )


class EmployeeDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):

    model = Employee
    context_object_name = "employee"
    login_url = "/accounts/login/"
    redirect_field_name = "next"

    def test_func(self):
        user = self.request.user
        employee = self.get_object()
        eligible_users = [employee, employee.supervisor]
        eligible_users.extend(employee.unit.super_managers())
        return user.employee in eligible_users or user.employee.has_full_report_access()

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["fiscal_year"] = current_fiscal_year()
        return context


class UnitDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):

    model = Unit
    context_object_name = "unit"
    login_url = "/accounts/login/"
    redirect_field_name = "next"

    def test_func(self):
        if self.request.user.employee.has_full_report_access():
            return True
        unit = self.get_object()
        return self.request.user.employee in unit.super_managers()

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        # For now get current fiscal year
        # Override this by query params when we add historic data
        fy = current_fiscal_year_object()
        context["report"] = unit_report(
            unit=self.object, start_date=fy.start.date(), end_date=fy.end.date()
        )
        context["fiscalyear"] = "{} - {}".format(fy.start.year, fy.end.year)
        return context


class UnitListView(LoginRequiredMixin, UserPassesTestMixin, ListView):

    model = Unit
    context_object_name = "units"
    login_url = "/accounts/login/"
    redirect_field_name = "next"

    def test_func(self):
        return (
            self.request.user.employee.has_full_report_access()
            or self.request.user.employee.is_unit_manager()
        )

    def get_queryset(self):
        if self.request.user.employee.has_full_report_access():
            return Unit.objects.filter(type="1")
        return Unit.objects.filter(manager=self.request.user.employee)


class FundDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):

    model = Fund
    context_object_name = "fund"
    login_url = "/accounts/login/"
    redirect_field_name = "next"

    def test_func(self):
        if self.request.user.employee.has_full_report_access():
            return True
        fund = self.get_object()
        return self.request.user.employee in fund.super_managers()

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        # For now get current fiscal year
        # Override this by query params when we add historic data
        fy = current_fiscal_year_object()
        context["employees"], context["totals"] = fund_report(
            fund=self.object, start_date=fy.start.date(), end_date=fy.end.date()
        )
        context["fiscalyear"] = "{} - {}".format(fy.start.year, fy.end.year)
        return context


class FundListView(LoginRequiredMixin, UserPassesTestMixin, ListView):

    model = Fund
    context_object_name = "funds"
    login_url = "/accounts/login/"
    redirect_field_name = "next"

    def test_func(self):
        return (
            self.request.user.employee.has_full_report_access()
            or self.request.user.employee.is_fund_manager()
        )

    def get_queryset(self):
        if self.request.user.employee.has_full_report_access():
            return Fund.objects.all()
        return Fund.objects.filter(manager=self.request.user.employee)
