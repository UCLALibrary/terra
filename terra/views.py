import csv
from django.http import HttpResponseRedirect, HttpResponse
from django.urls import reverse
from django.views.generic.list import ListView
from django.views.generic import View, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required

from .models import TravelRequest, Unit, Fund, Employee, ActualExpense
from .reports import (
    unit_report,
    fund_report,
    merge_data_type,
    get_type_and_employees,
    employee_total_report,
    get_subunits_and_employees,
)
from .utils import (
    current_fiscal_year_object,
    current_fiscal_year,
    fiscal_year_bookends,
    fiscal_year,
    current_fiscal_year_int,
)


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
        fy = current_fiscal_year_object()

        id_list = []
        for employee in Employee.objects.all():
            id_list.append(employee.id)
        context["report"] = employee_total_report(
            employee_ids=id_list, start_date=fy.start.date(), end_date=fy.end.date()
        )
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
        fy = fiscal_year(fiscal_year=self.kwargs["year"])
        context["fy"] = self.kwargs["year"]
        context["report"] = unit_report(
            unit=self.object, start_date=fy.start.date(), end_date=fy.end.date()
        )
        context["fiscalyear"] = "{} - {}".format(fy.start.year, fy.end.year)
        context["test"] = fy.start.date()
        return context


class UnitExportView(UnitDetailView):
    def render_to_response(self, context, **response_kwargs):
        unit = context.get("unit")
        team = unit.all_employees()
        fy = fiscal_year(fiscal_year=self.kwargs["year"])
        totals = context.get("totals")
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="{unit}_FY{fy}.csv"'
        writer = csv.writer(response)
        writer.writerow(
            [
                "Employee",
                "Type",
                "Prof Dev Requested",
                "Prof Dev Spent",
                "Prof Dev Days Out",
                "Admin Requested",
                "Admin Spent",
                "Admin Days Out",
                "Total Requested",
                "Total Spent",
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
                        employee.data["profdev_requested"],
                        employee.data["profdev_spent"],
                        employee.data["profdev_days_away"],
                        employee.data["admin_requested"],
                        employee.data["admin_spent"],
                        employee.data["admin_days_away"],
                        employee.data["total_requested"],
                        employee.data["total_spent"],
                        employee.data["total_days_ooo"],
                    ]
                )
            writer.writerow(
                [
                    "Subtotals",
                    "",
                    subunit["subunit_totals"]["profdev_requested"],
                    subunit["subunit_totals"]["profdev_spent"],
                    subunit["subunit_totals"]["profdev_days_away"],
                    subunit["subunit_totals"]["admin_requested"],
                    subunit["subunit_totals"]["admin_spent"],
                    subunit["subunit_totals"]["admin_days_away"],
                    subunit["subunit_totals"]["total_requested"],
                    subunit["subunit_totals"]["total_spent"],
                    subunit["subunit_totals"]["total_days_ooo"],
                ]
            )
        writer.writerow([])
        writer.writerow([])
        writer.writerow(
            [
                "Totals",
                "",
                context["report"]["unit_totals"]["profdev_requested"],
                context["report"]["unit_totals"]["profdev_spent"],
                context["report"]["unit_totals"]["profdev_days_away"],
                context["report"]["unit_totals"]["admin_requested"],
                context["report"]["unit_totals"]["admin_spent"],
                context["report"]["unit_totals"]["admin_days_away"],
                context["report"]["unit_totals"]["total_requested"],
                context["report"]["unit_totals"]["total_spent"],
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

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        # For now get current fiscal year
        # Override this by query params when we add historic data
        context["current_fy"] = current_fiscal_year_int()
        return context


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
                "Prof Dev Requested",
                "Prof Dev Spent",
                "Admin Requested",
                "Admin Spent",
                "Total Requested",
                "Total Spent",
            ]
        )
        for e in context["employees"]:
            writer.writerow(
                [
                    f"{e.user.last_name}, {e.user.first_name}",
                    e.get_type_display(),
                    e.profdev_requested,
                    e.profdev_spent,
                    e.admin_requested,
                    e.admin_spent,
                    e.total_requested,
                    e.total_spent,
                ]
            )
        writer.writerow(
            [
                "Totals",
                "",
                totals["profdev_requested"],
                totals["profdev_spent"],
                totals["admin_requested"],
                totals["admin_spent"],
                totals["total_requested"],
                totals["total_spent"],
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
        return (
            self.request.user.employee.has_full_report_access()
            or self.request.user.employee.is_UL()
        )

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
                "Prof Dev Requested",
                "Prof Dev Spent",
                "Prof Dev Days Out",
                "Admin Requested",
                "Admin Spent",
                "Admin Days Out",
                "Total Requested",
                "Total Spent",
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
                        employee["profdev_requested"],
                        employee["profdev_spent"],
                        employee["profdev_days_away"],
                        employee["admin_requested"],
                        employee["admin_spent"],
                        employee["admin_days_away"],
                        employee["total_requested"],
                        employee["total_spent"],
                        employee["total_days_ooo"],
                    ]
                )
            writer.writerow(
                [
                    "Subtotals",
                    "",
                    "",
                    value["totals"]["profdev_requested"],
                    value["totals"]["profdev_spent"],
                    value["totals"]["profdev_days_away"],
                    value["totals"]["admin_requested"],
                    value["totals"]["admin_spent"],
                    value["totals"]["admin_days_away"],
                    value["totals"]["total_requested"],
                    value["totals"]["total_spent"],
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
                context["merge"]["all_type_total"]["profdev_requested"],
                context["merge"]["all_type_total"]["profdev_spent"],
                context["merge"]["all_type_total"]["profdev_days_away"],
                context["merge"]["all_type_total"]["admin_requested"],
                context["merge"]["all_type_total"]["admin_spent"],
                context["merge"]["all_type_total"]["admin_days_away"],
                context["merge"]["all_type_total"]["total_requested"],
                context["merge"]["all_type_total"]["total_spent"],
                context["merge"]["all_type_total"]["total_days_ooo"],
            ]
        )
        return response


class ActualExpenseListView(LoginRequiredMixin, UserPassesTestMixin, ListView):

    model = ActualExpense
    context_object_name = "actualexpenses"
    login_url = "/accounts/login/"
    redirect_field_name = "next"

    def test_func(self):
        if self.request.user.employee.has_full_report_access():
            return True

    def get_context_data(self, *args, **kwargs):

        context = super().get_context_data(*args, **kwargs)
        context["report"] = get_subunits_and_employees(Unit.objects.get(pk=1))
        fy = current_fiscal_year_object()
        context["fiscalyear"] = fy
        context["unit_totals"] = unit_report(
            unit=(Unit.objects.get(pk=1)),
            start_date=fy.start.date(),
            end_date=fy.end.date(),
        )
        context["actualexpenses"] = ActualExpense.objects.all()
        context["a"] = current_fiscal_year_object()
        return


class ActualExpenseExportView(ActualExpenseListView):
    def render_to_response(self, context, **response_kwargs):

        response = HttpResponse(content_type="text/csv")
        response[
            "Content-Disposition"
        ] = f'attachment; filename="Actual_Expense_report.csv"'
        writer = csv.writer(response)
        writer.writerow(
            [
                "Department",
                "Employee",
                "Activity",
                "Departure Date",
                "Return Date",
                "Closed",
                "Reimbursed",
                "Fund",
                "Amount",
            ]
        )
        for v in context["report"]["subunits"].values():
            writer.writerow([])
            writer.writerow([v["subunit"]])
            for e in v["employees"].values():
                for actualexpense in context["actualexpenses"]:
                    if actualexpense.treq.traveler == e:
                        if actualexpense.in_fiscal_year:

                            writer.writerow(
                                [
                                    actualexpense.treq.traveler.unit,
                                    actualexpense.treq.traveler,
                                    actualexpense.treq.activity,
                                    actualexpense.treq.departure_date,
                                    actualexpense.treq.return_date,
                                    actualexpense.treq.closed,
                                    actualexpense.reimbursed,
                                    actualexpense.fund,
                                    actualexpense.total,
                                ]
                            )
                for subunit in context["unit_totals"]["subunits"].values():
                    for employee in subunit["employees"].values():
                        if employee == e and employee.data["total_spent"] != 0:
                            writer.writerow(
                                [
                                    f"{employee} Total",
                                    "",
                                    "",
                                    "",
                                    "",
                                    "",
                                    "",
                                    "",
                                    employee.data["total_spent"],
                                ]
                            )
                            writer.writerow([])
            for subunit in context["unit_totals"]["subunits"].values():
                if subunit["subunit"] == v["subunit"]:
                    writer.writerow(
                        [
                            "Subtotal",
                            "",
                            "",
                            "",
                            "",
                            "",
                            "",
                            "",
                            subunit["subunit_totals"]["total_spent"],
                        ]
                    )
        writer.writerow([])
        writer.writerow(
            [
                "Library Total",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                context["unit_totals"]["unit_totals"]["total_spent"],
            ]
        )

        return response
