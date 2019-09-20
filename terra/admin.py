from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from admin_auto_filters.filters import AutocompleteFilter
from django import forms
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

class InputFilter(admin.SimpleListFilter):
    template = 'terra/admin_filter.html'

    def lookups(self, request, model_admin):
        # Dummy, required to show the filter.
        return ((),)

    def choices(self, changelist):
        # Grab only the "all" option.
        all_choice = next(super().choices(changelist))
        all_choice['query_parts'] = (
            (k, v)
            for k, v in changelist.get_filters_params().items()
            if k != self.parameter_name
        )
        yield all_choice

class UIDFilter(InputFilter):
    parameter_name = 'uid'
    title = _('University ID')

    def queryset(self, request, queryset):
        if self.value() is not None:
            uid = self.value()

            return queryset.filter(
                uid=uid
            )


class UserFilter(InputFilter):
    parameter_name = 'user__last_name'
    title = _('Library Employee')

    def queryset(self, request, queryset):
        if self.value() is not None:
            user = self.value()

            return queryset.filter(
                user__last_name=user 
            )

class UnitFilter(InputFilter):
    parameter_name = 'unit__name'
    title = _('Library Unit')

    def queryset(self, request, queryset):
        if self.value() is not None:
            unit = self.value()

            return queryset.filter(
                unit__name=unit 
            )
            
class UnitManagerFilter(AutocompleteFilter):
    title = 'Manager' # display title
    field_name = 'manager' # name of the foreign key field

class EmployeeSupervisorFilter(AutocompleteFilter):
    title = 'Supervisor' # display title
    field_name = 'supervisor' # name of the foreign key field

class EmployeeUnitFilter(AutocompleteFilter):
    title = 'Unit' # display title
    field_name = 'unit' # name of the foreign key field

class UnitParentFilter(AutocompleteFilter):
    title = 'Parent Unit' # display title
    field_name = 'parent_unit' # name of the foreign key field

@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ("name", "manager", "employee_count", "parent_unit")
    list_filter = ("name",UnitManagerFilter,UnitParentFilter,) #"manager" ("parent_unit", custom_titled_filter('parent unit'))
    search_fields = ['parent_unit__name']
    autocomplete_fields = ['manager','parent_unit']
    class Media: 
        css = {}
        js = ()

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ("uid", "name", "unit", "supervisor", "active")
    list_display_links = ("uid", "name")
    sortable_by = ("uid", "user.get_full_name()", "unit", "supervisor", "active")
    list_filter = (UserFilter,EmployeeUnitFilter,"active",UIDFilter,EmployeeSupervisorFilter,) #"uid" "unit" ("user",custom_titled_filter('employee')) UnitFilter "supervisor"
    search_fields = ['user__last_name','supervisor__user__last_name__startswith','unit__name'] # this is required for django's autocomplete functionality ,'uid'
    autocomplete_fields = ['supervisor','unit']
    def get_search_results(self, request, queryset, search_term):
        queryset, use_distinct = super().get_search_results(request, queryset, search_term)
    
        if request.path == '/admin/terra/unit/autocomplete/':
            queryset = queryset.filter(supervisor__user__last_name=search_term)
    
        return queryset, use_distinct
    class Media: 
        css = {}
        js = ()


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
    list_filter = ("traveler","activity",("departure_date", custom_titled_filter('departure date')),("return_date", custom_titled_filter('return date')),("days_ooo", custom_titled_filter('days out-of-office')),"closed","funding",)

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
    list_display = ("id", "treq", "type", "approver", "timestamp")
    list_filter = (("timestamp", custom_titled_filter('approval date')),"approver","treq__traveler",("treq__activity__name", custom_titled_filter('activity')),"type",)

@admin.register(EstimatedExpense)
class EstimatedExpenseAdmin(admin.ModelAdmin):
    list_display = ("id", "treq", "type", "total_dollars")
    list_filter = ("treq__traveler",("treq__activity__name", custom_titled_filter('activity')),"type",("total", custom_titled_filter('total cost')),)

@admin.register(ActualExpense)
class ActualExpenseAdmin(admin.ModelAdmin):
    list_display = ("id", "treq", "type", "total_dollars")
    list_filter = ("treq__traveler",("treq__activity__name", custom_titled_filter('activity')),"type",("total", custom_titled_filter('total cost')),"fund",)
 
