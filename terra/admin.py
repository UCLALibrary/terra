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
    list_filter = ("name","manager",("parent_unit", custom_titled_filter('parent unit')),)

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ("uid", "name", "unit", "supervisor", "active")
    list_display_links = ("uid", "name")
    list_filter = ("user","unit","active","uid","supervisor",)

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
    list_filter = ("traveler","activity",("departure_date", custom_titled_filter('departure date')),("return_date", custom_titled_filter('return date')),("days_ooo", custom_titled_filter('days out-of-office')),"closed","funds",)
    inlines = (ApprovalInline,)

@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ("name", "start", "end", "city", "state", "country")
    list_filter = ("name",("start", custom_titled_filter('start date')),("end", custom_titled_filter('end date')),"city","state","country",)

@admin.register(Vacation)
class VacationAdmin(admin.ModelAdmin):
    list_display = ("id", "treq", "start", "end")
    list_filter = ("treq__traveler",("treq__activity__name", custom_titled_filter('activity')),("start", custom_titled_filter('start date')),("end", custom_titled_filter('end date')),)

@admin.register(Fund)
class FundAdmin(admin.ModelAdmin):
    list_display = ("__str__", "manager")
    list_filter = ("account",("cost_center", custom_titled_filter('cost center')),"fund","manager",)

@admin.register(Approval)
class ApprovalAdmin(admin.ModelAdmin):
    list_display = ("id", "treq", "approved_by", "approved_on", "fund", "amount")
    list_filter = (("approved_on", custom_titled_filter('approval date')),"approved_by","treq__traveler",("treq__activity__name", custom_titled_filter('activity')),)

@admin.register(EstimatedExpense)
class EstimatedExpenseAdmin(admin.ModelAdmin):
    list_display = ("id", "treq", "type", "total_dollars")
    list_filter = ("treq__traveler",("treq__activity__name", custom_titled_filter('activity')),"type",("total", custom_titled_filter('total cost')),)

@admin.register(ActualExpense)
class ActualExpenseAdmin(admin.ModelAdmin):
    list_display = ("id", "treq", "type", "total_dollars")
    list_filter = ("treq__traveler",("treq__activity__name", custom_titled_filter('activity')),"type",("total", custom_titled_filter('total cost')),"fund",)
 
