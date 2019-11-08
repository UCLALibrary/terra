from django import forms
from terra.models import ActualExpense, TravelRequest


class ActualExpenseForm(forms.ModelForm):
    class Meta:
        model = ActualExpense
        fields = "__all__"


class BaseActualExpenseFormSet(forms.BaseModelFormSet):
    class Meta:
        model = ActualExpense
