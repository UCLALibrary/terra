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
    list_filter = ("name","manager","parent_unit")

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
        "approved",
        "funded",
        "closed",
    )
    list_filter = ("traveler","activity","departure_date","return_date","days_ooo","closed","funding",)

@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ("name", "start", "end", "city", "state", "country")
    list_filter = ("name","start","end","city","state","country",)

@admin.register(Vacation)
class VacationAdmin(admin.ModelAdmin):
    list_display = ("id", "treq", "start", "end")
    list_filter = ("treq","start","end",)

@admin.register(Fund)
class FundAdmin(admin.ModelAdmin):
    list_display = ("__str__", "manager")
    list_filter = ("account","cost_center","fund","manager",)

@admin.register(Approval)
class ApprovalAdmin(admin.ModelAdmin):
    list_display = ("id", "treq", "type", "approver", "timestamp")
    list_filter = ("timestamp","approver","treq","type",)

@admin.register(EstimatedExpense)
class EstimatedExpenseAdmin(admin.ModelAdmin):
    list_display = ("id", "treq", "type", "total_dollars")
    list_filter = ("treq","type","total",)

@admin.register(ActualExpense)
class ActualExpenseAdmin(admin.ModelAdmin):
    list_display = ("id", "treq", "type", "total_dollars")
    list_filter = ("treq","type","total","fund",)
    
