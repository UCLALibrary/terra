import csv
from django.http import HttpResponseRedirect, HttpResponse
from django.urls import reverse
from django.views.generic.list import ListView
from django.views.generic import View, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required

from .models import TravelRequest, Unit, Fund, Employee, EMPLOYEE_TYPES
from .reports import unit_report, fund_report, merge_data_type, get_type_and_employees
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


class TreqDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):

    model = TravelRequest
    context_object_name = "treq"
    login_url = "/accounts/login/"
    redirect_field_name = "next"

    def test_func(self):
        user = self.request.user
        treq = self.get_object()
        eligible_users = [treq.traveler, treq.traveler.supervisor]
        eligible_users.extend(treq.traveler.unit.super_managers())
        return user.employee in eligible_users or user.employee.has_full_report_access()


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


class UnitExportView(UnitDetailView):
    def render_to_response(self, context, **response_kwargs):
        unit = context.get("unit")
        team = unit.all_employees()
        fy = context.get("fiscalyear", "").replace(" ", "")
        totals = context.get("totals")
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="{unit}_FY{fy}.csv"'
        writer = csv.writer(response)
        writer.writerow(
            [
                "Employee",
                "Type",
                "Prof Dev Approved",
                "Admin Approved",
                "Total Approved",
                "Prof Dev Expenditures",
                "Admin Expenditures",
                "Total Expenditures",
                "Working Days Out",
                "Vacation Days Out",
                "Total Days Out",
            ]
        )
        for subunit in context["report"]["subunits"].values():
            writer.writerow([])
            writer.writerow([subunit["subunit"]])
            for employee in subunit["employees"].values():
                writer.writerow(
                    [
                        employee,
                        employee.get_type_display(),
                        employee.data["profdev_alloc"],
                        employee.data["admin_alloc"],
                        employee.data["total_alloc"],
                        employee.data["profdev_expend"],
                        employee.data["admin_expend"],
                        employee.data["total_expend"],
                        employee.data["days_away"],
                        employee.data["days_vacation"],
                        employee.data["total_days_ooo"],
                    ]
                )
            writer.writerow(
                [
                    "Subtotals",
                    "",
                    subunit["subunit_totals"]["profdev_alloc"],
                    subunit["subunit_totals"]["admin_alloc"],
                    subunit["subunit_totals"]["total_alloc"],
                    subunit["subunit_totals"]["profdev_expend"],
                    subunit["subunit_totals"]["admin_expend"],
                    subunit["subunit_totals"]["total_expend"],
                    subunit["subunit_totals"]["days_away"],
                    subunit["subunit_totals"]["days_vacation"],
                    subunit["subunit_totals"]["total_days_ooo"],
                ]
            )
        writer.writerow([])
        writer.writerow([])
        writer.writerow(
            [
                "Totals",
                "",
                context["report"]["unit_totals"]["profdev_alloc"],
                context["report"]["unit_totals"]["admin_alloc"],
                context["report"]["unit_totals"]["total_alloc"],
                context["report"]["unit_totals"]["profdev_expend"],
                context["report"]["unit_totals"]["admin_expend"],
                context["report"]["unit_totals"]["total_expend"],
                context["report"]["unit_totals"]["days_away"],
                context["report"]["unit_totals"]["days_vacation"],
                context["report"]["unit_totals"]["total_days_ooo"],
            ]
        )
        return response


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


class FundExportView(FundDetailView):
    def render_to_response(self, context, **response_kwargs):
        fund = context.get("fund")
        fy = context.get("fiscalyear", "").replace(" ", "")
        totals = context.get("totals")
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="{fund}_FY{fy}.csv"'
        writer = csv.writer(response)
        writer.writerow(
            [
                "Employee",
                "Type",
                "Prof Dev Approved",
                "Admin Approved",
                "Total Approved",
                "Prof Dev Expenditures",
                "Admin Expenditures",
                "Total Expenditures",
            ]
        )
        for e in context["employees"]:
            writer.writerow(
                [
                    f"{e.user.last_name}, {e.user.first_name}",
                    e.get_type_display(),
                    e.profdev_alloc,
                    e.admin_alloc,
                    e.total_alloc,
                    e.profdev_expend,
                    e.admin_expend,
                    e.total_expend,
                ]
            )
        writer.writerow(
            [
                "Totals",
                "",
                totals["profdev_alloc"],
                totals["admin_alloc"],
                totals["total_alloc"],
                totals["profdev_expend"],
                totals["admin_expend"],
                totals["total_expend"],
            ]
        )
        return response


class FundListView(LoginRequiredMixin, UserPassesTestMixin, ListView):

    model = Fund
    context_object_name = "funds"
    login_url = "/accounts/login/"
    redirect_field_name = "next"

    def test_func(self):
        return self.request.user.employee.has_full_report_access()

    def get_queryset(self):
        if self.request.user.employee.has_full_report_access():
            funds = Fund.objects.all()
        else:
            funds = Fund.objects.filter(manager=self.request.user.employee)
        return funds.order_by("unit__name", "account", "cost_center", "fund")


class EmployeeTypeListView(LoginRequiredMixin, UserPassesTestMixin, ListView):

    model = Employee
    context_object_name = "employees"
    login_url = "/accounts/login/"
    redirect_field_name = "next"
    template_name = "terra/employee_type_list.html"

    def test_func(self):
        return self.request.user.employee.has_full_report_access()

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        # For now get current fiscal year
        # Override this by query params when we add historic data
        fy = current_fiscal_year_object()
        id_list = []
        for employee in Employee.objects.all():
            id_list.append(employee.id)
        context["merge"] = merge_data_type(
            employee_ids=id_list, start_date=fy.start.date(), end_date=fy.end.date()
        )
        context["fiscalyear"] = "{} - {}".format(fy.start.year, fy.end.year)
        return context


class EmployeeTypeExportView(EmployeeTypeListView):
    def render_to_response(self, context, **response_kwargs):
        fy = context.get("fiscalyear", "").replace(" ", "")
        response = HttpResponse(content_type="text/csv")
        response[
            "Content-Disposition"
        ] = f'attachment; filename="Employee_Type_FY{fy}.csv"'
        writer = csv.writer(response)
        writer.writerow(
            [
                "Unit",
                "Unit Manager",
                "Employee",
                "Prof Dev Approved",
                "Admin Approved",
                "Total Approved",
                "Prof Dev Expenditures",
                "Admin Expenditures",
                "Total Expenditures",
                "Working Days Out",
                "Vacation Days Out",
                "Total Days Out",
            ]
        )
        for key, value in context["merge"]["type"].items():
            writer.writerow([])
            writer.writerow([key])
            for employee in value["employees"]:
                writer.writerow(
                    [
                        employee["unit"],
                        employee["unit_manager"],
                        employee["name"],
                        employee["profdev_alloc"],
                        employee["admin_alloc"],
                        employee["total_alloc"],
                        employee["profdev_expend"],
                        employee["admin_expend"],
                        employee["total_expend"],
                        employee["days_away"],
                        employee["days_vacation"],
                        employee["total_days_ooo"],
                    ]
                )
            writer.writerow(
                [
                    "Subtotals",
                    "",
                    "",
                    value["totals"]["profdev_alloc"],
                    value["totals"]["admin_alloc"],
                    value["totals"]["total_alloc"],
                    value["totals"]["profdev_expend"],
                    value["totals"]["admin_expend"],
                    value["totals"]["total_expend"],
                    value["totals"]["days_away"],
                    value["totals"]["days_vacation"],
                    value["totals"]["total_days_ooo"],
                ]
            )
        writer.writerow([])
        writer.writerow([])
        writer.writerow(
            [
                "Totals",
                "",
                "",
                context["merge"]["all_type_total"]["profdev_alloc"],
                context["merge"]["all_type_total"]["admin_alloc"],
                context["merge"]["all_type_total"]["total_alloc"],
                context["merge"]["all_type_total"]["profdev_expend"],
                context["merge"]["all_type_total"]["admin_expend"],
                context["merge"]["all_type_total"]["total_expend"],
                context["merge"]["all_type_total"]["days_away"],
                context["merge"]["all_type_total"]["days_vacation"],
                context["merge"]["all_type_total"]["total_days_ooo"],
            ]
        )
        return response
