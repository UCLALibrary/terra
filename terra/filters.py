from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.shortcuts import redirect
from .autocomplete import (
    AutocompleteSelect,
    AutocompleteFilter,
)
#from admin_auto_filters.filters import AutocompleteFilter

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

class EmpLastNameFilter(InputFilter):
    parameter_name = 'user__last_name'
    title = _('Library Employee Last Name')

    def queryset(self, request, queryset):
        if self.value() is not None:
            user = self.value()

            return queryset.filter(
                user__last_name=user 
            )

class ApproverNameFilter(InputFilter):
    parameter_name = 'approver__user__last_name'
    title = _('Approver Last Name')

    def queryset(self, request, queryset):
        if self.value() is not None:
            user = self.value()

            return queryset.filter(
                approver__user__last_name=user 
            )

class FundManagerFilter(InputFilter):
    parameter_name = 'manager__user__last_name'
    title = _('Fund Manager Last Name')

    def queryset(self, request, queryset):
        if self.value() is not None:
            user = self.value()

            return queryset.filter(
                manager__user__last_name=user 
            )

class FundFilter(InputFilter):
    parameter_name = 'fund'
    title = _('Fund')

    def queryset(self, request, queryset):
        if self.value() is not None:
            fund = self.value()

            return queryset.filter(
                fund=fund 
            )

class CostCenterFilter(InputFilter):
    parameter_name = 'cost_center'
    title = _('Cost Center')

    def queryset(self, request, queryset):
        if self.value() is not None:
            cost_center = self.value()

            return queryset.filter(
                cost_center=cost_center 
            )

class AccountFilter(InputFilter):
    parameter_name = 'account'
    title = _('Account')

    def queryset(self, request, queryset):
        if self.value() is not None:
            account = self.value()

            return queryset.filter(
                account=account 
            )

class TreqEmpLastNameFilter(InputFilter):
    parameter_name = 'treq__traveler__user__last_name'
    title = _('Traveler Last Name')

    def queryset(self, request, queryset):
        if self.value() is not None:
            user = self.value()

            return queryset.filter(
                treq__traveler__user__last_name=user 
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
            
class SupervisorFilter(InputFilter):
    parameter_name = 'supervisor__user__last_name'
    title = _('Supervisor''s Last Name')

    def queryset(self, request, queryset):
        if self.value() is not None:
            user = self.value()

            return queryset.filter(
                supervisor__user__last_name=user 
            )
            
class ActivityNameFilter(InputFilter):
    parameter_name = 'name'
    title = _('Name of Activity')

    def queryset(self, request, queryset):
        if self.value() is not None:
            name = self.value()

            return queryset.filter(
                name=name
            )
            
class TreqActivityNameFilter(InputFilter):
    parameter_name = 'treq__activity__name'
    title = _('Name of Activity')

    def queryset(self, request, queryset):
        if self.value() is not None:
            name = self.value()

            return queryset.filter(
                treq__activity__name=name
            )
            
class ActivityCityFilter(InputFilter):
    parameter_name = 'city'
    title = _('City')

    def queryset(self, request, queryset):
        if self.value() is not None:
            city = self.value()

            return queryset.filter(
                city=city
            )
            
class ActivityStateFilter(InputFilter):
    parameter_name = 'state'
    title = _('State')

    def queryset(self, request, queryset):
        if self.value() is not None:
            state = self.value()

            return queryset.filter(
                state=state
            )
            
class ActivityCountryFilter(InputFilter):
    parameter_name = 'country'
    title = _('Country')

    def queryset(self, request, queryset):
        if self.value() is not None:
            country = self.value()

            return queryset.filter(
                country=country
            )
            
class UnitManagerFilter(AutocompleteFilter):
    title = 'Manager' # display title
    field_name = 'manager' # name of the foreign key field
