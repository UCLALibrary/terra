from django import forms
from terra.models import ActualExpense, TravelRequest


class ActualExpenseForm(forms.ModelForm):
    class Meta:
        model = ActualExpense
        fields = "__all__"


class BaseActualExpenseFormSet(forms.BaseModelFormSet):
    class Meta:
        model = ActualExpense

    def __init__(self, treq_id, *args, **kwargs):
        self.queryset = ActualExpense.objects.filter(treq=treq_id)
        super().__init__(*args, **kwargs)
        self.can_delete = True
