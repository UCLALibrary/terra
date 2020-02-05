from django.contrib import admin
from django.contrib.auth.admin import UserAdmin


from .models import (
    Unit,
    Employee,
    TravelRequest,
    Activity,
    Vacation,
    Fund,
    Funding,
    ActualExpense,
)


def custom_titled_filter(title):
    class Wrapper(admin.FieldListFilter):
        def __new__(cls, *args, **kwargs):
            instance = admin.FieldListFilter.create(*args, **kwargs)
            instance.title = title
            return instance

    return Wrapper


# Class to add fields to admin user creation popup form
class UserAdmin(UserAdmin):
    UserAdmin.add_fieldsets = (
        (
            None,
            {
                "fields": (
                    "first_name",
                    "last_name",
                    "email",
                    "username",
                    "password1",
                    "password2",
                )
            },
        ),
    )


# Inline class to support ManyToMany with Funding and TravelRequest
class FundingInline(admin.TabularInline):
    model = Funding
    extra = 1
    autocomplete_fields = ["funded_by", "fund"]


class ActualExpenseInline(admin.TabularInline):
    model = ActualExpense
    extra = 1
    autocomplete_fields = ["fund"]


@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ("name", "manager", "employee_count", "parent_unit")
    list_filter = (("parent_unit", custom_titled_filter("parent unit")),)
    search_fields = ["name"]
    autocomplete_fields = ["manager", "parent_unit"]


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = (
        "uid",
        "name",
        "type",
        "unit",
        "supervisor",
        "extra_allocation",
        "allocation_expire_date",
        "active",
    )
    list_display_links = ("uid", "name")
    list_filter = ("active", "type")
    search_fields = ["user__last_name", "user__first_name", "unit__name"]
    autocomplete_fields = ["supervisor", "unit", "user"]


# Functions to rename travelrequest list columns
def days_ooo(obj):
    return obj.days_ooo


days_ooo.short_description = "Days Out"


def approved_total(obj):
    return obj.approved_total()


approved_total.short_description = "Funding"


def expenditures_total(obj):
    return obj.expenditures_total()


expenditures_total.short_description = "Actual"


@admin.register(TravelRequest)
class TravelRequestAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "traveler",
        "activity",
        "departure_date",
        days_ooo,
        "administrative",
        "approved",
        "funded",
        "closed",
        approved_total,
        expenditures_total,
    )
    list_filter = (
        ("departure_date", custom_titled_filter("departure date")),
        ("return_date", custom_titled_filter("return date")),
        ("days_ooo", custom_titled_filter("days out-of-office")),
        "closed",
        "funds",
    )
    search_fields = [
        "traveler__user__last_name",
        "traveler__user__first_name",
        "activity__name",
    ]
    autocomplete_fields = ["activity", "approved_by", "traveler"]
    inlines = (FundingInline, ActualExpenseInline)


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ("name", "start", "end", "city", "state", "country")
    list_filter = (
        ("start", custom_titled_filter("start date")),
        ("end", custom_titled_filter("end date")),
        "city",
        "state",
        "country",
    )
    search_fields = ["name", "city", "state", "country"]


@admin.register(Vacation)
class VacationAdmin(admin.ModelAdmin):
    list_display = ("id", "treq", "start", "end")
    list_filter = (
        ("start", custom_titled_filter("start date")),
        ("end", custom_titled_filter("end date")),
    )
    search_fields = [
        "treq__traveler__user__last_name",
        "treq__traveler__user__first_name",
        "treq__activity__name",
    ]
    autocomplete_fields = ["treq"]


@admin.register(Fund)
class FundAdmin(admin.ModelAdmin):
    list_display = ("__str__", "manager")
    search_fields = [
        "account",
        "cost_center",
        "fund",
        "manager__user__last_name",
        "manager__user__first_name",
    ]
    autocomplete_fields = ["manager"]


@admin.register(Funding)
class FundingAdmin(admin.ModelAdmin):
    list_display = ("id", "treq", "funded_by", "funded_on", "fund", "amount")
    list_filter = (("funded_on", custom_titled_filter("funding date")),)
    search_fields = [
        "treq__traveler__user__last_name",
        "treq__traveler__user__first_name",
        "treq__activity__name",
    ]
    autocomplete_fields = ["funded_by", "fund", "treq"]


@admin.register(ActualExpense)
class ActualExpenseAdmin(admin.ModelAdmin):
    list_display = ("id", "treq", "type", "total_dollars", "date_paid")
    list_filter = ("type", ("total", custom_titled_filter("total cost")))
    search_fields = [
        "treq__traveler__user__last_name",
        "treq__traveler__user__first_name",
        "treq__activity__name",
    ]
    autocomplete_fields = ["fund", "treq"]
