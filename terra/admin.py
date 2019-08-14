from django.contrib import admin
from .models import Unit, Employee, TravelRequest, Activity, Vacation, Fund, \
	Approval, EstimatedExpense, ActualExpense


@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
	pass


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
	pass


@admin.register(TravelRequest)
class TravelRequestAdmin(admin.ModelAdmin):
	pass


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
	pass


@admin.register(Vacation)
class VacationAdmin(admin.ModelAdmin):
	pass


@admin.register(Fund)
class FundAdmin(admin.ModelAdmin):
	pass


@admin.register(Approval)
class ApprovalAdmin(admin.ModelAdmin):
	pass


@admin.register(EstimatedExpense)
class EstimatedExpenseAdmin(admin.ModelAdmin):
	pass


@admin.register(ActualExpense)
class ActualExpenseAdmin(admin.ModelAdmin):
	pass