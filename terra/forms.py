from django import forms
from terra.models import ActualExpense


class ActualExpenseForm(forms.ModelForm):
    class Meta:
        model = ActualExpense
        fields = ["treq", "type", "rate", "quantity", "total", "fund"]
