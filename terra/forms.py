from django import forms
from terra.models import ActualExpense, TravelRequest


class ActualExpenseForm(forms.ModelForm):
    class Meta:
        model = ActualExpense
        fields = ["treq", "type", "rate", "quantity", "total", "fund"]


"""
    def __init__(ActualExpense, *args, **kwargs):
        super(ActualExpenseForm, self).__init__(*args, **kwargs)
        ActualExpenseForm.fields["treq"].queryset = ActualExpense.treq.objects.filter(pk=5)

"""


class BaseActualExpenseFormSet(forms.BaseModelFormSet):
    class Meta:
        model = ActualExpense

    def __init__(self, treq_id, *args, **kwargs):
        self.queryset = ActualExpense.objects.filter(treq=treq_id)
        super().__init__(*args, **kwargs)
