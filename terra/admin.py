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

def custom_titled_filter(title):
    class Wrapper(admin.FieldListFilter):
        def __new__(cls, *args, **kwargs):
            instance = admin.FieldListFilter.create(*args, **kwargs)
            instance.title = title
            return instance
    return Wrapper

# Inline class to support ManyToMany with Approval and TravelRequest
class ApprovalInline(admin.TabularInline):
    model = Approval
    extra = 1

@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ("name", "manager", "employee_count", "parent_unit")
    list_filter = (("parent_unit", custom_titled_filter('parent unit')),)
    search_fields = ["name"]

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ("uid", "name", "unit", "supervisor", "active")
    list_display_links = ("uid", "name")
    list_filter = ("active",)
    search_fields = ["user__last_name", "user__first_name", "unit__name"]

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
    list_filter = (("departure_date", custom_titled_filter('departure date')),("return_date", custom_titled_filter('return date')),("days_ooo", custom_titled_filter('days out-of-office')),"closed","funds",)
    search_fields = ["traveler__user__last_name", "traveler__user__first_name", "activity__name"]
    inlines = (ApprovalInline,)

@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ("name", "start", "end", "city", "state", "country")
    list_filter = (("start", custom_titled_filter('start date')),("end", custom_titled_filter('end date')),"city","state","country",)
    search_fields = ["name", "city", "state", "country"]

@admin.register(Vacation)
class VacationAdmin(admin.ModelAdmin):
    list_display = ("id", "treq", "start", "end")
    list_filter = (("start", custom_titled_filter('start date')),("end", custom_titled_filter('end date')),)
    search_fields = ["treq__traveler__user__last_name", "treq__traveler__user__first_name", "treq__activity__name"]

@admin.register(Fund)
class FundAdmin(admin.ModelAdmin):
    list_display = ("__str__", "manager")
    search_fields = ["account", "cost_center", "fund", "manager__user__last_name", "manager__user__first_name"]

@admin.register(Approval)
class ApprovalAdmin(admin.ModelAdmin):
    list_display = ("id", "treq", "approved_by", "approved_on", "fund", "amount")
    list_filter = (("approved_on", custom_titled_filter('approval date')),)
    search_fields = ["treq__traveler__user__last_name", "treq__traveler__user__first_name", "treq__activity__name"]

@admin.register(EstimatedExpense)
class EstimatedExpenseAdmin(admin.ModelAdmin):
    list_display = ("id", "treq", "type", "total_dollars")
    list_filter = ("type",("total", custom_titled_filter('total cost')),)
    search_fields = ["treq__traveler__user__last_name", "treq__traveler__user__first_name", "treq__activity__name"]

@admin.register(ActualExpense)
class ActualExpenseAdmin(admin.ModelAdmin):
    list_display = ("id", "treq", "type", "total_dollars")
    list_filter = ("type",("total", custom_titled_filter('total cost')),)
    search_fields = ["treq__traveler__user__last_name", "treq__traveler__user__first_name", "treq__activity__name"]
 
