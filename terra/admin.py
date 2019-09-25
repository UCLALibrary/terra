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
from .filters import (
   custom_titled_filter,
   InputFilter,
   UIDFilter,
   EmpLastNameFilter,
   UnitFilter,
   SupervisorFilter,
   ActivityNameFilter,
   ActivityCityFilter,
   ActivityStateFilter,
   ActivityCountryFilter,
   TreqEmpLastNameFilter,
   TreqActivityNameFilter,
   FundManagerFilter,
   FundFilter,
   AccountFilter,
   CostCenterFilter,
   ApproverNameFilter,
   UnitManagerFilter,
)

@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ("name", "manager", "employee_count", "parent_unit")
    list_filter = ("name",UnitManagerFilter,("parent_unit", custom_titled_filter('parent unit')),) #"manager"
    search_fields = ['name','parent_unit__name']
    #autocomplete_fields = ['manager','parent_unit']
    def get_ordering(self, request):
        return ['name']
    class Media:
        pass;

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ("uid", "name", "unit", "supervisor", "active")
    list_display_links = ("uid", "name")
    list_filter = (EmpLastNameFilter,UnitFilter,"active",UIDFilter,SupervisorFilter,) #"unit" "user" "uid" "supervisor"
    search_fields = ['user__last_name__startswith','supervisor__user__last_name__startswith','unit__name']
    autocomplete_fields = ['unit','supervisor']
    sortable_by = ("uid", "name", "unit", "supervisor", "active")
    class Media:
        pass;

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
    list_filter = (TreqEmpLastNameFilter,TreqActivityNameFilter,("departure_date", custom_titled_filter('Departure Date')),("return_date", custom_titled_filter('Return Date')),("days_ooo", custom_titled_filter('Days Out-of-Office')),"closed","funding",) # "traveler" "activity"
    autocomplete_fields = ['funding']


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ("name", "start", "end", "city", "state", "country")
    list_filter = (ActivityNameFilter,("start", custom_titled_filter('Start Date')),("end", custom_titled_filter('End Date')),ActivityCityFilter,ActivityStateFilter,ActivityCountryFilter,) #"name" "city" "state" "country"


@admin.register(Vacation)
class VacationAdmin(admin.ModelAdmin):
    list_display = ("id", "treq", "start", "end")
    list_filter = (TreqEmpLastNameFilter,TreqActivityNameFilter,("start", custom_titled_filter('Start Date')),("end", custom_titled_filter('End Date')),) #"treq__traveler" ("treq__activity__name", custom_titled_filter('activity'))


@admin.register(Fund)
class FundAdmin(admin.ModelAdmin):
    list_display = ("__str__", "manager")
    list_filter = (AccountFilter,CostCenterFilter,FundFilter,FundManagerFilter,) # "manager" "fund" "account" ("cost_center", custom_titled_filter('Cost Center'))
    search_fields = ['fund']


@admin.register(Approval)
class ApprovalAdmin(admin.ModelAdmin):
    list_display = ("id", "treq", "type", "approver", "timestamp")
    list_filter = (("timestamp", custom_titled_filter('Approval Date')),ApproverNameFilter,TreqEmpLastNameFilter,TreqActivityNameFilter,"type",) # "treq__traveler" ("treq__activity__name", custom_titled_filter('activity')) "approver"


@admin.register(EstimatedExpense)
class EstimatedExpenseAdmin(admin.ModelAdmin):
    list_display = ("id", "treq", "type", "total_dollars")
    list_filter = (TreqEmpLastNameFilter,TreqActivityNameFilter,"type",("total", custom_titled_filter('Total Cost')),) # "treq__traveler" ("treq__activity__name", custom_titled_filter('activity'))


@admin.register(ActualExpense)
class ActualExpenseAdmin(admin.ModelAdmin):
    list_display = ("id", "treq", "type", "total_dollars")
    list_filter = (TreqEmpLastNameFilter,TreqActivityNameFilter,"type",("total", custom_titled_filter('Total Cost')),"fund",) # "treq__traveler" ("treq__activity__name", custom_titled_filter('activity')) 
    autocomplete_fields = ['fund']
 
