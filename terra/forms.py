from django import forms
from terra.models import ActualExpense, TravelRequest

from django.forms.widgets import Textarea, Input


class ActualExpenseForm(forms.ModelForm):
    class Meta:
        model = ActualExpense
        fields = ("treq", "type", "rate", "quantity", "total", "fund")
        # widgets={"treq": Textarea(attrs={'hidden':'hidden'})}


class BaseActualExpenseFormSet(forms.BaseModelFormSet):
    class Meta:
        model = ActualExpense

    def __init__(self, treq_id, *args, **kwargs):
        self.queryset = ActualExpense.objects.filter(treq=treq_id)
        super().__init__(*args, **kwargs)
        self.can_delete = True
