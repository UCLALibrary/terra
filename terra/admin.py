from django.contrib import admin
from .models import (
    Unit,
    Employee,
    TravelRequest,
    Activity,
    Vacation,
    Fund,
    Approval,
    EstimatedExpense,
    ActualExpense,
)


@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ("name", "manager", "employee_count", "parent_unit")


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ("uid", "name", "unit", "supervisor", "active")
    list_display_links = ("uid", "name")


@admin.register(TravelRequest)
class TravelRequestAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "traveler",
        "activity",
        "departure_date",
        "days_ooo",
        "administrative",
        "approved",
        "funded",
        "closed",
        "allocations_total",
        "expenditures_total",
    )


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ("name", "start", "end", "city", "state", "country")


@admin.register(Vacation)
class VacationAdmin(admin.ModelAdmin):
    list_display = ("id", "treq", "start", "end")


@admin.register(Fund)
class FundAdmin(admin.ModelAdmin):
    list_display = ("__str__", "manager")


@admin.register(Approval)
class ApprovalAdmin(admin.ModelAdmin):
    list_display = ("id", "treq", "type", "approver", "timestamp")


@admin.register(EstimatedExpense)
class EstimatedExpenseAdmin(admin.ModelAdmin):
    list_display = ("id", "treq", "type", "total_dollars")


@admin.register(ActualExpense)
class ActualExpenseAdmin(admin.ModelAdmin):
    list_display = ("id", "treq", "type", "total_dollars")
